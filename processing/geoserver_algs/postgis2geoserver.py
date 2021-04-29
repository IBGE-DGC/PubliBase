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
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       Qgis,
                       QgsProviderRegistry,
                       QgsDataSourceUri)

qgs_version = Qgis.QGIS_VERSION_INT
if qgs_version < 31400:
    from processing.tools import postgis
else:
    from qgis.core import QgsProcessingParameterProviderConnection
    from qgis.core import QgsProcessingParameterDatabaseSchema

import requests

class PostGIS2Geoserver(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    URL = 'URL'
    USER = 'USER'
    TABLE = 'TABLE' # Table or Layer that contains schema, table from PostGIS and corresponding Name, Title and Abstract 
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: PostGIS2Geoserver", string)    
    
    def createInstance(self):
        return PostGIS2Geoserver()

    def name(self):
        return 'postgis2geoserver'

    def displayName(self):
        return self.tr('Publish from PostGIS to Geoserver')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Publish layers from PostGIS to Geoserver according to a metadata table and a featuretypes URL. "
                       'The metadata table is a QGIS layer containing fields named "tablename", "name", "title", "abstract". '
                       'The "tablename" field contains the name of the tables to be published and the other parameters are of Geoserver. '
                       'An example of featuretypes URL is ' 
                       'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publishing/featuretypes , '
                       'which targets the datastore Publishing in workspace cite.')

    def initAlgorithm(self, config=None):
        # featuretypes URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            "URL"))

        # Table Metadata for publishing
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TABLE,
                self.tr('Publishing Metadata Table'),
                [QgsProcessing.TypeVector] 
            )
        )            
            
        # Geoserver user            
        self.addParameter(QgsProcessingParameterString(
            self.USER,
            self.tr("User"),
            "admin"))    

        # Geoserver password
        self.addParameter(QgsProcessingParameterString(
            self.PASSWORD,
            self.tr("Password"),
            "geoserver"))


    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters
        an URL example is 'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publicacao/featuretypes'
        """
        url = self.parameterAsString(parameters, self.URL, context)
        source = self.parameterAsSource(parameters, self.TABLE, context)      
        
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('source = ' + str(source))
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Get features from layer
        features = source.getFeatures()
        feedback.pushInfo('features = ' + str(features) + ' tipo = ' + str(type(features)))
        feedback.pushInfo('')
        
        meta_dict = {'tablename':[], 'name':[], 'title': [], 'abstract':[]}
        
        # Build metadata dictionary
        for f in features:
            meta_dict['tablename'].append(f['tablename'])
            meta_dict['name'].append(f['name'])
            meta_dict['title'].append(f['title'])
            meta_dict['abstract'].append(f['abstract'])
            
        feedback.pushInfo('meta_dict = ' + str(meta_dict))
        feedback.pushInfo('')
            
        # Build XML list for publishing
        payloads = []    
        for i in range(len(meta_dict['tablename'])):
            payload = (f"""<featureType>
                                <name>{meta_dict['name'][i]}</name> 
                                <nativeName>{meta_dict['tablename'][i]}</nativeName>
                                <abstract>{meta_dict['abstract'][i]}</abstract> 
                                <title>{meta_dict['title'][i]}</title>
                            </featureType>""")
            payloads.append(payload)
            feedback.pushInfo('payload = ' + payload)
        
        feedback.pushInfo('')
        feedback.pushInfo('payloads = ' + str(payloads))
        feedback.pushInfo('')
        
        # Publishing        
        for i, payload in enumerate(payloads):
            try:
                resp = requests.post(url, auth=(user, password), data=payload.encode('utf-8'),headers=headers)
                if resp.text == '':
                    feedback.pushInfo("Layer published was " + meta_dict['tablename'][i])
                else:
                    feedback.reportError("Error in publishing: " + resp.text)
            except Exception as e:
                feedback.reportError(str(e))
        
        return {'Result': 'Layers Published'}
