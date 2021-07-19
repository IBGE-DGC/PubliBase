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
                       QgsProject,
                       QgsMapLayer)

import os



# Function to save the project vector layer styles
def save_project_vector_styles(project, qml_folder, sld_folder):
    '''Save styles of vector layers in the project to qml and sld.
       The styles are saved into the respective folders. The name
       of each style will be the name of the layer in the Layers Panel.'''
    
    # dictionary with key = layer name and value = layer object
    # Only stores Vector Layers
    layers_dict = project.mapLayers()
    layers_list = {}
    for l in layers_dict.values():
        if l.type() == QgsMapLayer.VectorLayer:
            layers_list[l.name()] = l
            
    # Save Styles
    for name, l in layers_list.items():
        qml_path = os.path.join(qml_folder, name + '.qml')
        sld_path = os.path.join(sld_folder, name + '.sld')
        l.saveNamedStyle(qml_path)
        l.saveSldStyle(sld_path)



class SaveProjectVectorStyles(QgsProcessingAlgorithm):
    # Constants used to refer to parameters
    
    QML_FOLDER = 'QML_FOLDER'
    SLD_FOLDER = 'SLD_FOLDER'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Publi Base: SaveProjectVectorStyles", string)    
    
    def createInstance(self):
        return  SaveProjectVectorStyles()

    def name(self):
        return 'save_project_vector_styles'

    def displayName(self):
        return self.tr('Save Project Vector Styles')

    def group(self):
        return 'Utils'

    def groupId(self):
        return 'utils'

    def shortHelpString(self):
        return self.tr("Save styles of vector layers opened in the project to a QML "
                       "folder and a SLD folder.")

    def initAlgorithm(self, config=None):
        # Folder to save QML styles
        self.addParameter(QgsProcessingParameterFile(self.QML_FOLDER, 
                                                     self.tr("QML Folder"), 
                                                     1, optional=False))

        # Folder to save SLD styles
        self.addParameter(QgsProcessingParameterFile(self.SLD_FOLDER, 
                                                     self.tr("SLD Folder"), 
                                                     1, optional=False))              
            
    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters and running the processing
        """
        qml_folder = parameters[self.QML_FOLDER]
        sld_folder = parameters[self.SLD_FOLDER]
        
        # Debugging info
        feedback.pushInfo('Input variables')
        feedback.pushInfo('QML Folder = ' + qml_folder)
        
        feedback.pushInfo('SLD Folder = ' + sld_folder)
        feedback.pushInfo('')
        
        # Current Project Instance
        project = QgsProject.instance()
        
        # Save styles
        save_project_vector_styles(project, qml_folder, sld_folder)
        

        return {'Result': 'Styles saved'}
