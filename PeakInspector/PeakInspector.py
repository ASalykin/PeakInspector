# -*- coding: utf-8 -*-
import sys, os

from PyQt4 import QtGui, QtCore, uic
import numpy as np

import pandas as pd
# from pandas import DataFrame, read_csv

import scipy.signal as sig
from scipy import interpolate
 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from matplotlib import style


#TODO secondary tab in GUI with output options
#TODO multiple output formats and unified format of code for output production
#TODO cant open data with small amount of points - probably because of the SG filter
#TODO fix layout

# Initialise the final dataframe that will contain analysed data to export to Excel
multipleDataSets = pd.DataFrame()

#%% main function executed on mouse click for peak detection
def onclick(event):
    modifier = QtGui.QApplication.keyboardModifiers()
    global GUI, x, dataAfterFilter, dataBaseline, coords, amplitudes, peakIdx, area
    global pickable_artists_pts_AX2, pickable_artists_pts_AX3, pickable_artists_lns_AX2, pickable_artists_lns_AX3, amplitudeLineCoordinates, pickable_artists_fill_AX3
    global pickable_artists_plb_AX3, pickable_artists_prb_AX3, rightPeakBorder, leftPeakBorder, leftIntersectionPeakIdx, rightIntersectionPeakIdx, pickable_artists_lnsP_AX3
    
    if event.inaxes==ax3: # i.e. axes with detrended and filtered data
        if event.button == 1 and modifier == QtCore.Qt.NoModifier:
            # to prevent overwrtie of peak coordinates
            if 'coords' in globals():
                pass
            else: 
                GUI.clearData()

            # detect the closest time (x) index near the event
            xIdx = (np.abs(x-event.xdata)).argmin()

            # determine window frame (in amount of indexes) within which the peak should be found 
            peakDetectionWindow = GUI.BoxPeakDetectionWindow.value()
            leftBorderX = xIdx - peakDetectionWindow
            rigthBorderX = xIdx + peakDetectionWindow

            # prevent situation if borders could be out of index 
            if leftBorderX >= -1 and rigthBorderX < len(dataAfterFilter):
                indexInterval= dataAfterFilter[leftBorderX:rigthBorderX]
            elif leftBorderX <= -1 and rigthBorderX < len(dataAfterFilter):
                indexInterval=dataAfterFilter[0:rigthBorderX]
            elif leftBorderX >= 0 and rigthBorderX > len(dataAfterFilter):
                indexInterval=dataAfterFilter[leftBorderX:len(dataAfterFilter)]

            # find index and value of the peak within window frame
            yVal, yIdx = max((yVal, yIdx) for (yIdx, yVal) in enumerate(indexInterval))

            # find index of the peak within full dataset
            peakIdx = dataAfterFilter.index(yVal)

            # determine the amplitude region within which the peak borders would be automatically searched
            # lowerBaselineRegion equal 0 (see dataPreprocessing function in the main class)
            upperBaselineRegion = yVal*0.10            

            leftIntersectionPeakIdx = next((h for h in range(peakIdx, 1, -1) if \
                (dataAfterFilter[h] >= dataAfterFilter[h-1]) & \
                (dataAfterFilter[h] > dataAfterFilter[h+1]) & \
                (0 <= dataAfterFilter[h] <= upperBaselineRegion)), 0)

            rightIntersectionPeakIdx = next((k for k in range(peakIdx, len(dataAfterFilter)-1, 1) if \
                (dataAfterFilter[k] >= dataAfterFilter[k-1]) & \
                (dataAfterFilter[k] > dataAfterFilter[k+1]) & \
                (0 <= dataAfterFilter[k] <= upperBaselineRegion)), len(dataAfterFilter)-1)

            # save peak data coordinated for next analysis
            coords.append((x[peakIdx], dataAfterFilter[peakIdx]))
            leftPeakBorder.append((x[leftIntersectionPeakIdx], dataAfterFilter[leftIntersectionPeakIdx]))
            rightPeakBorder.append((x[rightIntersectionPeakIdx], dataAfterFilter[rightIntersectionPeakIdx]))

            # calculate the line between left and right border of the peak
            interpolatedLine = GUI.interpolation(leftPeakBorder[-1], rightPeakBorder[-1], leftIntersectionPeakIdx, rightIntersectionPeakIdx)

            # calculate the REAL peak with 0 baseline (substract the 'interpolatedLine' from corresponding region in processed dataset)
            peakFullArea = []
            peakFullArea[:] = [(i - j) for i,j in zip(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx], interpolatedLine)]
            lns3TruePeak, = ax3.plot(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx], peakFullArea, 'k--')

            # find the actual amplitude of the peak
            peakAmplitude = max(peakFullArea)
            amplitudes.append(peakAmplitude)
            amplitudeLineCoordinates.append(([x[peakIdx], x[peakIdx]], [peakAmplitude, 0]))
            area.append(peakFullArea)

            # Visualize peak coordinates
            pts2, = ax2.plot(coords[-1][0], coords[-1][1], 'bo', ms=4) # peak max on 2nd graph
            pts3, = ax3.plot(coords[-1][0], coords[-1][1], 'bo', ms=8, picker=20) # peak max on 3rd graph
            lns3, = ax3.plot(amplitudeLineCoordinates[-1][0], amplitudeLineCoordinates[-1][1], 'k') # line from max to baseline

            # visualise the whole peak which will be integrated
            pts3fill = ax3.fill_between(np.array(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                interpolatedLine, \
                np.array(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                facecolor='green', interpolate=True, alpha=0.4)
            
            # Visualise left and right peak border by dots
            pts3lb, = ax3.plot(leftPeakBorder[-1][0], leftPeakBorder[-1][1], 'ko', ms=4, picker=15)
            pts3rb, = ax3.plot(rightPeakBorder[-1][0], rightPeakBorder[-1][1], 'ko', ms=4, picker=15)
  
            # initiate/update fig instance
            GUI.fig.canvas.draw()

            # appead corresponding artists for further manipulation (to remove and move)
            pickable_artists_pts_AX2.append(pts2)
            pickable_artists_pts_AX3.append(pts3)
            pickable_artists_lns_AX3.append(lns3)
            pickable_artists_fill_AX3.append(pts3fill)
            pickable_artists_plb_AX3.append(pts3lb)
            pickable_artists_prb_AX3.append(pts3rb)
            pickable_artists_lnsP_AX3.append(lns3TruePeak)


        elif (event.button == 1 and modifier == QtCore.Qt.ControlModifier) or event.button == 2: # remove artists under the cursor  
            # DO NOT DELETE! Working example of context menu!
            # canvasSize = event.canvas.geometry()
            # Qpoint_click = event.canvas.mapToGlobal(QtCore.QPoint(event.x,canvasSize.height()-event.y))
            # GUI.lineMenu= QtGui.QMenu()
            # GUI.lineMenu.addAction("Test Menu")
            # GUI.lineMenu.move(Qpoint_click)
            # GUI.lineMenu.show()

            removePtsAx3=[] # placeholder for artists under the cursor            
            removePtsAx3 = [artist for artist in pickable_artists_pts_AX3 if artist.contains(event)[0]]

            xIdxArtist=[] # placeholder for artists' indexes among currently plotted artists

            for artist in removePtsAx3:
                removedArtistXdata = artist.get_xdata()
                xIdxArtist = [i for i, eachTuple in enumerate(coords) if eachTuple[0] == removedArtistXdata]
                indexA = xIdxArtist[0]

                artist.remove()
                pickable_artists_pts_AX2[indexA].remove()
                pickable_artists_lns_AX3[indexA].remove()
                pickable_artists_fill_AX3[indexA].remove()
                pickable_artists_plb_AX3[indexA].remove()
                pickable_artists_prb_AX3[indexA].remove()
                pickable_artists_lnsP_AX3[indexA].remove()

                del coords[indexA]
                del area[indexA]
                del amplitudes[indexA]
                del amplitudeLineCoordinates[indexA]
                del leftPeakBorder[indexA]
                del rightPeakBorder[indexA]
                del pickable_artists_pts_AX2[indexA]
                del pickable_artists_pts_AX3[indexA]
                del pickable_artists_lns_AX3[indexA]
                del pickable_artists_fill_AX3[indexA]
                del pickable_artists_plb_AX3[indexA]
                del pickable_artists_prb_AX3[indexA]
                del pickable_artists_lnsP_AX3[indexA]


            # print(coords)
            GUI.fig.canvas.draw()
        
        elif event.button == 3 and modifier == QtCore.Qt.NoModifier: # move artist under the cursor
            on_motion(event)

        elif event.button == 3 and modifier == QtCore.Qt.ControlModifier: #
            if 'coords' in globals():
                # detect the closest time (x) index near the event
                xIdxLeft = (np.abs(x-event.xdata)).argmin()
                leftIntersectionPeakIdx = xIdxLeft
                leftPeakBorder[-1] = [x[leftIntersectionPeakIdx], dataAfterFilter[leftIntersectionPeakIdx]]  

                # calculate the line between left and right border of the peak
                interpolatedLine = GUI.interpolation(leftPeakBorder[-1], rightPeakBorder[-1], leftIntersectionPeakIdx, rightIntersectionPeakIdx)

                # calculate the REAL peak with 0 baseline (substract the 'interpolatedLine' from corresponding region in processed dataset)
                peakFullArea = []
                peakFullArea[:] = [(i - j) for i,j in zip(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx], interpolatedLine)]
                area[-1] = peakFullArea

                pickable_artists_lnsP_AX3[-1].remove()
                del pickable_artists_lnsP_AX3[-1]
                lns3TruePeak, = ax3.plot(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx], peakFullArea, 'k--')
                pickable_artists_lnsP_AX3.append(lns3TruePeak)

                # find the actual amplitude of the peak
                peakAmplitude = max(peakFullArea)
                amplitudes[-1] = peakAmplitude
                
                pickable_artists_plb_AX3[-1].remove()
                del pickable_artists_plb_AX3[-1]
                pts3lb_new, = ax3.plot(leftPeakBorder[-1][0], leftPeakBorder[-1][1], 'ko', ms=4, picker=15)
                pickable_artists_plb_AX3.append(pts3lb_new)

                amplitudeLineCoordinates=list(amplitudeLineCoordinates)
                amplitudeLineCoordinates[-1][1][0]=peakAmplitude

                pickable_artists_lns_AX3[-1].remove()
                del pickable_artists_lns_AX3[-1]
                lns3_new, = ax3.plot(amplitudeLineCoordinates[-1][0], amplitudeLineCoordinates[-1][1], 'k') # line from max to baseline
                pickable_artists_lns_AX3.append(lns3_new)

                pickable_artists_fill_AX3[-1].remove()
                del pickable_artists_fill_AX3[-1]                              
                pts3fill = ax3.fill_between(np.array(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                                interpolatedLine, \
                                np.array(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                                facecolor='green', interpolate=True, alpha=0.4)
                pickable_artists_fill_AX3.append(pts3fill)

                GUI.fig.canvas.draw()


        elif event.button == 3 and modifier == QtCore.Qt.AltModifier: #
            if 'coords' in globals():
                # detect the closest time (x) index near the event
                xIdxRight = (np.abs(x-event.xdata)).argmin()
                rightIntersectionPeakIdx = xIdxRight
                rightPeakBorder[-1] = [x[rightIntersectionPeakIdx], dataAfterFilter[rightIntersectionPeakIdx]]  

                # calculate the line between left and right border of the peak
                interpolatedLine = GUI.interpolation(leftPeakBorder[-1], rightPeakBorder[-1], leftIntersectionPeakIdx, rightIntersectionPeakIdx)

                # calculate the REAL peak with 0 baseline (substract the 'interpolatedLine' from corresponding region in processed dataset)
                peakFullArea = []
                peakFullArea[:] = [(i - j) for i,j in zip(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx], interpolatedLine)]
                area[-1] = peakFullArea

                pickable_artists_lnsP_AX3[-1].remove()
                del pickable_artists_lnsP_AX3[-1]
                lns3TruePeak, = ax3.plot(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx], peakFullArea, 'k--')
                pickable_artists_lnsP_AX3.append(lns3TruePeak)

                # find the actual amplitude of the peak
                peakAmplitude = max(peakFullArea)
                amplitudes[-1] = peakAmplitude
                
                pickable_artists_prb_AX3[-1].remove()
                del pickable_artists_prb_AX3[-1]
                pts3rb_new, = ax3.plot(rightPeakBorder[-1][0], rightPeakBorder[-1][1], 'ko', ms=4, picker=15)
                pickable_artists_prb_AX3.append(pts3rb_new)

                amplitudeLineCoordinates=list(amplitudeLineCoordinates)
                amplitudeLineCoordinates[-1][1][0]=peakAmplitude

                pickable_artists_lns_AX3[-1].remove()
                del pickable_artists_lns_AX3[-1]
                lns3_new, = ax3.plot(amplitudeLineCoordinates[-1][0], amplitudeLineCoordinates[-1][1], 'k') # line from max to baseline
                pickable_artists_lns_AX3.append(lns3_new)

                pickable_artists_fill_AX3[-1].remove()
                del pickable_artists_fill_AX3[-1]                              
                pts3fill = ax3.fill_between(np.array(x[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                                interpolatedLine, \
                                np.array(dataAfterFilter[leftIntersectionPeakIdx:rightIntersectionPeakIdx]), \
                                facecolor='green', interpolate=True, alpha=0.4)
                pickable_artists_fill_AX3.append(pts3fill)

                GUI.fig.canvas.draw()

def on_motion(event):
    global ax3
    modifier = QtGui.QApplication.keyboardModifiers()
    if event.inaxes==ax3:
        if event.button == 3 and modifier == QtCore.Qt.NoModifier:
            global pickable_artists_plb_AX3, pickable_artists_prb_AX3, rightIntersectionPeakIdx, coords, pickable_artists_fill_AX3, x, dataAfterFilter, pickable_artists_lns_AX3, pickable_artists_lnsP_AX3
            global leftPeakBorder, rightPeakBorder, leftBorderIndex, rightBorderIndex, leftBorder, rightBorder, amplitudes, relativeAmplitudes, amplitudeLineCoordinates

            if 'pickable_artists_plb_AX3' and 'pickable_artists_prb_AX3' in globals():
                try: # to determine whether user pointed on the left peak border
                    if 'leftBorder' in globals():
                        leftBorderNew = [artist for artist in pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                        if leftBorderNew==leftBorder:
                            leftBorderXdata = leftBorder[0].get_xdata() # initial position of the left dot
                        else:
                            leftBorder=leftBorderNew
                            leftBorderXdata = leftBorder[0].get_xdata()
                            leftBorderIndex = [i for i, eachTuple in enumerate(leftPeakBorder) if eachTuple[0] == leftBorderXdata] # index of the left dot
                    else:
                        leftBorder = [artist for artist in pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                        leftBorderXdata = leftBorder[0].get_xdata() # initial position of the left dot
                        leftBorderIndex = [i for i, eachTuple in enumerate(leftPeakBorder) if eachTuple[0] == leftBorderXdata] # index of the left dot
                except:
                    pass

                try: # to determine whether user pointed on the right peak border
                    if 'rightBorder' in globals():
                        rightBorderNew = [artist for artist in pickable_artists_prb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot (under mouse)
                        if rightBorderNew==rightBorder:
                            rightBorderXdata = rightBorder[0].get_xdata() #
                        else:
                            rightBorder=rightBorderNew
                            rightBorderXdata = rightBorder[0].get_xdata()
                            rightBorderIndex = [i for i, eachTuple in enumerate(rightPeakBorder) if eachTuple[0] == rightBorderXdata] #
                    else:
                        rightBorder = [artist for artist in pickable_artists_prb_AX3 if artist.contains(event)[0]] #
                        rightBorderXdata = rightBorder[0].get_xdata() #
                        rightBorderIndex = [i for i, eachTuple in enumerate(rightPeakBorder) if eachTuple[0] == rightBorderXdata] #
                except:
                    pass

                # logic for peak movement
                if len(leftBorder)==1 and len(rightBorder)>=0:
                    idxL = (np.abs(x-event.xdata)).argmin()
                    leftBorder[0].set_xdata(x[idxL])
                    leftBorder[0].set_ydata(dataAfterFilter[idxL])

                    indexA = leftBorderIndex[0]
                    idxR = x.index(rightPeakBorder[indexA][0])

                    leftPeakBorder=list(leftPeakBorder)
                    leftPeakBorder = leftPeakBorder[:indexA] + [(x[idxL], dataAfterFilter[idxL])] + leftPeakBorder[indexA+1:] #

                    interpolatedLine = GUI.interpolation(leftPeakBorder[indexA], rightPeakBorder[indexA], idxL, idxR)

                    # calculation of peak amplitude
                    peakFullArea = []
                    peakFullArea[:] = [(i - j) for i,j in zip(dataAfterFilter[idxL:idxR], interpolatedLine)]
                    area[indexA]=peakFullArea

                    pickable_artists_lnsP_AX3[indexA].remove()
                    lns3TruePeak, = ax3.plot(x[idxL:idxR], peakFullArea, 'k--')
                    pickable_artists_lnsP_AX3 = pickable_artists_lnsP_AX3[:indexA] + [lns3TruePeak] + pickable_artists_lnsP_AX3[indexA+1:]

                    peakAmplitude = max(peakFullArea)
                    amplitudes = amplitudes[:indexA] + [peakAmplitude] + amplitudes[indexA+1:]

                    amplitudeLineCoordinates=list(amplitudeLineCoordinates)
                    amplitudeLineCoordinates[indexA][1][0]=peakAmplitude

                    pickable_artists_lns_AX3[indexA].remove()
                    lns3, = ax3.plot(amplitudeLineCoordinates[indexA][0], amplitudeLineCoordinates[indexA][1], 'k') # line from max to baseline
                    pickable_artists_lns_AX3 = pickable_artists_lns_AX3[:indexA] + [lns3] + pickable_artists_lns_AX3[indexA+1:]

                    pickable_artists_fill_AX3[indexA].remove()
                    pts3fill = ax3.fill_between(np.array(x[idxL:idxR]), \
                                    interpolatedLine, \
                                    np.array(dataAfterFilter[idxL:idxR]), \
                                    facecolor='green', interpolate=True, alpha=0.4)
                    pickable_artists_fill_AX3 = pickable_artists_fill_AX3[:indexA] + [pts3fill] + pickable_artists_fill_AX3[indexA+1:] #

                    GUI.fig.canvas.draw()


                elif (len(leftBorder)>=0 and len(rightBorder)==1):
                    idxR = (np.abs(x-event.xdata)).argmin()
                    rightBorder[0].set_xdata(x[idxR])
                    rightBorder[0].set_ydata(dataAfterFilter[idxR])

                    indexA = rightBorderIndex[0]
                    idxL = x.index(leftPeakBorder[indexA][0])

                    rightPeakBorder=list(rightPeakBorder)
                    rightPeakBorder = rightPeakBorder[:indexA] + [(x[idxR], dataAfterFilter[idxR])] + rightPeakBorder[indexA+1:] #

                    interpolatedLine = GUI.interpolation(leftPeakBorder[indexA], rightPeakBorder[indexA], idxL, idxR)

                    # calculation of peak amplitude
                    peakFullArea = []
                    peakFullArea[:] = [(i - j) for i,j in zip(dataAfterFilter[idxL:idxR], interpolatedLine)]
                    area[indexA]=peakFullArea

                    pickable_artists_lnsP_AX3[indexA].remove()
                    lns3TruePeak, = ax3.plot(x[idxL:idxR], peakFullArea, 'k--')
                    pickable_artists_lnsP_AX3 = pickable_artists_lnsP_AX3[:indexA] + [lns3TruePeak] + pickable_artists_lnsP_AX3[indexA+1:]

                    peakAmplitude = max(peakFullArea)
                    amplitudes = amplitudes[:indexA] + [peakAmplitude] + amplitudes[indexA+1:]

                    amplitudeLineCoordinates=list(amplitudeLineCoordinates)
                    amplitudeLineCoordinates[indexA][1][0]=peakAmplitude

                    pickable_artists_lns_AX3[indexA].remove()
                    lns3, = ax3.plot(amplitudeLineCoordinates[indexA][0], amplitudeLineCoordinates[indexA][1], 'k') # line from max to baseline
                    pickable_artists_lns_AX3 = pickable_artists_lns_AX3[:indexA] + [lns3] + pickable_artists_lns_AX3[indexA+1:]

                    pickable_artists_fill_AX3[indexA].remove()
                    pts3fill = ax3.fill_between(np.array(x[idxL:idxR]), \
                                    interpolatedLine, \
                                    np.array(dataAfterFilter[idxL:idxR]), \
                                    facecolor='green', interpolate=True, alpha=0.4)
                    pickable_artists_fill_AX3 = pickable_artists_fill_AX3[:indexA] + [pts3fill] + pickable_artists_fill_AX3[indexA+1:] #

                    GUI.fig.canvas.draw()

                else:
                    pass


#%% GUI
class MyWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('PeakInspector.ui', self)
        self.setWindowTitle('PeakInspector (beta) (c) ASalykin - Masaryk University - CC BY-SA 4.0')

        # Some interactive GUI elements
        self.BtnLoadFile.clicked.connect(self.loadFile)
        self.BtnReplot.clicked.connect(self.replot_graph)
        self.chbxDotPickEnable.stateChanged.connect(self.dotPickEnable)
        self.BtnSaveCurrent.clicked.connect(self.coordsAnalysis)
        # self.BoxBaselineTreshold.valueChanged.connect(self.replot_graph)
        self.BtnSaveFullDataset.clicked.connect(self.save_data)
        self.BoxMplPlotStyle.currentIndexChanged.connect(self.mplStyleChange)
        
        style.use(self.BoxMplPlotStyle.currentText())
        # Possible styles:
        #['ggplot', 'dark_background', 'bmh', 'grayscale', 'fivethirtyeight']

        self.fig = plt.figure()
        self.show()

    def mplStyleChange(self,):
        pass

    def addmpl(self,):
        global cid_mouse, cidmotion
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self.CanvasWidget, coordinates=True)
        self.CanvasLayout.addWidget(self.toolbar)        
        self.CanvasLayout.addWidget(self.canvas)
        if self.chbxDotPickEnable.isChecked():
            cid_mouse=self.canvas.mpl_connect('button_press_event', onclick)
            cidmotion = self.canvas.mpl_connect('motion_notify_event', on_motion)
        self.canvas.draw()

    def dotPickEnable(self,): # if checked, user can choose peaks
        global cid_mouse, cidmotion
        try: # if figure and canvas is initiated
            if self.chbxDotPickEnable.isChecked():            
                    cid_mouse=self.canvas.mpl_connect('button_press_event', onclick)
                    cidmotion = self.canvas.mpl_connect('motion_notify_event', on_motion)
            else:
                self.canvas.mpl_disconnect(cid_mouse)
                self.canvas.mpl_disconnect(cidmotion)
        except:
            pass

    def rmmpl(self,): #
        global cid_mouse, cidmotion
        self.canvas.mpl_disconnect(cid_mouse)
        self.canvas.mpl_disconnect(cidmotion)
        self.CanvasLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.CanvasLayout.removeWidget(self.toolbar)
        self.toolbar.close()

    def loadFile(self,):
        global x, y, graphName, cid_mouse

        # Check if we already have some file loaded - then remove canvas
        if 'cid_mouse' in globals():
            self.rmmpl()

        # Make sure that np data arrays and lists from previous dataset are empty
        x=np.empty([])
        y=np.empty([])
        self.clearData()

        try:
            name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')

            # get more readable file name for graph title
            try:
                slashIndex = self.findCharacter(name, '/')
                dotIndex = self.findCharacter(name, '.')
                graphName = name[slashIndex[-1]+1:dotIndex[-1]]
            except:
                graphName = name

            SkipHeaderRows=self.BoxSkipHeader.value()
            SkipFooterRows=self.BoxSkipFooter.value()

            # upnpack file
            try: # if data file has 2 columns
                if self.BoxDelimeterChoice.currentText()=='Tab':
                    delimeter = "\t"
                elif self.BoxDelimeterChoice.currentText()=='Space':
                    delimeter = " "
                elif self.BoxDelimeterChoice.currentText()=='Comma':
                    delimeter = ","
                elif self.BoxDelimeterChoice.currentText()=='Dot':
                    delimeter = "."   
                x, y = np.genfromtxt(name,  
                    delimiter=delimeter, 
                    skip_header=SkipHeaderRows, 
                    skip_footer=SkipFooterRows, 
                    unpack=True)  
             
            except: # if data file has 1 column
                y = np.genfromtxt(name,
                skip_header=SkipHeaderRows, 
                skip_footer=SkipFooterRows, unpack=True)
                x=np.arange(0,len(y), 1)       


            # prevent any change in 'x'
            if len(x)>0:
                x=tuple(x)
                self.dataPreprocessing(y)
                self.baselineCalculation()
                self.plotData()
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "File was not loaded! \n Please be sure that your file has \
                \n 1) 1 or 2 columns; \n 2) check headers, footers and delimeter \n and try again.") 

    def dataPreprocessing(self, dataToPreprocess):
        global dataDetrended, dataAfterFilter
        try:
            # Detrend dataset
            if self.chbxDetrendData.isChecked():
                dataDetrended=sig.detrend(dataToPreprocess)
            else:
                dataDetrended=dataToPreprocess

            # Application of Savitzkyi-Golay filter for data smoothing
            SGWindowFrame=self.BoxSGwindowFrame.value()
            SGPolynomDegree=self.BoxSGpolynomDegree.value()
            dataAfterFilter = sig.savgol_filter(dataDetrended, SGWindowFrame, SGPolynomDegree)
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "Not possible to detrend and/or smooth data! \n Please check your dataset and try again.")

    def baselineCalculation(self, ):
        '''
        Calculate baseline of detrended data and add it to dataset for baseline to be equal 0
        '''
        global dataDetrended, dataAfterFilter, x
        # OLD WAY OF BASELINE CALCULATION
        # baselineTreshold=self.BoxBaselineTreshold.value()
        # tresholdFilter = min(dataAfterFilter)+(max(dataAfterFilter)-min(dataAfterFilter))*baselineTreshold
        # if tresholdFilter == min(dataAfterFilter):
        #     dataBaseline = tresholdFilter
        # else:
        #     medianForPlotData = [m for m in dataAfterFilter if m<tresholdFilter]
        #     dataBaseline = np.median(medianForPlotData)

        # dataAfterFilter = [x+abs(dataBaseline) for x in dataAfterFilter]
        # dataDetrended = [x+abs(dataBaseline) for x in dataDetrended]
        dataBaseline = min(dataAfterFilter)
        if self.chbxDetrendData.isChecked():            
            dataAfterFilter = [x+abs(dataBaseline) for x in dataAfterFilter]
            dataDetrended = [x+abs(dataBaseline) for x in dataDetrended]
        else:
            dataAfterFilter = [x-abs(dataBaseline) for x in dataAfterFilter]
            dataDetrended = [x-abs(dataBaseline) for x in dataDetrended]

    def interpolation(self, p1, p2, leftIndex, rightIndex):
        global x
        f = interpolate.interp1d([p1[0], p2[0]], [p1[1], p2[1]])
        num = len(x[leftIndex:rightIndex])
        xx = np.linspace(x[leftIndex], x[rightIndex], num)
        return f(xx)

    def plotData(self,):
        global x, y, dataDetrended, dataAfterFilter, graphName, baselinePlotArtist
        global ax1, ax2, ax3


        if self.BoxPlotCustomStyle.currentText()=='Line':
                    plotStyleCustom = '-'
                    markerSize = 1
        elif self.BoxPlotCustomStyle.currentText()=='Line & small markers':
                    plotStyleCustom = 'o-'
                    markerSize = 3
        elif self.BoxPlotCustomStyle.currentText()=='Line & big markers':
                    plotStyleCustom = 'o-'
                    markerSize = 6
        elif self.BoxPlotCustomStyle.currentText()=='Small markers':
                    plotStyleCustom = 'o'
                    markerSize = 3
        elif self.BoxPlotCustomStyle.currentText()=='Big markers':
                    plotStyleCustom = 'o'
                    markerSize = 6

        fontSize=14

        ax1 = plt.subplot2grid((4,1), (0,0), rowspan=1, colspan=1)
        plt.title(graphName)
        ax1.plot(x, y, plotStyleCustom, ms=markerSize, linewidth=1) # plot raw data
        plt.ylabel('Original raw data', fontsize=fontSize)

        ax2 = plt.subplot2grid((4,1), (1,0), rowspan=1, colspan=1)
        ax2.plot(x, dataDetrended, plotStyleCustom, ms=markerSize, linewidth=1) # plot detrended data
        plt.ylabel('Detrended data', fontsize=fontSize)

        ax3 = plt.subplot2grid((4,1), (2,0), rowspan=2, colspan=1, sharex=ax2, sharey=ax2)
        ax3.plot(x, dataAfterFilter, plotStyleCustom, ms=markerSize, linewidth=1) # plot filtered detrended data
        baselinePlotArtist = ax3.plot([x[0], x[-1]], [0, 0], 'k', linewidth=1) # plot baseline        
        plt.ylabel('Savitzky-Golay filter \n for detrended data', fontsize=fontSize) 
        ax3.set_xlim(0, x[-1])
        plt.xlabel('Time, sec')


        self.addmpl()

    def replot_graph(self, ):
        global coords
        if 'coords' in globals():
            GUI.clearData()
        self.rmmpl()
        self.dataPreprocessing(y)
        self.baselineCalculation()
        self.plotData()   

    def findCharacter(self, s, ch): # for graph title
        return [i for i, ltr in enumerate(s) if ltr == ch] 

    def coordsAnalysis(self,):
        global coords, area, leftPeakBorder, rightPeakBorder, x, y, dataAfterFilter, amplitudes
        global graphName, relativeAmplitude, periods, frequencies, multipleDataSets

        coordX, coordY = zip(*coords)
        leftpbX,  leftpbY = zip(*leftPeakBorder)
        rightpbX, rightpbY = zip(*rightPeakBorder)

        relativeAmplitude = []
        # maximum amplitude and relative amplitudes
        amplMAX = max(amplitudes)
        # amplMED = np.median(amplitudes)        
        relativeAmplitude[:] = [(i / amplMAX) for i in amplitudes]

        # create temporal Pandas DataFrame for sorting and calculation:
        DataSetForCalculation = list(zip(coordX, amplitudes, relativeAmplitude, leftpbX,  leftpbY, rightpbX, rightpbY, area))
        df = pd.DataFrame(data = DataSetForCalculation, 
            columns=[   'Peak Time', \
                        'Amplitude', \
                        'Relative Amplitude \n (F/Fmax)', \
                        'Peak Start Time', \
                        'Peak Start Ordinate', \
                        'Peak Stop Time', \
                        'Peak Stop Ordinate', \
                        'Area'])

        # Sort data in DataFrame according to the time of peak appearance
        DFsorted = df.sort(['Peak Time'], ascending=True)
        DFsorted.index = range(0,len(DFsorted)) # reset indexing

        periods = []
        # calculate periods
        for i in range(1, len(DFsorted['Peak Time'])):
            period = DFsorted.at[i,'Peak Time'] - DFsorted.at[i-1,'Peak Time']
            periods.append(period)
        periods.insert(0, np.nan) # add placeholder because len(periods)=len(peaks)-1

        # calculate frequencies based on calculated periods
        frequencies = []
        frequencies[:] = [(1/i) for i in periods]

        peakStartStopTime = []
        # Analise peak start - stop time        
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakTime = DFsorted.at[i,'Peak Stop Time'] - DFsorted.at[i,'Peak Start Time']
            peakStartStopTime.append(peakTime)

        peakUpTime = []
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakUp = DFsorted.at[i,'Peak Time'] - DFsorted.at[i,'Peak Start Time']
            peakUpTime.append(peakUp) 

        peakDownTime = []
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakDown = DFsorted.at[i,'Peak Stop Time'] - DFsorted.at[i,'Peak Time']
            peakDownTime.append(peakDown)

        peakArea=[]
        # Compute area under the peak using the composite trapezoidal rule.
        for i in range(0, len(DFsorted['Peak Time']), 1):
            ar = np.trapz(DFsorted.at[i,'Area'])
            peakArea.append(ar)

        halfDecayTime = []
        halfDecayAmplitude = []
        # Analise the half time decay       
        for i in range(0, len(DFsorted['Peak Time']), 1):
            halfDecayAmpl = DFsorted.at[i,'Amplitude']/2 # calculate the half of the amplitude
            peakIdx = x.index(DFsorted.at[i,'Peak Time']) # find index of the peak time
            stopIdx = x.index(DFsorted.at[i,'Peak Stop Time']) # find index of the right peak border
            dataDecayRegion = dataAfterFilter[peakIdx:stopIdx] # determine the amplitude region where to search for halftime decay index
            timeDecayRegion = x[peakIdx:stopIdx]
            halfDecayIdx = (np.abs(dataDecayRegion-halfDecayAmpl)).argmin() # find the closet value in dataDecayRegion that corresponds to the half amplitude

            halfDecayAmplitude.append(halfDecayAmpl)
            halfDecayTime.append(timeDecayRegion[halfDecayIdx]-DFsorted.at[i,'Peak Time'])

        amplitudeToBaseline=[]
        # Compute the deltaF/F0
        SGWindowFrame=self.BoxSGwindowFrame.value()
        SGPolynomDegree=self.BoxSGpolynomDegree.value()
        origDataFiltered = sig.savgol_filter(y, SGWindowFrame, SGPolynomDegree)
        for i in range(0, len(DFsorted['Peak Time']), 1):
            startIdx = x.index(DFsorted.at[i,'Peak Start Time'])
            F0=origDataFiltered[startIdx]
            relativeFcomputation=DFsorted.at[i,'Amplitude']/F0
            amplitudeToBaseline.append(relativeFcomputation)

        relativeAmplitudeToBaseline = []
        # maximum amplitude and relative amplitudes
        maxATB = max(amplitudeToBaseline) # max of amplitude to baseline
        relativeAmplitudeToBaseline[:] = [(i / maxATB) for i in amplitudeToBaseline]

        maxAmplitudeToBaseline=[]
        # maximum deltaF/F0 amplitude
        maxAmplitudeToBaseline = list(range(0, len(DFsorted['Peak Time'])-1))
        maxAmplitudeToBaseline[:] = [np.nan for i in maxAmplitudeToBaseline]
        maxAmplitudeToBaseline.insert(0, maxATB)

        # add file name as first column
        namePlaceHolder = list(range(0, len(DFsorted['Peak Time'])-1))
        namePlaceHolder[:] = [np.nan for i in namePlaceHolder]
        namePlaceHolder.insert(0, graphName)

        # add maximum amplitude
        maxAmplitude = list(range(0, len(DFsorted['Peak Time'])-1))
        maxAmplitude[:] = [np.nan for i in maxAmplitude]
        maxAmplitude.insert(0, max(DFsorted['Amplitude']))

        # peak sorting
        topPeaksNum = []
        midPeaksNum = []
        lowPeaksNum = []
        topPeaksNum[:] = [p for p in amplitudes if (p > amplMAX*0.66)] 
        midPeaksNum[:] = [p for p in amplitudes if  (p > amplMAX*0.33 and p <= amplMAX*0.66)]
        lowPeaksNum[:] = [p for p in amplitudes if (p > 0 and p <= amplMAX*0.33)]

        topPeaksFrequency = list(range(0, len(DFsorted['Peak Time'])-1))
        topPeaksFrequency[:] = [np.nan for i in topPeaksFrequency]
        topPeaksFrequency.insert(0, len(topPeaksNum)/(x[-1]-x[0]))

        midPeaksFrequency = list(range(0, len(DFsorted['Peak Time'])-1))
        midPeaksFrequency[:] = [np.nan for i in midPeaksFrequency]
        midPeaksFrequency.insert(0, len(midPeaksNum)/(x[-1]-x[0]))

        lowPeaksFrequency = list(range(0, len(DFsorted['Peak Time'])-1))
        lowPeaksFrequency[:] = [np.nan for i in lowPeaksFrequency]
        lowPeaksFrequency.insert(0, len(lowPeaksNum)/(x[-1]-x[0]))


        finalDataSet = list(zip(namePlaceHolder, \
            DFsorted['Peak Time'],\
            DFsorted['Amplitude'],\
            DFsorted['Relative Amplitude \n (F/Fmax)'], \
            maxAmplitude,            
            amplitudeToBaseline, \
            relativeAmplitudeToBaseline,\
            maxAmplitudeToBaseline,\
            periods, \
            frequencies,  \
            halfDecayTime, \
            halfDecayAmplitude,\
            DFsorted['Peak Start Time'], \
            DFsorted['Peak Start Ordinate'], \
            DFsorted['Peak Stop Time'], \
            DFsorted['Peak Stop Ordinate'], \
            peakUpTime, \
            peakDownTime, \
            peakStartStopTime, \
            peakArea,\
            topPeaksFrequency,\
            midPeaksFrequency,\
            lowPeaksFrequency))

        finalDF = pd.DataFrame(data = finalDataSet, 
            columns=[   'File Name',\
                        'Peak Time', \
                        'Amplitude, F', \
                        'Relative F (F_to_Fmax)', \
                        'MAX F',\
                        'deltaF_to_F0', \
                        'Relative deltaF_to_F0', \
                        'MAX deltaF_to_F0', \
                        'Period',\
                        'Frequency',\
                        'Halfdecay Time',\
                        'Halfdecay Amplitude',\
                        'Start Time', \
                        'Start Ordinate', \
                        'Stop Time', \
                        'Stop Ordinate',\
                        'Time to peak',\
                        'Decay time',
                        'Full peak time',\
                        'AUC',
                        'Top peaks, Hz',\
                        'Mid peaks, Hz',\
                        'Low peaks, Hz'])
        # finalDF.index = range(0,len(finalDF)) # reset indexing        

        # append current analysed dataset to existing ones
        multipleDataSets = multipleDataSets.append(finalDF)

        if self.chbxSaveFig.isChecked():
            os.makedirs('_Figures', exist_ok=True)
            DPI = GUI.BoxDPI.value()
            plt.savefig(os.path.join('_Figures', 'Fig_{figName}.png'.format(figName=graphName)), dpi=DPI)

        del df
        del DFsorted
        finalDF = pd.DataFrame()

        self.loadFile()

    def save_data(self, ):
        global multipleDataSets
        try:
            fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save file')
            writer = pd.ExcelWriter('{fileName}.xlsx'.format(fileName=fileName))
            # multipleDataSets.to_excel('{fileName}.xlsx'.format(fileName=fileName), index=True) 
            multipleDataSets.to_excel(writer, index=True, sheet_name='Results')
            writer.sheets['Results'].set_zoom(85)
            writer.sheets['Results'].set_column('A:A', 5)
            writer.sheets['Results'].set_column('B:B', 35)
            writer.sheets['Results'].set_column('C:X', 17)
            writer.save()

            message = MessageBox()
            message.about(self, 'Data saved', "Data were saved!")
            del multipleDataSets
            multipleDataSets = pd.DataFrame()
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "Data were not exported to Excel! \n Please try again.")

    def mplStyleChange(self, ):
        style.use(self.BoxMplPlotStyle.currentText())

    def clearData(self,):
        global coords, area, amplitudes, amplitudeLineCoordinates, leftPeakBorder, rightPeakBorder, pickable_artists_pts_AX2, pickable_artists_lnsP_AX3
        global pickable_artists_pts_AX3, pickable_artists_lns_AX3, pickable_artists_fill_AX3, pickable_artists_plb_AX3, pickable_artists_prb_AX3
        coords=[]
        area=[]
        amplitudes=[]
        amplitudeLineCoordinates = []
        leftPeakBorder = []
        rightPeakBorder = []
        pickable_artists_pts_AX2 = []
        pickable_artists_pts_AX3 = []
        pickable_artists_lns_AX3 = []
        pickable_artists_fill_AX3 = []
        pickable_artists_plb_AX3 = []
        pickable_artists_prb_AX3 = []
        pickable_artists_lnsP_AX3 = []

    def closeEvent(self, event):
        global multipleDataSets
        if multipleDataSets.empty:
            reply = MessageBox.question(self, 'Warning!',
                "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        else:
            reply = MessageBox.question(self, 'Warning!',
                "You have unsaved analysed data! \n Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class MessageBox(QtGui.QMessageBox):
     def __init__(self, parent=None):
         QtGui.QMessageBox.__init__(self, parent)
         self.setWindowTitle('Message box')


# if __name__ == '__main__':
def run():
    global GUI, app
    app = QtGui.QApplication(sys.argv)
    GUI = MyWindow()
    GUI.showMaximized()
    sys.exit(app.exec_())

run()
