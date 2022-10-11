# Major Project - Aspect-Slope Mapping Processing Tool
# Ryan Turner
# s3924894

#import necessary modules
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
import math
import processing
import os

#create class to store both the GUI and processing tool code
class AspectSlopeMapping(QgsProcessingAlgorithm):
    
    #create constants used to refer to parameters and outputs
    INPUT = 'INPUT'
    ASPECTVIZ = 'ASPECTVIZ'
    ASPECTYN = 'ASPECTYN'
    ASPECTZ = 'ASPECTZ'
    SLOPEYN = 'SLOPEYN'
    SLOPEZ = 'SLOPEZ'
    OUTPUT = 'OUTPUT'

    #descriptors of the processing tool
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AspectSlopeMapping()

    def name(self):
        return 'aspectslopemapping'

    def displayName(self):
        return self.tr('Aspect-Slope Mapping and Visualisation Tool')

    def group(self):
        return self.tr("Ryan's Scripts")

    def groupId(self):
        return 'examplescripts'

    def shortHelpString(self):
        return self.tr("All-in-one aspect-slope mapping and visualisation tool. \
                       Select your favoured aspect to highlight in the final visualisation output. \
                       A selection of no preference will use a default full spectrum colour scheme.\
                       Also choose whether you would like an aspect and/or slope map intermediate output as well.")

    def initAlgorithm(self, config=None):
        
        #define the input raster parameter
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Select the input DEM raster layer'),
                [QgsProcessing.TypeRaster]
            )
        )
        #define the aspect visualisation options
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ASPECTVIZ,
                self.tr('Select the preferred aspect (no preference will output with a full spectrum colour scheme)'),
                options = [('No preference'), ('North'), ('North East'), ('East'), ('South East'), ('South'), ('South West'), ('West'), ('North West')],
                defaultValue = 0,
            )
        )
        #define the aspect output choice
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ASPECTYN,
                self.tr('Output an independent aspect map?'),
                options = [('Yes'), ('No')],
                defaultValue = 0
            )
        )
        #define the aspect z factor
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ASPECTZ,
                self.tr('Enter the aspect Z factor (minimum of 1)'),
                defaultValue = 1
            )
        )
        #define the slope output choice
        self.addParameter(
            QgsProcessingParameterEnum(
                self.SLOPEYN,
                self.tr('Output a independent slope map?'),
                options = [('Yes'), ('No')],
                defaultValue = 0
            )
        )
        #define the slope z factor
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SLOPEZ,
                self.tr('Enter the slope Z factor (minimum of 1'),
                defaultValue = 1
            )
        )
        #define feature sink
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Aspect-Slope Map Output')
            )
        )
 
    def processAlgorithm(self, parameters, context, feedback):

        #assign parameters to variables for later use
        #ensure raster is set to raster layer type
        rasterSource = self.parameterAsRasterLayer(
            parameters,
            self.INPUT,
            context
        )
        #provide user feedback if the input raster is invalid
        if rasterSource is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        #define aspect visualisation parameter
        aspectViz = self.parameterAsDouble(
            parameters,
            self.ASPECTVIZ,
            context
        )
        #define aspect yes or no parameter
        aspectYN = self.parameterAsDouble(
            parameters,
            self.ASPECTYN,
            context
        )
        #define aspect z factor
        aspectZ = self.parameterAsDouble(
            parameters,
            self.ASPECTZ,
            context
        )
        #define slope yes or no parameter
        slopeYN = self.parameterAsDouble(
            parameters,
            self.SLOPEYN,
            context
        )
        #define slope z factor
        slopeZ = self.parameterAsDouble(
            parameters,
            self.SLOPEZ,
            context
        )
        
        #store aspect function parameters
        aspectDict = {'INPUT' : rasterSource,
                      'Z_FACTOR' : aspectZ,
                      'OUTPUT' : 'TEMPORARY_OUTPUT'}
        #run aspect processing tool and load results
        aspect = processing.run("qgis:aspect", aspectDict, context=context, feedback=feedback)
        #create output layer
        aspectLayer = QgsRasterLayer(aspect['OUTPUT'], 'Aspect')
        #add to map if user selected yes to parameter
        if aspectYN == 0:
            QgsProject.instance().addMapLayer(aspectLayer)

        #store slope function parameters
        slopeDict = {'INPUT' : rasterSource, 
                     'Z_FACTOR' : slopeZ,
                     'OUTPUT' : 'TEMPORARY_OUTPUT'}
        #run slope processing tool and load results
        slope = processing.run("qgis:slope", slopeDict, context=context, feedback=feedback)
        #create output layer
        slopeLayer = QgsRasterLayer(slope['OUTPUT'], 'Slope')
        #add to map if user selected yes to parameter
        if slopeYN == 0:
            QgsProject.instance().addMapLayer(slopeLayer)
        
        #store aspect reclassification values based on cardinal directions
        aspectTable =  ['0','22.499','10',
                        '22.5','67.499','20',
                        '67.5','112.499','30',
                        '112.5','157.499','40',
                        '157.5','202.499','50',
                        '202.5','247.499','60',
                        '247.5','292.499','70',
                        '292.5','337.499','80',
                        '337.5','360.5','10']
        #store aspect reclassification function parameters
        aspectReclassDict = {'INPUT_RASTER' : aspectLayer,
                             'RASTER_BAND' : 1,
                             'TABLE' : aspectTable,
                             'NO_DATA' : -9999,
                             'RANGE_BOUNDARIES' : 0,
                             'NODATA_FOR_MISSING' : False,
                             'DATA_TYPE' : 5,
                             'OUTPUT' : 'TEMPORARY_OUTPUT'}
        #run reclassify by table tool and load results
        aspectReclass = processing.run("qgis:reclassifybytable", aspectReclassDict, context=context, feedback=feedback)
        #create output layer
        aspectReclassLayer = QgsRasterLayer(aspectReclass['OUTPUT'], 'Aspect Reclass')
        
        #store slope reclassification values
        slopeTable = ['0','4.999','0',
                      '5','14.999','2',
                      '15','29.999','4',
                      '30','44.999','6',
                      '45','90.0','8']
        #store slope reclassification function parameters
        slopeReclassDict = {'INPUT_RASTER' : slopeLayer,
                             'RASTER_BAND' : 1,
                             'TABLE' : slopeTable,
                             'NO_DATA' : -9999,
                             'RANGE_BOUNDARIES' : 0,
                             'NODATA_FOR_MISSING' : False,
                             'DATA_TYPE' : 5,
                             'OUTPUT' : 'TEMPORARY_OUTPUT'}
        #run reclassify by table tool and load results
        slopeReclass = processing.run("qgis:reclassifybytable", slopeReclassDict, context=context, feedback=feedback)
        #create output layer
        slopeReclassLayer = QgsRasterLayer(slopeReclass['OUTPUT'], 'Slope Reclass')

        #get user's aspect preference
        if aspectViz == 0:
            label = 'Visualised'
        if aspectViz == 1:
            label = 'North'
        if aspectViz == 2:
            label = 'North East'
        if aspectViz == 3:
            label = 'East'
        if aspectViz == 4:
            label = 'South East'
        if aspectViz == 5:
            label = 'South'
        if aspectViz == 6:
            label = 'South West'
        if aspectViz == 7:
            label = 'West'
        if aspectViz == 8:
            label = 'North West'
        
        #use raster calculator addition to add both reclassed layers together
        rasterAddDict = {'INPUT_A' : aspectReclassLayer,
                         'BAND_A' : 1,
                         'INPUT_B' : slopeReclassLayer,
                         'BAND_B' : 1,
                         'FORMULA' : ('A+B'),
                         'NO_DATA' : 0,
                         'OUTPUT' : 'TEMPORARY_OUTPUT'}
        #run raster calculator tool and load results
        rasterAdd = processing.run("gdal:rastercalculator", rasterAddDict, context=context, feedback=feedback)
        #create output layer labelled with aspect preference
        rasterAddLayer = QgsRasterLayer(rasterAdd['OUTPUT'], ('Aspect-Slope -' + str(label)))
        #add to map
        QgsProject.instance().addMapLayer(rasterAddLayer)
        
        #begin visualisation process
        
        #create a function to read the lines of a QGIS colour map file
        def GetColorRampItemListFromText(file_contents):
            #remove the header
            file_contents = file_contents.split('\n')[2:]
            #split the values by comma for each line and store the values in a list
            file_contents = [list(map(int,line.split(',')[0:4])) for line in file_contents]
            #get colour information from each position in the list for each line
            valueList = [QgsColorRampShader.ColorRampItem(line[0], QColor(line[1],line[2],line[3])) for line in file_contents]
            return valueList
        
        #symoblise final output based on user selection
        if aspectViz == 0: #no aspect preference, full rainbow colour scheme
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,181,181,181,255,label
            12,159,192,133,255,label
            14,157,221,94,255,label
            16,154,251,12,255,label
            18,15,241,57,255,label
            20,181,181,181,255,label
            22,114,168,144,255,label
            24,61,171,113,255,label
            26,0,173,67,255,label
            28,0,137,27,255,label
            30,181,181,181,255,label
            32,124,142,173,255,label
            34,80,120,182,255,label
            36,0,104,192,255,label
            38,0,86,157,255,label
            40,181,181,181,255,label
            42,140,117,160,255,label
            44,119,71,157,255,label
            46,108,0,163,255,label
            48,72,0,140,255,label
            50,181,181,181,255,label
            52,180,123,161,255,label
            54,192,77,156,255,label
            56,202,0,156,255,label
            58,154,0,121,255,label
            60,181,181,181,255,label
            62,203,139,143,255,label
            64,231,111,122,255,label
            66,255,85,104,255,label
            68,255,51,75,255,label
            70,181,181,181,255,label
            72,197,165,138,255,label
            74,226,166,108,255,label
            76,255,171,71,255,label
            78,255,140,8,255,label
            80,181,181,181,255,label
            82,189,191,137,255,label
            84,214,219,94,255,label
            86,240,244,0,255,label
            88,255,250,0,255,label"""
            
        if aspectViz == 1: #north aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,191,54,12,255,label
            12,216,67,21,255,label
            14,230,74,25,255,label
            16,244,81,30,255,label
            18,255,87,34,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
            
        if aspectViz == 2: #north east aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,191,54,12,255,label
            22,216,67,21,255,label
            24,230,74,25,255,label
            26,244,81,30,255,label
            28,255,87,34,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
            
        if aspectViz == 3: #east aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,191,54,12,255,label
            32,216,67,21,255,label
            34,230,74,25,255,label
            36,244,81,30,255,label
            38,255,87,34,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
            
        if aspectViz == 4: #south east aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,191,54,12,255,label
            42,216,67,21,255,label
            44,230,74,25,255,label
            46,244,81,30,255,label
            48,255,87,34,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
        
        if aspectViz == 5: #south aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,191,54,12,255,label
            52,216,67,21,255,label
            54,230,74,25,255,label
            56,244,81,30,255,label
            58,255,87,34,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
        
        if aspectViz == 6: #south west aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,191,54,12,255,label
            62,216,67,21,255,label
            64,230,74,25,255,label
            66,244,81,30,255,label
            68,255,87,34,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
            
        if aspectViz == 7: #west aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,191,54,12,255,label
            72,216,67,21,255,label
            74,230,74,25,255,label
            76,244,81,30,255,label
            78,255,87,34,255,label
            80,33,33,33,255,label
            82,66,66,66,255,label
            84,97,97,97,255,label
            86,117,117,117,255,label
            88,158,158,158,255,label"""
            
        if aspectViz == 8: #north west aspect preference
            file_contents = """# QGIS Generated Color Map Export File
            INTERPOLATION:INTERPOLATED
            10,33,33,33,255,label
            12,66,66,66,255,label
            14,97,97,97,255,label
            16,117,117,117,255,label
            18,158,158,158,255,label
            20,33,33,33,255,label
            22,66,66,66,255,label
            24,97,97,97,255,label
            26,117,117,117,255,label
            28,158,158,158,255,label
            30,33,33,33,255,label
            32,66,66,66,255,label
            34,97,97,97,255,label
            36,117,117,117,255,label
            38,158,158,158,255,label
            40,33,33,33,255,label
            42,66,66,66,255,label
            44,97,97,97,255,label
            46,117,117,117,255,label
            48,158,158,158,255,label
            50,33,33,33,255,label
            52,66,66,66,255,label
            54,97,97,97,255,label
            56,117,117,117,255,label
            58,158,158,158,255,label
            60,33,33,33,255,label
            62,66,66,66,255,label
            64,97,97,97,255,label
            66,117,117,117,255,label
            68,158,158,158,255,label
            70,33,33,33,255,label
            72,66,66,66,255,label
            74,97,97,97,255,label
            76,117,117,117,255,label
            78,158,158,158,255,label
            80,191,54,12,255,label
            82,216,67,21,255,label
            84,230,74,25,255,label
            86,244,81,30,255,label
            88,255,87,34,255,label"""
       
        #update the list from the file contents
        valueList = GetColorRampItemListFromText(file_contents)
        
        #set the colour ramp type to interpolated
        colRamp = QgsColorRampShader()
        colRamp.setColorRampType(QgsColorRampShader.Interpolated)
        
        #update the colour ramp with the values list
        colRamp.setColorRampItemList(valueList)
        
        #define the shader
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(colRamp)
        
        #define and apply the render
        renderer = QgsSingleBandPseudoColorRenderer(rasterAddLayer.dataProvider(), 1, shader)
        
        #set min and max values
        renderer.setClassificationMin(10)
        renderer.setClassificationMax(88)
        
        #set renderer and refresh the layer
        rasterAddLayer.setRenderer(renderer)
        rasterAddLayer.triggerRepaint()
        
        return {}