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

import subprocess 

class PostGISSchema2Geopackage(QgsProcessingAlgorithm):
    # Constants used to refer to parameters 

    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    SHAPEFILE = 'SHAPEFILE'
    GEOPACKAGE = 'GEOPACKAGE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: PostGISSchema2Geopackage", string)

    def createInstance(self):
        return PostGISSchema2Geopackage()

    def name(self):
        return 'postgis_schema2geopackage'

    def displayName(self):
        return self.tr('PostGIS Schema to Geopackage')

    def group(self):
        return self.tr('Export')

    def groupId(self):
        return 'export'

    def shortHelpString(self):
        return self.tr("Export the layers in a PostGIS schema to a geopackage.")

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
        if shape == '':
            target_ogr = "ogr2ogr -f GPKG {} -overwrite {} ".format(geopackage, shape)
        else:
            target_ogr = "ogr2ogr -f GPKG {} -overwrite -clipsrc {} ".format(geopackage, shape)    
            
        source_ogr = 'PG:"host={} dbname={} schemas={} port={} user={} password={}" '.format(uri.host(), uri.database(), schema, uri.port(), uri.username(), uri.password())
        string_ogr = target_ogr + source_ogr
        feedback.pushInfo('Text for ogr2ogr = ' + string_ogr)

        # Export schema to geopackage
        try:
            process = subprocess.run(string_ogr, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise QgsProcessingException(str(e.stderr.decode('utf-8')))

        return {'Result': 'Exported'}