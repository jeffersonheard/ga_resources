import os
import math
from django.conf import settings
from osgeo import osr
from pysqlite2 import dbapi2 as db
from hashlib import md5
from collections import OrderedDict
from ga_resources import dispatch
import sh

CACHE_ROOT = getattr(settings, 'CACHE_ROOT', settings.MEDIA_ROOT)
LAYER_CACHE_PATH = getattr(settings, "LAYER_CACHE_PATH", os.path.join(CACHE_ROOT, '.cache', 'layers'))

if not os.path.exists(CACHE_ROOT):
    sh.mkdir('-p', CACHE_ROOT)

if not os.path.exists(LAYER_CACHE_PATH):
    sh.mkdir('-p', LAYER_CACHE_PATH)


def data_cache_path(page, page_id_field='slug'):
    """
    Get (and make) local data cache path for data
    :param page:
    :return:
    """
    path = os.path.join(CACHE_ROOT, '.cache', 'data', *os.path.split(getattr(page, page_id_field)))
    if not os.path.exists(path):
        sh.mkdir('-p', path)


def delete_data_cache(page, page_id_field='slug'):
    path = data_cache_path(page, page_id_field)
    sh.rm('-rf', path)

def trim_cache(layers=list(), styles=list()):
    """destroy relevant tile caches and cached mapnik files that are affected by a style or layer change"""
    names = []
    data = db.connect(os.path.join(LAYER_CACHE_PATH, 'directory.sqlite'))
    c = data.cursor()
    c.executemany('select basename from layers where slug=?', layers)
    names.extend( c.fetchall() )
    c.close()
    c = data.cursor()
    c.executemany('select basename from styles where slug=?', styles)
    names.extend( c.fetchall() )

    for name in names:
        if os.path.exists(name + '.mbtiles'):
            os.unlink(name + '.mbtiles')
        if os.path.exists(name + '.json'):
            os.unlink(name + '.json')
        if os.path.exists(name + '.wmsresults'):
            os.unlink(name + '.wmsresults')
        if os.path.exists(name + '.mml'):
            os.unlink(name + '.mml')
        if os.path.exists(name + '.xml'):
            os.unlink(name + '.xml')
        if os.path.exists(name + '.carto'):
            os.unlink(name + '.carto')


### following procedures and functions are in support of the tiled mapping services, TMS

def deg2num(lat_deg, lon_deg, zoom):
    """
    degree to tile number

    :param lat_deg: degrees lon
    :param lon_deg: degrees lat
    :param zoom: web mercator zoom level
    :return: x, y tile coordinates as a tuple
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    """
    Tile number to degree of southwest point.

    :param xtile: column
    :param ytile: row
    :param zoom: mercator zoom level
    :return: the degree of the southwest corner as a lat/lon pair.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)


