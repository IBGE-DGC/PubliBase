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
                       QgsProcessingParameterString,
                       QgsProcessingParameterFile,
                       QgsProcessingException)

import requests
import os

class DownloadStylesFromWorkspace(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    WORKSPACE = 'WORKSPACE'
    FOLDER = 'FOLDER'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: DownloadStylesFromWorkspace", string)    
    
    def createInstance(self):
        return DownloadStylesFromWorkspace()

    def name(self):
        return 'download_styles_from_workspace'

    def displayName(self):
        return self.tr('Download Styles From Workspace')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Download into a folder all the styles from a specific Workspace with the URL "
                       "from Geoserver and the Workspace name. "
                       'An example of Geoserver URL is http://localhost:8080/geoserver/web .')

    def initAlgorithm(self, config=None):
        # Geoserver URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            self.tr("Geoserver URL")))

        # Workspace
        self.addParameter(
            QgsProcessingParameterString(
                self.WORKSPACE,
                self.tr('Workspace Name')
            )
        )

        # Folder to save styles
        self.addParameter(QgsProcessingParameterFile(self.FOLDER, 
                                                     self.tr("Folder"), 
                                                     1, optional=False))            
            
        # Geoserver user            
        self.addParameter(QgsProcessingParameterString(
            self.USER,
            self.tr("User"),
            "admin",
            optional=True))    

        # Geoserver password
        self.addParameter(QgsProcessingParameterString(
            self.PASSWORD,
            self.tr("Password"),
            "geoserver",
            optional=True))


    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters
        an URL example is 'http://localhost:8080/geoserver/web/'
        """
        url = self.parameterAsString(parameters, self.URL, context)
        workspace = self.parameterAsString(parameters, self.WORKSPACE, context)
        folder = parameters[self.FOLDER]
        
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('workspace = ' + workspace)
        feedback.pushInfo('folder = ' + folder)
        
        feedback.pushInfo('user = ' + user + ' '  + str(type(user)))
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Workspaces Styles REST URL
        url = url.rstrip('web/')
        url = url + u'/rest/workspaces/' + workspace + '/styles/'      
        
        feedback.pushInfo('workspaces Styles URL = ' + str(url))
        feedback.pushInfo('')
        
        # Get all styles available in Workspace
        # Try request without authentication if user is empty string 
        if user == '':
            res = requests.get(url)
        else:
            res = requests.get(url, auth=(user, password))
        
        # raise error if applicable 
        try:
            res.raise_for_status()
        except Exception as e:
            raise QgsProcessingException(str(e))    
    
        # Get styles list 
        res_json = res.json()
        
        json_style = res_json['styles']['style']
        style_names = [el['name'] for el in json_style]       
            
        feedback.pushInfo('style names = ' + str(style_names))
        feedback.pushInfo('')
            
        # Save styles in the selected folder
        for style in style_names:
            # Get style
            if user == '':
                res_style = requests.get(url + style + '.sld')
            else:
                res_style = requests.get(url + style + '.sld', auth=(user, password))
                
            # raise error if applicable 
            try:
                res_style.raise_for_status()
            except Exception as e:
                feedback.reportError('Error in getting style "{}": '.format(style) + str(e))
                continue
                
            # Save file
            file_path = os.path.join(folder, style + '.sld')
            with open(file_path, 'wb') as file:
                file.write(res_style.content)
                
            feedback.pushInfo('Style saved: {}'.format(style))
            

        return {'Result': 'Styles downloaded'}
