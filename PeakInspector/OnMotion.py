from abc import ABCMeta, abstractmethod
from PyQt4 import QtGui, QtCore
import numpy as np


class OnMotion:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    def on_motion(self, event):
        modifier = QtGui.QApplication.keyboardModifiers()
        if event.inaxes == self.ax3 and event.button == 3 and modifier == QtCore.Qt.NoModifier:
            try: # to determine whether user pointed on the left peak border
                if len(self.left_border) > 0:
                    self.left_border_new = [artist for artist in self.pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                    if self.left_border_new == self.left_border:
                        self.left_border_x_data = self.left_border[0].get_xdata() # initial position of the left dot
                    else:
                        self.left_border = self.left_border_new
                        self.left_border_x_data = self.left_border[0].get_xdata()
                        self.left_border_index = [i for i, eachTuple in enumerate(self.left_peak_border) if eachTuple[0] == self.left_border_x_data] # index of the left dot
                else:
                    self.left_border = [artist for artist in self.pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                    self.left_border_x_data = self.left_border[0].get_xdata() # initial position of the left dot
                    self.left_border_index = [i for i, eachTuple in enumerate(self.left_peak_border) if eachTuple[0] == self.left_border_x_data] # index of the left dot
            except:
                print("left")

            try:# to determine whether user pointed on the right peak border
                if len(self.right_border) > 0:
                    self.right_border_new = [artist for artist in self.pickable_artists_prb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot (under mouse)
                    if self.right_border_new == self.right_border:
                        self.right_border_x_data = self.right_border[0].get_xdata() #
                    else:
                        self.right_border = self.right_border_new
                        self.right_border_x_data = self.right_border[0].get_xdata()
                        self.right_border_index = [i for i, eachTuple in enumerate(self.right_peak_border) if eachTuple[0] == self.right_border_x_data] #
                else:
                    self.right_border = [artist for artist in self.pickable_artists_prb_AX3 if artist.contains(event)[0]]
                    self.right_border_x_data = self.right_border[0].get_xdata() #
                    self.right_border_index = [i for i, eachTuple in enumerate(self.right_peak_border) if eachTuple[0] == self.right_border_x_data] #
            except:
                print("right")

            if len(self.left_border) == 1 and len(self.right_border) >= 0:
                idxL = (np.abs(self.x-event.xdata)).argmin()
                self.left_border[0].set_xdata(self.x[idxL])
                self.left_border[0].set_ydata(self.data_after_filter[idxL])

                indexA = self.left_border_index[0]
                idxR = self.x.index(self.right_peak_border[indexA][0])

                self.left_peak_border = list(self.left_peak_border)
                self.left_peak_border = self.left_peak_border[:indexA] + [(self.x[idxL], self.data_after_filter[idxL])] + self.left_peak_border[indexA + 1:] #

                interpolated_line = self.interpolation(self.left_peak_border[indexA], self.right_peak_border[indexA], idxL, idxR)

                # calculation of peak amplitude
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.data_after_filter[idxL:idxR], interpolated_line)]
                self.area[indexA] = peak_full_area

                self.pickable_artists_lnsP_AX3[indexA].remove()
                lns3TruePeak, = self.ax3.plot(self.x[idxL:idxR], peak_full_area, 'k--')
                self.pickable_artists_lnsP_AX3 = self.pickable_artists_lnsP_AX3[:indexA] + [lns3TruePeak] + self.pickable_artists_lnsP_AX3[indexA+1:]

                peakAmplitude = max(peak_full_area)
                self.amplitudes = self.amplitudes[:indexA] + [peakAmplitude] + self.amplitudes[indexA+1:]

                self.amplitude_line_coordinates = list(self.amplitude_line_coordinates)
                self.amplitude_line_coordinates[indexA][1][0] = peakAmplitude

                self.pickable_artists_lns_AX3[indexA].remove()
                lns3, = self.ax3.plot(self.amplitude_line_coordinates[indexA][0], self.amplitude_line_coordinates[indexA][1], 'k') # line from max to baseline
                self.pickable_artists_lns_AX3 = self.pickable_artists_lns_AX3[:indexA] + [lns3] + self.pickable_artists_lns_AX3[indexA+1:]

                self.pickable_artists_fill_AX3[indexA].remove()
                pts3fill = self.ax3.fill_between(np.array(self.x[idxL:idxR]),
                                interpolated_line,
                                np.array(self.data_after_filter[idxL:idxR]),
                                facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3 = self.pickable_artists_fill_AX3[:indexA] + [pts3fill] + self.pickable_artists_fill_AX3[indexA+1:] #

            elif len(self.left_border) >= 0 and len(self.right_border) == 1:
                idxR = (np.abs(self.x-event.xdata)).argmin()
                self.right_border[0].set_xdata(self.x[idxR])
                self.right_border[0].set_ydata(self.data_after_filter[idxR])

                indexA = self.right_border_index[0]
                idxL = self.x.index(self.left_peak_border[indexA][0])

                self.right_peak_border = list(self.right_peak_border)
                self.right_peak_border = self.right_peak_border[:indexA] + [(self.x[idxR], self.data_after_filter[idxR])] + self.right_peak_border[indexA + 1:] #

                interpolated_line = self.interpolation(self.left_peak_border[indexA], self.right_peak_border[indexA], idxL, idxR)

                # calculation of peak amplitude
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.data_after_filter[idxL:idxR], interpolated_line)]
                self.area[indexA] = peak_full_area

                self.pickable_artists_lnsP_AX3[indexA].remove()
                lns3TruePeak, = self.ax3.plot(self.x[idxL:idxR], peak_full_area, 'k--')
                self.pickable_artists_lnsP_AX3 = self.pickable_artists_lnsP_AX3[:indexA] + [lns3TruePeak] + self.pickable_artists_lnsP_AX3[indexA+1:]

                peakAmplitude = max(peak_full_area)
                self.amplitudes = self.amplitudes[:indexA] + [peakAmplitude] + self.amplitudes[indexA+1:]

                self.amplitude_line_coordinates = list(self.amplitude_line_coordinates)
                self.amplitude_line_coordinates[indexA][1][0] = peakAmplitude

                self.pickable_artists_lns_AX3[indexA].remove()
                lns3, = self.ax3.plot(self.amplitude_line_coordinates[indexA][0], self.amplitude_line_coordinates[indexA][1], 'k') # line from max to baseline
                self.pickable_artists_lns_AX3 = self.pickable_artists_lns_AX3[:indexA] + [lns3] + self.pickable_artists_lns_AX3[indexA+1:]

                self.pickable_artists_fill_AX3[indexA].remove()
                pts3fill = self.ax3.fill_between(np.array(self.x[idxL:idxR]),
                                interpolated_line,
                                np.array(self.data_after_filter[idxL:idxR]),
                                facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3 = self.pickable_artists_fill_AX3[:indexA] + [pts3fill] + self.pickable_artists_fill_AX3[indexA+1:]  #

            else: # placeholder for logic in next versions
                pass

            self.fig.canvas.draw()
