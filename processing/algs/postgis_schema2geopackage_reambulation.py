# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsVectorLayer,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       Qgis,
                       QgsProviderRegistry,
                       QgsDataSourceUri)

qgs_version = Qgis.QGIS_VERSION_INT
if qgs_version < 31400:
    from processing.tools import postgis
else:
    from qgis.core import QgsProcessingParameterProviderConnection
    from qgis.core import QgsProcessingParameterDatabaseSchema

    
import sqlite3 as lite
import psycopg2
import subprocess 
from PyQt5.QtCore import QVariant


class PostGISSchema2GeopackageReambulation(QgsProcessingAlgorithm):
    # Constants used to refer to parameters

    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    SHAPEFILE = 'SHAPEFILE'
    GEOPACKAGE = 'GEOPACKAGE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: PostGISSchema2GeopackageReambulation", string)    
    
    def createInstance(self):
        return PostGISSchema2GeopackageReambulation()

    def name(self):
        return 'postgis_schema2geopackage_reambulation'

    def displayName(self):
        return self.tr('Reambulation: PostGIS Schema to Geopackage')

    def group(self):
        return self.tr('Reambulation')

    def groupId(self):
        return 'reambulation'

    def shortHelpString(self):
        return self.tr("Export the layers in a PostGIS schema to a geopackage in order to do reambulation.")

    def initAlgorithm(self, config=None):
        # Database Connection
        if qgs_version < 31400:
            db_param = QgsProcessingParameterString(
                self.DATABASE,
                self.tr('Database Connection'))
            db_param.setMetadata({
                'widget_wrapper': {
                    'class': 'processing.gui.wrappers_postgis.ConnectionWidgetWrapper'}})
        else:
            db_param = QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr('Database Connection'),
                'postgres')

        self.addParameter(db_param)
        
        # Schema
        if qgs_version < 31400:
            schema_param = QgsProcessingParameterString(
                self.SCHEMA,
                self.tr('Schema'), 'bc250_base')
            schema_param.setMetadata({
                'widget_wrapper': {
                    'class': 'processing.gui.wrappers_postgis.SchemaWidgetWrapper',
                    'connection_param': self.DATABASE}})
        else:
            schema_param = QgsProcessingParameterDatabaseSchema(
                self.SCHEMA,
                self.tr('Schema'), 
                defaultValue='bc250_base', 
                connectionParameterName=self.DATABASE)

        self.addParameter(schema_param)     
     
        # Shapefile used to clip
        self.addParameter(QgsProcessingParameterFile(self.SHAPEFILE, self.tr('Clip Shapefile'), extension='shp', optional=True))
        
        # Geopackage
        self.addParameter(QgsProcessingParameterFileDestination(self.GEOPACKAGE, 'Geopackage', '*.gpkg'))
        
    def processAlgorithm(self, parameters, context, feedback):
        # Retrieving parameters
        if qgs_version < 31400:
            connection_name = self.parameterAsString(parameters, self.DATABASE, context)
            db = postgis.GeoDB.from_name(connection_name)
            uri = db.uri
        
            schema = self.parameterAsString(parameters, self.SCHEMA, context)
        else:
            connection_name = self.parameterAsConnectionName(parameters, self.DATABASE, context)
            md = QgsProviderRegistry.instance().providerMetadata('postgres')
            conn = md.createConnection(connection_name)
            uri = QgsDataSourceUri(conn.uri())

            schema = self.parameterAsSchema(parameters, self.SCHEMA, context)

        shape = self.parameterAsFile(parameters, self.SHAPEFILE, context)
        geopackage = parameters[self.GEOPACKAGE]

        # Execute ogr2ogr only in case the shape is Valid or no shape was provided
        shape_qgs = QgsVectorLayer(shape, 'test_valid', 'ogr')
        
        # Test is shape is valid 
        if shape_qgs.isValid() or shape == '':
            feedback.pushInfo("Valid shape")
        else:
            raise QgsProcessingException("Invalid shape")

        # Text for ogr2ogr
        extension = shape_qgs.extent()
        if shape == '':
            target_ogr = "ogr2ogr -f GPKG {} -overwrite -forceNullable {} ".format(geopackage, shape)
        else:
            target_ogr = "ogr2ogr -f GPKG {} -overwrite -forceNullable -spat {} {} {} {} ".format(geopackage, str(extension.xMinimum()), str(extension.yMinimum()), str(extension.xMaximum()), str(extension.yMaximum()))    
            
        source_ogr = 'PG:"host={} dbname={} schemas={} port={} user={} password={}" '.format(uri.host(), uri.database(), schema, uri.port(), uri.username(), uri.password())
        string_ogr = target_ogr + source_ogr
        feedback.pushInfo('Text for ogr2ogr = ' + string_ogr)

        # Export schema to geopackage
        try:
            processo = subprocess.run(string_ogr, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise QgsProcessingException(str(e.stderr.decode('utf-8')))



        # Connect with PostGIS database
        con = psycopg2.connect(user = uri.username(), password = uri.password(), 
                                       host = uri.host(), port = uri.port(), database = uri.database())

        feedback.pushInfo('Uri = ' + str(uri))
        feedback.pushInfo('Uri text = ' + uri.uri())         
        feedback.pushInfo('Connection = ' + str(con))
        feedback.pushInfo('')

        # Query columns with array type
        with con:
            select_schema_tables = "SELECT table_name FROM information_schema.tables " \
                                   "WHERE table_type = '{}' AND table_schema = '{}'".format('BASE TABLE', schema)
            
            feedback.pushInfo('consulta = ' + select_schema_tables)

                                    
            cur = con.cursor()
             
            cur.execute(select_schema_tables)
             
            rows = cur.fetchall()
 
            schema_tables = [table[0] for table in rows]
            feedback.pushInfo('schema tables = ' + str(schema_tables))
            feedback.pushInfo('')
            
            dict_table_arrcolumns = dict()
            
            feedback.pushInfo('Loop para gerar dicionário. Uma lista contendo nome das colunas ARRAY para cada tabela')
            for table in schema_tables:
                select_columns = "SELECT column_name FROM information_schema.columns " \
                                 "WHERE data_type = 'ARRAY' AND table_schema = '{}' AND table_name = '{}'".format(schema, table)
                
                feedback.pushInfo('consulta para tabela ' + table + ': ' + select_columns)
                        
                
                cur.execute(select_columns)
                
                rows = cur.fetchall()
                
                table_arrcolumns = [table[0] for table in rows]

                if table_arrcolumns != []:
                    dict_table_arrcolumns[table] = table_arrcolumns
                
            feedback.pushInfo('dicionario tabelas - colunas tipo array = ' + str(dict_table_arrcolumns))
            feedback.pushInfo('')
                        
        cur.close()
        con.close()


# =============================================================================
#         # Connect with Geopackage to UPDATE columns of array type 
#         feedback.pushInfo('Connecting to Geopackage to update array columns')
#         with lite.connect(geopackage) as con:
#             feedback.pushInfo('Con = ' + str(con))
#             
#             # Create cursor
#             cur = con.cursor()
#             
#             # Loop in dictionary of table:array columns
#             for table, arrcolumn in dict_table_arrcolumns.items():
#                 for column in arrcolumn:
#                     # Select query = """SELECT tipoproduto, '{' || substr(replace(tipoproduto, ')', '}'), 4) FROM {}""".format(table)
#                     update_query = """UPDATE {} SET {} = '{{' || substr(replace({}, ')', '}}'), 4)""".format(table, column, column)
#                     feedback.pushInfo('Update query = ' + update_query)
#                     cur.execute(update_query)
#                     con.commit()
# =============================================================================
                    
                    
        # UPDATE columns of array type inside Geopackage using PyQGIS
        for table, arrcolumn in dict_table_arrcolumns.items():
            uri_geopackage = geopackage + '|layername=' + table
            source = QgsVectorLayer(uri_geopackage, 'geopackage_layer', 'ogr')
            if not source.isValid():
                raise QgsProcessingException('Source layer not valid') 
            
            features = source.getFeatures()

            for f in features:
                fid = f.id()
                for column in arrcolumn:
                    fvalue = f[column]
                    if isinstance(fvalue, QVariant):
                        continue
                    mfvalue = '{' + fvalue.replace(')', '}')[3:]
                    findex = source.fields().indexFromName(column)
                    attr = {findex:mfvalue}
                    source.dataProvider().changeAttributeValues({ fid : attr })

    
        return {'Result': 'Exported'}
    
    
