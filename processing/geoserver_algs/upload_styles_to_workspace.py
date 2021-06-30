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
import glob
from zipfile import ZipFile




class SLDFolderUploader:
    # Uploads a folder with SLDs to a Geoserver Workspace
    
    def __init__(self, geoserver_url, workspace, folder, 
                 user='admin', password='geoserver'):
        
        # Get Styles Workspace URL        
        geoserver_url = geoserver_url.rstrip('web/')
        self.url = geoserver_url + u'/rest/workspaces/' + workspace + '/styles' 
        
        # Store folder and workspace
        self.folder = folder
        self.workspace = workspace
        
        # Store user and password
        self.user = user
        self.password = password
        
        # List of sld files in folder
        self.filelist = [file for file in glob.glob(os.path.join(self.folder, '*.sld'))]

    def zip_slds(self):
        
        # Zip all sld files in list
        for sld_path in self.filelist:
            # Build zip filename to save the style
            sld_path_name = os.path.splitext(sld_path)[0] # Complete path without extension
            sld_path_zip = sld_path_name + '.zip'
    
            # Get only the basename with extension (to save within the zip)
            sld_basename_ext = os.path.basename(sld_path)
    
            # Write SLD to zip
            with ZipFile(sld_path_zip, 'w') as zip_obj:
                zip_obj.write(sld_path, sld_basename_ext)         
    

    def upload_zipfiles(self, feedback):

        # Headers of POST request
        headers = {'Content-Type': 'application/zip'}
        
        # Upload all the zipped SLD files
        for sld_path in self.filelist:
            # Build zip filename to save the style
            sld_path_name = os.path.splitext(sld_path)[0] # Complete path without extension
            sld_path_zip = sld_path_name + '.zip'
    
            # Get only the basename with extension 
            sld_basename_ext = os.path.basename(sld_path) 
            
            # Upload SLD to Geoserver Workspace
            sld_basename = os.path.splitext(sld_basename_ext)[0] # Style name on Geoserver
            
            parameters = {'name': sld_basename}
            
            with open(sld_path_zip, 'rb') as fileobj:
                res = requests.post(self.url, auth=(self.user, self.password), 
                                    data = fileobj, headers=headers, 
                                    params=parameters)
                
                try:
                    res.raise_for_status()
                except Exception as e:
                    feedback.reportError('Error in upload of style {}: {}'.format(sld_basename_ext, e))
                else:
                    feedback.pushInfo('SLD file {} was uploaded successfully'.format(sld_basename_ext))
                    


class UploadStylesToWorkspace(QgsProcessingAlgorithm):
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
        return QCoreApplication.translate("Publi Base: UploadStylesToWorkspace", string)    
    
    def createInstance(self):
        return  UploadStylesToWorkspace()

    def name(self):
        return 'upload_styles_to_workspace'

    def displayName(self):
        return self.tr('Upload Styles To Workspace')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Upload styles form a folder to a specific Workspace with the URL "
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
            optional=False))    

        # Geoserver password
        self.addParameter(QgsProcessingParameterString(
            self.PASSWORD,
            self.tr("Password"),
            "geoserver",
            optional=False))


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
        
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Object that will zip and upload SLDs
        folder1 = SLDFolderUploader(url, workspace, folder, user, password)
        
        # Zip
        folder1.zip_slds()
        
        # Upload
        folder1.upload_zipfiles(feedback)
        

        return {'Result': 'Styles uploaded'}