class MBTileCache(object):
    """
    MBTiles is MapBox's tile cache format.  We use it to store rendered tiles for display in a compact format.
    """

    STANDARD_SRS = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m" \
                   " +nadgrids=@null"

    def __init__(self, layers, styles, bgcolor=None, transparent=True, query=None, srs=STANDARD_SRS, **kwargs):
        """
        Defines a cache that is specific to a set of layers, styles, spatial reference, and extra keyword args that
        are passed to the renderer.

        NOTE: currently only the standard SRS is supported.  This relies on the slippy map tile specification for
        geodetic coordinate to tile index location.

        :param layers: A list of layer identifier strings
        :param styles: A list of style identifier strings
        :param srs: A spatial reference system in proj.4 format. Typically (and by standard) Google Mercator
        :param kwargs: Extra keyword args to pass to the renderer
        """
        self.srs = srs
        self.name = CacheManager.cache_entry_name(layers, self.srs, styles, bgcolor, transparent, query)
        self.cachename = self.name + '.mbtiles'
        self.layers = layers if not isinstance(layers, basestring) else [layers]
        self.styles = styles if not isinstance(styles, basestring) else [styles]
        self.kwargs = kwargs

        # build a coordinate transformation based on the spatial reference passed in
        e4326 = osr.SpatialReference()
        e3857 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        e3857.ImportFromEPSG(3857)
        self.crx = osr.CoordinateTransformation(e4326, e3857)

        self.cache = db.connect(self.cachename)
        self._ensure_cache_initted()

    def _ensure_cache_initted(self):
        if not os.path.exists(self.cachename):
            conn = self.cache
            cursor = conn.cursor()
            cursor.executescript("""
                    BEGIN TRANSACTION;
                    CREATE TABLE android_metadata (locale text);
                    CREATE TABLE grid_key (grid_id TEXT,key_name TEXT);
                    CREATE TABLE grid_utfgrid (grid_id TEXT,grid_utfgrid BLOB);
                    CREATE TABLE keymap (key_name TEXT,key_json TEXT);
                    CREATE TABLE images (tile_data blob,tile_id text);
                    CREATE TABLE map
                        (zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_id TEXT,grid_id TEXT);
                    CREATE TABLE metadata (name text,value text);
                    CREATE VIEW tiles
                        AS SELECT
                            map.zoom_level AS zoom_level,
                            map.tile_column AS tile_column,
                            map.tile_row AS tile_row,
                            images.tile_data AS tile_data
                            FROM map
                            JOIN images ON images.tile_id = map.tile_id
                            ORDER BY zoom_level,tile_column,tile_row;
                    CREATE VIEW grids
                        AS SELECT
                            map.zoom_level AS zoom_level,
                            map.tile_column AS tile_column,
                            map.tile_row AS tile_row,
                            grid_utfgrid.grid_utfgrid AS grid
                            FROM map
                            JOIN grid_utfgrid ON grid_utfgrid.grid_id = map.grid_id;
                    CREATE VIEW grid_data
                        AS SELECT
                            map.zoom_level AS zoom_level,
                            map.tile_column AS tile_column,
                            map.tile_row AS tile_row,
                            keymap.key_name AS key_name,
                            keymap.key_json AS key_json
                            FROM map
                            JOIN grid_key ON map.grid_id = grid_key.grid_id
                            JOIN keymap ON grid_key.key_name = keymap.key_name;
                    CREATE UNIQUE INDEX grid_key_lookup ON grid_key (grid_id,key_name);
                    CREATE UNIQUE INDEX grid_utfgrid_lookup ON grid_utfgrid (grid_id);
                    CREATE UNIQUE INDEX keymap_lookup ON keymap (key_name);
                    CREATE UNIQUE INDEX images_id ON images (tile_id);
                    CREATE UNIQUE INDEX map_index ON map (zoom_level, tile_column, tile_row);
                    CREATE UNIQUE INDEX name ON metadata (name);
                    END TRANSACTION;
                    ANALYZE;
                    VACUUM;
               """)
            cursor.close()

    def fetch_tile(self, z, x, y):
        """
        Fetch map by slippy map tile ID.  Render it if it's not rendered already.

        :param z: zoom level
        :param x: x
        :param y: y
        :return:
        """
        tile_id = u':'.join(str(k) for k in (z,x,y))
        sw = self.crx.TransformPoint(*num2deg(x, y+1, z))
        ne = self.crx.TransformPoint(*num2deg(x+1, y, z))
        width = 256
        height = 256
        insert_map = "INSERT OR REPLACE INTO map (tile_id,zoom_level,tile_column,tile_row,grid_id) VALUES(?,?,?,?,'');"
        insert_data = "INSERT OR REPLACE INTO images (tile_id,tile_data) VALUES(?,?);"

        c = self.cache.cursor()
        c.execute("SELECT tile_data FROM images WHERE tile_id=?", [tile_id])
        try:
            blob = buffer(c.fetchone()[0])
        except:
            dispatch.tile_rendered.send(sender=CacheManager, layers=self.layers, styles=self.styles)
            from ga_resources.tasks import render as delayed_render
            blob = delayed_render.delay(
                'png', width, height,
                (sw[0], sw[1], ne[0], ne[1]), self.srs, self.styles, self.layers, **self.kwargs).get()
            if len(blob) > 350:
                blob = buffer(blob)
                d = self.cache.cursor()
                d.execute(insert_map, [tile_id, z, x, y])
                d.execute(insert_data, [tile_id, blob])
                self.cache.commit()
                d.close()
        c.close()

        return blob

    def seed_tiles(self, min_zoom, max_zoom, minx, miny, maxx, maxy):
        """
        Force rendering of tiles for an area.

        :param min_zoom:
        :param max_zoom:
        :param minx:
        :param miny:
        :param maxx:
        :param maxy:
        :return:
        """
        for z in range(min_zoom, max_zoom+1):
            mnx, mny = deg2num(miny, minx, z)
            mxx, mxy = deg2num(maxy, maxx, z)
            for x in range(mnx, mxx+1):
                for y in range(mny, mxy+1):
                    self.fetch_tile(z, x, y)

    @classmethod
    def shave_cache(cls, filename, bbox):
        """
        Empties a bounding box out of the cache at all zoom levels to be regenerated on demand.  For supporting
        minor edits on data.

        :param filename:
        :param bbox:
        :return:
        """

        x1, y1, x2, y2 = bbox
        conn = db.connect(filename)
        c = conn.cursor()
        c.execute('select min(zoom_level) from map')
        c.execute('select max(zoom_level) from map')
        min_zoom = c.fetchone()
        max_zoom = c.fetchone()

        if min_zoom:
            min_zoom = min_zoom[0]
        else:
            min_zoom = 0
        if max_zoom:
            max_zoom = max_zoom[0]
        else:
            max_zoom = 32

        c.close()

        c = conn.cursor()

        del_map_entry = """
        DELETE FROM map WHERE
            tile_column >= ? AND
            tile_row >= ? AND
            tile_column <= ? AND
            tile_row <= ? AND
            zoom_level = ?
        """

        del_tile_data = """
        DELETE FROM images
        WHERE tile_id IN (
            SELECT tile_id
            FROM map WHERE
                tile_column >= ? AND
                tile_row >= ? AND
                tile_column <= ? AND
                tile_row <= ? AND
                zoom_level = ?
        )
        """
        e4326 = osr.SpatialReference()
        e3857 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        e3857.ImportFromEPSG(3857)
        crx = osr.CoordinateTransformation(e3857, e4326)
        x1, y1, _ = crx.TransformPoint(x1, y1)
        x2, y2, _ = crx.TransformPoint(x2, y2)

        for zoom in range(min_zoom, max_zoom+1):
            a1, b1 = deg2num(y1, x1, zoom)
            a2, b2 = deg2num(y2, x2, zoom)
            c.execute(del_tile_data, [a1, b1, a2, b2, zoom])
            c.execute(del_map_entry, [a1, b1, a2, b2, zoom])

        c.execute('ANALYZE')
        c.execute('VACUUM')

        conn.commit()
        conn.close()


