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
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterString)

import requests
import xml.etree.ElementTree as ET

class ReplaceStringInNameAndTitleOfStoreLayers(QgsProcessingAlgorithm):
    # Constants used to refer to parameters

    URL = 'URL'
    USER = 'USER'
    PASSWORD = 'PASSWORD'
    FIND = 'FIND'
    REPLACE = 'REPLACE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: ReplaceStringInNameAndTitleOfStoreLayers", string) 

    def createInstance(self):
        return ReplaceStringInNameAndTitleOfStoreLayers()

    def name(self):
        return 'replace_string_in_name_and_title_of_store_layers'

    def displayName(self):
        return self.tr('Replace String in Name and Title of Store Layers')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Replace all string occurrences in the names and titles of the layers of a store by another string. "
                "A featuretypes URL is needed. "
                'An example of featuretypes URL is ' 
                'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publishing/featuretypes , '
                'which targets the datastore Publishing in workspace cite.')

    def initAlgorithm(self, config=None):
        # featuretypes URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            "URL"))

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
        
        # Find string
        self.addParameter(QgsProcessingParameterString(
            self.FIND,
            self.tr("Find")))
        
        # Replace string
        self.addParameter(QgsProcessingParameterString(
            self.REPLACE,
            self.tr("Replace")))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters
        an URL example is 'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publicacao/featuretypes'
        """
        url = parameters[self.URL]
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        find = parameters[self.FIND]
        replace = parameters[self.REPLACE]

        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('headers = ' + str(headers))
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Get layers in the datastore 
        headers = {'Accept': 'application/xml'}
        resp = requests.get(url,auth=(user,password), headers=headers)
        resp.raise_for_status() # raise error depending on the result
        xml = resp.text
        feedback.pushInfo('xml featuretypes')
        feedback.pushInfo(xml)
        feedback.pushInfo('')        
        
        # Store featuretypes name parsing xml to Python
        featuretypes_name = []
        root = ET.fromstring(xml)
        feedback.pushInfo(str(root))
        for element in root:
            name_element = element.find('name')
            name = name_element.text
            featuretypes_name.append(name)
        
        feedback.pushInfo('FeatureTypes Names')                
        feedback.pushInfo(str(featuretypes_name))
        feedback.pushInfo('')
        
        # Loop over FeatureTypes Name to get titles
        featuretypes_title = []
        for name in featuretypes_name:
            resp = requests.get(url + '/' + name,auth=(user,password), headers=headers)
            resp.raise_for_status() # raise error depending on the result
            xml = resp.text
            feedback.pushInfo(xml)
            root = ET.fromstring(xml)
            feedback.pushInfo(str(root))
            title_element = root.find('title')
            title = title_element.text
            featuretypes_title.append(title)
                
        feedback.pushInfo('FeatureTypes Title')   
        feedback.pushInfo(str(featuretypes_title))
        feedback.pushInfo('')
                
        # Create list that stores renamed featuretypes and renamed titles of featuretypes
        featuretypes_name_r = [s.replace(find, replace) for s in featuretypes_name]
        featuretypes_title_r = [s.replace(find, replace) for s in featuretypes_title]
        
        feedback.pushInfo('FeatureTypes Name Renamed')
        feedback.pushInfo(str(featuretypes_name_r))
        feedback.pushInfo('FeatureTypes Title Renamed')
        feedback.pushInfo(str(featuretypes_title_r))
        feedback.pushInfo('')
        
        # Store payloads in list      
        payloads = []
        for i in range(len(featuretypes_name_r)):
            a = ("""<featureType>
                    <name>""" + featuretypes_name_r[i] + """</name>
                    <title>""" + featuretypes_title_r[i] + """</title>
                    </featureType>""")
            payloads.append(a)
            
        feedback.pushInfo("Payloads")
        feedback.pushInfo(str(payloads))
        feedback.pushInfo('')
        
        
        # Replacing names
        headers = {'Content-type': 'text/xml'}
        for i, payload in enumerate(payloads):
            resp = requests.put(url + '/' + featuretypes_name[i], auth=(user, password), data=payload.encode('utf-8'), headers=headers)
            feedback.pushInfo("Name before renaming was " + featuretypes_name[i])
            feedback.pushInfo("Name after renaming is " + featuretypes_name_r[i])
            feedback.pushInfo("Title before renaming was " + featuretypes_title[i])
            feedback.pushInfo("Title after renaming is " + featuretypes_title_r[i])
            feedback.pushInfo('server response for above layer was = ' + resp.text)
            feedback.pushInfo('')
            
        
        return {'Result': 'Strings replaced'}
