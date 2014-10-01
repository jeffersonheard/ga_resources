# from ga_ows.views import wms, wfs
from django.utils.text import slugify
from tarfile import TarFile
from uuid import uuid4
from zipfile import ZipFile
import json

from django.contrib.gis.geos import Polygon, GEOSGeometry
from django.core.files import File
import numpy
import os
from osgeo import osr
from . import Driver
from pandas import DataFrame
import sh
from shapely import geometry, wkb
import pandas
from pysqlite2 import dbapi2 as db
import geojson
import shapely
import re
from ga_resources.drivers import iter
from django import dispatch


def identity(x):
    return '"' + str(x) + '"' if isinstance(x, basestring) else str(x)


def transform(geom, crx):
    if crx:
        geom.Transform(crx)
    return geom


class SpatialiteDriver(Driver):
    """
    Config Parameters:
        * dbname : string (required if not use_django_dbms)
        * table : the default table to use
        * tables : dict of layer names -> tables, must all be in the same coordinate system for now.  Can also be select
          queries. paired with the geometry field name.
        * estimate_extent : see mapnik documentation
        * srid : the native srid of the tables
    """
    WEB_MERCATOR_EXTENT = [-20037508.34, -20037508.34, 20037508.34, 20037508.34]

    def _layer_name(self, s):
        s = unicode(s)
        layer_name = os.path.split(s)[-1]
        layer_name = re.sub('-', '_', slugify(layer_name.rsplit('.', 1)[0]))
        return layer_name


    def __init__(self, data_resource, **kwargs):
        self._conn = None  # lazily open the connection
        self._layers = []  # the whole set of layers available from this resource
        self._default_layer = None  # the default layer object (dict)
        self._conn_template = None  # the template for Mapnik rendering
        self._ready = False  # has ready_data_resource been called yet?
        self.src_ext = 'sqlite'

        super(SpatialiteDriver, self).__init__(data_resource, **kwargs)

    def _connection(self):
        # create a database connection, or use the
        if self._conn is None:
            conn = db.connect(self.get_filename('sqlite') if 'filename' not in self.resource.driver_config else self.resource.driver_config['filename'])
            conn.enable_load_extension(True)
            conn.execute("select load_extension('libspatialite.so')")
            conn.execute("select load_extension('/usr/lib/sqlite3/pcre.so')")
            self._conn = conn
        return self._conn

    def ready_data_resource(self, **kwargs):
        if not self._ready:
            super(SpatialiteDriver, self).ready_data_resource(**kwargs)
            cfg = self.resource.driver_config or {}

            connection = self._connection()
            self._conn_template = {
                'type': 'sqlite',
                'file': self.get_filename('sqlite') if 'filename' not in cfg else cfg['filename'],
                'extent': self.resource.native_bounding_box.extent,
                'wkb_format': 'spatialite'
            }
            def addcfg(k):
                if k in cfg:
                    self._conn_template[k] = cfg[k]

            addcfg('key_field')
            addcfg('encoding')

            # introspect the database to get all the layers
            self._layers = {
                table: {
                    'table': table,
                    'geometry_column': 'GEOMETRY' if geometry_column == 'geometry' else geometry_column,
                    'srid': srid
                }
                for table, geometry_column, _, _, srid, _
                in connection.execute("select * from geometry_columns").fetchall()
            }

            # add any layers that require special selects from the config
            self._layers.update(cfg.get('custom_layers', {}))

            # if there's more than one layer, the user can specify the name of the default
            set_default = cfg.get('default_layer', None)
            if set_default:
                self._default_layer = self._layers[set_default]
            else:
                self._default_layer = self._layers.values()[0]

            self._ready = True

    def get_rendering_parameters(self, **kwargs):
        connection = self._connection()
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(self._default_layer['srid'])

        if 'sublayer' in kwargs:
            table, geometry_field = self._layers[kwargs['sublayer']]
            table = table if not table.lower().startswith('select') else '(' + table + ')'
            srid = connection.execute(
                "select srid({geometry_field}) from {table} limit 1".format(
                    geometry_field=geometry_field,
                    table = table if not table.lower().startswith('select') else '(' + table + ')',
                )).fetchone()[0] # grab the first layer with a geometry
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(srid)
        else:
            table, geometry_field = self._layers[self._default_layer]['table']
            table = table if not table.lower().startswith('select') else '(' + table + ')'
            srid = connection.execute(
                "select srid({geometry_field}) from {table} limit 1".format(
                    geometry_field=geometry_field,
                    table=table if not table.lower().startswith('select') else '(' + table + ')',
                )).fetchone()[0]
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(srid)

        conn = {}.update(self._conn_template)
        conn['table'] = table

        return self.id, srs, conn

    @property
    def layers(self):
        return self._layers

    def _convert_zipfile(self, source_filename):
        # unzip file
        # take stock of files unzipped
        # if shapefiles exist, then look at unique base-names
        # and create new layers in the output spatialite for each base-name
        # and add projection files for each layer if they don't exist

        def _write_shapefile_layer(layer_name, out_filename):
            if not os.path.exists(layer_name + '.prj'):
                with open(layer_name + '.prj', 'w') as prj:
                    prj.write(e4326)

            sh.ogr2ogr(
                '-explodecollections',
                '-skipfailures',
                '-append',
                '-gt', '131072',
                '-t_srs', 'epsg:3857',
                '-f', 'SQLite',
                '-dsco', 'SPATIALITE=YES',
                out_filename, self.cache_path + '/' + layer_name + '.shp'
            )

        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        e4326 = e4326.ExportToWkt()

        out_filename = self.get_filename('sqlite')
        filename = self.get_filename('zip')
        archive = ZipFile(filename)
        names = archive.namelist()
        names = filter(lambda x: ('.' in x) and (not x.startswith('__MACOSX')), sorted(names))
        extensions = {os.path.splitext(name)[-1].lower() for name in names}

        layer_name = self._layer_name(sorted(names)[0])
        if '.shp' in extensions:
            written = []
            for name in names:
                xtn = os.path.splitext(name)[-1]
                this_layer_name = self._layer_name(name)
                if os.path.exists(self.cache_path + '/' + this_layer_name + xtn):
                    os.unlink(self.cache_path + '/' + this_layer_name + xtn)

                archive.extract(name, self.cache_path)
                if name != (this_layer_name + xtn):
                    sh.mv(self.cache_path + '/' + name, self.cache_path + "/" + this_layer_name + xtn)

                written.append(self.cache_path + '/' + this_layer_name + xtn)

                if layer_name != this_layer_name:
                    _write_shapefile_layer(layer_name, out_filename)
                    layer_name = this_layer_name
            _write_shapefile_layer(layer_name, out_filename)
            for name in written:
                os.unlink(name)


        else:
            sh.unzip(filename)
            sh.ogr2ogr(
                '-explodecollections',
                '-skipfailures',
                '-overwrite',
                '-gt', '131072',
                '-t_srs', 'epsg:3857',
                '-f', 'SQLite',
                '-dsco', 'SPATIALITE=YES',
                out_filename, source_filename
            )


    def _convert_dataset(self):
        # convert any other kind of file to spatialite.  this way the sqlite driver can be used with any OGR compatible
        # file
        source_file = self.resource.resource_file
        source_filename, source_extension = os.path.splitext(source_file.name)
        source_extension = source_extension.lower()

        if source_extension.endswith('zip'):
            self._convert_zipfile(source_filename)
            self.resource.original_file = self.resource.resource_file
            self.resource.resource_file = File(open(self.get_filename('sqlite')), name=self.resource.slug.split('/')[-1] + '.sqlite')
            self.resource.save()


        elif not self.src_ext.endswith('sqlite'):
            in_filename = self.get_filename(self.src_ext)
            out_filename = self.get_filename('sqlite')
            sh.rm('-f', out_filename)

            if os.path.exists(out_filename):
                os.unlink(out_filename)

            sh.ogr2ogr(
                '-explodecollections',
                '-skipfailures',
                '-overwrite',
                '-gt', '131072',
                '-t_srs', 'epsg:3857',
                '-f', 'SQLite',
                '-dsco', 'SPATIALITE=YES',
                out_filename, in_filename
            )
            self.resource.original_file = self.resource.resource_file
            self.resource.resource_file = File(open(out_filename), name=self.resource.slug.split('/')[-1] + '.sqlite')
            self.resource.save()

    def cache_data_file(self, freshen=False):
        fresh = super(SpatialiteDriver, self).cache_data_file(freshen=freshen)

        if self.resource.resource_file and self.resource.resource_file.path.endswith('sqlite') and not fresh:
            return False
        else:
            self._convert_dataset()
            return True


    def compute_spatial_metadata(self):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        super(SpatialiteDriver, self).compute_spatial_metadata()
        connection = self._connection()

        table, geometry_field, _, _, srid, _ = connection.execute("select * from geometry_columns").fetchone() # grab the first layer with a geometry
        self._srid = srid if srid else 3857

        dataframe = self.get_filename('dfx')
        if os.path.exists(dataframe):
            os.unlink(dataframe)

        c = connection.cursor()
        c.execute("select AsText(Extent(w.{geom_field})) from {table} as w".format(
            geom_field=geometry_field,
            table=table
        ))

        try:
            xmin, ymin, xmax, ymax = GEOSGeometry(c.fetchone()[0]).extent
        except TypeError:
            xmin = ymin = xmax = ymax = 0.0

        crs = osr.SpatialReference()
        crs.ImportFromEPSG(srid)
        self.resource.native_srs = crs.ExportToProj4()
        c.execute("create index if not exists {table}_ogc_fid on {table} (OGC_FID)".format(table=table))
        c.close()

        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        crx = osr.CoordinateTransformation(crs, e4326)
        x04326, y04326, _ = crx.TransformPoint(xmin, ymin)
        x14326, y14326, _ = crx.TransformPoint(xmax, ymax)
        self.resource.bounding_box = Polygon.from_bbox((x04326, y04326, x14326, y14326))
        self.resource.native_bounding_box = Polygon.from_bbox((xmin, ymin, xmax, ymax))
        self.resource.three_d = False

        self.resource.save()

    def _table(self, **kwargs):
        # todo, this should accept layer as a keyword argument
        cfg = self.resource.driver_config
        if 'sublayer' in kwargs:
            table, geometry_field = cfg['tables'][kwargs['sublayer']]
        else:
            table, geometry_field = self._tablename, self._geometry_field

        return table, geometry_field

    def get_data_for_point(self, wherex, wherey, srs, fuzziness=0, **kwargs):
        result, x1, y1, epsilon = super(SpatialiteDriver, self).get_data_for_point(wherex, wherey, srs, fuzziness, **kwargs)
        cfg = self.resource.driver_config
        table, geometry_field = self._table(**kwargs)

        if epsilon == 0:
            geometry = "GeomFromText('POINT({x} {y})', {srid})".format(
                x=x1,
                y=y1,
                srid=self._srid
            )
        else:
            geometry = "ST_Buffer(GeomFromText('POINT({x} {y})', {srid}), {epsilon})".format(
                x=x1,
                y=y1,
                srid=self._srid,
                epsilon=epsilon
            )

        cursor = self._cursor(**kwargs)
        if table.strip().lower().startswith('select'):
            table = '(' + table + ")"

        cursor.execute("""
        SELECT * FROM {table} as w WHERE ST_Intersects({geometry}, w.{geometry_field}) = 1 
	    AND w.OGC_FID in (
             SELECT ROWID FROM SpatialIndex WHERE f_table_name = '{index}' and search_frame = {geometry})
        """.format(
            geometry=geometry,
            table=table,
            index=table if 'index' not in self.resource.driver_config else self.resource.driver_config['index'],
            geometry_field=geometry_field
        ))


        rows = [list(r) for r in cursor.fetchall()]
        if len(rows):
            keys = [c[0] for c in cursor.description]
            try:
                geometry_column = keys.index(geometry_field)
                keys = keys[:geometry_column] + keys[geometry_column+1:]
                rows = [r[:geometry_column] + r[geometry_column+1:] for r in rows]
            except:
                pass

        return [dict(zip(keys, r)) for r in rows]

    def attrquery(self, key, value):
        if '__' not in key:
            return key + '=' + value

        key, op = key.split('__')
        op = {
            'gt': ">",
            'gte': ">=",
            'lt': "<",
            'lte': '<=',
            'startswith': 'LIKE',
            'endswith': 'LIKE',
            'istartswith': 'ILIKE',
            'iendswith': 'ILIKE',
            'icontains': "ILIKE",
            'contains': "LIKE",
            'in': 'IN',
            'ne': "<>"
        }[op]

        value = {
            'gt': identity,
            'gte': identity,
            'lt': identity,
            'lte': identity,
            'startswith': lambda x: '%' + x,
            'endswith': lambda x: x + '%',
            'istartswith': lambda x: '%' + x,
            'iendswith': lambda x: x + '%',
            'icontains': lambda x: '%' + x + '%',
            'contains': lambda x: '%' + x + '%',
            'in': lambda x: x if isinstance(x, basestring) else '(' + ','.join(identity(a) for a in x) + ')',
            'ne': identity
        }[op](value)

        return ' '.join([key, op, value])

    def _cursor(self, **kwargs):
        connection = self._connection()
        if 'big' in kwargs or (
                self.resource.big and 'count' not in kwargs): # if we don't have control over the result size of a big resource, use a server side cursor
            cursor = connection.cursor('cx' + uuid4().hex)
        else:
            cursor = connection.cursor()

        return cursor


    def as_dataframe(self, **kwargs):
        """
        Creates a dataframe object for a shapefile's main layer using layer_as_dataframe. This object is cached on disk for
        layer use, but the cached copy will only be picked up if the shapefile's mtime is older than the dataframe's mtime.

        :param shp: The shapefile
        :return:
        """

        dfx_path = self.get_filename('dfx')
        if os.path.exists(dfx_path):
            try:
                self._df = pandas.read_pickle(dfx_path)
            except:
                os.unlink(self.get_filename('dfx'))

        if len(kwargs) != 0:
            cfg = self.resource.driver_config
            lyr = {}
            crx = xrc = None

            if 'bbox' in kwargs:
                minx, miny, maxx, maxy = kwargs['bbox']

                if 'srs' in kwargs:
                    if isinstance(kwargs['srs'], basestring):
                        s_srs = osr.SpatialReference()
                        if kwargs['srs'].lower().startswith('epsg:'):
                            s_srs.ImportFromEPSG(int(kwargs['srs'].split(':')[1]))
                        else:
                            s_srs.ImportFromProj4(kwargs['srs'])
                    else:
                        s_srs = kwargs['srs']

                    t_srs = self.resource.srs

                    if s_srs.ExportToProj4() != t_srs.ExportToProj4():
                        crx = osr.CoordinateTransformation(s_srs, t_srs)
                        minx, miny, _ = crx.TransformPoint(minx, miny)
                        maxx, maxy, _ = crx.TransformPoint(maxx, maxy)
                        xrc = osr.CoordinateTransformation(t_srs, s_srs)

                lyr['bbox'] = (minx, miny, maxx, maxy)
            elif 'boundary' in kwargs:
                lyr['boundary'] = kwargs['boundary']

            if 'query' in kwargs:
                lyr['query'] = []

                if isinstance(kwargs['query'], basestring):
                    query = json.loads(kwargs['query'])
                else:
                    query = kwargs['query']

                lyr['query'] = ' AND '.join(self.attrquery(key, value) for key, value in query.items())

            start = kwargs['start'] if 'start' in kwargs else 0
            count = start + kwargs['count'] if 'count' in kwargs else -1


            # contsruct query

            cursor = self.connection # _cursor(**kwargs)

            q = "SELECT AsBinary({geometry_column}), * FROM {table} AS w WHERE "
            addand = False
            if 'bbox' in lyr:
                q += "MBRIntersects(GeomFromText('BBOX({xmin} {ymin} {xax} {ymax})'), w.{geometry_column})"
                q += """ AND w.ROWID in (
                  SELECT ROWID FROM SpatialIndex WHERE f_table_name = '{index}' and search_frame = GeomFromText('BBOX({xmin} {ymin} {xax} {ymax})'))
                """
                addand = True

            if 'boundary' in lyr:
                q += "ST_Intersects(GeomFromText('{boundary}', w.{geometry_column}))"
                q += """ AND w.ROWID in (
                  SELECT ROWID FROM SpatialIndex WHERE f_table_name = '{index}' and search_frame = GeomFromText('BBOX({xmin} {ymin} {xax} {ymax})'))
                """
                addand = True

            if 'query' in lyr:
                if addand:
                    q += ' AND '
                q += lyr['query']

            if count > 0:
                q += ' LIMIT {count}'.format(count=count)

            table, geometry_column = self._table(**kwargs)
            if table.strip().lower().startswith('select'):
                table = '(' + table + ")"

            cursor.execute(q.format(
                boundary=cfg.get('boundary', None),
                geometry_column=geometry_column,
                table=table,
                index = table if 'index' not in self.resource.driver_config else self.resource.driver_config['index']
                **lyr.get('bbox', [None, None, None, None])
            ))
            for i in range(start):
                cursor.fetchone()

            names = [c[0] for c in cursor.description]
            throwaway_ix = names[1:].index(geometry_column) + 1
            records = []
            for record in cursor:
                records.append({name: value for i, (name, value) in enumerate(zip(names, record)) if i != throwaway_ix})
                records[-1]['geometry'] = wkb.loads(record['asbinary'])

            df = DataFrame.from_records(
                data=records,
                index='fid'
            )

            if 'sort_by' in kwargs:
                df = df.sort_index(by=kwargs['sort_by'])

            return df

        elif hasattr(self, '_df'):
            return self._df


        else:
            table, geometry_column = self._table(**kwargs)

            query = "SELECT AsBinary({geometry_column}), * FROM {table}".format(table=table if not table.lower().startswith('select') else '(' + table + ')',
                                                                                geometry_column=geometry_column)
            cursor = self._cursor(**kwargs)
            cursor.execute("select load_extension('libspatialite.so')")


            cursor.execute(query)
            names = [c[0] for c in cursor.description]

            throwaway_ix = names[1:].index(geometry_column) + 1
            records = []
            for record in cursor:
                records.append({name: value for i, (name, value) in enumerate(zip(names, record)) if i != throwaway_ix})
                try:
                    records[-1]['geometry'] = wkb.loads(str(records[-1]['AsBinary(GEOMETRY)']))
                except:
                    pass
                del records[-1]['AsBinary(GEOMETRY)']

            df = DataFrame.from_records(data=records)
            df.to_pickle(dfx_path)
            self._df = df
            return self._df

    def query(
            self,
            geometry_operator='intersects',
            query_geometry=None,
            query_mbr=None,
            query_geometry_srid=None,
            only=None,
            start=None,
            end=None,
            limit=None,
            geometry_format='geojson',
            order_by=None,
            **kwargs
    ):
        operators = {
            'eq': '=',
            '=': '=',
            'gt': '>',
            'ge': '>=',
            'lt': '<',
            'le': '<=',
            'contains': 'like',
            'startswith': 'like',
            'endswith': 'like',
            'isnull': '',
            'notnull': '',
            'ne': '!=',
            'regexp': 'regexp',
            'glob': 'glob',
            'match': 'match',
            'between': 'between',
            'like': 'like'
        }
        geom_operators = {
            'equals','disjoint','touches','within','overlaps','crosses','intersects','contains',
            'mbrequal','mbrdisjoint','mbrtouches','mbrwithin','mbroverlaps','mbrintersects','mbrcontains'
        }

        c = self._cursor()
        keys = self.schema() if not only else only
        table = self._tablename
        index = self._index_name
        geometry = self._geometry_field
        geometry_operator = geometry_operator.lower() if geometry_operator else None

        if query_geometry and not isinstance(query_geometry, basestring):
            query_geometry = query_geometry.wkt
        elif query_mbr:
            query_mbr = shapely.geometry.box(*query_mbr)
            query_geometry = query_mbr.wkt

        limit_clause = 'LIMIT {limit}'.format(**locals()) if limit else ''
        start_clause = 'OGC_FID >= {start}'.format(**locals()) if start else False
        end_clause = 'OGC_FID >= {end}'.format(**locals()) if end else False
        columns = ','.join(keys)
        checks = [key.split('__') if '__' in key else [key, '='] for key in kwargs.keys()]
        where_clauses = ['{variable} {op} ?'.format(variable=v, op=operators[o]) for v, o in checks]
        where_values = ["%" + x + '%' if checks[i][1] == 'contains' else x for i, x in enumerate(kwargs.values())]
        where_values = [x + '%' if checks[i][1] == 'startswith' else x for i, x in enumerate(where_values)]
        where_values = ['%' + x if checks[i][1] == 'endswith' else x for i, x in enumerate(where_values)]

        if start_clause:
            where_clauses.append(start_clause)
        if end_clause:
            where_clauses.append(end_clause)

        if query_geometry:
            qg = "GeomFromText(?, {srid})".format(srid=int(query_geometry_srid)) if query_geometry_srid else "GeomFromText(?)"
            if geometry_operator not in geom_operators and \
                    not geometry_operator.startswith('distance') and \
                    not geometry_operator.startswith('relate'):
                raise NotImplementedError('unsupported query operator for geometry')

            if geometry_operator.startswith('relate'):
                geometry_operator, matrix = geometry_operator.split(':')
                geometry_where = "relate({geometry}, {qg}, '{matrix}')"

            elif geometry_operator.startswith('distance'):
                geometry_operator, srid, comparator, val = geometry_operator.split(":")
                op = operators[comparator]
                val = float(val)
                geometry_where = "distance(transform({geometry}, {srid}), {qg}) {op} {val}".format(**locals()) if len(srid)>0 else "distance({geometry}, {qg}) {op} {val}".format(
                    **locals())
            else:
                geometry_where = """{geometry_operator}({geometry}, {qg})""".format(**locals())

            where_values.append(query_geometry)
            where_clauses.append(geometry_where)

        where_clauses = ' where ' +  ' and '.join(where_clauses) if len(where_clauses) > 0 else ''

        query1 = 'select {columns} from {table} {where_clauses} {limit_clause}'.format(**locals())
        query2 = 'select AsBinary({geometry}) from {table} {where_clauses} {limit_clause}'.format(**locals())

        c.execute("select load_extension('libspatialite.so')")
        c.execute(query1, where_values)

        records = []
        for row in c.fetchall():
            records.append(dict(p for p in zip(keys, row) if p[0] != geometry))

        geo = []
        if (not only) or (geometry in only):
            c.execute(query2, where_values)

            if geometry_format.lower() == 'geojson':
                geo = [json.loads(geojson.dumps(wkb.loads(str(g[0])))) for g in c.fetchall()]
            elif geometry_format.lower() == 'wkt':
                geo = [wkb.loads(str(g[0])).wkt for g in c.fetchall()]
            else:
                geo = [None for g in c.fetchall()]

        gj = []
        for i, record in enumerate(records):
            if (not only) or (geometry in only):
                record[geometry] = geo[i]
            gj.append(record)

        return gj


    @classmethod
    def create_dataset(cls, title, parent=None, geometry_column_name='GEOMETRY', srid=4326, geometry_type='GEOMETRY', owner=None, columns_definitions=()):
        from ga_resources.models import DataResource
        from uuid import uuid4

        filename = os.path.join('/tmp', uuid4().hex + '.sqlite')
        conn = db.connect(filename)
        conn.enable_load_extension(True)
        conn.execute("select load_extension('libspatialite.so')")
        conn.executescript("""
            select initspatialmetadata();
            create table layer (
                OGC_FID INTEGER PRIMARY KEY
            );
            select AddGeometryColumn('layer', '{geometry_column_name}', {srid}, '{geometry_type}', 2, 1);
            select CreateSpatialIndex('layer','{geometry_column_name}');
        """.format(**locals()))

        for column, datatype in columns_definitions:
            conn.execute('alter table layer add column {column} {datatype}'.format(column=column, datatype=datatype))
        conn.commit()
        conn.close()

        ds = DataResource.objects.create(
            title = title,
            parent = parent,
            driver = 'ga_resources.drivers.spatialite',
            resource_file=File(open(filename), filename),
            in_menus=[],
            owner=owner

        )
        ds.resource.compute_spatial_metadata()
        os.unlink(filename)
        return ds

    @classmethod
    def create_dataset_with_parent_geometry(cls, title, parent_dataresource, parent=None, geometry_column_name='GEOMETRY', srid=4326,
                                            geometry_type='GEOMETRY', owner=None, columns_definitions=()):
        from ga_resources.models import DataResource
        from uuid import uuid4

        pconn = parent_dataresource.resource._connection() # FIXME assumes the spatialite driver for the parent, but much faster
        c = pconn.cursor()
        c.execute('select OGC_FID, AsBinary(Transform({geom}, {srid})) from {table}'.format(geom=parent_dataresource.resource._geometry_field, table=parent_dataresource.resource._table_name, srid=srid))
        records = c.fetchall()

        filename = os.path.join('/tmp', uuid4().hex + '.sqlite')
        conn = db.connect(filename)
        conn.enable_load_extension(True)
        conn.execute("select load_extension('libspatialite.so')")
        conn.executescript("""
                    select initspatialmetadata();
                    create table layer (
                        OGC_FID INTEGER PRIMARY KEY
                    );
                    select AddGeometryColumn('layer', '{geometry_column_name}', {srid}, '{geometry_type}', 2, 1);
                    select CreateSpatialIndex('layer','{geometry_column_name}');
                """.format(**locals()))


        conn.executemany('insert into layer (OGC_FID, {geometry_column_name}) values (?, GeomFromWKB(?, {srid}))'.format(**locals()), records)
        conn.commit()

        for column, datatype in columns_definitions:
            conn.execute(
                'alter table layer add column {column} {datatype}'.format(column=column, datatype=datatype))

        conn.close()

        ds = DataResource.objects.create(
            title=title,
            parent=parent,
            driver='ga_resources.drivers.spatialite',
            resource_file=File(open(filename), filename),
            in_menus=[],
            owner=owner
        )
        ds.resource.compute_spatial_metadata()
        for name,ctype in columns_definitions:
            ds.resource.add_column(name, ctype)
        os.unlink(filename)
        return ds

    @classmethod
    def join_data_with_existing_geometry(
            cls, title, parent_dataresource,
            new_data, join_field_in_existing_data, join_field_in_new_data,
            parent=None, geometry_column_name='GEOMETRY', srid=4326, geometry_type='GEOMETRY', owner=None):
        from ga_resources.models import DataResource
        from uuid import uuid4

        pconn = parent_dataresource.resource._connection() # FIXME assumes the spatialite driver for the parent, but much faster
        c = pconn.cursor()
        c.execute('select OGC_FID, AsBinary(Transform({geom}, {srid}), {join_field_in_existing_data}) from {table}'.format(
            geom=parent_dataresource.resource._geometry_field,
            table=parent_dataresource.resource._table_name,
            srid=srid,
            join_field_in_existing_data=join_field_in_existing_data))
        records = c.fetchall()

        filename = os.path.join('/tmp', uuid4().hex + '.sqlite')
        conn = db.connect(filename)
        conn.enable_load_extension(True)
        conn.execute("select load_extension('libspatialite.so')")
        conn.executescript("""
                    select initspatialmetadata();
                    create table layer (
                        OGC_FID INTEGER PRIMARY KEY
                    );
                    select AddGeometryColumn('layer', '{geometry_column_name}', {srid}, '{geometry_type}', 2, 1);
                    select CreateSpatialIndex('layer','{geometry_column_name}');
                    create index layer_{join_field_on_existing_data} on layer ({join_field_on_existing_data});
                """.format(**locals()))


        conn.executemany('insert into layer (OGC_FID, {geometry_column_name}, {join_field_in_existing_data}) values (?, GeomFromWKB(?, {srid}))'.format(**locals()), records)
        conn.commit()

        for column in new_data.keys():
            if new_data[column].dtype is numpy.float64:
                datatype = 'REAL'
            elif new_data[column].dtype is numpy.int64:
                datatype = 'INTEGER'
            else:
                datatype = 'TEXT'

            conn.execute(
                'alter table layer add column {column} {datatype}'.format(column=column, datatype=datatype))

        columns = list(new_data.keys())
        conn.executemany("""
            UPDATE layer SET
            {columns}
            WHERE {join_field_in_existing_data}=?
        """.format(
            columns=','.join(k + '=?' for k in columns),
            join_field_in_existing_data=join_field_in_existing_data
        ), [[r[c] for c in columns] + [r[join_field_in_new_data]] for _, r in new_data.iterrows()] )

        conn.close()

        ds = DataResource.objects.create(
            title=title,
            parent=parent,
            driver='ga_resources.drivers.spatialite',
            resource_file=File(open(filename), filename),
            in_menus=[],
            owner=owner
        )
        ds.resource.compute_spatial_metadata()
        os.unlink(filename)
        return ds

    @classmethod
    def derive_dataset(cls, title, parent_page, parent_dataresource, owner=None):
        from ga_resources.models import DataResource
        from django.conf import settings
        # create a new sqlite datasource
        slug, srs, child_spec = parent_dataresource.driver_instance.get_rendering_parameters()
        filename = child_spec['file']
        new_filename = parent_dataresource.driver_instance.get_filename('sqlite').split('/')[-1]
        new_filename = settings.MEDIA_ROOT + '/' + new_filename
        sh.ogr2ogr(
            '-f', 'SQLite',
            '-dsco', 'SPATIALITE=YES',
            '-t_srs', 'EPSG:3857',
            '-overwrite',
            '-skipfailures',
            new_filename, filename
        )
        ds = DataResource.objects.create(
            title=title,
            content=parent_dataresource.content,
            parent=parent_page,
            resource_file = new_filename,
            driver='ga_resources.drivers.spatialite',
            in_menus=[],
            owner=owner

        )
        return ds