class WMSResultsCache(object):
    """
    Cache for rendered WMS results.
    """
    def __init__(self, layers, srs, styles, **kwargs):
        self.name = CacheManager.cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', None),
            query=kwargs.get('query', None)
        )
        self.cachename = self.name + '.wmscache'

        self.srs = srs
        self.layers = layers
        self.styles = styles
        self.kwargs = kwargs

        if os.path.exists(self.cachename):
            conn = db.connect(self.cachename)
            conn.enable_load_extension(True)
            conn.execute("select load_extension('libspatialite.so')")
        else:
            conn = db.connect(self.cachename)
            conn.enable_load_extension(True)
            conn.execute("select load_extension('libspatialite.so')")
            cursor = conn.cursor()
            cursor.executescript("""
                 BEGIN TRANSACTION;
                 SELECT InitSpatialMetadata();
                 CREATE TABLE tiles (hash_key TEXT, last_use DATETIME, tile_data BLOB);
                 SELECT AddGeometryColumn('tiles','bounds', 4326, 'POLYGON', 'XY');
                 SELECT CreateSpatialIndex('tiles','bounds');
                 CREATE UNIQUE INDEX hash_key_lookup ON tiles (hash_key);
                 CREATE INDEX lru ON tiles (last_use);
                 END TRANSACTION;
                 ANALYZE;
                 VACUUM;
            """)
            cursor.close()
            CacheManager.get().register_cache(layers, styles, self.cachename)

        self.cache = conn


    @classmethod
    def shave_cache(self, filename, bbox):
        """
        Empties a cache of all records overlapping a certain bounding box so they are regenerated on demand.  For
        supporting minor edits on data

        :param filename:
        :param bbox:
        :return:
        """
        x1,y1,x2,y2 = bbox
        conn = db.connect(filename)
        conn.execute('delete from tiles where Intersects(bounds, BuildMBR({x1},{y1},{x2},{y2}))'.format(**locals()))
        conn.close()


    def fetch_data(self, fmt, width, height, bbox, srs, styles, layers, **kwargs):
        """
        Fetch the rendered map data for a particular bounding box or render it.

        :param fmt:
        :param width:
        :param height:
        :param bbox:
        :param srs:
        :param styles:
        :param layers:
        :param kwargs:
        :return:
        """
        cache_basis_for_spec = CacheManager.cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', None),
            query=kwargs.get('query', None)
        )
        filename = "{name}.{bbox}.{width}x{height}.{fmt}".format(
            name=cache_basis_for_spec,
            bbox='_'.join(str(b) for b in bbox),
            width=width,
            height=height,
            fmt=fmt
        )

        c = self.cache.cursor()
        c.execute("UPDATE tile_data last_use = datetime('now') WHERE hash_key=?", filename)
        c.execute('SELECT tile_data FROM tiles WHERE hash_key=?', filename)
        insert_data = """
            INSERT INTO tile_data (hash_key, last_use, tile_data, bounds)
            VALUES (
                ?,
                datetime('now'),
                ?,
                GeomFromText('POLYGON(({x1} {y1}, {x2} {y1}, {x2} {y2}, {x1} {y2}, {x1} {y1})')
            )
        """.format(x1=bbox[0],y1=bbox[1],x2=bbox[2],y2=bbox[3])
        try:
            blob = c.fetchone()[0]
        except:
            from ga_resources.drivers import render
            dispatch.wms_rendered.send(CacheManager, layers=self.layers, styles=self.styles)
            tile_id, blob = render('png', width, height, bbox, self.srs, self.styles,
                                   self.layers, **self.kwargs)

            with self.cache.cursor() as d:
                d.execute(insert_data, filename, blob)
        return blob



