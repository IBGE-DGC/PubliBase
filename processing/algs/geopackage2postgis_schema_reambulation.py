# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 12:14:04 2020

@author: Marcel
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingException,
                       QgsProcessingParameterString,
                       QgsProcessingAlgorithm,
                       QgsVectorLayer,
                       QgsProcessingParameterFile,
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
import processing
import psycopg2

class Geopackage2PostGISSchemaReambulation(QgsProcessingAlgorithm):
    # Constants used to refer to parameters    
    
    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    GEOPACKAGE = 'GEOPACKAGE'
    #CLEAN_SCHEMA = 'CLEAN_SCHEMA'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: Geopackage2PostGISSchemaReambulation", string) 

    def createInstance(self):
        return Geopackage2PostGISSchemaReambulation()

    def name(self):
        return 'geopackage2postgis_schema_reambulation'

    def displayName(self):
        return self.tr('Reambulation: Geopackage to PostGIS Schema')   
    
    def group(self):
        return self.tr('Reambulation')

    def groupId(self):
        return 'reambulation'

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
                self.tr('Schema'), 'bc250_reamb')
            schema_param.setMetadata({
                'widget_wrapper': {
                    'class': 'processing.gui.wrappers_postgis.SchemaWidgetWrapper',
                    'connection_param': self.DATABASE}})
        else:
            schema_param = QgsProcessingParameterDatabaseSchema(
                self.SCHEMA,
                self.tr('Schema'), 
                defaultValue='bc250_reamb', 
                connectionParameterName=self.DATABASE)

        self.addParameter(schema_param) 
        
      
        # Geopackage
        self.addParameter(QgsProcessingParameterFile(self.GEOPACKAGE, 'Geopackage', 0, 'gpkg'))
        
        # Clean Schema
        '''
        # If it is necessary to clean the schema
        self.addParameter(QgsProcessingParameterBoolean(self.CLEAN_SCHEMA,
                                                        'Clean Schema',
                                                        False, optional=True))        
        '''
        
        

    


    def processAlgorithm(self, parameters, context, feedback):
        
        # Dummy function to enable running an alg inside an alg
        def no_post_process(alg, context, feedback):
            pass
        

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

        geopackage = parameters[self.GEOPACKAGE]

        



        # Debugging info
        '''
        feedback.pushInfo('Input parameters:')
        feedback.pushInfo('connection = ' + connection)
        feedback.pushInfo('db = ' + str(db))
        feedback.pushInfo('schema = ' + schema)
        feedback.pushInfo('geopackage = ' + geopackage)
        feedback.pushInfo('')
        '''
        
        # Raise error if reamb isn't in schema name
        if not 'reamb' in schema:
            raise QgsProcessingException('A palavra reamb precisa fazer parte do nome do esquema')        

        # Connect with Geopackage 
        feedback.pushInfo('Listing non-empty layers from geopackage')
        with lite.connect(geopackage) as con:
            feedback.pushInfo('Con = ' + str(con))
            
            layers_import = [] # will store the non-empty tables
            
            # Create cursor
            cur = con.cursor()
            
            # Fetch layer names
            cur.execute("SELECT table_name FROM gpkg_geometry_columns")
            rows = cur.fetchall()
            layer_names = [camada[0] for camada in rows]
            feedback.pushInfo('Layers = ' + str(layer_names)) 
            

            
            # Append non-empty geometry layers to list 
            for layer in layer_names:
                # Count rows
                cur.execute("SELECT COUNT(1) FROM {}".format(layer))
                
                rows = cur.fetchall()
                rows_count = rows[0][0]                
                #feedback.pushInfo('Rows = ' + str(rows_count))
                
                # Append to list
                if rows_count > 0:
                    #feedback.pushInfo('Table non-empty = ' + str(rows_count))
                    layers_import.append(layer)
        
                    
        feedback.pushInfo('Non-empty tables = ' + str(layers_import))
        feedback.pushInfo('')

        
        # Connect with PostGIS database
        con = psycopg2.connect(user = uri.username(), password = uri.password(), 
                                       host = uri.host(), port = uri.port(), database = uri.database())

        feedback.pushInfo('Uri = ' + str(uri))
        feedback.pushInfo('Uri text = ' + uri.uri())         
        feedback.pushInfo('Connection = ' + str(con))
        
        
        # Clean PostGIS schema if marked
        #cleanSchema = self.parameterAsBool(parameters, self.CLEAN_SCHEMA, context)
        cleanSchema = False
         
        if cleanSchema:
            with con:
                select_schema_tables = "SELECT table_name FROM information_schema.tables " \
                                        "WHERE table_type = '{}' AND table_schema = '{}'".format('BASE TABLE', schema)
                                        
                cur = con.cursor()
                 
                cur.execute(select_schema_tables)
                 
                rows = cur.fetchall()
     
                schema_tables = [table[0] for table in rows]
                 
                for table in schema_tables:
                    feedback.pushInfo("Deleting from {}.{}".format(schema, table))
                    cur.execute("DELETE FROM {}.{}".format(schema, table))
                    con.commit()
                        
        cur.close()
        con.close()
         
        feedback.pushInfo('')




       
# =============================================================================
#         # Testing
#         nome = 'cbge_trecho_arruamento_l'
#         # QGIS Vector Layer from geopackage layer 
#         uri_geopackage = geopackage + '|layername=' + nome
#         vlayer = QgsVectorLayer(uri_geopackage, 'geopackage_layer', 'ogr')
# 
#         # Use database table as QGIS Vector Layer
#         uri_tabela = uri
#         uri_tabela.setDataSource(schema, nome, 'geom')
#         uri_tabela.setWkbType(vlayer.wkbType())
#         uri_tabela.setSrid(str(vlayer.sourceCrs().postgisSrid()))
#         target = QgsVectorLayer(uri_tabela.uri(), 'teste', 'postgres')
#         feedback.pushInfo(uri_tabela.uri())
#         feedback.pushInfo('Validade = ' + str(target.isValid()))
#          
# 
#         processing.run("script:appendfeaturestolayer", {'SOURCE_LAYER':vlayer, 'TARGET_LAYER':target, 'ACTION_ON_DUPLICATE':0}, context=context, feedback=feedback, onFinish=no_post_process)
# =============================================================================

        
        
        
        # Import layers
        for layer in layers_import:
            feedback.pushInfo("Importing {}.{}".format(schema, layer))
            

             
            # QGIS Vector Layer from source 
            uri_geopackage = geopackage + '|layername=' + layer
            source = QgsVectorLayer(uri_geopackage, 'geopackage_layer', 'ogr')
            if not source.isValid():
                raise QgsProcessingException('Source layer not valid') 
                
            # QGIS Vector Layer from target
            uri_table = uri
            uri_table.setDataSource(schema, layer, 'geom')
            uri_table.setWkbType(source.wkbType())
            uri_table.setSrid(str(source.sourceCrs().postgisSrid()))
            target = QgsVectorLayer(uri_table.uri(), 'schema_table', 'postgres')
            if not target.isValid():
                raise QgsProcessingException('Target layer not valid') 
            
            # Run QGIS script for importing
            processing.run("publibase:appendfeaturestolayer", {'SOURCE_LAYER':source, 'TARGET_LAYER':target, 'ACTION_ON_DUPLICATE':0}, context=context, feedback=feedback, onFinish=no_post_process)
            feedback.pushInfo('')    
 
       



        return {'Result':'Layers imported'}

