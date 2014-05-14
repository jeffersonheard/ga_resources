from tastypie.api import Api
from tastypie.fields import ForeignKey, ManyToManyField
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import *
from tastypie.authorization import Authorization

from ga_resources import models
from mezzanine.pages.models import Page
from django.contrib.auth import models as auth
from django.conf.urls import url
from .utils import get_user

class PagePermissionsMixinAuthentication(Authentication):
    def __init__(self):
        super(PagePermissionsMixinAuthentication, self).__init__()
        self.multi = MultiAuthentication(
            SessionAuthentication,
            ApiKeyAuthentication,
            DigestAuthentication,
            BasicAuthentication,
            Authentication # public pages are available to unauthenticated users.
        )



class PagePermissionsMixinAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return filter(lambda x: x.can_view(bundle.request), object_list)

    def read_detail(self, object_list, bundle):
        return bundle.obj.can_view(bundle.request)

    def create_list(self, object_list, bundle):
        return filter(lambda x: (not x.parent) or x.parent.can_add(bundle.request), object_list)

    def create_detail(self, object_list, bundle):
        if bundle.obj.parent:
            if bundle.obj.parent.can_add(bundle.request):
                return True
            else:
                return get_user(bundle.request).is_authenticated()

        return bundle.obj.user == bundle.request.user

    def update_list(self, object_list, bundle):
        return filter(lambda x: x.can_change(bundle.request), object_list)

    def update_detail(self, object_list, bundle):
        return bundle.obj.can_change(bundle.request)

    def delete_list(self, object_list, bundle):
        return bundle.obj.can_delete(bundle.request)

    def delete_detail(self, object_list, bundle):
        return bundle.obj.can_delete(bundle.request)



class AbstractPageResource(ModelResource):
    """Abstract class that provides sensible defaults for creating new pages via the RESTful API. e.g. unless there's
     some specific value passed in for whether or not the page should show up in the header, footer, and sidebar, we
     want to dehydrate that field specifically"""

    def _dehydrate_with_default(self, bundle, datum, default):
        if datum not in bundle.data or bundle.data[datum] is None:
            return default

    def dehydrate_in_menus(self, bundle):
        return self._dehydrate_with_default(bundle, 'in_menus', False)

    def dehydrate_requires_login(self, bundle):
        return self._dehydrate_with_default(bundle, 'requires_login', False)

    def dehydrate_in_sitemap(self, bundle):
        return self._dehydrate_with_default(bundle, 'in_sitemap', False)


class BaseMeta(object):
    allowed_methods = ['get', 'put', 'post', 'delete']
    authorization = PagePermissionsMixinAuthorization()
    authentication = Authentication()
    filtering = { 'slug' : ALL, 'title' : ALL, 'parent' : ALL_WITH_RELATIONS }


class Group(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = SessionAuthentication()
        allowed_methods = ['get']
        queryset = auth.Group.objects.all()
        resource_name = "group"


class User(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = SessionAuthentication()
        allowed_methods = ['get']
        queryset = auth.User.objects.all()
        resource_name = "user"


class CatalogPage(AbstractPageResource):
    parent = ForeignKey('self', 'parent', null=True)
    owner = ForeignKey('ga_resources.api.User', 'owner', null=True)

    class Meta:
        authorization = PagePermissionsMixinAuthorization()
        authentication = Authentication()
        queryset = models.CatalogPage.objects.all()
        resource_name = 'catalog'
        allowed_methods = ['get']
        detail_uri_name = "slug"
        filtering = {'slug': ALL_WITH_RELATIONS, 'title': ALL, 'parent': ALL_WITH_RELATIONS}

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class PageResource(AbstractPageResource):
    parent = ForeignKey('self', 'parent', null=True, blank=True)

    class Meta:
        queryset = Page.objects.all()
        resource_name = 'page'
        allowed_methods = ['get']
        detail_uri_name = "slug"
        filtering = {'slug': ALL_WITH_RELATIONS, 'title': ALL, 'parent': ALL_WITH_RELATIONS}
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
 

class DataResource(AbstractPageResource):
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)

    class Meta(BaseMeta):
        authorization = PagePermissionsMixinAuthorization()
        authentication = Authentication()

        queryset = models.DataResource.objects.all()
        resource_name = 'data'
        fields = ['title','status','content','resource_file','resource_url','resource_irods_file','kind','driver','parent']
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class Style(AbstractPageResource):
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)
    class Meta(BaseMeta):
        authorization = PagePermissionsMixinAuthorization()
        authentication = Authentication()

        queryset = models.Style.objects.all()
        resource_name = "style"
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]



class RenderedLayer(AbstractPageResource):
    data_resource = ForeignKey(DataResource, 'data_resource')
    default_style = ForeignKey(Style, 'default_style', related_name='default_for_layer')
    styles = ManyToManyField(Style, 'styles')
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)

    class Meta(BaseMeta):
        authorization = PagePermissionsMixinAuthorization()
        authentication = Authentication()

        queryset = models.RenderedLayer.objects.all()
        resource_name = 'rendered_layer'
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


api = Api()
api.register(User())
api.register(Group())
api.register(DataResource())
api.register(CatalogPage())
api.register(Style())
api.register(RenderedLayer())
api.register(PageResource())
