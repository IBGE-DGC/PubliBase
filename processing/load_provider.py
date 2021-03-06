#-*- coding: utf-8 -*-
"""
/***************************************************************************
                                  Publi Base
                             --------------------
        begin                : 2021-05-04
        copyright            : (C) 2021 by Marcel Rotunno (IBGE)
        email                : marcelgaucho@yahoo.com.br
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
import os
from PyQt5.QtCore import QSettings, qVersion, QFileInfo, QTranslator, QCoreApplication


from qgis.core import QgsProcessingProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig

# Import algorithms
# Algorithms in general
from .algs.postgis_schema2geopackage import PostGISSchema2Geopackage
from .algs.postgis_schema2geopackage_reambulation import PostGISSchema2GeopackageReambulation
from .algs.geopackage2postgis_schema_reambulation import Geopackage2PostGISSchemaReambulation
from .algs.postgis_schema2shapefile import PostGISSchema2Shapefile
from .algs.AppendFeaturesToLayer import AppendFeaturesToLayer

# Geoserver algorithms
from .geoserver_algs.postgis_schema2geoserver_ccar import PostGISSchema2GeoserverCCAR
from .geoserver_algs.postgis_schema2geoserver_ccar_not_advertised import PostGISSchema2GeoserverCCARNotAdvertised
from .geoserver_algs.postgis2geoserver import PostGIS2Geoserver
from .geoserver_algs.advertise_store_layers import AdvertiseStoreLayers
from .geoserver_algs.deadvertise_store_layers import DeAdvertiseStoreLayers
from .geoserver_algs.replace_string_in_name_and_title_of_store_layers import ReplaceStringInNameAndTitleOfStoreLayers
from .geoserver_algs.create_workspace import CreateWorkspace
from .geoserver_algs.download_styles_from_workspace import DownloadStylesFromWorkspace
from .geoserver_algs.upload_styles_to_workspace import UploadStylesToWorkspace
from .geoserver_algs.associate_layers_to_workspace_styles import AssociateLayersToWorkspaceStyles
from .geoserver_algs.find_layers_without_workspace_style import FindLayersWithoutWorkspaceStyle
from .geoserver_algs.delete_styles_from_workspace import DeleteStylesFromWorkspace 

# Utils algorithms
from .utils_algs.save_project_vector_styles import SaveProjectVectorStyles


class LoadAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        # Activate provider by default
        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_PUBLI_BASE', 'Activate', True))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        ProcessingConfig.removeSetting('ACTIVATE_PUBLI_BASE')

    def isActive(self):
        """Return True if the provider is activated and ready to run algorithms"""
        return ProcessingConfig.getSetting('ACTIVATE_PUBLI_BASE')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_PUBLI_BASE', active)

    def id(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'publibase'

    def name(self):
        """This is the localised full name.
        """
        return 'Publi Base'

    def icon(self):
        """We return the default icon.
        """
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        for alg in [PostGISSchema2Geopackage(), PostGISSchema2Shapefile(), PostGISSchema2GeopackageReambulation(),
                    Geopackage2PostGISSchemaReambulation(), AppendFeaturesToLayer(), PostGISSchema2GeoserverCCAR(),
                    PostGISSchema2GeoserverCCARNotAdvertised(), PostGIS2Geoserver(), AdvertiseStoreLayers(),
                    DeAdvertiseStoreLayers(), ReplaceStringInNameAndTitleOfStoreLayers(), CreateWorkspace(),
                    DownloadStylesFromWorkspace(), UploadStylesToWorkspace(), AssociateLayersToWorkspaceStyles(),
                    FindLayersWithoutWorkspaceStyle(), DeleteStylesFromWorkspace(), SaveProjectVectorStyles()]:
            self.addAlgorithm(alg)
