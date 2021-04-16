# -*- coding: utf-8 -*-
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
def classFactory(iface):
    from .publi_base import PubliBase
    return PubliBase(iface)
