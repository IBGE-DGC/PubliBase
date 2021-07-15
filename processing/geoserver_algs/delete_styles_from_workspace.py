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


class WorkspaceStylesDeleter:
    '''Deletes all styles inside a workspace'''  
    def __init__(self, geoserver_url, styles_workspace, 
                 user='admin', password='geoserver'):
        # Store some variables
        self.geoserver_url = geoserver_url.rstrip('web/')
        self.styles_workspace = styles_workspace
        self.styles_url = self.geoserver_url + u'/rest/workspaces/' + self.styles_workspace + u'/styles/'  

        # Store user and password
        self.user = user
        self.password = password        
        
        # Styles of the styles workspace
        self.styles = self.retrieve_styles()
        

    def retrieve_styles(self):
        '''Retrieve the styles from the workspace'''
    
        # Styles Request and List
        headers={'Accept': 'application/json'}
        res = requests.get(self.styles_url, auth = (self.user, self.password), headers=headers)
        res_json = res.json()
        
        try:
            json_style = res_json['styles']['style']
        except TypeError as e:
            # If this exception occurs, there are
            # no styles in the workspace, so an empty
            # list is returned
            print('Error occured while '
                  'retrieving styles: {}'.format(e))
            return []
            
        
        style_names = [el['name'] for el in json_style] 
        
        return style_names
    
    
    def delete_styles(self, feedback, recurse=False):
        '''Delete the styles in the workspace'''
        parameters = {'recurse': str(recurse)}
        
        for style in self.styles:
            res = requests.delete(self.styles_url + style, 
                                  auth = (self.user, self.password),
                                  params=parameters)
            
            # Treat error
            try:
                res.raise_for_status()
            except Exception as e:
                feedback.reportError('Error in deletion of style {}: {}'.format(style, e))
            else:
                feedback.pushInfo('Style {} deleted successfully'.format(style))



class DeleteStylesFromWorkspace(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    WORKSPACE = 'WORKSPACE'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: DeleteStylesFromWorkspace", string)    
    
    def createInstance(self):
        return  DeleteStylesFromWorkspace()

    def name(self):
        return 'delete_styles_from_workspace'

    def displayName(self):
        return self.tr('Delete Styles from Workspace')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Delete all styles inside a workspace. If a style is already associated "
                       "to a layer, it won't be deleted. "
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
        
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('workspace = ' + workspace)
        
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Object that will delete the styles
        styles_deleter = WorkspaceStylesDeleter(url, 
                                                workspace,
                                                user,
                                                password)
        
        # Delete styles
        styles_deleter.delete_styles(feedback)
        

        return {'Result': 'Styles deleted'}
