import os
from PyQt4 import QtGui, uic
import numpy as np
import pandas as pd
import scipy.signal as sig
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib import style
# Possible styles:
# ['ggplot', 'dark_background', 'bmh', 'grayscale', 'fivethirtyeight']

from MessageBox import MessageBox
from OnClick import OnClick
from OnMotion import OnMotion


class MainWindow(QtGui.QMainWindow, OnClick, OnMotion):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("PeakInspector_layout.ui", self)
        self.setWindowTitle("PeakInspector (beta) (c) ASalykin - Masaryk University - CC-BY-SA 4.0")

        # Variables:
        self.multipleDataSets = pd.DataFrame()  # Initialise the final dataframe to export to Excel

        # Connect buttons to class methods:
        self.BtnLoadFile.clicked.connect(self.loadFile)
        self.BtnReplot.clicked.connect(self.replot_graph)
        self.chbxDotPickEnable.stateChanged.connect(self.dotPickEnable)
        self.BtnSaveCurrent.clicked.connect(self.coordinatesAnalysis)
        self.BtnSaveFullDataset.clicked.connect(self.save_data)
        self.BoxMplPlotStyle.currentIndexChanged.connect(self.mplStyleChange)
        style.use(self.BoxMplPlotStyle.currentText())

        # Initialise figure instance
        self.fig = plt.figure()
        self.show()

    def mplStyleChange(self, ):
        pass

    def addmpl(self, ):
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self.CanvasWidget, coordinates=True)
        self.CanvasLayout.addWidget(self.toolbar)
        self.CanvasLayout.addWidget(self.canvas)
        if self.chbxDotPickEnable.isChecked():
            self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_click)
            self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.draw()

    def dotPickEnable(self, ):  # if checked, user can choose peaks
        try:  # if figure and canvas is initiated
            if self.chbxDotPickEnable.isChecked():
                self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_click)
                self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            else:
                self.canvas.mpl_disconnect(self.cid_click)
                self.canvas.mpl_disconnect(self.cid_motion)
        except:
            pass

    def rmmpl(self, ):  #
        self.canvas.mpl_disconnect(self.cid_click)
        self.canvas.mpl_disconnect(self.cid_motion)
        self.CanvasLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.CanvasLayout.removeWidget(self.toolbar)
        self.toolbar.close()

    def loadFile(self, ):
        # Check if we already have some file loaded - then remove canvas
        if hasattr(self, 'cid_click'):
            self.rmmpl()

        # Make sure that np data arrays and lists from previous dataset are empty
        self.x = np.empty([])
        self.y = np.empty([])
        self.clear_data()

        try:
            name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')

            # get more readable file name for graph title
            try:
                slashIndex = self.find_character(name, '/')
                dotIndex = self.find_character(name, '.')
                self.graphName = name[slashIndex[-1] + 1:dotIndex[-1]]
            except:
                self.graphName = name

            SkipHeaderRows = self.BoxSkipHeader.value()
            SkipFooterRows = self.BoxSkipFooter.value()

            # upnpack file
            try:  # if data file has 2 columns
                if self.BoxDelimeterChoice.currentText() == 'Tab':
                    delimeter = "\t"
                elif self.BoxDelimeterChoice.currentText() == 'Space':
                    delimeter = " "
                elif self.BoxDelimeterChoice.currentText() == 'Comma':
                    delimeter = ","
                elif self.BoxDelimeterChoice.currentText() == 'Dot':
                    delimeter = "."
                self.x, self.y = np.genfromtxt(name,
                                     delimiter=delimeter,
                                     skip_header=SkipHeaderRows,
                                     skip_footer=SkipFooterRows,
                                     unpack=True)

            except:  # if data file has 1 column
                self.y = np.genfromtxt(name,
                                  skip_header=SkipHeaderRows,
                                  skip_footer=SkipFooterRows, unpack=True)
                self.x = np.arange(0, len(self.y), 1)

            # prevent any change in 'x'
            if len(self.x) > 0:
                self.x = tuple(self.x)
                self.dataPreprocessing(self.y)
                self.baselineCalculation()
                self.plotData()
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "File was not loaded! \n Please be sure that your file has \
                \n 1) 1 or 2 columns; \n 2) check headers, footers and delimeter \n and try again.")

    def dataPreprocessing(self, dataToPreprocess):
        try:
            # Detrend dataset
            if self.chbxDetrendData.isChecked():
                self.dataDetrended = sig.detrend(dataToPreprocess)
            else:
                self.dataDetrended = dataToPreprocess

            # Application of Savitzkyi-Golay filter for data smoothing
            SGWindowFrame = self.BoxSGwindowFrame.value()
            SGPolynomDegree = self.BoxSGpolynomDegree.value()
            self.dataAfterFilter = sig.savgol_filter(self.dataDetrended, SGWindowFrame, SGPolynomDegree)
        except:
            message = MessageBox()
            message.about(self, 'Warning!',
                          "Not possible to detrend and/or smooth data! \n Please check your dataset and try again.")

    def baselineCalculation(self, ):
        '''
        Calculate baseline of detrended data and add it to dataset for baseline to be equal 0
        '''
        dataBaseline = min(self.dataAfterFilter)
        if self.chbxDetrendData.isChecked():
            self.dataAfterFilter = [i + abs(dataBaseline) for i in self.dataAfterFilter]
            self.dataDetrended = [i + abs(dataBaseline) for i in self.dataDetrended]
        else:
            self.dataAfterFilter = [i - abs(dataBaseline) for i in self.dataAfterFilter]
            self.dataDetrended = [i - abs(dataBaseline) for i in self.dataDetrended]

    def interpolation(self, p1, p2, leftIndex, rightIndex):
        f = interpolate.interp1d([p1[0], p2[0]], [p1[1], p2[1]])
        num = len(self.x[leftIndex:rightIndex])
        xx = np.linspace(self.x[leftIndex], self.x[rightIndex], num)
        return f(xx)

    def plotData(self, ):
        if self.BoxPlotCustomStyle.currentText() == 'Line':
            plot_style_custom = '-'
            marker_size = 1
        elif self.BoxPlotCustomStyle.currentText() == 'Line & small markers':
            plot_style_custom = 'o-'
            marker_size = 3
        elif self.BoxPlotCustomStyle.currentText() == 'Line & big markers':
            plot_style_custom = 'o-'
            marker_size = 6
        elif self.BoxPlotCustomStyle.currentText() == 'Small markers':
            plot_style_custom = 'o'
            marker_size = 3
        elif self.BoxPlotCustomStyle.currentText() == 'Big markers':
            plot_style_custom = 'o'
            marker_size = 6

        font_size = 14

        self.ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=1, colspan=1)
        plt.title(self.graphName)
        self.ax1.plot(self.x, self.y, plot_style_custom, ms=marker_size, linewidth=1)  # plot raw data
        plt.ylabel('Original raw data', fontsize=font_size)

        self.ax2 = plt.subplot2grid((4, 1), (1, 0), rowspan=1, colspan=1)
        self.ax2.plot(self.x, self.dataDetrended, plot_style_custom, ms=marker_size, linewidth=1)  # plot detrended data
        plt.ylabel('Detrended data', fontsize=font_size)

        self.ax3 = plt.subplot2grid((4, 1), (2, 0), rowspan=2, colspan=1, sharex=self.ax2, sharey=self.ax2)
        self.ax3.plot(self.x, self.dataAfterFilter, plot_style_custom, ms=marker_size, linewidth=1)  # plot filtered detrended data
        self.baselinePlotArtist = self.ax3.plot([self.x[0], self.x[-1]], [0, 0], 'k', linewidth=1)  # plot baseline
        plt.ylabel('Savitzky-Golay filter \n for detrended data', fontsize=font_size)
        self.ax3.set_xlim(0, self.x[-1])
        plt.xlabel('Time, sec')

        self.addmpl()

    def replot_graph(self, ):
        self.clear_data()
        self.rmmpl()
        self.dataPreprocessing(self.y)
        self.baselineCalculation()
        self.plotData()

    def coordinatesAnalysis(self, ):
        global graphName, relativeAmplitude, periods, frequencies

        coordX, coordY = zip(*self.coordinates)
        leftpbX, leftpbY = zip(*self.left_peak_border)
        rightpbX, rightpbY = zip(*self.right_peak_border)

        relativeAmplitude = []
        # maximum amplitude and relative self.amplitudes
        amplMAX = max(self.amplitudes)
        # amplMED = np.median(self.amplitudes)
        relativeAmplitude[:] = [(i / amplMAX) for i in self.amplitudes]

        # create temporal Pandas DataFrame for sorting and calculation:
        DataSetForCalculation = list(
            zip(coordX, self.amplitudes, relativeAmplitude, leftpbX, leftpbY, rightpbX, rightpbY, self.area))
        df = pd.DataFrame(data=DataSetForCalculation,
                          columns=['Peak Time',
                                   'Amplitude',
                                   'Relative Amplitude \n (F/Fmax)',
                                   'Peak Start Time',
                                   'Peak Start Ordinate',
                                   'Peak Stop Time',
                                   'Peak Stop Ordinate',
                                   'Area'])

        # Sort data in DataFrame according to the time of peak appearance
        DFsorted = df.sort_values(['Peak Time'], ascending=True)
        DFsorted.index = range(0, len(DFsorted))  # reset indexing

        periods = []
        # calculate periods
        for i in range(1, len(DFsorted['Peak Time'])):
            period = DFsorted.at[i, 'Peak Time'] - DFsorted.at[i - 1, 'Peak Time']
            periods.append(period)
        periods.insert(0, np.nan)  # add placeholder because len(periods)=len(peaks)-1

        # calculate frequencies based on calculated periods
        frequencies = []
        frequencies[:] = [(1 / i) for i in periods]

        peakStartStopTime = []
        # Analise peak start - stop time
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakTime = DFsorted.at[i, 'Peak Stop Time'] - DFsorted.at[i, 'Peak Start Time']
            peakStartStopTime.append(peakTime)

        peakUpTime = []
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakUp = DFsorted.at[i, 'Peak Time'] - DFsorted.at[i, 'Peak Start Time']
            peakUpTime.append(peakUp)

        peakDownTime = []
        for i in range(0, len(DFsorted['Peak Time']), 1):
            peakDown = DFsorted.at[i, 'Peak Stop Time'] - DFsorted.at[i, 'Peak Time']
            peakDownTime.append(peakDown)

        peakArea = []
        # Compute area under the peak using the composite trapezoidal rule.
        for i in range(0, len(DFsorted['Peak Time']), 1):
            ar = np.trapz(DFsorted.at[i, 'Area'])
            peakArea.append(ar)

        halfDecayTime = []
        halfDecayAmplitude = []
        # Analise the half time decay
        for i in range(0, len(DFsorted['Peak Time']), 1):
            halfDecayAmpl = DFsorted.at[i, 'Amplitude'] / 2  # calculate the half of the amplitude
            peakIdx = self.x.index(DFsorted.at[i, 'Peak Time'])  # find index of the peak time
            stopIdx = self.x.index(DFsorted.at[i, 'Peak Stop Time'])  # find index of the right peak border
            dataDecayRegion = self.dataAfterFilter[
                              peakIdx:stopIdx]  # determine the amplitude region where to search for halftime decay index
            timeDecayRegion = self.x[peakIdx:stopIdx]
            halfDecayIdx = (np.abs(
                dataDecayRegion - halfDecayAmpl)).argmin()  # find the closet value in dataDecayRegion that corresponds to the half amplitude

            halfDecayAmplitude.append(halfDecayAmpl)
            halfDecayTime.append(timeDecayRegion[halfDecayIdx] - DFsorted.at[i, 'Peak Time'])

        amplitudeToBaseline = []
        # Compute the deltaF/F0
        SGWindowFrame = self.BoxSGwindowFrame.value()
        SGPolynomDegree = self.BoxSGpolynomDegree.value()
        origDataFiltered = sig.savgol_filter(self.y, SGWindowFrame, SGPolynomDegree)
        for i in range(0, len(DFsorted['Peak Time']), 1):
            startIdx = self.x.index(DFsorted.at[i, 'Peak Start Time'])
            F0 = origDataFiltered[startIdx]
            relativeFcomputation = DFsorted.at[i, 'Amplitude'] / F0
            amplitudeToBaseline.append(relativeFcomputation)

        relativeAmplitudeToBaseline = []
        # maximum amplitude and relative self.amplitudes
        maxATB = max(amplitudeToBaseline)  # max of amplitude to baseline
        relativeAmplitudeToBaseline[:] = [(i / maxATB) for i in amplitudeToBaseline]

        maxAmplitudeToBaseline = []
        # maximum deltaF/F0 amplitude
        maxAmplitudeToBaseline = list(range(0, len(DFsorted['Peak Time']) - 1))
        maxAmplitudeToBaseline[:] = [np.nan for i in maxAmplitudeToBaseline]
        maxAmplitudeToBaseline.insert(0, maxATB)

        # add file name as first column
        namePlaceHolder = list(range(0, len(DFsorted['Peak Time']) - 1))
        namePlaceHolder[:] = [np.nan for i in namePlaceHolder]
        namePlaceHolder.insert(0, self.graphName)

        # add maximum amplitude
        maxAmplitude = list(range(0, len(DFsorted['Peak Time']) - 1))
        maxAmplitude[:] = [np.nan for i in maxAmplitude]
        maxAmplitude.insert(0, max(DFsorted['Amplitude']))

        # peak sorting
        topPeaksNum = []
        midPeaksNum = []
        lowPeaksNum = []
        topPeaksNum[:] = [p for p in self.amplitudes if (p > amplMAX * 0.66)]
        midPeaksNum[:] = [p for p in self.amplitudes if (p > amplMAX * 0.33 and p <= amplMAX * 0.66)]
        lowPeaksNum[:] = [p for p in self.amplitudes if (p > 0 and p <= amplMAX * 0.33)]

        topPeaksFrequency = list(range(0, len(DFsorted['Peak Time']) - 1))
        topPeaksFrequency[:] = [np.nan for i in topPeaksFrequency]
        topPeaksFrequency.insert(0, len(topPeaksNum) / (self.x[-1] - self.x[0]))

        midPeaksFrequency = list(range(0, len(DFsorted['Peak Time']) - 1))
        midPeaksFrequency[:] = [np.nan for i in midPeaksFrequency]
        midPeaksFrequency.insert(0, len(midPeaksNum) / (self.x[-1] - self.x[0]))

        lowPeaksFrequency = list(range(0, len(DFsorted['Peak Time']) - 1))
        lowPeaksFrequency[:] = [np.nan for i in lowPeaksFrequency]
        lowPeaksFrequency.insert(0, len(lowPeaksNum) / (self.x[-1] - self.x[0]))

        finalDataSet = list(zip(namePlaceHolder,
                                DFsorted['Peak Time'],
                                DFsorted['Amplitude'],
                                DFsorted['Relative Amplitude \n (F/Fmax)'],
                                maxAmplitude,
                                amplitudeToBaseline,
                                relativeAmplitudeToBaseline,
                                maxAmplitudeToBaseline,
                                periods,
                                frequencies,
                                halfDecayTime,
                                halfDecayAmplitude,
                                DFsorted['Peak Start Time'],
                                DFsorted['Peak Start Ordinate'],
                                DFsorted['Peak Stop Time'],
                                DFsorted['Peak Stop Ordinate'],
                                peakUpTime,
                                peakDownTime,
                                peakStartStopTime,
                                peakArea,
                                topPeaksFrequency,
                                midPeaksFrequency,
                                lowPeaksFrequency))

        final_dataframe = pd.DataFrame(data=finalDataSet,
                                       columns=['File Name',
                                                'Peak Time',
                                                'Amplitude, F',
                                                'Relative F (F_to_Fmax)',
                                                'MAX F',
                                                'deltaF_to_F0',
                                                'Relative deltaF_to_F0',
                                                'MAX deltaF_to_F0',
                                                'Period',
                                                'Frequency',
                                                'Halfdecay Time',
                                                'Halfdecay Amplitude',
                                                'Start Time',
                                                'Start Ordinate',
                                                'Stop Time',
                                                'Stop Ordinate',
                                                'Time to peak',
                                                'Decay time',
                                                'Full peak time',
                                                'AUC',
                                                'Top peaks, Hz',
                                                'Mid peaks, Hz',
                                                'Low peaks, Hz'])

        # append current analysed dataset to existing ones
        self.multipleDataSets = self.multipleDataSets.append(final_dataframe)

        if self.chbxSaveFig.isChecked():
            os.makedirs('_Figures', exist_ok=True)
            DPI = self.BoxDPI.value()
            plt.savefig(os.path.join('_Figures', 'Fig_{figName}.png'.format(figName=self.graphName)), dpi=DPI)

        del df
        del DFsorted
        final_dataframe = pd.DataFrame()

        self.loadFile()

    def save_data(self, ):
        global multipleDataSets
        try:
            fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save file')
            writer = pd.ExcelWriter('{fileName}.xlsx'.format(fileName=fileName))
            self.multipleDataSets.to_excel(writer, index=True, sheet_name='Results')
            writer.sheets['Results'].set_zoom(85)
            writer.sheets['Results'].set_column('A:A', 5)
            writer.sheets['Results'].set_column('B:B', 35)
            writer.sheets['Results'].set_column('C:X', 17)
            writer.save()

            message = MessageBox()
            message.about(self, 'Data saved', "Data were saved!")
            self.multipleDataSets = pd.DataFrame()
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "Data were not exported to Excel! \n Please try again.")

    def mplStyleChange(self, ):
        style.use(self.BoxMplPlotStyle.currentText())

    def clear_data(self):
        self.coordinates = []
        self.area = []
        self.amplitudes = []
        self.amplitude_line_coordinates = []
        self.left_peak_border = []
        self.right_peak_border = []
        self.pickable_artists_pts_AX2 = []
        self.pickable_artists_pts_AX3 = []
        self.pickable_artists_lns_AX3 = []
        self.pickable_artists_fill_AX3 = []
        self.pickable_artists_plb_AX3 = []
        self.pickable_artists_prb_AX3 = []
        self.pickable_artists_lnsP_AX3 = []

    def closeEvent(self, event):
        """Exchange default event to add a dialog"""
        if self.multipleDataSets.empty:
            reply = MessageBox.question(self, 'Warning!',
                                        "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        else:
            reply = MessageBox.question(self, 'Warning!',
                                        "You have unsaved analysed data! \n Are you sure to quit?",
                                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    @staticmethod
    def find_character(s, ch):  # for graph title
        return [i for i, ltr in enumerate(s) if ltr == ch]
