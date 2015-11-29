from abc import ABCMeta, abstractmethod
import numpy as np
from PyQt4 import QtGui, QtCore

from OnMotion import OnMotion


#%% main function executed on mouse click for peak detection
class OnClick:
    __metaclass__ = ABCMeta

    def __init__(self):
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

    def on_click(self, event):
        modifier = QtGui.QApplication.keyboardModifiers()
        if event.inaxes == self.ax3: # i.e. axes with detrended and filtered data
            if event.button == 1 and modifier == QtCore.Qt.NoModifier:
                # detect the closest time (x) index near the event
                xIdx = (np.abs(self.x-event.xdata)).argmin()

                # determine window frame (in amount of indexes) within which the peak should be found
                peakDetectionWindow = self.BoxPeakDetectionWindow.value()
                leftBorderX = xIdx - peakDetectionWindow
                rigthBorderX = xIdx + peakDetectionWindow

                # prevent situation if borders could be out of index
                if leftBorderX >= -1 and rigthBorderX < len(self.dataAfterFilter):
                    index_interval = self.dataAfterFilter[leftBorderX:rigthBorderX]
                elif leftBorderX <= -1 and rigthBorderX < len(self.dataAfterFilter):
                    index_interval = self.dataAfterFilter[0:rigthBorderX]
                elif leftBorderX >= 0 and rigthBorderX > len(self.dataAfterFilter):
                    index_interval = self.dataAfterFilter[leftBorderX:len(self.dataAfterFilter)]

                # find index and value of the peak within window frame
                yVal, yIdx = max((yVal, yIdx) for (yIdx, yVal) in enumerate(index_interval))

                # find index of the peak within full dataset
                self.peakIdx = self.dataAfterFilter.index(yVal)

                # determine the amplitude region within which the peak borders would be automatically searched
                # lowerBaselineRegion equal 0 (see dataPreprocessing function in the main class)
                upperBaselineRegion = yVal*0.10

                self.leftIntersectionPeakIdx = next((h for h in range(self.peakIdx, 1, -1) if
                    (self.dataAfterFilter[h] >= self.dataAfterFilter[h-1]) &
                    (self.dataAfterFilter[h] > self.dataAfterFilter[h+1]) &
                    (0 <= self.dataAfterFilter[h] <= upperBaselineRegion)), 0)

                self.rightIntersectionPeakIdx = next((k for k in range(self.peakIdx, len(self.dataAfterFilter)-1, 1) if
                    (self.dataAfterFilter[k] >= self.dataAfterFilter[k-1]) &
                    (self.dataAfterFilter[k] > self.dataAfterFilter[k+1]) &
                    (0 <= self.dataAfterFilter[k] <= upperBaselineRegion)), len(self.dataAfterFilter)-1)

                # save peak data coordinated for next analysis
                self.coordinates.append((self.x[self.peakIdx], self.dataAfterFilter[self.peakIdx]))
                self.left_peak_border.append((self.x[self.leftIntersectionPeakIdx], self.dataAfterFilter[self.leftIntersectionPeakIdx]))
                self.right_peak_border.append((self.x[self.rightIntersectionPeakIdx], self.dataAfterFilter[self.rightIntersectionPeakIdx]))

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.leftIntersectionPeakIdx, self.rightIntersectionPeakIdx)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], interpolated_line)]
                lns3_true_peak, = self.ax3.plot(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], peak_full_area, 'k--')

                # find the actual amplitude of the peak
                peak_amplitude = max(peak_full_area)
                self.amplitudes.append(peak_amplitude)
                self.amplitude_line_coordinates.append(([self.x[self.peakIdx], self.x[self.peakIdx]], [peak_amplitude, 0]))
                self.area.append(peak_full_area)

                # Visualize peak coordinates (and save artists)
                pts2, = self.ax2.plot(self.coordinates[-1][0], self.coordinates[-1][1], 'bo', ms=4) # peak max on 2nd graph
                pts3, = self.ax3.plot(self.coordinates[-1][0], self.coordinates[-1][1], 'bo', ms=8, picker=20) # peak max on 3rd graph
                lns3, = self.ax3.plot(self.amplitude_line_coordinates[-1][0], self.amplitude_line_coordinates[-1][1], 'k') # line from max to baseline

                # visualise the whole peak area which will be integrated
                pts3fill = self.ax3.fill_between(np.array(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 interpolated_line,
                                                 np.array(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 facecolor='green', interpolate=True, alpha=0.4)

                # Visualise left and right peak border by dots (and save artists)
                pts3lb, = self.ax3.plot(self.left_peak_border[-1][0], self.left_peak_border[-1][1], 'ko', ms=4, picker=15)
                pts3rb, = self.ax3.plot(self.right_peak_border[-1][0], self.right_peak_border[-1][1], 'ko', ms=4, picker=15)

                # initiate/update fig instance
                self.fig.canvas.draw()

                # appead corresponding artists for further manipulation (to remove and move)
                self.pickable_artists_pts_AX2.append(pts2)
                self.pickable_artists_pts_AX3.append(pts3)
                self.pickable_artists_lns_AX3.append(lns3)
                self.pickable_artists_fill_AX3.append(pts3fill)
                self.pickable_artists_plb_AX3.append(pts3lb)
                self.pickable_artists_prb_AX3.append(pts3rb)
                self.pickable_artists_lnsP_AX3.append(lns3_true_peak)

            elif (event.button == 1 and modifier == QtCore.Qt.ControlModifier) or event.button == 2: # remove artists under the cursor
                removePtsAx3 = [artist for artist in self.pickable_artists_pts_AX3 if artist.contains(event)[0]]

                xIdxArtist=[] # placeholder for artists' indexes among currently plotted artists

                for artist in removePtsAx3:
                    removedArtistXdata = artist.get_xdata()
                    xIdxArtist = [i for i, eachTuple in enumerate(self.coordinates) if eachTuple[0] == removedArtistXdata]
                    indexA = xIdxArtist[0]

                    artist.remove()
                    self.pickable_artists_pts_AX2[indexA].remove()
                    self.pickable_artists_lns_AX3[indexA].remove()
                    self.pickable_artists_fill_AX3[indexA].remove()
                    self.pickable_artists_plb_AX3[indexA].remove()
                    self.pickable_artists_prb_AX3[indexA].remove()
                    self.pickable_artists_lnsP_AX3[indexA].remove()

                    del self.coordinates[indexA]
                    del self.area[indexA]
                    del self.amplitudes[indexA]
                    del self.amplitude_line_coordinates[indexA]
                    del self.left_peak_border[indexA]
                    del self.right_peak_border[indexA]
                    del self.pickable_artists_pts_AX2[indexA]
                    del self.pickable_artists_pts_AX3[indexA]
                    del self.pickable_artists_lns_AX3[indexA]
                    del self.pickable_artists_fill_AX3[indexA]
                    del self.pickable_artists_plb_AX3[indexA]
                    del self.pickable_artists_prb_AX3[indexA]
                    del self.pickable_artists_lnsP_AX3[indexA]


                # print(self.coords)
                self.fig.canvas.draw()

            elif event.button == 3 and modifier == QtCore.Qt.NoModifier: # move artist under the cursor
                OnMotion.on_motion(self, event)

            elif event.button == 3 and modifier == QtCore.Qt.ControlModifier: #
                # detect the closest time (x) index near the event
                xIdxLeft = (np.abs(self.x - event.xdata)).argmin()
                self.leftIntersectionPeakIdx = xIdxLeft
                self.left_peak_border[-1] = [self.x[self.leftIntersectionPeakIdx], self.dataAfterFilter[self.leftIntersectionPeakIdx]]

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.leftIntersectionPeakIdx, self.rightIntersectionPeakIdx)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], interpolated_line)]
                self.area[-1] = peak_full_area

                self.pickable_artists_lnsP_AX3[-1].remove()
                del self.pickable_artists_lnsP_AX3[-1]
                lns3_true_peak, = self.ax3.plot(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], peak_full_area, 'k--')
                self.pickable_artists_lnsP_AX3.append(lns3_true_peak)

                # find the actual amplitude of the peak
                peak_amplitude = max(peak_full_area)
                self.amplitudes[-1] = peak_amplitude

                self.pickable_artists_plb_AX3[-1].remove()
                del self.pickable_artists_plb_AX3[-1]
                pts3lb_new, = self.ax3.plot(self.left_peak_border[-1][0], self.left_peak_border[-1][1], 'ko', ms=4, picker=15)
                self.pickable_artists_plb_AX3.append(pts3lb_new)

                self.amplitude_line_coordinates = list(self.amplitude_line_coordinates)
                self.amplitude_line_coordinates[-1][1][0]=peak_amplitude

                self.pickable_artists_lns_AX3[-1].remove()
                del self.pickable_artists_lns_AX3[-1]
                lns3_new, = self.ax3.plot(self.amplitude_line_coordinates[-1][0], self.amplitude_line_coordinates[-1][1], 'k') # line from max to baseline
                self.pickable_artists_lns_AX3.append(lns3_new)

                self.pickable_artists_fill_AX3[-1].remove()
                del self.pickable_artists_fill_AX3[-1]
                pts3fill = self.ax3.fill_between(np.array(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 interpolated_line,
                                                 np.array(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3.append(pts3fill)

                self.fig.canvas.draw()

            elif event.button == 3 and modifier == QtCore.Qt.AltModifier:  #
                # detect the closest time (x) index near the event
                x_idx_right = (np.abs(self.x - event.xdata)).argmin()
                self.rightIntersectionPeakIdx = x_idx_right
                self.right_peak_border[-1] = [self.x[self.rightIntersectionPeakIdx], self.dataAfterFilter[self.rightIntersectionPeakIdx]]

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.leftIntersectionPeakIdx, self.rightIntersectionPeakIdx)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], interpolated_line)]
                self.area[-1] = peak_full_area

                self.pickable_artists_lnsP_AX3[-1].remove()
                del self.pickable_artists_lnsP_AX3[-1]
                lns3_true_peak, = self.ax3.plot(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx], peak_full_area, 'k--')
                self.pickable_artists_lnsP_AX3.append(lns3_true_peak)

                # find the actual amplitude of the peak
                peak_amplitude = max(peak_full_area)
                self.amplitudes[-1] = peak_amplitude

                self.pickable_artists_prb_AX3[-1].remove()
                del self.pickable_artists_prb_AX3[-1]
                pts3rb_new, = self.ax3.plot(self.right_peak_border[-1][0], self.right_peak_border[-1][1], 'ko', ms=4, picker=15)
                self.pickable_artists_prb_AX3.append(pts3rb_new)

                self.amplitude_line_coordinates=list(self.amplitude_line_coordinates)
                self.amplitude_line_coordinates[-1][1][0]=peak_amplitude

                self.pickable_artists_lns_AX3[-1].remove()
                del self.pickable_artists_lns_AX3[-1]
                lns3_new, = self.ax3.plot(self.amplitude_line_coordinates[-1][0], self.amplitude_line_coordinates[-1][1], 'k') # line from max to baseline
                self.pickable_artists_lns_AX3.append(lns3_new)

                self.pickable_artists_fill_AX3[-1].remove()
                del self.pickable_artists_fill_AX3[-1]
                pts3fill = self.ax3.fill_between(np.array(self.x[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 interpolated_line,
                                                 np.array(self.dataAfterFilter[self.leftIntersectionPeakIdx:self.rightIntersectionPeakIdx]),
                                                 facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3.append(pts3fill)

                self.fig.canvas.draw()