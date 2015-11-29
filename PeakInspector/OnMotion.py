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
            try:  # to determine whether user pointed on the left peak border
                if 'self.leftBorder' in globals():
                    self.leftBorderNew = [artist for artist in self.pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                    if self.leftBorderNew == self.leftBorder:
                        self.leftBorderXdata = self.leftBorder[0].get_xdata() # initial position of the left dot
                    else:
                        self.leftBorder = self.leftBorderNew
                        self.leftBorderXdata = self.leftBorder[0].get_xdata()
                        self.leftBorderIndex = [i for i, eachTuple in enumerate(self.left_peak_border) if eachTuple[0] == self.leftBorderXdata] # index of the left dot
                else:
                    self.leftBorder = [artist for artist in self.pickable_artists_plb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot...
                    self.leftBorderXdata = self.leftBorder[0].get_xdata() # initial position of the left dot
                    self.leftBorderIndex = [i for i, eachTuple in enumerate(self.left_peak_border) if eachTuple[0] == self.leftBorderXdata] # index of the left dot
            except:
                pass

            try:  # to determine whether user pointed on the right peak border
                if 'self.rightBorder' in globals():
                    self.rightBorderNew = [artist for artist in self.pickable_artists_prb_AX3 if artist.contains(event)[0]] # return the artist of the left black dot (under mouse)
                    if self.rightBorderNew == self.rightBorder:
                        self.rightBorderXdata = self.rightBorder[0].get_xdata() #
                    else:
                        self.rightBorder = self.rightBorderNew
                        self.rightBorderXdata = self.rightBorder[0].get_xdata()
                        self.rightBorderIndex = [i for i, eachTuple in enumerate(self.right_peak_border) if eachTuple[0] == self.rightBorderXdata] #
                else:
                    self.rightBorder = [artist for artist in self.pickable_artists_prb_AX3 if artist.contains(event)[0]] #
                    self.rightBorderXdata = self.rightBorder[0].get_xdata() #
                    self.rightBorderIndex = [i for i, eachTuple in enumerate(self.right_peak_border) if eachTuple[0] == self.rightBorderXdata] #
            except:
                pass

            if len(self.leftBorder) == 1 and len(self.rightBorder) >= 0:
                idxL = (np.abs(self.x-event.xdata)).argmin()
                self.leftBorder[0].set_xdata(self.x[idxL])
                self.leftBorder[0].set_ydata(self.dataAfterFilter[idxL])

                indexA = self.leftBorderIndex[0]
                idxR = self.x.index(self.right_peak_border[indexA][0])

                self.left_peak_border = list(self.left_peak_border)
                self.left_peak_border = self.left_peak_border[:indexA] + [(self.x[idxL], self.dataAfterFilter[idxL])] + self.left_peak_border[indexA+1:] #

                interpolated_line = self.interpolation(self.left_peak_border[indexA], self.right_peak_border[indexA], idxL, idxR)

                # calculation of peak amplitude
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.dataAfterFilter[idxL:idxR], interpolated_line)]
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
                pts3fill = self.ax3.fill_between(np.array(self.x[idxL:idxR]), \
                                interpolated_line, \
                                np.array(self.dataAfterFilter[idxL:idxR]), \
                                facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3 = self.pickable_artists_fill_AX3[:indexA] + [pts3fill] + self.pickable_artists_fill_AX3[indexA+1:] #

                self.fig.canvas.draw()

            elif (len(self.leftBorder) >= 0 and len(self.rightBorder)==1):
                idxR = (np.abs(self.x-event.xdata)).argmin()
                self.rightBorder[0].set_xdata(self.x[idxR])
                self.rightBorder[0].set_ydata(self.dataAfterFilter[idxR])

                indexA = self.rightBorderIndex[0]
                idxL = self.x.index(self.left_peak_border[indexA][0])

                self.right_peak_border = list(self.right_peak_border)
                self.right_peak_border = self.right_peak_border[:indexA] + [(self.x[idxR], self.dataAfterFilter[idxR])] + self.right_peak_border[indexA+1:] #

                interpolated_line = self.interpolation(self.left_peak_border[indexA], self.right_peak_border[indexA], idxL, idxR)

                # calculation of peak amplitude
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.dataAfterFilter[idxL:idxR], interpolated_line)]
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
                pts3fill = self.ax3.fill_between(np.array(self.x[idxL:idxR]), \
                                interpolated_line, \
                                np.array(self.dataAfterFilter[idxL:idxR]), \
                                facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3 = self.pickable_artists_fill_AX3[:indexA] + [pts3fill] + self.pickable_artists_fill_AX3[indexA+1:] #

                self.fig.canvas.draw()

            else:
                pass
