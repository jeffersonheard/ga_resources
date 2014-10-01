"""
Abstract base classes and utility functions for creating querysets and iterators out of data
"""

class VectorDataManager(object):
    def __init__(self, resource):
        self.resource = resource
        self.driver = resource.driver_instance

    def add_column(self, column_name, column_type):
        raise NotImplementedError()

    def remove_column(self, column_name, column_type):
        raise NotImplementedError()

    def create_index(self, table=None, *fields):
        raise NotImplementedError()

    def drop_index(self, table=None, *fields):
        raise NotImplementedError()

    def join_dataframe(self, dataframe, join_key):
        raise NotImplementedError()

    def replace_data_in_features(self, dataframe, join_key):
        raise NotImplementedError()

    def append_feature_collection(self):
        raise NotImplementedError()

    def append_feature(self):
        raise NotImplementedError()

    def get_feature(self, ogc_fid, geometry_format='geojson'):
        raise NotImplementedError()

    def update_feature(self, ogc_fid, **values):
        raise NotImplementedError()

    def delete_feature(self, ogr_fid):
        raise NotImplementedError()

    def features_at_point(self, wherex, wherey, srs, fuzziness=0, **kwargs):
        raise NotImplementedError()

    @property
    def tables(self):
        raise NotImplementedError()

    @property
    def layers(self):
        raise NotImplementedError()

    @property
    def field_names(self):
        raise NotImplementedError()

    @property
    def schema(self):
        raise NotImplementedError()

    @property
    def queryset(self):
        return QuerySet(self.resource)


class QuerySet(object):
    def __init__(self, resource, parent=None):
        self.resource = resource

    def all(self):
        pass

    def filter(self):
        pass

    def exclude(self):
        pass

    def annotate(self):
        pass

    def aggregate(self):
        pass

    def values(self):
        pass

    def values_list(self):
        pass

    def sqlite(self):
        """
        Return a spatialite dataset with the query results poured into it.

        :return:
        """
        pass

    def geojson(self):
        """
        Return a featurecollection with the query results poured into it.
        :return:
        """

    def dataframe(self):
        """
        Return a feature collection as a dataframe in Pandas for analysis.

        :return:
        """

    def get(self):
        pass

    def spatial_filter(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def transform(self, srid):
        pass