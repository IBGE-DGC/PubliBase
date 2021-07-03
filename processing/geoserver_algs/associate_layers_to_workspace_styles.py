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

class StyleAssociator:
    '''Associate each featuretype of a store with a style'''  
    def __init__(self, geoserver_url, layers_workspace, layers_store, 
                 styles_workspace, user='admin', password='geoserver'):
        # Store some variables
        self.geoserver_url = geoserver_url.rstrip('web/')
        self.layers_workspace = layers_workspace
        self.layers_store = layers_store
        self.styles_workspace = styles_workspace
        
        # Store user and password
        self.user = user
        self.password = password        
        
        # Featuretypes list of the layers workspace
        self.featuretypes = self.retrieve_featuretypes()        

        # Styles of the styles workspace
        self.styles = self.retrieve_styles()
        
        # Association dictionary
        self.assoc_dict = self.build_association_dictionary()
        
        

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
    

    def retrieve_styles(self):
        '''Retrieve the styles featuretypes from the workspace'''
    
        styles_url = self.geoserver_url + u'/rest/workspaces/' + self.styles_workspace + u'/styles'  
    
        # Styles Request and List
        headers={'Accept': 'application/json'}
        res = requests.get(styles_url, auth = (self.user, self.password), headers=headers)
        res_json = res.json()
        json_style = res_json['styles']['style']
        style_names = [el['name'] for el in json_style] 
        
        return style_names

    def build_association_dictionary(self):
        '''Build dictionary that associate each featuretype with a style'''

        assoc_dict = {}
        for featuretype in self.featuretypes:
            # List that will contain the associated styles
            assoc_styles = []
            
            # Add stylenames whose name is a substring of the featuretype
            cur_length = 0
            for style in self.styles:
                if style in featuretype and len(style) >= cur_length:
                    assoc_styles.append(style)
                    cur_length = len(style)
        
            # Associated style is the one whose name has the longest length
            # If there is no associated style, associated style is None
            if assoc_styles:
                assoc_style = assoc_styles[-1]
            else:
                assoc_style = None
            
            # Add the entry to the dictionary
            assoc_dict[featuretype] = assoc_style
            
        return assoc_dict


    def associate_styles(self, feedback):
        '''Perform the association'''
        # Layers REST URL
        layers_url = self.geoserver_url + u'/rest/layers/'
        
        # Add workspace prefix to layers url 
        layers_url_piece = layers_url + self.layers_workspace + ':'  
        
        # Loop and Associate styles 
        headers = {'Content-Type': 'application/json'}
        for layer, style in self.assoc_dict.items():
            # Go to the next style if there is no style to associate
            if style is None:
                continue
            
            # Body of the request
            body =  '''{
                       "layer":{
                          "defaultStyle":{
                             "name":"%s:%s"
                          }
                       }
                    }''' % (self.styles_workspace, style)
        
            # Make the PUT request
            url_put = layers_url_piece + layer
            res = requests.put(url_put, auth=(self.user, self.password), 
                                            data=body, headers=headers)
        
            # Raise error if applicable
            try:
                res.raise_for_status()
            except Exception as e:
                feedback.reportError('Error in association of layer {} '
                                     'with style {}:{}'.format(layer, 
                                                               style, e))
            else:
                feedback.pushInfo('Layer {} successfully associated '
                                  'with style {}'.format(layer, style))



class AssociateLayersToWorkspaceStyles(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    URL = 'URL'
    LAYERS_WORKSPACE = 'LAYERS_WORKSPACE'
    LAYERS_STORE = 'LAYERS_STORE'
    STYLES_WORKSPACE = 'STYLES_WORKSPACE'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: AssociateLayersToWorkspaceStyles", string)    
    
    def createInstance(self):
        return  AssociateLayersToWorkspaceStyles()

    def name(self):
        return 'associate_layers_to_workspace_styles'

    def displayName(self):
        return self.tr('Associate Layers to Workspace Styles')

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return self.tr("Associates, based on the names, layers in a store with the "
                       "styles in a workspace.\n\n The default style for a layer "
                       "will be the style whose name is the longest substring of the layer name. "
                       "If there is more than one style that meets this requirement, "
                       "the style chosen will be the one that is placed last in the workspace's "
                       "REST style list (e.g. http://localhost:8080/geoserver/rest/workspaces/"
                       "workspace_example/styles, where workspace_example is the workspace name). "
                       "If no style satisfies the requirement, "
                       "the layer's default style remains unchanged. \n\n"
                       'An example of Geoserver URL is http://localhost:8080/geoserver/web .')

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
        
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('layers workspace = ' + layers_workspace)
        feedback.pushInfo('layers store = ' + layers_store)
        feedback.pushInfo('styles workspace = ' + styles_workspace)
        
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Object that will associate styles
        style_association = StyleAssociator(url, layers_workspace, 
                                            layers_store, styles_workspace,
                                            user, password)
        
        # Associate styles
        style_association.associate_styles(feedback)
        

        return {'Result': 'Styles associated'}