class CacheManager(object):

    @staticmethod
    def cache_entry_name(layers, srs, styles, bgcolor=None, transparent=True, query=None):
        """
        Calculate a cache entry name based on parameters that would create a unique tile set

        :param layers: a list of layer identifiers (strings)
        :param srs: a spatial reference string (typically proj.4 or EPSG code)
        :param styles: a list of style identifiers (strings)
        :param bgcolor: a hextuple of RGB background color
        :param transparent: whether or not the background is transparent
        :param query: a query that limits the results
        :return: a path/base_file_name string that can be used to create a set of files
        """
        d = OrderedDict(layers=layers, srs=srs, styles=styles, bgcolor=bgcolor, transparent=transparent)
        if query: # insert the query keys, but ensure a consistent order
            keys = sorted(query.keys())
            for k in keys:
                d[k] = query[k]

        shortname = md5()
        for key, value in d.items():
            shortname.update(key)
            shortname.update(unicode(value))
        cache_entry_basename = shortname.hexdigest()
        return os.path.join(LAYER_CACHE_PATH, cache_entry_basename)

    def __init__(self, layer_id_field='slug', style_id_field='slug'):
        """
        Create the cache.

        :param layer_id_field: the name of the attribute on the layer class that designates its id
        :param style_id_field: the name of the attribute on the style class that designates its id
        """
        self.cachename = os.path.join(LAYER_CACHE_PATH, 'directory.sqlite')
        self.tile_caches = {}
        self.wms_caches = {}
        self.layer_id_field = layer_id_field
        self.style_id_field = style_id_field

        if os.path.exists(self.cachename):
            conn = db.connect(self.cachename)
        else:
            conn = db.connect(self.cachename)
            cursor = conn.cursor()
            cursor.executescript("""
                BEGIN TRANSACTION;
                CREATE TABLE caches (name text PRIMARY KEY, kind text);
                CREATE TABLE layers (slug text primary key, cache_name text);
                CREATE TABLE styles (slug text primary key, cache_name text);
                END TRANSACTION;
                ANALYZE;
                VACUUM;
            """)
            conn.commit()

        self.conn = conn

    @classmethod
    def get(cls):
        """
        Get a thread-local object for this cache manager

        :return:
        """
        import threading

        if not hasattr(cls, '_mgr'):
            cls._mgr = threading.local()
        if not hasattr(cls._mgr, 'mgr'):
            cls._mgr.mgr = CacheManager()

        return cls._mgr.mgr

    def get_tile_cache(self, layers, styles, bgcolor=None, transparent=True, query=None, srs=MBTileCache.STANDARD_SRS):
        """
         Get the tile cache for a unique set of layers, styles
        :param layers: a list of Layer objects (or analogues) or string layer identifiers
        :param styles: a list of Style objects (or analogues) or string stylesheet identifiers
        :param bgcolor: a hextuple of RGB background color
        :param transparent: whether or not the background is transparent
        :param query: a query that limits the results
        :param srs: a spatial reference identifier or proj.4 string
        :return: an MBTileCache object
        """

        name = CacheManager.cache_entry_name(
            layers,
            srs,
            styles,
            bgcolor,
            transparent,
            query
        )

        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO caches (name, kind) VALUES (:name, :kind)", {"name": name, "kind": "tile" })
        for layer in layers:
            c.execute("INSERT OR REPLACE INTO layers (slug, cache_name) VALUES (:layer, :name)", {
                "layer": layer if isinstance(layer, basestring) else getattr(layer, self.layer_id_field),
                "name": name
            })
        for style in styles:
            c.execute("INSERT OR REPLACE INTO styles (slug, cache_name) VALUES (:style, :name)", {
                "style": style if isinstance(style, basestring) else getattr(style, self.style_id_field),
                "name": name
            })
        self.conn.commit()

        if name not in self.tile_caches:
            self.tile_caches[name] = MBTileCache(layers, styles,
                                                 bgcolor,
                                                 transparent,
                                                 query
            )
        return self.tile_caches[name]


    def get_wms_cache(self, layers, srs, styles, **kwargs):
        name = CacheManager.cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', True),
            query=kwargs.get('query', None)
        )
        if name not in self.wms_caches:
            self.wms_caches[name] = MBTileCache(layers, styles,
                                                bgcolor=kwargs.get('bgcolor', None),
                                                transparent=kwargs.get('transparent', True),
                                                query=kwargs.get('query', None))
        return self.wms_caches[name]


    def shave_caches(self, layers, bbox):
        """Iterate over all caches using a particular resource and remove any resources overlapping the bounding box"""

        c = self.conn.cursor()
        c.executemany(
            'select cache_name from layers where slug=?',
            [(layer if isinstance(layer, basestring) else getattr(layer, self.layer_id_field)) for layer in layers]
        )
        for (k,) in c.fetchall():
            MBTileCache.shave_cache(k+'.mbtiles', bbox.extent)

    def remove_caches_for_layer(self, layer):
        """Iterate over all the caches using a particular layer and burn them"""
        c = self.conn.cursor()
        c.execute(
            'select cache_name from layers where slug=?',
            [layer if isinstance(layer, basestring) else getattr(layer, self.layer_id_field)]
        )
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                os.unlink(k + '.mbtiles')
            if os.path.exists(k + '.json'):
                os.unlink(k + '.json')
            if os.path.exists(k + '.wmsresults'):
                os.unlink(k + '.wmsresults')
            if os.path.exists(k + '.mml'):
                os.unlink(k + '.mml')
            if os.path.exists(k + '.xml'):
                os.unlink(k + '.xml')
            if os.path.exists(k + '.carto'):
                os.unlink(k + '.carto')

            c.execute('delete from caches where name=?', [k])
            c.execute('delete from layers where cache_name=?', [k])
            c.execute('delete from styles where cache_name=?', [k])

    def remove_caches_for_style(self, style):
        """Iterate over all caches using a particular stylesheet and burn them"""
        c = self.conn.cursor()
        c.execute('select cache_name from styles where slug=?', [
            style if isinstance(style, basestring) else getattr(style, self.style_id_field)])
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                os.unlink(k + '.mbtiles')
            if os.path.exists(k + '.json'):
                os.unlink(k + '.json')
            if os.path.exists(k + '.wmsresults'):
                os.unlink(k + '.wmsresults')
            if os.path.exists(k + '.mml'):
                os.unlink(k + '.mml')
            if os.path.exists(k + '.xml'):
                os.unlink(k + '.xml')
            if os.path.exists(k + '.carto'):
                os.unlink(k + '.carto')
            c.execute('delete from caches where name=?', [k])
            c.execute('delete from layers where cache_name=?', [k])
            c.execute('delete from styles where cache_name=?', [k])

    def layer_cache_size(self, layer):
        sz = 0
        c = self.conn.cursor()
        c.execute(
            'select cache_name from layers where slug=?',
            [layer if isinstance(layer, basestring) else getattr(layer, self.layer_id_field)]
        )
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                sz += os.stat(k + '.mbtiles').st_size
        return sz



def resource_cache_size(resource):
    from ga_resources import models as m
    self = CacheManager()

    return sum(self.layer_cache_size(layer) for layer in
               m.RenderedLayer.objects.filter(
                   data_resource__slug=resource if isinstance(resource, basestring) else resource.slug
               )
    )


def remove_caches_for_resource(resource):
    """Iterate over all caches using a particular resource and burn them"""

    from ga_resources import models as m
    self = CacheManager()

    for layer in m.RenderedLayer.objects.filter(data_resource__slug = resource):
        self.remove_caches_for_layer(layer.slug)
