# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mezzanine.core.fields
import django.contrib.gis.db.models.fields
from django.conf import settings
import timedelta.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('public', models.BooleanField(default=True)),
                ('edit_groups', models.ManyToManyField(related_name='group_editable_ga_resources_catalogpage', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(related_name='editable_ga_resources_catalogpage', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(related_name='owned_ga_resources_catalogpage', to=settings.AUTH_USER_MODEL, null=True)),
                ('view_groups', models.ManyToManyField(related_name='group_viewable_ga_resources_catalogpage', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(related_name='viewable_ga_resources_catalogpage', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='DataResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('public', models.BooleanField(default=True)),
                ('resource_file', models.FileField(null=True, upload_to=b'ga_resources', blank=True)),
                ('resource_url', models.URLField(null=True, blank=True)),
                ('resource_config', models.TextField(null=True, blank=True)),
                ('last_change', models.DateTimeField(null=True, blank=True)),
                ('last_refresh', models.DateTimeField(null=True, blank=True)),
                ('next_refresh', models.DateTimeField(db_index=True, null=True, blank=True)),
                (b'refresh_every', timedelta.fields.TimedeltaField(max_value=None, min_value=None)),
                ('md5sum', models.CharField(max_length=64, null=True, blank=True)),
                ('metadata_url', models.URLField(null=True, blank=True)),
                ('metadata_xml', models.TextField(null=True, blank=True)),
                ('native_bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('three_d', models.BooleanField(default=False)),
                ('native_srs', models.TextField(null=True, blank=True)),
                ('driver', models.CharField(default=b'ga_resources.drivers.spatialite', max_length=255, choices=[(b'ga_resources.drivers.spatialite', b'Spatialite (universal)'), (b'ga_resources.drivers.shapefile', b'Shapefile'), (b'ga_resources.drivers.geotiff', b'GeoTIFF'), (b'ga_resources.drivers.postgis', b'PostGIS'), (b'ga_resources.drivers.kmz', b'Google Earth KMZ'), (b'ga_resources.drivers.ogr', b'OGR DataSource')])),
                ('big', models.BooleanField(default=False, help_text=b'Set this to be true if the dataset is more than 100MB')),
                ('edit_groups', models.ManyToManyField(related_name='group_editable_ga_resources_dataresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(related_name='editable_ga_resources_dataresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(related_name='owned_ga_resources_dataresource', to=settings.AUTH_USER_MODEL, null=True)),
                ('view_groups', models.ManyToManyField(related_name='group_viewable_ga_resources_dataresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(related_name='viewable_ga_resources_dataresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='OrderedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordering', models.IntegerField(default=0)),
                ('data_resource', models.ForeignKey(to='ga_resources.DataResource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelatedResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('resource_file', models.FileField(upload_to=b'ga_resources')),
                ('foreign_key', models.CharField(max_length=64, null=True, blank=True)),
                ('local_key', models.CharField(max_length=64, null=True, blank=True)),
                ('left_index', models.BooleanField(default=False)),
                ('right_index', models.BooleanField(default=False)),
                ('how', models.CharField(default=b'left', max_length=8, choices=[(b'left', b'left'), (b'right', b'right'), (b'outer', b'outer'), (b'inner', b'inner')])),
                ('driver', models.CharField(default=b'ga_resources.drivers.related.excel', max_length=255)),
                ('key_transform', models.IntegerField(blank=True, null=True, choices=[(1, b'Capitalize'), (2, b'Lower case'), (0, b'Upper case')])),
                ('foreign_resource', models.ForeignKey(to='ga_resources.DataResource')),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='RenderedLayer',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('public', models.BooleanField(default=True)),
                ('default_class', models.CharField(default=b'default', max_length=255)),
                ('data_resource', models.ForeignKey(to='ga_resources.DataResource')),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='ResourceGroup',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('is_timeseries', models.BooleanField(default=False)),
                ('min_time', models.DateTimeField(null=True)),
                ('max_time', models.DateTimeField(null=True)),
                ('resources', models.ManyToManyField(to='ga_resources.DataResource', through='ga_resources.OrderedResource', blank=True)),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=('pages.page',),
        ),
        migrations.CreateModel(
            name='Style',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('public', models.BooleanField(default=True)),
                ('legend', models.ImageField(height_field=b'legend_height', width_field=b'legend_width', null=True, upload_to=b'ga_resources.styles.legends', blank=True)),
                ('legend_width', models.IntegerField(null=True, blank=True)),
                ('legend_height', models.IntegerField(null=True, blank=True)),
                ('stylesheet', models.TextField()),
                ('edit_groups', models.ManyToManyField(related_name='group_editable_ga_resources_style', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(related_name='editable_ga_resources_style', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(related_name='owned_ga_resources_style', to=settings.AUTH_USER_MODEL, null=True)),
                ('view_groups', models.ManyToManyField(related_name='group_viewable_ga_resources_style', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(related_name='viewable_ga_resources_style', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=('pages.page', models.Model),
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='default_style',
            field=models.ForeignKey(related_name='default_for_layer', to='ga_resources.Style'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='edit_groups',
            field=models.ManyToManyField(related_name='group_editable_ga_resources_renderedlayer', null=True, to='auth.Group', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='edit_users',
            field=models.ManyToManyField(related_name='editable_ga_resources_renderedlayer', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='owner',
            field=models.ForeignKey(related_name='owned_ga_resources_renderedlayer', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='styles',
            field=models.ManyToManyField(to='ga_resources.Style'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='view_groups',
            field=models.ManyToManyField(related_name='group_viewable_ga_resources_renderedlayer', null=True, to='auth.Group', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='renderedlayer',
            name='view_users',
            field=models.ManyToManyField(related_name='viewable_ga_resources_renderedlayer', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderedresource',
            name='resource_group',
            field=models.ForeignKey(to='ga_resources.ResourceGroup'),
            preserve_default=True,
        ),
    ]
