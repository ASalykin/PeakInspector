from abc import ABCMeta, abstractmethod
import numpy as np
from PyQt5 import QtGui, QtCore
from OnMotion import OnMotion
from PyQt5.QtWidgets import QApplication


class OnClick:
    __metaclass__ = ABCMeta

    def on_click(self, event):
        modifier = QApplication.keyboardModifiers()
        if event.inaxes == self.ax3: # i.e. axes with detrended and filtered data
            if event.button == 1 and modifier == QtCore.Qt.NoModifier:
                # detect the closest time (x) index near the event
                xIdx = (np.abs(self.x-event.xdata)).argmin()

                # determine window frame (in amount of indexes) within which the peak should be found
                peakDetectionWindow = self.BoxPeakDetectionWindow.value()
                leftBorderX = xIdx - peakDetectionWindow
                rigthBorderX = xIdx + peakDetectionWindow

                # prevent situation if borders could be out of index
                if leftBorderX >= -1 and rigthBorderX < len(self.data_after_filter):
                    index_interval = self.data_after_filter[leftBorderX:rigthBorderX]
                elif leftBorderX <= -1 and rigthBorderX < len(self.data_after_filter):
                    index_interval = self.data_after_filter[0:rigthBorderX]
                elif leftBorderX >= 0 and rigthBorderX > len(self.data_after_filter):
                    index_interval = self.data_after_filter[leftBorderX:len(self.data_after_filter)]

                # find index and value of the peak within window frame
                yVal, yIdx = max((yVal, yIdx) for (yIdx, yVal) in enumerate(index_interval))

                # find index of the peak within full dataset
                self.peak_index = self.data_after_filter.index(yVal)

                # determine the amplitude region within which the peak borders would be automatically searched
                # lowerBaselineRegion equal 0 (see dataPreprocessing function in the main class)
                upperBaselineRegion = yVal*0.10

                self.left_intersection_index = next((h for h in range(self.peak_index, 1, -1) if
                                                     (self.data_after_filter[h] >= self.data_after_filter[h-1]) &
                                                     (self.data_after_filter[h] > self.data_after_filter[h+1]) &
                                                     (0 <= self.data_after_filter[h] <= upperBaselineRegion)), 0)

                self.right_intersection_index = next((k for k in range(self.peak_index, len(self.data_after_filter) - 1, 1) if
                                                      (self.data_after_filter[k] >= self.data_after_filter[k-1]) &
                                                      (self.data_after_filter[k] > self.data_after_filter[k+1]) &
                                                      (0 <= self.data_after_filter[k] <= upperBaselineRegion)), len(self.data_after_filter) - 1)

                # save peak data coordinated for next analysis
                self.coordinates.append((self.x[self.peak_index], self.data_after_filter[self.peak_index]))
                self.left_peak_border.append((self.x[self.left_intersection_index], self.data_after_filter[self.left_intersection_index]))
                self.right_peak_border.append((self.x[self.right_intersection_index], self.data_after_filter[self.right_intersection_index]))

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.left_intersection_index, self.right_intersection_index)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.data_after_filter[self.left_intersection_index:self.right_intersection_index], interpolated_line)]
                lns3_true_peak, = self.ax3.plot(self.x[self.left_intersection_index:self.right_intersection_index], peak_full_area, 'k--')

                # find the actual amplitude of the peak
                peak_amplitude = max(peak_full_area)
                self.amplitudes.append(peak_amplitude)
                self.amplitude_line_coordinates.append(([self.x[self.peak_index], self.x[self.peak_index]], [peak_amplitude, 0]))
                self.area.append(peak_full_area)

                # Visualize peak coordinates (and save artists)
                pts2, = self.ax2.plot(self.coordinates[-1][0], self.coordinates[-1][1], 'bo', ms=4) # peak max on 2nd graph
                pts3, = self.ax3.plot(self.coordinates[-1][0], self.coordinates[-1][1], 'bo', ms=8, picker=20) # peak max on 3rd graph
                lns3, = self.ax3.plot(self.amplitude_line_coordinates[-1][0], self.amplitude_line_coordinates[-1][1], 'k') # line from max to baseline

                # visualise the whole peak area which will be integrated
                pts3fill = self.ax3.fill_between(np.array(self.x[self.left_intersection_index:self.right_intersection_index]),
                                                 interpolated_line,
                                                 np.array(self.data_after_filter[self.left_intersection_index:self.right_intersection_index]),
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

                # xIdxArtist=[] # placeholder for artists' indexes among currently plotted artists

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
                self.left_intersection_index = xIdxLeft
                self.left_peak_border[-1] = [self.x[self.left_intersection_index], self.data_after_filter[self.left_intersection_index]]

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.left_intersection_index, self.right_intersection_index)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.data_after_filter[self.left_intersection_index:self.right_intersection_index], interpolated_line)]
                self.area[-1] = peak_full_area

                self.pickable_artists_lnsP_AX3[-1].remove()
                del self.pickable_artists_lnsP_AX3[-1]
                lns3_true_peak, = self.ax3.plot(self.x[self.left_intersection_index:self.right_intersection_index], peak_full_area, 'k--')
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
                pts3fill = self.ax3.fill_between(np.array(self.x[self.left_intersection_index:self.right_intersection_index]),
                                                 interpolated_line,
                                                 np.array(self.data_after_filter[self.left_intersection_index:self.right_intersection_index]),
                                                 facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3.append(pts3fill)

                self.fig.canvas.draw()

            elif event.button == 3 and modifier == QtCore.Qt.AltModifier:  #
                # detect the closest time (x) index near the event
                x_idx_right = (np.abs(self.x - event.xdata)).argmin()
                self.right_intersection_index = x_idx_right
                self.right_peak_border[-1] = [self.x[self.right_intersection_index], self.data_after_filter[self.right_intersection_index]]

                # calculate the line between left and right border of the peak
                interpolated_line = self.interpolation(self.left_peak_border[-1], self.right_peak_border[-1], self.left_intersection_index, self.right_intersection_index)

                # calculate the REAL peak with 0 baseline (substract the 'interpolated_line' from corresponding region in processed dataset)
                peak_full_area = []
                peak_full_area[:] = [(i - j) for i,j in zip(self.data_after_filter[self.left_intersection_index:self.right_intersection_index], interpolated_line)]
                self.area[-1] = peak_full_area

                self.pickable_artists_lnsP_AX3[-1].remove()
                del self.pickable_artists_lnsP_AX3[-1]
                lns3_true_peak, = self.ax3.plot(self.x[self.left_intersection_index:self.right_intersection_index], peak_full_area, 'k--')
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
                pts3fill = self.ax3.fill_between(np.array(self.x[self.left_intersection_index:self.right_intersection_index]),
                                                 interpolated_line,
                                                 np.array(self.data_after_filter[self.left_intersection_index:self.right_intersection_index]),
                                                 facecolor='green', interpolate=True, alpha=0.4)
                self.pickable_artists_fill_AX3.append(pts3fill)

                self.fig.canvas.draw()
