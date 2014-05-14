# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field edit_users on 'RenderedLayer'
        m2m_table_name = db.shorten_name(u'ga_resources_renderedlayer_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('renderedlayer', models.ForeignKey(orm[u'ga_resources.renderedlayer'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['renderedlayer_id', 'user_id'])

        # Adding M2M table for field view_users on 'RenderedLayer'
        m2m_table_name = db.shorten_name(u'ga_resources_renderedlayer_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('renderedlayer', models.ForeignKey(orm[u'ga_resources.renderedlayer'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['renderedlayer_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'RenderedLayer'
        m2m_table_name = db.shorten_name(u'ga_resources_renderedlayer_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('renderedlayer', models.ForeignKey(orm[u'ga_resources.renderedlayer'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['renderedlayer_id', 'group_id'])

        # Adding M2M table for field view_groups on 'RenderedLayer'
        m2m_table_name = db.shorten_name(u'ga_resources_renderedlayer_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('renderedlayer', models.ForeignKey(orm[u'ga_resources.renderedlayer'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['renderedlayer_id', 'group_id'])

        # Adding M2M table for field edit_users on 'DataResource'
        m2m_table_name = db.shorten_name(u'ga_resources_dataresource_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dataresource', models.ForeignKey(orm[u'ga_resources.dataresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dataresource_id', 'user_id'])

        # Adding M2M table for field view_users on 'DataResource'
        m2m_table_name = db.shorten_name(u'ga_resources_dataresource_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dataresource', models.ForeignKey(orm[u'ga_resources.dataresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dataresource_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'DataResource'
        m2m_table_name = db.shorten_name(u'ga_resources_dataresource_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dataresource', models.ForeignKey(orm[u'ga_resources.dataresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dataresource_id', 'group_id'])

        # Adding M2M table for field view_groups on 'DataResource'
        m2m_table_name = db.shorten_name(u'ga_resources_dataresource_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dataresource', models.ForeignKey(orm[u'ga_resources.dataresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['dataresource_id', 'group_id'])

        # Adding M2M table for field edit_users on 'CatalogPage'
        m2m_table_name = db.shorten_name(u'ga_resources_catalogpage_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('catalogpage', models.ForeignKey(orm[u'ga_resources.catalogpage'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['catalogpage_id', 'user_id'])

        # Adding M2M table for field view_users on 'CatalogPage'
        m2m_table_name = db.shorten_name(u'ga_resources_catalogpage_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('catalogpage', models.ForeignKey(orm[u'ga_resources.catalogpage'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['catalogpage_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'CatalogPage'
        m2m_table_name = db.shorten_name(u'ga_resources_catalogpage_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('catalogpage', models.ForeignKey(orm[u'ga_resources.catalogpage'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['catalogpage_id', 'group_id'])

        # Adding M2M table for field view_groups on 'CatalogPage'
        m2m_table_name = db.shorten_name(u'ga_resources_catalogpage_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('catalogpage', models.ForeignKey(orm[u'ga_resources.catalogpage'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['catalogpage_id', 'group_id'])

        # Adding M2M table for field edit_users on 'Style'
        m2m_table_name = db.shorten_name(u'ga_resources_style_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('style', models.ForeignKey(orm[u'ga_resources.style'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['style_id', 'user_id'])

        # Adding M2M table for field view_users on 'Style'
        m2m_table_name = db.shorten_name(u'ga_resources_style_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('style', models.ForeignKey(orm[u'ga_resources.style'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['style_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'Style'
        m2m_table_name = db.shorten_name(u'ga_resources_style_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('style', models.ForeignKey(orm[u'ga_resources.style'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['style_id', 'group_id'])

        # Adding M2M table for field view_groups on 'Style'
        m2m_table_name = db.shorten_name(u'ga_resources_style_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('style', models.ForeignKey(orm[u'ga_resources.style'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['style_id', 'group_id'])


    def backwards(self, orm):
        # Removing M2M table for field edit_users on 'RenderedLayer'
        db.delete_table(db.shorten_name(u'ga_resources_renderedlayer_edit_users'))

        # Removing M2M table for field view_users on 'RenderedLayer'
        db.delete_table(db.shorten_name(u'ga_resources_renderedlayer_view_users'))

        # Removing M2M table for field edit_groups on 'RenderedLayer'
        db.delete_table(db.shorten_name(u'ga_resources_renderedlayer_edit_groups'))

        # Removing M2M table for field view_groups on 'RenderedLayer'
        db.delete_table(db.shorten_name(u'ga_resources_renderedlayer_view_groups'))

        # Removing M2M table for field edit_users on 'DataResource'
        db.delete_table(db.shorten_name(u'ga_resources_dataresource_edit_users'))

        # Removing M2M table for field view_users on 'DataResource'
        db.delete_table(db.shorten_name(u'ga_resources_dataresource_view_users'))

        # Removing M2M table for field edit_groups on 'DataResource'
        db.delete_table(db.shorten_name(u'ga_resources_dataresource_edit_groups'))

        # Removing M2M table for field view_groups on 'DataResource'
        db.delete_table(db.shorten_name(u'ga_resources_dataresource_view_groups'))

        # Removing M2M table for field edit_users on 'CatalogPage'
        db.delete_table(db.shorten_name(u'ga_resources_catalogpage_edit_users'))

        # Removing M2M table for field view_users on 'CatalogPage'
        db.delete_table(db.shorten_name(u'ga_resources_catalogpage_view_users'))

        # Removing M2M table for field edit_groups on 'CatalogPage'
        db.delete_table(db.shorten_name(u'ga_resources_catalogpage_edit_groups'))

        # Removing M2M table for field view_groups on 'CatalogPage'
        db.delete_table(db.shorten_name(u'ga_resources_catalogpage_view_groups'))

        # Removing M2M table for field edit_users on 'Style'
        db.delete_table(db.shorten_name(u'ga_resources_style_edit_users'))

        # Removing M2M table for field view_users on 'Style'
        db.delete_table(db.shorten_name(u'ga_resources_style_view_users'))

        # Removing M2M table for field edit_groups on 'Style'
        db.delete_table(db.shorten_name(u'ga_resources_style_edit_groups'))

        # Removing M2M table for field view_groups on 'Style'
        db.delete_table(db.shorten_name(u'ga_resources_style_view_groups'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ga_resources.catalogpage': {
            'Meta': {'ordering': "['title']", 'object_name': 'CatalogPage', '_ormbases': [u'pages.Page']},
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_ga_resources_catalogpage'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'editable_ga_resources_catalogpage'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'owned_ga_resources_catalogpage'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_ga_resources_catalogpage'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'viewable_ga_resources_catalogpage'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'ga_resources.dataresource': {
            'Meta': {'ordering': "['title']", 'object_name': 'DataResource', '_ormbases': [u'pages.Page']},
            'big': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bounding_box': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'driver': ('django.db.models.fields.CharField', [], {'default': "'ga_resources.drivers.spatialite'", 'max_length': '255'}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_ga_resources_dataresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'editable_ga_resources_dataresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'last_change': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_refresh': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'metadata_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'metadata_xml': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'native_bounding_box': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'native_srs': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'next_refresh': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'owned_ga_resources_dataresource'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'refresh_every': ('timedelta.fields.TimedeltaField', [], {'null': 'True', 'blank': 'True'}),
            'resource_config': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'resource_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'resource_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'three_d': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_ga_resources_dataresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'viewable_ga_resources_dataresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'ga_resources.orderedresource': {
            'Meta': {'object_name': 'OrderedResource'},
            'data_resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ga_resources.DataResource']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ga_resources.ResourceGroup']"})
        },
        u'ga_resources.relatedresource': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'RelatedResource', '_ormbases': [u'pages.Page']},
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'driver': ('django.db.models.fields.CharField', [], {'default': "'ga_resources.drivers.related.excel'", 'max_length': '255'}),
            'foreign_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'foreign_resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ga_resources.DataResource']"}),
            'how': ('django.db.models.fields.CharField', [], {'default': "'left'", 'max_length': '8'}),
            'key_transform': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'left_index': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'local_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'resource_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'right_index': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'ga_resources.renderedlayer': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'RenderedLayer', '_ormbases': [u'pages.Page']},
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'data_resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ga_resources.DataResource']"}),
            'default_class': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'default_style': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'default_for_layer'", 'to': u"orm['ga_resources.Style']"}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_ga_resources_renderedlayer'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'editable_ga_resources_renderedlayer'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'owned_ga_resources_renderedlayer'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'styles': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ga_resources.Style']", 'symmetrical': 'False'}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_ga_resources_renderedlayer'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'viewable_ga_resources_renderedlayer'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'ga_resources.resourcegroup': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'ResourceGroup', '_ormbases': [u'pages.Page']},
            'is_timeseries': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'min_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'resources': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ga_resources.DataResource']", 'symmetrical': 'False', 'through': u"orm['ga_resources.OrderedResource']", 'blank': 'True'})
        },
        u'ga_resources.style': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'Style', '_ormbases': [u'pages.Page']},
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_ga_resources_style'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'editable_ga_resources_style'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'legend': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'legend_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'legend_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'owned_ga_resources_style'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'stylesheet': ('django.db.models.fields.TextField', [], {}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_ga_resources_style'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'viewable_ga_resources_style'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'pages.page': {
            'Meta': {'ordering': "(u'titles',)", 'object_name': 'Page'},
            '_meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'content_model': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gen_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_menus': ('mezzanine.pages.fields.MenusField', [], {'default': '(1, 2, 3)', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'in_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'keywords_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'children'", 'null': 'True', 'to': u"orm['pages.Page']"}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'titles': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['ga_resources']