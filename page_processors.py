# this should be used as the page processor for anything with pagepermissionsmixin
# page_processor_for(MyPage)(ga_resources.views.page_permissions_page_processor)
from mezzanine.pages.page_processors import processor_for
from .models import CatalogPage


def page_permissions_page_processor(request, page):
    page = page.get_content_model()
    edit_groups = page.edit_groups.all()
    view_groups = page.view_groups.all()
    edit_users = page.edit_users.all()
    view_users = page.view_users.all()

    return {
        "edit_groups": edit_groups,
        "view_groups": view_groups,
        "edit_users": edit_users,
        "view_users": view_users,
    }

@processor_for(CatalogPage)
def catalog_page_processor(request, page):
    viewable_children = []
    viewable_siblings = []
    for child in page.children.all():
        if not hasattr(page, 'can_view') or page.can_view(request):
            viewable_children.append(child)

    if page.parent:
        for child in page.parent.children.exclude(slug=page.slug):
            if not hasattr(page, 'can_view') or page.can_view(request):
                viewable_siblings.append(child)

    ctx = page_permissions_page_processor(request, page)
    ctx['viewable_children'] = viewable_children
    ctx['viewable_siblings'] = viewable_siblings

    return ctx