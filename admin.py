from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from ga_resources.models import *
from django.forms import ModelForm
from django import forms

class RenderedLayerAdminForm(ModelForm):
    data_resource = forms.ModelChoiceField(queryset=DataResource.objects.order_by('slug'))
    default_style = forms.ModelChoiceField(queryset=Style.objects.order_by('slug'))
    styles = forms.ModelMultipleChoiceField(queryset=Style.objects.order_by('slug'))

    class Meta:
        model = RenderedLayer
        exclude = []

class RenderedLayerAdmin(PageAdmin):
    form = RenderedLayerAdminForm


admin.site.register(CatalogPage, PageAdmin)
admin.site.register(DataResource, PageAdmin)
admin.site.register(RenderedLayer, RenderedLayerAdmin)
admin.site.register(Style, PageAdmin)
