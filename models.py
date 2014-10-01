import datetime
from logging import getLogger
import json

from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.contrib.gis.db import models
from django.utils.timezone import utc
from mezzanine.pages.models import Page
from mezzanine.core.models import RichText
from mezzanine.conf import settings as s
from timedelta.fields import TimedeltaField
import sh
import os
from osgeo import osr
import importlib

_log = getLogger('ga_resources')

def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    :param request:
    :return: django.contrib.auth.User
    """
    if isinstance(request, User):
        return request

    from tastypie.models import ApiKey
    if isinstance(request, basestring):
        try:
            return User.objects.get(username=request)
        except:
            return User.objects.get(email=request)
    elif isinstance(request, int):
        return User.objects.get(pk=request)

    elif 'api_key' in request.REQUEST:
        api_key = ApiKey.objects.get(key=request.REQUEST['api_key'])
        return api_key.user
    elif request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user


class PagePermissionsMixin(models.Model):
    owner = models.ForeignKey(User, related_name='owned_%(app_label)s_%(class)s', null=True)
    public = models.BooleanField(default=True)
    edit_users = models.ManyToManyField(User, related_name='editable_%(app_label)s_%(class)s', null=True, blank=True)
    view_users = models.ManyToManyField(User, related_name='viewable_%(app_label)s_%(class)s', null=True, blank=True)
    edit_groups = models.ManyToManyField(Group, related_name='group_editable_%(app_label)s_%(class)s', null=True, blank=True)
    view_groups = models.ManyToManyField(Group, related_name='group_viewable_%(app_label)s_%(class)s', null=True, blank=True)

    def can_add(self, request):
        return self.can_change(request)

    def can_delete(self, request):
        return self.can_change(request)

    def can_change(self, request):
        user = get_user(request)

        if user.is_authenticated():
            if user.is_superuser:
                ret = True
            elif user.pk == self.owner.pk:
                ret = True
            else:
                if self.edit_users.filter(pk=user.pk).exists():
                    ret = True
                elif self.edit_groups.filter(pk__in=[g.pk for g in user.groups.all()]):
                    ret = True
                else:
                    ret =  False
        else:
            ret = False

        return ret

    def can_view(self, request):
        user = get_user(request)

        if self.public or not self.owner:
            return True

        if user.is_authenticated():
            if user.is_superuser:
                ret = True
            elif user.pk == self.owner.pk:
                ret = True
            else:
                if self.view_users.filter(pk=user.pk).exists():
                    ret = True
                elif self.view_groups.filter(pk__in=[g.pk for g in user.groups.all()]):
                    ret = True
                else:
                    ret = False
        else:
            ret = False

        return ret

    def copy_permissions_to_children(self, recurse=False):
        # pedantically implemented.  should use set logic to minimize changes, but ptobably not important
        for child in self.children.all():
            if isinstance(child, PagePermissionsMixin):
                child.edit_users = [u for u in self.edit_users.all()]
                child.view_users = [u for u in self.view_users.all()]
                child.edit_groups = [g for g in self.edit_groups.all()]
                child.view_groups = [g for g in self.view_groups.all()]
                child.publicly_viewable = self.publicly_viewable
                child.owner = self.owner
                child.save()
                    
                if recurse:
                    child.copy_permissions_to_children(recurse=True)


    def copy_permissions_from_parent(self):
        if self.parent:
            parent = self.parent.get_content_model()
            if isinstance(parent, PagePermissionsMixin):
                self.view_groups = [g for g in self.parent.view_groups.all()]
                self.edit_groups = [g for g in self.parent.edit_groups.all()]
                self.view_users = [u for u in self.parent.view_users.all()]
                self.edit_users = [u for u in self.parent.edit_users.all()]
                self.public = self.parent.public
                self.owner = self.parent.owner
                self.save()

    class Meta:
        abstract=True


class CatalogPage(Page, PagePermissionsMixin):
    """Maintains an ordered catalog of data.  These pages are rendered specially but otherwise are not special."""

    class Meta:
        ordering = ['title']

    @property
    def siblings(self):
        if self.parent:
            return set(self.parent.children.all()) - {self}
        else:
            return set()

    @classmethod
    def ensure_page(cls, *titles, **kwargs):
        parent = kwargs.get('parent', None)
        child = kwargs.get('child', None)
        if child:
            del kwargs['child']
        if parent:
            del kwargs['parent']

        if not cls.objects.filter(title=titles[0], parent=parent).exists():
            p = cls.objects.create(title=titles[0], parent=parent, **kwargs)
        else:
            p = cls.objects.get(title=titles[0], parent=parent)

        for title in titles[1:]:
            if not cls.objects.filter(title=title, parent=p).exists():
                p = cls.objects.create(title=title, parent=p, **kwargs)
            else:
                p = cls.objects.get(title=title, parent=p)

        if child:
            child.parent = p
            child.save()

        return p

    def can_add(self, request):
        return PagePermissionsMixin.can_add(self, request)

    def can_change(self, request):
        return PagePermissionsMixin.can_change(self, request)

    def can_delete(self, request):
        return PagePermissionsMixin.can_delete(self, request)


def set_permissions_for_new_catalog_page(sender, instance, created, *args, **kwargs):
    if instance.parent and created:
        instance.copy_permissions_from_parent()

set_permissions = post_save.connect(set_permissions_for_new_catalog_page, sender=CatalogPage, weak=False)


class DataResourceMixin(models.Model):
    """Represents a file that has been uploaded to Geoanalytics for representation"""
    original_file = models.FileField(upload_to='ga_resources', null=True, blank=True)
    resource_file = models.FileField(upload_to='ga_resources', null=True, blank=True)
    resource_url = models.URLField(null=True, blank=True)
    resource_config = models.TextField(null=True, blank=True)
    last_change = models.DateTimeField(null=True, blank=True)
    last_refresh = models.DateTimeField(null=True, blank=True) # updates happen only to resources that were not uploaded by the user.
    next_refresh = models.DateTimeField(null=True, blank=True, db_index=True) # will be populated every time the update manager runs
    refresh_every = TimedeltaField(null=True, blank=True)
    md5sum = models.CharField(max_length=64, blank=True, null=True) # the unique md5 sum of the data
    metadata_url = models.URLField(null=True, blank=True)
    metadata_xml = models.TextField(null=True, blank=True)
    native_bounding_box = models.PolygonField(null=True, blank=True)
    bounding_box = models.PolygonField(null=True, srid=4326, blank=True)
    three_d = models.BooleanField(default=False)
    native_srs = models.TextField(null=True, blank=True)
    driver = models.CharField(
        default='ga_resources.drivers.spatialite',
        max_length=255,
        null=False,
        blank=False,
        choices=getattr(s, 'INSTALLED_DATARESOURCE_DRIVERS', (
            ('ga_resources.drivers.spatialite', 'Spatialite (universal vector)'),
            ('ga_resources.drivers.shapefile', 'Shapefile'),
            ('ga_resources.drivers.geotiff', 'GeoTIFF'),
            ('ga_resources.drivers.postgis', 'PostGIS'),
            ('ga_resources.drivers.kmz', 'Google Earth KMZ'),
            ('ga_resources.drivers.ogr', 'OGR DataSource'),
        )))

    big = models.BooleanField(default=False, help_text='Set this to be true if the dataset is more than 100MB') # causes certain drivers to optimize for datasets larger than memory

    @property
    def srs(self):
        if not self.native_srs:
            self.driver_instance.compute_spatial_metadata()
        srs = osr.SpatialReference()
        srs.ImportFromProj4(self.native_srs.encode('ascii'))
        return srs

    @property
    def dataframe(self):
        return self.driver_instance.as_dataframe()

    @property
    def driver_instance(self):
        """deprecated"""
        if not hasattr(self, '_driver_instance'):
            self._driver_instance = importlib.import_module(self.driver).driver(self)
        return self._driver_instance

    @property
    def resource(self):
        return self.driver_instance

    def modified(self):
        self.last_refresh = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.driver_instance.clear_cache()

    @property
    def cache_path(self):
        p = os.path.join(s.MEDIA_ROOT, ".cache", "resources", *os.path.split(self.slug))
        if not os.path.exists(p):
            os.makedirs(p)  # just in case it's not there yet.
        return p

    @property
    def driver_config(self):
        return json.loads(self.resource_config) if self.resource_config else {}

    class Meta:
        abstract = True


class StyleMixin(models.Model):
    class Meta:
        abstract = True

    legend = models.ImageField(upload_to='ga_resources.styles.legends', width_field='legend_width', height_field='legend_height', null=True, blank=True)
    legend_width = models.IntegerField(null=True, blank=True)
    legend_height = models.IntegerField(null=True, blank=True)
    stylesheet = models.TextField()

    def modified(self):
        if s.WMS_CACHE_DB.exists(self.slug):
            cached_filenames = s.WMS_CACHE_DB.smembers(self.slug)
            for filename in cached_filenames:
                sh.rm('-rf', sh.glob(filename+"*"))
            s.WMS_CACHE_DB.srem(self.slug, cached_filenames)




class DataResource(Page, RichText, DataResourceMixin, PagePermissionsMixin):
    class Meta:
        ordering = ['title']

    def can_add(self, request):
        return PagePermissionsMixin.can_add(self, request)

    def can_change(self, request):
        return PagePermissionsMixin.can_change(self, request)

    def can_delete(self, request):
        return PagePermissionsMixin.can_delete(self, request)



class Style(Page, StyleMixin, PagePermissionsMixin):
    """A stylesheet in CartoCSS format."""
    class Meta:
        ordering = ['title']

    def can_add(self, request):
        return PagePermissionsMixin.can_add(self, request)

    def can_change(self, request):
        return PagePermissionsMixin.can_change(self, request)

    def can_delete(self, request):
        return PagePermissionsMixin.can_delete(self, request)



class RenderedLayer(Page, RichText, PagePermissionsMixin):
    """All the general stuff for a layer.  Layers inherit ownership and group info from the data resource"""
    data_resource = models.ForeignKey(DataResource, related_name="%(app_label)s_%(class)s_layers")
    default_style = models.ForeignKey(Style, related_name="%(app_label)s_%(class)s_is_default_for")
    default_class = models.CharField(max_length=255, default='default')
    styles = models.ManyToManyField(Style, related_name="%(app_label)s_%(class)s_layers") # fixme this must be a generic relation, not a many-to-many

    def can_add(self, request):
        return PagePermissionsMixin.can_add(self, request)

    def can_change(self, request):
        return PagePermissionsMixin.can_change(self, request)

    def can_delete(self, request):
        return PagePermissionsMixin.can_delete(self, request)

