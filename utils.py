""" This module contains miscellaneous utility functions and classes for creating the OWS webservices.  The most useful
functions in the module are probably the date manipulation functions.
"""

from collections import namedtuple
import datetime
import json
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import MultipleChoiceField, Field
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.formats import sanitize_separators
from mezzanine.pages.models import Page
from .models import CatalogPage, PagePermissionsMixin
from osgeo import osr
from tastypie.models import ApiKey
import re


def to_referrer(request):
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def to_user(u):
    """
    Return a user whether we were passed a username, an email address, or a User instance.

    :param u:  a username, an email address, or a User instance
    :return: auth.User
    """
    if isinstance(u, basestring):
        try:
            u = User.objects.get(username=u)
        except:
            u = User.objects.get(email=u)
    return u


def to_group(u):
    """
    Return a group whether we were passed a name or a Group instance.

    :param u: a name or a Group instance.
    :return: auth.Group
    """
    if isinstance(u, basestring):
        u = Group.objects.get(name=u)
    return u

def create_geoanalytics_page(cls, owner=None, edit_users=None, edit_groups=None, view_users=None, view_groups=None,
                             parent=None, inherit=True, **kwargs):
    """
    Create a new page in TerraHub using its default rules for permission
    inheritance and menu presence.

    By default we inherit read/write permissions from the parent and menu
    presence is None unless specified.

    :param cls: classname of the page to be created
    :param owner: auth.User, string username, or string email address of the owner of the page
    :param edit_users: these users have view and edit permissions (replaces inherited)
    :param edit_groups: these groups and all their users have view and edit permissions
    :param view_users: these users have view permissions
    :param view_groups: these groups have view permissions
    :param parent: this is the parent page.
    :param inherit: if the parent page subclasses the PagePermissionsMixin, the created page inherits its permissions
    :param kwargs: any other keyword args to pass to cls.objects.create()
    :return: the new, saved instance of the Page
    """

    kwargs['in_menus'] = [] if not 'in_menus' in kwargs else kwargs['in_menus']
    if parent:
        if isinstance(parent, basestring):
            parent = Page.objects.get(slug=kwargs['parent'])

    owner = to_user(owner)

    new = cls.objects.create(parent=parent, owner=owner, **kwargs)

    edit_users = [to_user(user) for user in edit_users] if edit_users else None
    view_users = [to_user(user) for user in view_users] if view_users else None
    edit_groups = [to_group(group) for group in edit_groups] if edit_groups else None
    view_groups = [to_group(group) for group in view_groups] if view_groups else None

    if hasattr(kwargs.get('parent', None), 'public'):
        new.copy_permissions_from_parent()
    if edit_users:
        new.edit_users = edit_users
    if edit_groups:
        new.edit_groups = edit_groups
    if view_users:
        view_users.extend(edit_users or [])
        new.view_users = view_users
    if view_groups:
        view_groups.extend(edit_groups or [])
        new.view_groups = view_groups

    if not any((inherit, parent, edit_groups, view_groups, edit_users, view_users, owner)):
        new.public = True
        new.save()

    if inherit:
        new.copy_permissions_from_parent()

    return new

def create_geoanalytics_user(username, email, password, superuser=False, staff=False, first_name=None, last_name=None, *groups):
    """
    Creates a user, making sure that the API key also gets created.

    :param username: the username to created
    :param email: the email address for the created user
    :param password: the password for the user
    :param superuser: if the user is a supseruser
    :param staff: if the user is staff
    :param groups: the groups that the user is a part of
    :return: auth.User
    """
    if superuser:
        u = User.objects.create_superuser(
            username=username,
            email=email,
            first_name=first_name or '',
            last_name=last_name or '',
            password=password)
    else:
        u = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name or '',
            last_name=last_name or '',
            password=password)

    if staff:
        u.is_staff=True
        u.save()
    u.groups = [g for g in groups]
    ApiKey.objects.get_or_create(user=u)
    return u


def best_name(user):
    """
    :param user: auth.User
    :return: first name + last name or username if the others aren't defined.
    """
    profile = user.get_profile()
    if profile.display_name:
        return profile.display_name
    elif user.first_name:
        return user.first_name + (' ' + user.last_name if user.last_name else '')
    elif user.email:
        address, server = user.email.split('@')
        return address + ' at ' + server
    else:
        return user.username


