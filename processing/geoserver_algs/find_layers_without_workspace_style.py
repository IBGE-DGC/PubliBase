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
                       QgsProcessingParameterFileDestination)

import requests

class LayersWithoutWorkspaceStyle:
    '''Associate each featuretype of a store with a style'''  
    def __init__(self, geoserver_url, layers_workspace, layers_store, 
                 user='admin', password='geoserver'):
        # Store some variables
        self.geoserver_url = geoserver_url.rstrip('web/')
        self.layers_workspace = layers_workspace
        self.layers_store = layers_store
        
        # Store user and password
        self.user = user
        self.password = password        
        
        # Featuretypes list of the layers workspace
        self.featuretypes = self.retrieve_featuretypes()        

        # Get each layer along with default style 
        self.layers_styles = self.retrieve_layers_with_style()
        

    def retrieve_featuretypes(self):
        '''Retrieve the featuretypes from the store'''
        
        featuretypes_url = self.geoserver_url + u'/rest/workspaces/' \
                           + self.layers_workspace + u'/datastores/' \
                           + self.layers_store + u'/featuretypes'    
    
        # FeatureTypes Request and List
        headers={'Accept': 'application/json'}
        res = requests.get(featuretypes_url, auth = (self.user, self.password), 
                           headers=headers)
        res_json = res.json()
        json_featuretype = res_json['featureTypes']['featureType']
        featuretype_names = [el['name'] for el in json_featuretype] 
    
        return featuretype_names
    

    def retrieve_layers_with_style(self):
        '''Retrieve the default styles from the store layers'''
        # Layers REST URL
        layers_url = self.geoserver_url + u'/rest/layers/'
        
        # Add workspace prefix to layers url 
        layers_url_piece = layers_url + self.layers_workspace + ':'  
        
        # Build dict
        layers_styles = {}
        headers = {'Content-Type': 'application/json'}
        for layer in self.featuretypes:
            # Make request
            url = layers_url_piece + layer
            res = requests.get(url, auth=(self.user, self.password), 
                               headers=headers)
            
            # Get style name in the format workspace:style
            res_json = res.json()
            default_dict = res_json['layer']['defaultStyle']
            name = default_dict['name']
            
            # Add entry to the dict
            layers_styles[layer] = name

        return layers_styles
    
    
    def find_layers(self, workspace):
        '''Find the layers in which the style is from outside the workspace'''
        layers_outside_workspace = []
        
        for layer, style in self.layers_styles.items():
            workspace_style_split = style.split(':')
            
            if (workspace_style_split[0] != workspace or
                len(workspace_style_split) == 1):
                layers_outside_workspace.append(layer)
                
        return layers_outside_workspace
                
                
                      
                



class FindLayersWithoutWorkspaceStyle(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    LAYERS_WORKSPACE = 'LAYERS_WORKSPACE'
    LAYERS_STORE = 'LAYERS_STORE'
    STYLES_WORKSPACE = 'STYLES_WORKSPACE'
    OUTPUT_FILE = 'OUTPUT_FILE'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: FindLayersWithoutWorkspaceStyle", string)    
    
    def createInstance(self):
        return  FindLayersWithoutWorkspaceStyle()

    def name(self):
        return 'find_layers_without_workspace_style'

    def displayName(self):
        return self.tr('Find Layers without a Workspace Style')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Finds each layer, in a store, that has a default style that "
                       "isn't located in a certain workspace.\n\n The layers list is saved "
                       "in a text file.\n\n"
                       "An example of Geoserver URL is http://localhost:8080/geoserver/web .")

    def initAlgorithm(self, config=None):
        # Geoserver URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            self.tr("Geoserver URL")))

        # Layers Workspace
        self.addParameter(
            QgsProcessingParameterString(
                self.LAYERS_WORKSPACE,
                self.tr('Layers Workspace')
            )
        )

        # Layers Store
        self.addParameter(
            QgsProcessingParameterString(
                self.LAYERS_STORE,
                self.tr('Layers Store')
            )
        )          

        # Styles Workspace
        self.addParameter(
            QgsProcessingParameterString(
                self.STYLES_WORKSPACE,
                self.tr('Styles Workspace')
            )
        )

        # Output Text File
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                self.tr('Output text file'),
                '*.txt'))
            
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
        layers_workspace = self.parameterAsString(parameters, self.LAYERS_WORKSPACE, context)
        layers_store = self.parameterAsString(parameters, self.LAYERS_STORE, context)
        styles_workspace = self.parameterAsString(parameters, self.STYLES_WORKSPACE, context)
        output_file = self.parameterAsFile(parameters, self.OUTPUT_FILE, context)
        
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('layers workspace = ' + layers_workspace)
        feedback.pushInfo('layers store = ' + layers_store)
        feedback.pushInfo('styles workspace = ' + styles_workspace)
        feedback.pushInfo('output file = ' + output_file)
        
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Object that will extract the layers
        layer_finder = LayersWithoutWorkspaceStyle(url, 
                                                  layers_workspace, 
                                                  layers_store,
                                                  user,
                                                  password)
        # Find layers
        layers_found =  layer_finder.find_layers(styles_workspace)
        
        feedback.pushInfo(str(layers_found))
        
        # Write the layers to a text file
        with open(output_file, 'w') as file:
            for layer in layers_found:
                file.write(layer + '\n')
        

        return {'Result': 'Algorithm Completed'}
