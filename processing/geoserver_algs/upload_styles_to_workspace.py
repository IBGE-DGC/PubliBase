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
                       QgsProcessingException,
                       QgsProcessingParameterBoolean)

import requests
import os
import glob
from zipfile import ZipFile



class SLDFolderUploader:
    '''Uploads a folder with SLDs to a Geoserver Workspace'''
    
    def __init__(self, geoserver_url, workspace, folder, 
                 user='admin', password='geoserver'):
        
        # Get Styles Workspace URL        
        self.geoserver_url = geoserver_url.rstrip('web/')
        self.styles_url = self.geoserver_url + u'/rest/workspaces/' + workspace + '/styles' 
        
        # Store folder and workspace
        self.folder = folder
        self.workspace = workspace
        
        # Store user and password
        self.user = user
        self.password = password
        
        # List of sld files in folder
        self.filelist = [file for file in glob.glob(os.path.join(self.folder, '*.sld'))]
        
        # Iniatialize the list that will store the existing styles to replace if required
        self.existing_styles_filelist = []

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

        feedback.pushInfo('\nUploading styles\n')
        # Clear the list of existing styles
        self.existing_styles_filelist.clear()
        
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
                res = requests.post(self.styles_url, auth=(self.user, self.password), 
                                    data = fileobj, headers=headers, 
                                    params=parameters)
                
                try:
                    res.raise_for_status()
                except Exception as e:
                    feedback.reportError('Error in upload of style {}: {}'.format(sld_basename_ext, e))
                    print(e)
                    # Append file path to existing files 
                    # to be overwritten later if required
                    if res.status_code == 403:
                        self.existing_styles_filelist.append(sld_path)                       
                    
                else:
                    feedback.pushInfo('SLD file {} was uploaded successfully'.format(sld_basename_ext))
                    
 
    def overwrite_existing_styles(self, feedback):
        
        feedback.pushInfo('\nOverwriting existing styles\n')
        # Headers of PUT request
        headers = {'Content-Type': 'application/zip'}
        
        # Overwrite the existing styles with their zipped files 
        for sld_path in self.existing_styles_filelist:
            # Build zip filename to save the style
            sld_path_name = os.path.splitext(sld_path)[0] # Complete path without extension
            sld_path_zip = sld_path_name + '.zip'
    
            # Get only the basename with extension 
            sld_basename_ext = os.path.basename(sld_path) 
            
            # Upload SLD to Geoserver Workspace
            sld_basename = os.path.splitext(sld_basename_ext)[0] # Style name on Geoserver
            
            parameters = {'name': sld_basename}
            
            with open(sld_path_zip, 'rb') as fileobj:
                print('Trying to overwrite the style {}'.format(parameters['name']))
                url = self.styles_url + '/' + parameters['name']
                res_put = requests.put(url, 
                                       auth=(self.user, self.password),
                                       data = fileobj, 
                                       headers=headers)
            
                try:
                    res_put.raise_for_status()
                except Exception as e_put:
                    feedback.reportError('Error in overwriting style {}: {}'.format(parameters['name'], e_put))
                else:
                    feedback.pushInfo('Style {} was overwritten successfully'.format(parameters['name']))
                    
            


class UploadStylesToWorkspace(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    WORKSPACE = 'WORKSPACE'
    FOLDER = 'FOLDER'
    OVERWRITE = 'OVERWRITE'
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
        
        # Overwrite parameter
        self.addParameter(QgsProcessingParameterBoolean(self.OVERWRITE,
                                                        self.tr("Overwrite existing styles"),
                                                        False))
        
        
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
        overwrite = parameters[self.OVERWRITE]
        
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('workspace = ' + workspace)
        feedback.pushInfo('folder = ' + folder)
        feedback.pushInfo('overwrite = ' + str(overwrite))
        
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Object that will zip and upload SLDs
        folder1 = SLDFolderUploader(url, workspace, folder, user, password)
        
        # Zip
        folder1.zip_slds()
        
        # Upload
        folder1.upload_zipfiles(feedback)
        
        # Overwrite existing styles
        if overwrite:
            folder1.overwrite_existing_styles(feedback)
        

        return {'Result': 'Styles uploaded'}