def json_or_jsonp(r, i, code=200):
    """
    If callback or jsonp paraemters are defined, then return as JSONP else return as JSON

    :param r: HttpRequest
    :param i: The instance to serialize to JSON (probably a dict) or a string that is assumed to be JSON
    :param code: The Response code to return
    :return:
    """
    if not isinstance(i, basestring):
        i = json.dumps(i)

    if 'callback' in r.REQUEST:
        return HttpResponse('{c}({i});'.format(c=r.REQUEST['callback'], i=i), mimetype='text/javascript')
    elif 'jsonp' in r.REQUEST:
        return HttpResponse('{c}({i});'.format(c=r.REQUEST['jsonp'], i=i), mimetype='text/javascript')
    else:
        return HttpResponse(i, mimetype='application/json', status=code)

def user_page(user):
    user_page, created = CatalogPage.objects.get_or_create(title=best_name(user), owner=user, in_menus=[], public=False, parent=None)
    if created:
        user_page.title = best_name(user) # this is a hack to assure that the slug is correct
        user_page.save()

    return user_page

def get_data_page_for_user(user):
    p, _ = CatalogPage.objects.get_or_create(title="Datasets", in_menus=[], public=False, owner=user, parent=user_page(user))
    return p


def get_layer_page_for_user(user):
    p, _ = CatalogPage.objects.get_or_create(title="Layers", in_menus=[], public=False, owner=user, parent=user_page(user))
    return p


def get_stylesheet_page_for_user(user):
    p, _ = CatalogPage.objects.get_or_create(title="Stylesheets", in_menus=[], public=False, owner=user, parent=user_page(user))
    return p

def authorize(request, page=None, edit=False, add=False, delete=False, view=False, do_raise=True):
    if isinstance(page, basestring):
        page = Page.objects.get(slug=page)

    user = request if isinstance(request, User) else get_user(request.user)

    if user.is_superuser:
        return True

    if isinstance(page.get_content_model(), PagePermissionsMixin):
        page = page.get_content_model()

        if view:
            can_view = (not page.owner) or \
                       page.public or \
                       (user.is_authenticated() and (page.can_change(request) or page.can_view(request)))
        else:
            can_view = None
    else:
        can_view = True

    if edit:
        can_change = user.is_authenticated() and page.can_change(request)
    else:
        can_change = None

    if add:
        can_add = user.is_authenticated() and page.can_add(request)
    else:
        can_add = None

    if delete:
        can_delete = user.is_authenticated() and page.can_delete(request)
    else:
        can_delete = None

    auth = all((
        ((not view) or can_view),
        ((not edit) or can_change),
        ((not add) or can_add),
        ((not delete) or can_delete)
    ))

    if not auth:
        if do_raise:
            raise PermissionDenied(json.dumps({
                "error": "Unauthorized",
                "user": user.email if user.is_authenticated() else None,
                "page": page.slug if page else None,
                "edit": edit,
                "add": add,
                "delete": delete,
                "view": view
            }))
        else:
            return False
    else:
        return True

