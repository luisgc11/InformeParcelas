# -*- coding: utf-8 -*-
"""
/***************************************************************************
 InformeParcelasDockWidget
                                 A QGIS plugin
 Informe de Parcelas: Coordenadas, Información y Plano kml
                             -------------------
        begin                : 2018-04-28
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Luis Gonzalez Calvo
        email                : luisgc11@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys
import shutil
reload(sys)
sys.setdefaultencoding("utf-8")

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsApplication,QgsCoordinateReferenceSystem
from qgis.core import *
from qgis.core import QgsRasterLayer
from qgis.core import QgsRaster
from qgis.core import QgsField,QgsFeature,QgsGeometry
from qgis.core import QgsVectorLayer
from qgis.core import QgsMapLayerRegistry
from PyQt4.QtCore import QVariant

from math import floor
import re
import csv

import constants

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'informe_parcelas_dockwidget_base.ui'))


class InformeParcelasDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(InformeParcelasDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.initialize()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def initialize(self):
        aux_path_plugin = 'python/plugins/' + constants.INFORME_PARCELAS_NAME
        qgisUserDbFilePath = QgsApplication.qgisUserDbFilePath()
        self.path_plugin = os.path.join(QFileInfo(QgsApplication.qgisUserDbFilePath()).path(),aux_path_plugin)
        path_file_qsettings = self.path_plugin + '/' +constants.INFORME_PARCELAS_SETTINGS_FILE_NAME
        self.settings = QSettings(path_file_qsettings,QSettings.IniFormat)
        self.lastPath = self.settings.value("last_path")
        if not self.lastPath:
            self.lastPath = QDir.currentPath()
            self.settings.setValue("last_path",self.lastPath)
            self.settings.sync()


        #Cargamos la capa para obtener la información
        layer = QgsVectorLayer("C:/Informe_Parcelas/Poligonos Informe/Pol01_Fincas_Nuevos_Propietarios.shp", "Pol01_Fincas", "ogr")
        if not layer:
            print "Layer failed to load!"
        QgsMapLayerRegistry.instance().addMapLayer(layer)

        self.selec_PropietarioPushButton.setEnabled(True)
        self.selec_ParcelaPushButton.setEnabled(True
                                                )
        self.n_parcelaLineEdit.setEnabled(False)
        self.n_propietarioLineEdit.setEnabled(False)
        self.csvcFileLineEdit.setEnabled(False)
        self.csviFileLineEdit.setEnabled(False)
        self.kmlFileLineEdit.setEnabled(False)

        #self.listadoPushButton.setEnabled(False)
        #self.planoPushButton.setEnabled(False)

        #Selección para información e informes a generar
        QObject.connect(self.selec_ParcelaPushButton, SIGNAL("clicked(bool)"), self.selec_Parcela)
        QObject.connect(self.selec_PropietarioPushButton, SIGNAL("clicked(bool)"), self.selec_Propietario)
        QObject.connect(self.csvcFilePushButton,SIGNAL("clicked(bool)"), self.selec_CsvcFile)
        QObject.connect(self.csviFilePushButton, SIGNAL("clicked(bool)"), self.selec_CsviFile)
        QObject.connect(self.kmlFilePushButton,SIGNAL("clicked(bool)"), self.selec_KmlFile)
        #QObject.connect(self.listadoPushButton,SIGNAL("clicked(bool)"),self.getListado)
        #QObject.connect(self.planoPushButton,SIGNAL("clicked(bool)"),self.getPlano)
        QObject.connect(self.terminarPushButton, SIGNAL("clicked(bool)"), self.terminar)
        self.pointNumbers = []
        self.num_format = re.compile(r'^\-?[1-9][0-9]*\.?[0-9]*')
    """
    #Procesos para generar listado y plano pdf.
    def getListado(self):
        return self.listadoFieldCheckBox.isChecked()

    def getPlano(self):
        return self.planoFieldCheckBox.isChecked()

    def pdf(self):
        fileName = QFileDialog.getSaveFileName(self.dlg, "Save file", "report.pdf", "(*.pdf)")
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(QPrinter.A4)
        if fileName:
            printer.setOutputFileName(fileName)
            doc = document
            doc.print_(printer)
    """

    def selec_CsvcFile(self):
        self.csvcFileLineEdit.setEnabled(True)

        #Archivo de coordenadas nº punto, coordenada x, coordenada y
        #Nommbramos el archivo de salida según corresponda a un propietario o parcela
        if self.n_propietarioLineEdit.text():
            archivocsvc = "C:/Informe_Parcelas/Informe_coord_Prop_" + str(self.n_propietarioLineEdit.text()) + ".csv"
        elif self.n_parcelaLineEdit.text():
            archivocsvc = "C:/Informe_Parcelas/Informe_coord_Parc_" + str(self.n_parcelaLineEdit.text()) + ".csv"
        else:
            print "No se ha seleccionado propietario o parcela"

        self.csvcFileLineEdit.setText(archivocsvc)
        print (archivocsvc)
        csvsalidac = open(archivocsvc, 'w')
        salidac = csv.writer(csvsalidac)

        layer = self.iface.activeLayer()
        features = layer.getFeatures()
        #Numero de punto para grabar en el archivo de coordenadas.
        i = 101
        # Obtenemos las coordenadas de los vértices
        # empiezo en el 1, ya que el 0 y el último son el mismo
        for feature in features:
            geom = feature.geometry()
            n = 1
            ver = geom.vertexAt(1)
            points = []
            while ver != QgsPoint(0, 0):
                n += 1
                points.append(ver)
                ver = geom.vertexAt(n)
            #Escribimos en el archivo el numero de punto y las coordenadas
            for punto in points:
                salidac.writerow([i, punto.x(), punto.y()])
                i += 1

        #Cerramos los archivos
        del salidac
        csvsalidac.close()

        self.iface.zoomToActiveLayer()
        layer.setSelectedFeatures([])

    def selec_CsviFile(self):
        self.csviFileLineEdit.setEnabled(True)

        #Archivo con información de las parcelas y el propietario, con los campos
        #Nº Propietario', 'Propietario','Nº Poligono','Nº Parcela','Area'
        # Nommbramos el archivo de salida según corresponda a un propietario o parcela
        if self.n_propietarioLineEdit.text():
            archivocsvp = "C:/Informe_Parcelas/Informe_Prop_" + str(self.n_propietarioLineEdit.text()) + ".csv"
        elif self.n_parcelaLineEdit.text():
            archivocsvp = "C:/Informe_Parcelas/Informe_Parc_" + str(self.n_parcelaLineEdit.text()) + ".csv"
        else:
            print "No se ha seleccionado propietario o parcela"

        print (archivocsvp)
        self.csviFileLineEdit.setText(archivocsvp)
        csvsalidap = open(archivocsvp, 'w')
        salidap = csv.writer(csvsalidap)
        salidap.writerow(['Informe Propietario'])
        salidap.writerow(['Nº Propietario', 'Propietario','Nº Poligono','Nº Parcela','Area'])
        salidap.writerow([''])
        layer = self.iface.activeLayer()
        features = layer.getFeatures()
        for feature in features:
           #Grabamos en el archivo Informe_propietario los datos de las parcelas.
            attrs = feature.attributes()
            salidap.writerow([attrs[3], attrs[4], attrs[1], attrs[6], attrs[0]])

        #Cerramos los archivos
        del salidap
        csvsalidap.close()

        self.iface.zoomToActiveLayer()
        layer.setSelectedFeatures([])

    def selec_KmlFile(self):
        #Generamos un archivo kml con las fincas seleccionadas
        self.kmlFileLineEdit.setEnabled(True)

        if self.n_propietarioLineEdit.text():
            fileNamekml = "C:/Informe_Parcelas/Prop_" + str(self.n_propietarioLineEdit.text())
        elif self.n_parcelaLineEdit.text():
            fileNamekml = "C:/Informe_Parcelas/Parc_" + str(self.n_parcelaLineEdit.text())
        else:
            print "No se ha seleccionado propietario o parcela"
        self.kmlFileLineEdit.setText(fileNamekml)
        vectorLyr = self.iface.activeLayer()
        vectorLyr.isValid()
        dest_crs = QgsCoordinateReferenceSystem(4326)
        QgsVectorFileWriter.writeAsVectorFormat(vectorLyr, fileNamekml, "utf-8",
                                                dest_crs, "KML")

    """
    #Funcién para numerar los vértices de las parcelas
    def capa_csv_temp(self):

        input = "/home/zeito/pyqgis_data/polygon8.shp"

        layer = QgsVectorLayer(input, "polygon", "ogr")
        feats = [feat for feat in layer.getFeatures()]
        temp = QgsVectorLayer("Polygon?crs=epsg:25830",
                              "result",
                              "memory")

        QgsMapLayerRegistry.instance().addMapLayer(temp)
        temp_data = temp.dataProvider()
        attr = layer.dataProvider().fields().toList()
        temp_data.addAttributes(attr)
        temp.updateFields()
        temp_data.addFeatures(feats)
     """

    def selec_Parcela(self):
        self.n_parcelaLineEdit.setEnabled(True)
        self.n_propietarioLineEdit.setText('')
        curLayer = self.iface.mapCanvas().currentLayer()
        label = "Indicar Numero de Parcela"
        titulo = "N. de Parcela"
        n_parcela = 1
        ok = False
        while not ok:
            [text, ok] = QInputDialog.getText(self, titulo, label, QLineEdit.Normal, str(n_parcela))
            if ok and text:
                text = text.strip()
                if not text.isdigit():
                    ok = False
                else:
                    self.n_parcelaLineEdit.setText(text)
            else:
                if not ok:
                    ok = True
        curLayer.setSubsetString('"Parcela"=\'%s\'' % text)
        self.iface.zoomToActiveLayer()

    def selec_Propietario(self):
        self.n_propietarioLineEdit.setEnabled(True)
        self.n_parcelaLineEdit.setText('')
        curLayer = self.iface.mapCanvas().currentLayer()
        label = "Indicar Numero de Propietario"
        titulo = "N. de Propietario"
        n_propietario = 1
        ok = False
        while not ok:
            [text, ok] = QInputDialog.getText(self, titulo, label, QLineEdit.Normal, str(n_propietario))
            if ok and text:
                text = text.strip()
                if not text.isdigit():
                    ok = False
                else:
                    self.n_propietarioLineEdit.setText(text)
            else:
                if not ok:
                 ok = True
        curLayer.setSubsetString('"N_Propieta"=\'%s\'' % text)
        self.iface.zoomToActiveLayer()

    def terminar(self):
        #Borramos los valores utilizados
        self.n_propietarioLineEdit.setText('')
        self.n_parcelaLineEdit.setText('')
        self.csvcFileLineEdit.setText('')
        self.csviFileLineEdit.setText('')
        self.kmlFileLineEdit.setText('')

        self.n_parcelaLineEdit.setEnabled(False)
        self.n_propietarioLineEdit.setEnabled(False)
        self.csvcFileLineEdit.setEnabled(False)
        self.csviFileLineEdit.setEnabled(False)
        self.kmlFileLineEdit.setEnabled(False)

        curLayerFin = self.iface.mapCanvas().currentLayer()
        curLayerFin.setSubsetString('')
        self.iface.zoomToActiveLayer()
        print "Fin"