driver = SpatialiteDriver


class SpatialiteVectorDataManager(iter.VectorDataManager):


    def _cursor(self, **kwargs):
        connection = self.driver._connection()
        if 'big' in kwargs or (
                self.resource.big and 'count' not in kwargs): # if we don't have control over the result size of a big resource, use a server side cursor
            cursor = connection.cursor('cx' + uuid4().hex)
        else:
            cursor = connection.cursor()

        return cursor

    @property
    def field_names(self):
        conn = self.driver._connection()
        names = [c[0] for c in conn.cursor().execute('select * from {table} limit 1'.format(table=self._tablename)).description]
        return names

    @property
    def schema(self):
        conn = self.driver._connection()
        human_names = {
            'VARCHAR': 'Text',
            'FLOAT': 'Real',
            'POLYGON': 'Polygon',
            'POINT': 'Point',
            'LINESTRING': 'LineString',
            'MULTIPOINT': 'MultiPoint',
            'MULTIPOLYGON': 'MultiPolygon',
            'MULTILINESTRING': 'MultiLineString',
            'GEOMETRYCOLLECTION': 'GeometryCollection',
        }

        return dict(
            [(name, human_names.get(typename, '*')) for
                _, name, typename, _, _, _ in
                conn.execute('pragma table_info({table})'.format(table=self._index_name)).fetchall()])

    def create_index(self, table=None, *fields):
        c = self._cursor()
        index_name = '_'.join(fields)
        c.execute('create index {index_name} on {table} ({fields})'.format(
            index_name=index_name,
            table=self._tablename,
            fields=','.join(fields)
        ))

    def drop_index(self, table=None, *fields):
        c = self._cursor()
        index_name = '_'.join(fields)
        c.execute('create index {index_name} on {table} ({fields})'.format(
            index_name=index_name,
            table=self._tablename,
            fields=','.join(fields)
        ))

    def add_column(self, name, field_type, table=None):
        c = self._cursor()
        c.execute('alter table {table} add column {column_name} {column_type}'.format(
            table=self._tablename,
            column_name=name,
            column_type=field_type
        ))
        c.close()
        self._conn.commit()

    def delete_feature(self, key, layer=None):
        c = self._cursor()
        c.execute('delete from {table} where ogc_fid={key}'.format(
            table=self._tablename,
            key=key
        ))
        c.close()
        self._conn.commit()

    def append_feature(self, layer=None, **values):
        c = self._cursor()
        insert_stmt = 'insert into {table} ({keys}) values ({values})'

        keys = [k for k in values.keys() if k != 'srid']
        vals = [values[key] for key in keys]
        parms = ','.join(['?' if key != self._geometry_field else 'GeomFromText(?, {srid})'.format(srid=self._srid if "srid" not in values else values['srid']) for key in keys])
        insert_stmt = insert_stmt.format(
            table=self._tablename,
            keys=','.join(keys),
            values=parms
        )
        c.execute(insert_stmt, vals)
        c.execute('SELECT max(OGC_FID) from {table}'.format(table=self._tablename))
        new_id = c.fetchone()[0]
        c.close()
        self._conn.commit()
        return self.get_row(ogc_fid=new_id, geometry_format='wkt')

    def update_feature(self, ogc_fid, layer=None, **values):
        c = self._cursor()
        insert_stmt = 'update {table} set {set_clause} where OGC_FID={ogc_fid}'
        table = self._tablename
        if 'OGC_FID' in values:
            del values['OGC_FID']

        set_clause = ','.join(["{key}=:{key}".format(key=key) if key != self._geometry_field else '{key}=GeomFromText(:{key}, {srid})'.format(key=key, srid=self._srid if "srid" not in values else
        values['srid']) for key in values.keys()])

        c.execute(insert_stmt.format(**locals()), values)
        c.close()
        self._conn.commit()
        return self.get_row(ogc_fid=ogc_fid, geometry_format='wkt')

    def get_feature(self, ogc_fid, geometry_format='geojson'):
        c = self._cursor()
        keys = self.schema()
        table = self._tablename
        geometry = self._geometry_field

        select = 'select * from {table} where OGC_FID={ogc_fid}'.format(**locals())
        select2 = 'select AsBinary({geometry}) from {table} where OGC_FID={ogc_fid}'.format(**locals())

        c.execute("select load_extension('libspatialite.so')")
        values = c.execute(select).fetchone()
        record = dict(p for p in zip(keys, c.execute(select).fetchone()) if p[0] != geometry)
        geo = c.execute(select2).fetchone()
        # gj = { 'type' : 'feature', 'geometry' : json.loads(geojson.dumps(wkb.loads(str(geo[0])))), 'properties' : record }
        gj = record
        if geometry_format.lower() == 'geojson':
            gj[self._geometry_field] = json.loads(geojson.dumps(wkb.loads(str(geo[0]))))
        elif geometry_format.lower() == 'wkt':
            gj[self._geometry_field] = wkb.loads(str(geo[0])).wkt

        return gj

    def get_feature_collection(self, ogc_fid_start=0, ogc_fid_end=None, limit=50, layer=None, geometry_format='geojson'):
        c = self._cursor()
        keys = self.schema()
        table = self._tablename
        geometry = self._geometry_field

        if ogc_fid_end:
            select = 'select * from {table} where OGC_FID >= {ogc_fid_start} and OGC_FID <= {ogc_fid_end};'.format(**locals())
            select2 ='select AsBinary({geometry}) from {table} where OGC_FID >= {ogc_fid_start} and OGC_FID <= {ogc_fid_end}'.format(**locals())
        elif limit > -1:
            select = 'select * from {table} where OGC_FID >= {ogc_fid_start} LIMIT {limit};'.format(
                **locals())
            select2 = 'select AsBinary({geometry}) from {table} where OGC_FID >= {ogc_fid_start} LIMIT {limit};'.format(
                **locals())
        else:
            select = 'select * from {table} where OGC_FID >= {ogc_fid_start}'.format(**locals())
            select2 = 'select AsBinary({geometry}) from {table} where OGC_FID >= {ogc_fid_start}'.format(**locals())

        c.execute("select load_extension('libspatialite.so')")
        c.execute(select)

        records = []
        for row in c.fetchall():
            records.append( dict(p for p in zip(keys, row) if p[0] != geometry) )

        c.execute(select2)
        if geometry_format.lower() == 'geojson':
            geo = [json.loads(geojson.dumps(wkb.loads(str(g[0])))) for g in c.fetchall()]
        elif geometry_format.lower() == 'wkt':
            geo = [wkb.loads(str(g[0])).wkt for g in c.fetchall()]
        else:
            geo = [None for g in c.fetchall()]

        gj = []
        for i, record in enumerate(records):
            record[self._geometry_field] = geo[i]
            gj.append(record)
            # gj.append({'type': 'feature', 'geometry': geo[i], 'properties': record})
        return gj