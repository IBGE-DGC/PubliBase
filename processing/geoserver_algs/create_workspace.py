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
from qgis.core import (QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString)

import requests

class CreateWorkspace(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    WORKSPACE = 'WORKSPACE'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: CreateWorkspace", string)    
    
    def createInstance(self):
        return CreateWorkspace()

    def name(self):
        return 'create_workspace'

    def displayName(self):
        return self.tr('Create Workspace')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Create a Workspace in Geoserver with the URL from Geoserver and the Workspace name. "
                       'An example of Geoserver URL is http://localhost:8080/geoserver/web .')

    def initAlgorithm(self, config=None):
        # Geoserver URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            "URL"))

        # Workspace
        self.addParameter(
            QgsProcessingParameterString(
                self.WORKSPACE,
                self.tr('Workspace Name')
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
        an URL example is 'http://localhost:8080/geoserver/web/'
        """
        url = self.parameterAsString(parameters, self.URL, context)
        workspace = self.parameterAsString(parameters, self.WORKSPACE, context)      
        
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('workspace = ' + str(workspace))
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Workspaces REST URL
        url = url.rstrip('web/')
        url = url + u'/rest/workspaces'
        
        feedback.pushInfo('workspaces URL = ' + str(url))
        feedback.pushInfo('')
        
        # Build XML for POST
        xml_post = (f"""<workspace>
                            <name>{workspace}</name> 
                        </workspace>""")        
            
        feedback.pushInfo('xml_post = ' + str(xml_post))
        feedback.pushInfo('')
            
        # Create the workspace        
        try:
            res = requests.post(url, auth=(user, password), data=xml_post.encode('utf-8'), headers=headers)
            if res.status_code == 201:
                feedback.pushInfo("Success: " + res.reason)
            else:
                raise QgsProcessingException("Error : " + res.reason)
        except Exception as e:
            raise QgsProcessingException(str(e))
        
        return {'Result': 'Workspace Created'}