def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    :param request:
    :return: django.contrib.auth.User
    """
    if isinstance(request, User):
        return request
    if request is None:
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

def _from_today(match):    
    plusminus = match.group(1)
    amt = match.group(2)

    if plusminus == '-':
        return datetime.date.today() - datetime.timedelta(days=int(amt))
    else:
        return datetime.date.today() + datetime.timedelta(days=int(amt))

def _from_now(match):
    def maybeint(i):
        if i:
            return int(i)
        else:
            return 0

    plusminus = match.group(1)
    weeks = maybeint( match.group(2) )
    days = maybeint( match.group(3) )
    hours =  maybeint(match.group(4) )
    mins =maybeint(match.group(5) )
    seconds = maybeint(match.group(6))
    milliseconds = maybeint(match.group(7))


    if plusminus == '-':
        return datetime.datetime.utcnow() - datetime.timedelta(
            weeks=weeks, days=days, hours=hours, mins=mins, seconds=seconds, milliseconds=milliseconds)

def parsetime(t):
    """Parses a time string into a datetime object.  This is the function used by parse the dates in an OWS request, so
    all OWS requests accept these date formats.  ParseTime accepts the following formats:
        
        * '%Y.%m.%d-%H:%M:%S.%f'
        * '%Y.%m.%d-%H:%M:%S'
        * '%Y.%m.%d-%H:%M'
        * '%Y.%m.%d'
        * '%Y%m%d%H%M%S%f'
        * '%Y%m%d%H%M%S'
        * '%Y%m%d%H%M'
        * '%Y%m%d'
        * '%Y.%m'
        * '%Y'
        * '%Y.%m.%d-%H:%M:%S.%f'
        * '%Y/%m/%d-%H:%M:%S'
        * '%Y/%m/%d-%H:%M'
        * '%Y/%m/%d'
        * '%Y/%m'
        * '%Y'
        * "now"
        * "today"
        * "today+${days}"
        * "now+${weeks}w${days}d${hours}h${mins}m${seconds}s${millisecs}ms"
    
    :param t: a string in one of the above formats.
    :return: a datetime object
    """
    
    timeformats = [
        '%Y.%m.%d-%H:%M:%S.%f',
        '%Y.%m.%d-%H:%M:%S',
        '%Y.%m.%d-%H:%M',
        '%Y.%m.%d',
        '%Y%m%d%H%M%S%f',
        '%Y%m%d%H%M%S',
        '%Y%m%d%H%M',
        '%Y%m%d',
        '%Y.%m',
        '%Y',
        '%Y.%m.%d-%H:%M:%S.%f',
        '%Y/%m/%d-%H:%M:%S',
        '%Y/%m/%d-%H:%M',
        '%Y/%m/%d',
        '%Y/%m',
        '%Y'
    ]
    alt_formats = {
       'now' : datetime.datetime.utcnow(),
       'today' : datetime.date.today(),
    }
    high_level = [
        (re.compile('today(\+|-)([0-9]+)'), _from_today),
        (re.compile('now(\+|-)([0-9]+w)?([0-9]+d)?([0-9]+h)?([0-9]+m)?([0-9]+s)?([0-9]+ms)?'), _from_now)
    ]

    if not t:
        return None

    ret = None
    for tf in timeformats:
        try:
            ret = datetime.datetime.strptime(t, tf)
        except:
            pass

    if not ret and t in alt_formats:
        return alt_formats[t]
    elif not ret:
        for tf, l in high_level:
            k = tf.match(t)
            if k:
                ret = l(k)
    if ret:
        return ret
    else:
        raise ValueError('time data does not match any valid format: ' + t)

def create_spatialref(srs, srs_format='srid'):
    """
    **Deprecated - use Django's SpatialRef class**. Create an :py:class:`osgeo.osr.SpatialReference` from an srid, wkt,
    projection, or epsg code.  srs_format should be one of: srid, wkt, proj,
    epsg to represent a format in numerical srid form, well-known text, proj4,
    or epsg formats.
    """
    spatialref = osr.SpatialReference()
    if srs_format:
        if srs_format == 'srid':
            spatialref.ImportFromEPSG(srs)
        elif srs_format == 'wkt':
            spatialref.ImportFromWkt(srs)
        elif srs_format == 'proj':
            spatialref.ImportFromProj4(srs)
    else:
        spatialref.ImportFromEPSG(int(srs.split(':')[1]))
    return spatialref

mimetypes = namedtuple("MimeTypes", (
    'json', 'jsonp')
)(
    json='application/json',
    jsonp='text/plain'
)


class CaseInsensitiveDict(dict):
    """
    A subclass of :py:class:django.utils.datastructures.MultiValueDict that treats all keys as lower-case strings
    """

    def __init__(self, key_to_list_mapping=()):
        def fix(pair):
            key, value = pair
            return key.lower(),value
        super(CaseInsensitiveDict, self).__init__([fix(kv) for kv in key_to_list_mapping])

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)

    def get(self, key, default=None):
        if key not in self:
            return default
        else:
            return self[key]

    def getlist(self, key):
        if key not in self:
            return []
        elif isinstance(self[key], list):
            return self[key]
        elif isinstance(self[key], tuple):
            return list(self[key])
        else:
            return [self[key]]


class MultipleValueField(MultipleChoiceField):
    """A field for pulling in arbitrary lists of strings instead of constraining them by choice"""
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])

class BBoxField(Field):
    """A field that represents a bounding box in minx,miny,maxx,maxy format - parses the bbox field from an OWS request.
    """
    def to_python(self, value):
        value = super(BBoxField, self).to_python(value)
        if not value:
            return -180.0,-90.0,180.0,90.0

        try:
            lx, ly, ux, uy = value.split(',')
            if self.localize:
                lx = float(sanitize_separators(lx))
                ly = float(sanitize_separators(ly))
                ux = float(sanitize_separators(ux))
                uy = float(sanitize_separators(uy))

                if uy < ly or ux < lx:
                    raise ValidationError("BBoxes must be in lower-left(x,y), upper-right(x,y) order")
        except (ValueError, TypeError):
            raise ValidationError("BBoxes must be four floating point values separated by commas")

        lx = float(sanitize_separators(lx))
        ly = float(sanitize_separators(ly))
        ux = float(sanitize_separators(ux))
        uy = float(sanitize_separators(uy))
        return lx, ly, ux, uy
