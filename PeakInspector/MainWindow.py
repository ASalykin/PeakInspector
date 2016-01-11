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
        self.setWindowTitle("PeakInspector (beta) (c) A.Salykin - Masaryk University - CC-BY-SA 4.0")

        # main variable:
        self.multiple_data_sets = pd.DataFrame()  # Initialise the final dataframe to export to Excel

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

        self.left_border = []
        self.right_border = []

        # Connect buttons to class methods:
        self.BtnLoadFile.clicked.connect(self.load_file)
        self.BtnReplot.clicked.connect(self.replot_graph)
        self.chbxDotPickEnable.stateChanged.connect(self.dot_pick_enable)
        self.BtnSaveCurrent.clicked.connect(self.coordinates_analysis)
        self.BtnSaveFullDataset.clicked.connect(self.save_data)
        self.BoxMplPlotStyle.currentIndexChanged.connect(self.mpl_style_change)

        style.use(self.BoxMplPlotStyle.currentText())

        self.BtnLoadFile.setStyleSheet("background-color: #7CF2BD")
        self.BtnReplot.setStyleSheet("background-color: #FAF6F2")
        self.BtnSaveCurrent.setStyleSheet("background-color: #FAF6F2")
        self.BtnSaveFullDataset.setStyleSheet("background-color: #FAF6F2")

        # Initialise figure instance
        self.fig = plt.figure()
        self.show()

    def addmpl(self, ):
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self.CanvasWidget, coordinates=True)
        self.CanvasLayout.addWidget(self.toolbar)
        self.CanvasLayout.addWidget(self.canvas)
        if self.chbxDotPickEnable.isChecked():
            self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_click)
            self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.draw()

    def rmmpl(self, ):  #
        self.canvas.mpl_disconnect(self.cid_click)
        self.canvas.mpl_disconnect(self.cid_motion)
        self.CanvasLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.CanvasLayout.removeWidget(self.toolbar)
        self.toolbar.close()

    def dot_pick_enable(self, ):  # if checked, user can choose peaks
        try:  # if figure and canvas is initiated
            if self.chbxDotPickEnable.isChecked():
                self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_click)
                self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            else:
                self.canvas.mpl_disconnect(self.cid_click)
                self.canvas.mpl_disconnect(self.cid_motion)
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "File was not loaded! \n Please be sure that your file has \
                \n 1) 1 or 2 columns; \n 2) check headers, footers and delimeter \n and try again.")

    def load_file(self, ):
        self.BtnLoadFile.setStyleSheet("background-color: #FAF6F2")
        # Check if we already have some file loaded - then remove canvas
        if hasattr(self, 'cid_click'):
            self.rmmpl()

        # Make sure that np data arrays and lists from previous dataset are empty
        self.x = np.empty([])
        self.y = np.empty([])
        self.clear_data()

        name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        if not name:
            return self.import_error()

        # get more readable file name for graph title
        try:
            slash_index = self.find_character(name, '/')
            dot_index = self.find_character(name, '.')
            self.graph_name = name[slash_index[-1] + 1:dot_index[-1]]
        except:
            self.graph_name = name[-10:]

        skip_header_rows = self.BoxSkipHeader.value()
        skip_footer_rows = self.BoxSkipFooter.value()

        if self.BoxDelimeterChoice.currentText() == 'Tab':
            delimiter = "\t"
        elif self.BoxDelimeterChoice.currentText() == 'Space':
            delimiter = " "
        elif self.BoxDelimeterChoice.currentText() == 'Comma':
            delimiter = ","
        elif self.BoxDelimeterChoice.currentText() == 'Dot':
            delimiter = "."

        # unpack file
        try:  # if data file has 2 columns
            self.x, self.y = np.genfromtxt(name,
                                 delimiter = delimiter,
                                 skip_header = skip_header_rows,
                                 skip_footer = skip_footer_rows,
                                 unpack = True)
            if len(self.y) < 100:
                return self.import_error()
            return self.process_opened_file()

        except:  # if data file has 1 column
            self.y = np.genfromtxt(name,
                              skip_header=skip_header_rows,
                              skip_footer=skip_footer_rows, unpack=True)
            if len(self.y) < 100:
                return self.import_error()
            self.x = np.arange(0, len(self.y), 1)
            return self.process_opened_file()

    def import_error(self,):
        message = MessageBox()
        message.about(self, 'Warning!', "Data were not loaded. \n Please, be sure that:\n "
                                                "1. Data have 1 or 2 columns.\n"
                                                "2. Data are longer than 100 points.\n"
                                                "3. Delimiter is correctly specified.\n"
                                                "4. Rows in data contain only numeric values\n")

    def process_opened_file(self, ):
        self.x = tuple(self.x)
        self.data_preprocessing(self.y)
        self.baseline_calculation()
        self.plot_data()

    def data_preprocessing(self, data_to_preprocess):
        try:
            # Detrend dataset
            if self.chbxDetrendData.isChecked():
                self.data_detrended = sig.detrend(data_to_preprocess)
            else:
                self.data_detrended = data_to_preprocess

            # Application of Savitzkyi-Golay filter for data smoothing
            sg_window_frame = self.BoxSGwindowFrame.value()
            sg_polynom_degree = self.BoxSGpolynomDegree.value()
            self.data_after_filter = sig.savgol_filter(self.data_detrended, sg_window_frame, sg_polynom_degree)
        except:
            message = MessageBox()
            message.about(self, 'Warning!',
                          "Not possible to detrend and/or smooth data! \n Please check your dataset and try again.")

    def baseline_calculation(self, ):
        '''
        Calculate baseline of detrended data and add it to dataset for baseline to be equal 0
        '''
        databaseline = min(self.data_after_filter)
        if self.chbxDetrendData.isChecked():
            self.data_after_filter = [i + abs(databaseline) for i in self.data_after_filter]
            self.data_detrended = [i + abs(databaseline) for i in self.data_detrended]
        else:
            self.data_after_filter = [i - abs(databaseline) for i in self.data_after_filter]
            self.data_detrended = [i - abs(databaseline) for i in self.data_detrended]

    def interpolation(self, p1, p2, left_index, right_index):
        f = interpolate.interp1d([p1[0], p2[0]], [p1[1], p2[1]])
        num = len(self.x[left_index:right_index])
        xx = np.linspace(self.x[left_index], self.x[right_index], num)
        return f(xx)

    def plot_data(self, ):
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
        plt.title(self.graph_name)
        self.ax1.plot(self.x, self.y, plot_style_custom, ms=marker_size, linewidth=1)  # plot raw data
        plt.ylabel('Original raw data', fontsize=font_size)

        self.ax2 = plt.subplot2grid((4, 1), (1, 0), rowspan=1, colspan=1)
        self.ax2.plot(self.x, self.data_detrended, plot_style_custom, ms=marker_size, linewidth=1)  # plot detrended data
        plt.ylabel('Detrended data', fontsize=font_size)

        self.ax3 = plt.subplot2grid((4, 1), (2, 0), rowspan=2, colspan=1, sharex=self.ax2, sharey=self.ax2)
        self.ax3.plot(self.x, self.data_after_filter, plot_style_custom, ms=marker_size, linewidth=1)  # plot filtered detrended data
        self.baselinePlotArtist = self.ax3.plot([self.x[0], self.x[-1]], [0, 0], 'k', linewidth=1)  # plot baseline
        plt.ylabel('Savitzky-Golay filter \n for detrended data', fontsize=font_size)
        self.ax3.set_xlim(0, self.x[-1])
        plt.xlabel('Time, sec')

        self.addmpl()

    def replot_graph(self, ):
        self.clear_data()
        self.rmmpl()
        self.data_preprocessing(self.y)
        self.baseline_calculation()
        self.plot_data()

    def coordinates_analysis(self, ):
        """
        Main function
        """
        coord_x, coord_y = zip(*self.coordinates)
        leftpb_x, leftpb_y = zip(*self.left_peak_border)
        rightpb_x, rightpb_y= zip(*self.right_peak_border)

        # absolute amplitude % and MAX
        relative_amplitude = []
        ampl_max = max(self.amplitudes)
        relative_amplitude[:] = [(i / ampl_max) for i in self.amplitudes]

        # create temporal Pandas DataFrame for sorting and calculation:
        temp_dataset = list(
            zip(coord_x, self.amplitudes, relative_amplitude, leftpb_x, leftpb_y, rightpb_x, rightpb_y, self.area))
        df = pd.DataFrame(data=temp_dataset,
                          columns=['Peak Time',
                                   'Amplitude',
                                   'Relative Amplitude \n (F/Fmax)',
                                   'Peak Start Time',
                                   'Peak Start Ordinate',
                                   'Peak Stop Time',
                                   'Peak Stop Ordinate',
                                   'Area'])

        # Sort data in DataFrame according to the time of peak appearance
        df_sorted = df.sort_values(['Peak Time'], ascending=True)
        df_sorted.index = range(0, len(df_sorted))  # reset indexing

        # calculate periods
        periods = []
        for i in range(1, len(df_sorted['Peak Time'])):
            periods.append(df_sorted.at[i, 'Peak Time'] - df_sorted.at[i - 1, 'Peak Time'])
        periods.insert(0, np.nan)  # add placeholder because len(periods)=len(peaks)-1

        # calculate frequencies based on calculated periods
        frequencies = []
        frequencies[:] = [(1 / i) for i in periods]

        # Analise peak start - stop time (left and right peak borders)
        peak_full_time = []
        for i in range(0, len(df_sorted['Peak Time']), 1):
            peak_full_time.append(df_sorted.at[i, 'Peak Stop Time'] - df_sorted.at[i, 'Peak Start Time'])
        peak_up_time = []
        for i in range(0, len(df_sorted['Peak Time']), 1):
            peak_up_time.append(df_sorted.at[i, 'Peak Time'] - df_sorted.at[i, 'Peak Start Time'])
        peak_down_time = []
        for i in range(0, len(df_sorted['Peak Time']), 1):
            peak_down_time.append(df_sorted.at[i, 'Peak Stop Time'] - df_sorted.at[i, 'Peak Time'])

        # Compute area under the peak using the composite trapezoidal rule.
        peak_area = []
        for i in range(0, len(df_sorted['Peak Time']), 1):
            peak_area.append(np.trapz(df_sorted.at[i, 'Area']))

        # Analise the peak decay area
        half_decay_time = []
        half_decay_amplitude = []
        for i in range(0, len(df_sorted['Peak Time']), 1):
            half_decay_ampl = df_sorted.at[i, 'Amplitude'] / 2  # calculate the half of the amplitude
            peak_index = self.x.index(df_sorted.at[i, 'Peak Time'])  # find index of the peak time
            stop_idx = self.x.index(df_sorted.at[i, 'Peak Stop Time'])  # find index of the right peak border
            data_decay_region = self.data_after_filter[peak_index:stop_idx]  # determine the amplitude region where to search for halftime decay index
            time_decay_region = self.x[peak_index:stop_idx]
            half_decay_idx = (np.abs(data_decay_region - half_decay_ampl)).argmin()  # find the closet value in data_decay_region that corresponds to the half amplitude

            half_decay_amplitude.append(half_decay_ampl)
            half_decay_time.append(time_decay_region[half_decay_idx] - df_sorted.at[i, 'Peak Time'])

        # Compute amplitude normalised to the baseline
        normalised_amplitude = []
        sg_window_frame = self.BoxSGwindowFrame.value()
        sg_polynom_degree = self.BoxSGpolynomDegree.value()
        orig_data_filtered = sig.savgol_filter(self.y, sg_window_frame, sg_polynom_degree)
        for i in range(0, len(df_sorted['Peak Time']), 1):
            start_idx = self.x.index(df_sorted.at[i, 'Peak Start Time'])
            F0 = orig_data_filtered[start_idx]
            amplitude_normed_computation = df_sorted.at[i, 'Amplitude'] / F0
            normalised_amplitude.append(amplitude_normed_computation)

        # normalised amplitude %
        relative_normalised_amplitude = []
        maxATB = max(normalised_amplitude)
        relative_normalised_amplitude[:] = [(i / maxATB) for i in normalised_amplitude]

        # normalised amplitude MAX
        normalised_amplitude_max = list(range(0, len(df_sorted['Peak Time']) - 1))
        normalised_amplitude_max[:] = [np.nan for _ in normalised_amplitude_max]
        normalised_amplitude_max.insert(0, maxATB)

        # add file name as first column
        file_name = list(range(0, len(df_sorted['Peak Time']) - 1))
        file_name[:] = [np.nan for _ in file_name]
        file_name.insert(0, self.graph_name)

        # add maximum amplitude
        absolute_amplitude_max = list(range(0, len(df_sorted['Peak Time']) - 1))
        absolute_amplitude_max[:] = [np.nan for _ in absolute_amplitude_max]
        absolute_amplitude_max.insert(0, max(df_sorted['Amplitude']))

        # peak sorting
        big_peaks_number = [p for p in self.amplitudes if (p > ampl_max * 0.66)]
        medium_peaks_number = [p for p in self.amplitudes if (p > ampl_max * 0.33 and p <= ampl_max * 0.66)]
        small_peaks_number = [p for p in self.amplitudes if (p > 0 and p <= ampl_max * 0.33)]

        big_peaks_frequency = list(range(0, len(df_sorted['Peak Time']) - 1))
        big_peaks_frequency[:] = [np.nan for _ in big_peaks_frequency]
        big_peaks_frequency.insert(0, len(big_peaks_number) / (self.x[-1] - self.x[0]))

        medium_peaks_frequency = list(range(0, len(df_sorted['Peak Time']) - 1))
        medium_peaks_frequency[:] = [np.nan for _ in medium_peaks_frequency]
        medium_peaks_frequency.insert(0, len(medium_peaks_number) / (self.x[-1] - self.x[0]))

        small_peaks_frequency = list(range(0, len(df_sorted['Peak Time']) - 1))
        small_peaks_frequency[:] = [np.nan for _ in small_peaks_frequency]
        small_peaks_frequency.insert(0, len(small_peaks_number) / (self.x[-1] - self.x[0]))

        final_dataset = list(zip(file_name,
                                df_sorted['Peak Time'],
                                df_sorted['Amplitude'],
                                df_sorted['Relative Amplitude \n (F/Fmax)'],
                                absolute_amplitude_max,
                                normalised_amplitude,
                                relative_normalised_amplitude,
                                normalised_amplitude_max,
                                periods,
                                frequencies,
                                half_decay_time,
                                half_decay_amplitude,
                                df_sorted['Peak Start Time'],
                                df_sorted['Peak Start Ordinate'],
                                df_sorted['Peak Stop Time'],
                                df_sorted['Peak Stop Ordinate'],
                                peak_up_time,
                                peak_down_time,
                                peak_full_time,
                                peak_area,
                                big_peaks_frequency,
                                medium_peaks_frequency,
                                small_peaks_frequency))

        final_dataframe = pd.DataFrame(data=final_dataset,
                                       columns=['File name',
                                                'Peak time',
                                                'Absolute amplitude',
                                                'Absolute amplitude (%)',
                                                'Absolute amplitude MAX',
                                                'Normalised amplitude',
                                                'Normalised amplitude (%)',
                                                'Normalised amplitude MAX',
                                                'Period',
                                                'Frequency',
                                                'Half-decay time',
                                                'Half-decay amplitude',
                                                'Start time',
                                                'Start ordinate',
                                                'Stop time',
                                                'Stop ordinate',
                                                'Ascending time',
                                                'Decay time',
                                                'Full peak time',
                                                'AUC',
                                                'Big peaks, Hz',
                                                'Mid peaks, Hz',
                                                'Small peaks, Hz'])

        # specify data for export acording to the settings tab in GUI
        # and append current analysed dataset to existing ones
        try:
            columns_to_delete_for_export = []
            if not self.chbxFileName.isChecked(): columns_to_delete_for_export.append('File name')
            if not self.chbxPeakTime.isChecked(): columns_to_delete_for_export.append('Peak time')
            if not self.chbxAmplAbs.isChecked(): columns_to_delete_for_export.append('Absolute amplitude')
            if not self.chbxAmplAbsRel.isChecked(): columns_to_delete_for_export.append('Absolute amplitude (%)')
            if not self.chbxAmplAbsMax.isChecked(): columns_to_delete_for_export.append('Absolute amplitude MAX')
            if not self.chbxAmplNorm.isChecked(): columns_to_delete_for_export.append('Normalised amplitude')
            if not self.chbxAmplNormRel.isChecked(): columns_to_delete_for_export.append('Normalised amplitude (%)')
            if not self.chbxAmplNormMax.isChecked(): columns_to_delete_for_export.append('Normalised amplitude MAX')
            if not self.chbxPeriod.isChecked(): columns_to_delete_for_export.append('Period')
            if not self.chbxFreq.isChecked(): columns_to_delete_for_export.append('Frequency')
            if not self.chbxHalfDecayTime.isChecked(): columns_to_delete_for_export.append('Half-decay time')
            if not self.chbxHalfDecayAmpl.isChecked(): columns_to_delete_for_export.append('Half-decay amplitude')
            if not self.chbxLeftBorderTime.isChecked(): columns_to_delete_for_export.append('Start time')
            if not self.chbxLeftBorder.isChecked(): columns_to_delete_for_export.append('Start ordinate')
            if not self.chbxRightBorderTime.isChecked(): columns_to_delete_for_export.append('Stop time')
            if not self.chbxRightBorder.isChecked(): columns_to_delete_for_export.append('Stop ordinate')
            if not self.chbxTimeToPeak.isChecked(): columns_to_delete_for_export.append('Ascending time')
            if not self.chbxDecayTime.isChecked(): columns_to_delete_for_export.append('Decay time')
            if not self.chbxFullPeakTime.isChecked(): columns_to_delete_for_export.append('Full peak time')
            if not self.chbxAUC.isChecked(): columns_to_delete_for_export.append('AUC')
            if not self.chbxSmallPeaks.isChecked(): columns_to_delete_for_export.append('Big peaks, Hz')
            if not self.chbxMidPeaks.isChecked(): columns_to_delete_for_export.append('Mid peaks, Hz')
            if not self.chbxBigPeaks.isChecked(): columns_to_delete_for_export.append('Small peaks, Hz')
            final_dataframe.drop(columns_to_delete_for_export, axis=1, inplace=True)

            self.multiple_data_sets = self.multiple_data_sets.append(final_dataframe)

            if self.chbxSaveFig.isChecked():
                os.makedirs('_Figures', exist_ok=True)
                dpi = self.BoxDPI.value()
                plt.savefig(os.path.join('_Figures', 'Fig_{figName}.png'.format(figName=self.graph_name)), dpi=dpi)

            del df
            del df_sorted
            del final_dataframe

            dialog = MessageBox.question(self, '', "Current dataset was analysed \n and added to previous ones (if exist). \n Would you like to load next file? ",
                                         QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if dialog == QtGui.QMessageBox.Yes:
                self.load_file()
            else:
                self.rmmpl()
                self.BtnSaveFullDataset.setStyleSheet("background-color: #7CF2BD")
                self.BtnLoadFile.setStyleSheet("background-color: #7CF2BD")

        except:
            message = MessageBox()
            message.about(self, 'Warning!', "Data were not added to existing dataset. \n Plese be sure that you did not change the output settings.")

    def save_data(self, ):
        try:
            file_name = QtGui.QFileDialog.getSaveFileName(self, 'Save file')
            writer = pd.ExcelWriter('{}.xlsx'.format(file_name))
            self.multiple_data_sets.to_excel(writer, index=True, sheet_name='Results')
            writer.sheets['Results'].set_zoom(80)
            writer.sheets['Results'].set_column('A:A', 5)
            writer.sheets['Results'].set_column('B:X', 23)
            writer.save()

            message = MessageBox()
            message.about(self, 'Data saved', "Data were saved!")
            self.multiple_data_sets = pd.DataFrame()
            self.BtnSaveFullDataset.setStyleSheet("background-color: #FAF6F2")
            self.BtnLoadFile.setStyleSheet("background-color: #7CF2BD")
        except:
            message = MessageBox()
            message.about(self, 'Warning!', "Data were not exported to Excel! \n Please try again.")

    def mpl_style_change(self, ):
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
        if self.multiple_data_sets.empty:
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
