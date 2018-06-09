# -*- coding: utf-8 -*-
"""
/***************************************************************************
 InformeParcelas
                                 A QGIS plugin
 Informe de Parcelas Coordenadas y Plano kml
                             -------------------
        begin                : 2018-04-28
        copyright            : (C) 2018 by Luis Gonzalez Calvo
        email                : luisgc11@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load InformeParcelas class from file InformeParcelas.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from informe_parcelas import InformeParcelas
    return InformeParcelas(iface)