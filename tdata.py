"""
This exists because once you get to the point of dealing with model inheritance
and FileFields there's no really good way to write fixtures in the normal
fomrat.  Therefore we have a Python file that loads the data the way we want it
in the test database
"""

from django.contrib.auth.models import Group
from ga_resources.models import *
from .utils import create_geoanalytics_user, create_geoanalytics_page
from collections import namedtuple

def create_groups(*names):
    gs = []
    for name in names:
        gs.append(Group.objects.get_or_create(name=name)[0])
    return gs


# default stylesheet for testing purposes
SS = '''
.default { 
    polygon-fill: #fff; 
    line-width: 0.5;
    line-color: #000;
}
'''

def clear_test_data():
    """Nukes the test data from space.  Might have some collateral damage..."""
    from django.db.models import get_model
    get_model('auth','User').objects.all().delete()
    get_model('auth','Group').objects.all().delete()
    get_model('ga_resources','Style').objects.all().delete()
    get_model('ga_resources','RenderedLayer').objects.all().delete()
    get_model('ga_resources','DataResource').objects.all().delete()
    get_model('ga_resources','CatalogPage').objects.all().delete()

def create_test_data():
    """
    Create a set of test data in the database from scratch.

    * Groups: good_users, bad_users
    * Users:
        * superuser: member of good users, superuser
        * owner: owns all the data, staff, not superuser
        * regular1 - 4: is not staff, not superuser, member of good users
        * abusive_user: is not staff, not superuser, member of good users
        * abusive_staff: staff, not superuser, member of bad users
        * abusive_superuser: is not staff, is superuser, member of bad users
        * orphan: has no group memberships and no staff or superuser position
    * Catalog Pages:
        * unowned_catalog_page: no owner, public
        * public_catalog_page: owner is owner, public
        * private_catalog_page: owner is owner, not public
        * catalog_page_shared_with_user: view_users contains regular1
        * catalog_page_shared_with_group: view_groups contains good_users
    * DataResources: follows catalog pages pattern, all of them are children of their catalog pages
    * RenderedLayers: follows catalog pages pattern, all of them are children of their corresponding catalog pages
    * Styles: follows catalog pages pattern. all of them are children of their corresponding catalog pages

    :return: a dict of all the test data that was created.
    """
    good_users, bad_users = create_groups('Good Users', 'Bad Users')
    superuser = create_geoanalytics_user('root2', 'jeff@terrahub.io', 'foobar', True, True, 'Jeff','Heard',good_users)
    owner = create_geoanalytics_user('owner', 'owner@terrahub.io', 'foobar', False, True, 'Mike','Whitson',good_users)

    staff_user = create_geoanalytics_user('staff1', 'regular1@terrahub.io', 'foobar', False, True, 'Casey','Averill', good_users)
    regular1 = create_geoanalytics_user('regular1', 'regular1@terrahub.io', 'foobar', False, False, 'John','Galloway', good_users)
    regular2 = create_geoanalytics_user('regular2', 'regular2@terrahub.io', 'foobar', False, False, 'Tracey','Callison',good_users)
    regular3 = create_geoanalytics_user('regular3', 'regular3@terrahub.io', 'foobar', False, False, 'Lisa','Chensvold',good_users)
    regular4 = create_geoanalytics_user('regular4', 'regular4@terrahub.io', 'foobar', False, False, 'Bob','Heard',good_users)
    abusive_user = create_geoanalytics_user('abusive_user', 'abusive1@terrahub.io', 'foobar', False, False, 'Snively','Whiplash', bad_users)
    abusive_staff = create_geoanalytics_user('abusive_staff', 'abusive2@terrahub.io', 'foobar', True, False, 'George','Bush', bad_users)
    abusive_superuser = create_geoanalytics_user('abusive_superuser', 'abusive3@terrahub.io', 'foobar', False, True, 'Rick','Perry',bad_users)
    orphan = create_geoanalytics_user('orphan', 'orphan@terrahub.io', 'foobar', 'Annie','Orpan', False, False)

    unowned_catalog_page = create_geoanalytics_page(CatalogPage, title='unowned cp', in_menus=[1])
    public_catalog_page = create_geoanalytics_page(CatalogPage, title='public cp', in_menus=[1], owner=owner, public=True)
    private_catalog_page = create_geoanalytics_page(CatalogPage, title='private cp', owner=owner, in_menus=[1], public=False)
    catalog_page_shared_with_group = create_geoanalytics_page(CatalogPage, title='cp shared with group', owner=owner,
                                                          view_groups=[good_users], in_menus=[1], public=False)
    catalog_page_shared_with_user = create_geoanalytics_page(CatalogPage, title='cp shared with user', owner=owner,
                                                         view_users=[regular1], in_menus=[1], public=False)
    catalog_page_shared_with_orphan = create_geoanalytics_page(CatalogPage, title='cp shared with orphan', owner=owner,
                                                           view_users=[orphan], in_menus=[1], public=False)
    catalog_page_editable_with_group = create_geoanalytics_page(CatalogPage, title='cp editable with group', owner=owner,
                                                            edit_groups=[good_users], in_menus=[1], public=False)
    catalog_page_editable_with_user = create_geoanalytics_page(CatalogPage, title='cp editable with user', owner=owner,
                                                           edit_users=[regular1], in_menus=[1], public=False)
    catalog_page_editable_with_orphan = create_geoanalytics_page(CatalogPage, title='cp editable with orphan', owner=owner,
                                                             edit_users=[orphan], in_menus=[1], public=False)

    # datasets

    unowned_dataset = create_geoanalytics_page(DataResource, title='unowned dataset')
    public_dataset = create_geoanalytics_page(DataResource, title='public dataset', owner=owner)
    private_dataset = create_geoanalytics_page(DataResource, title='private dataset', parent=private_catalog_page)
    dataset_shared_with_group = create_geoanalytics_page(DataResource,
                                                     title='dataset shared with group',
                                                     parent=catalog_page_shared_with_group,
                                                     driver='ga_resources.drivers.spatialite',
                                                     resource_file='test_data/10m-admin-0-countries.zip')

    dataset_shared_with_user = create_geoanalytics_page(DataResource,
                                                    title='dataset shared with user',
                                                    parent=catalog_page_shared_with_user,
                                                    driver='ga_resources.drivers.spatialite',
                                                    resource_file='test_data/10m-admin-0-countries.zip')

    dataset_shared_with_orphan = create_geoanalytics_page(DataResource,
                                                      title='dataset shared with orphan',
                                                      parent=catalog_page_shared_with_orphan,
                                                      driver='ga_resources.drivers.spatialite',
                                                      resource_file='test_data/10m-admin-0-countries.zip')

    dataset_editable_with_group = create_geoanalytics_page(DataResource,
                                                       title='dataset editable with group',
                                                       parent=catalog_page_editable_with_group,
                                                       driver='ga_resources.drivers.spatialite',
                                                       resource_file='test_data/10m-admin-0-countries.zip')

    dataset_editable_with_user = create_geoanalytics_page(DataResource,
                                                      title='dataset editable with user',
                                                      parent=catalog_page_editable_with_user,
                                                      driver='ga_resources.drivers.spatialite',
                                                      resource_file='test_data/10m-admin-0-countries.zip')

    dataset_editable_with_orphan = create_geoanalytics_page(DataResource,
                                                        title='dataset editable with orphan',
                                                        parent=catalog_page_editable_with_orphan,
                                                        driver='ga_resources.drivers.spatialite',
                                                        resource_file='test_data/10m-admin-0-countries.zip')

    dataset_remote_file = create_geoanalytics_page(DataResource,
                                               title='dataset shared with group',
                                               parent=catalog_page_shared_with_group,
                                               driver='ga_resources.drivers.spatialite',
                                               resource_url='http://mapbox-geodata.s3.amazonaws.com/natural-earth-1.4.0/cultural/10m-admin-0-countries.zip')

    # styles

    unowned_style = create_geoanalytics_page(Style,
                                         title='unowned style',
                                         stylesheet=SS)
    public_style = create_geoanalytics_page(Style,
                                        title='public style',
                                        stylesheet=SS)
    private_style = create_geoanalytics_page(Style,
                                         title='private style',
                                         parent=private_catalog_page,
                                         stylesheet=SS)
    style_shared_with_group = create_geoanalytics_page(Style,
                                                   title='style shared with group',
                                                   parent=catalog_page_shared_with_group,
                                                   stylesheet=SS)
    style_shared_with_user = create_geoanalytics_page(Style,
                                                  title='style shared with user',
                                                  parent=catalog_page_shared_with_user,
                                                  stylesheet=SS)
    style_shared_with_orphan = create_geoanalytics_page(Style,
                                                    title='style shared with orphan',
                                                    parent=catalog_page_shared_with_orphan,
                                                    stylesheet=SS)
    style_editable_with_group = create_geoanalytics_page(Style,
                                                     title='style editable with group',
                                                     parent=catalog_page_editable_with_group,
                                                     stylesheet=SS)
    style_editable_with_user = create_geoanalytics_page(Style,
                                                    title='style editable with user',
                                                    parent=catalog_page_editable_with_user,
                                                    stylesheet=SS)
    style_editable_with_orphan = create_geoanalytics_page(Style,
                                                      title='style editable with orphan',
                                                      parent=catalog_page_editable_with_orphan,
                                                      stylesheet=SS)

    # layers 

    unowned_layer = create_geoanalytics_page(RenderedLayer,
                                         title='unowned layer',
                                         data_resource=unowned_dataset,
                                         default_style=unowned_style)

    public_layer = create_geoanalytics_page(RenderedLayer,
                                        title='public layer',
                                        data_resource=public_dataset,
                                        default_style=unowned_style)

    private_layer = create_geoanalytics_page(RenderedLayer,
                                         title='private layer',
                                         parent=private_catalog_page,
                                         data_resource=private_dataset,
                                         default_style=unowned_style)

    layer_shared_with_group = create_geoanalytics_page(RenderedLayer,
                                                   title='layer shared with group',
                                                   parent=catalog_page_shared_with_group,
                                                   data_resource=dataset_shared_with_group,
                                                   default_style=unowned_style)

    layer_shared_with_user = create_geoanalytics_page(RenderedLayer,
                                                  title='layer shared with user',
                                                  parent=catalog_page_shared_with_user,
                                                  data_resource=dataset_shared_with_user,
                                                  default_style=unowned_style)

    layer_shared_with_orphan = create_geoanalytics_page(RenderedLayer,
                                                    title='layer shared with orphan',
                                                    parent=catalog_page_shared_with_orphan,
                                                    data_resource=dataset_shared_with_orphan,
                                                    default_style=unowned_style)

    layer_editable_with_group = create_geoanalytics_page(RenderedLayer,
                                                     title='layer editable with group',
                                                     parent=catalog_page_editable_with_group,
                                                     data_resource=dataset_editable_with_group,
                                                     default_style=unowned_style)

    layer_editable_with_user = create_geoanalytics_page(RenderedLayer,
                                                    title='layer editable with user',
                                                    parent=catalog_page_editable_with_user,
                                                    data_resource=dataset_editable_with_user,
                                                    default_style=unowned_style)

    layer_editable_with_orphan = create_geoanalytics_page(RenderedLayer,
                                                      title='layer editable with orphan',
                                                      parent=catalog_page_editable_with_orphan,
                                                      data_resource=dataset_editable_with_orphan,
                                                      default_style=unowned_style)

    return namedtuple('geoanalytics_test_data', locals().keys())(**locals())

