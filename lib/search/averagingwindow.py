"""Class for keeping an average of a moving window.
"""
from collections import deque

class AveragingWindow(object):
    """Keeps the average of a maximum number of data points.
    """

    def __init__(self, window_size):
        """Sets the maximum number of data points handled.
        """
        self.window_size = window_size
        self._points = deque()

        self.sum = 0
        self.count = 0.0
        self._average = None

    @property
    def average(self):
        """Average of the currently stored data points, or None for no points.
        """
        return self._average

    def add_point(self, value):
        """Adds a data point to the moving average.
        """
        # Adds the new value and stores it on the queue
        self.sum += value
        self._points.append(value)

        if self.count < self.window_size:
            # Increments the count while adding new points
            self.count += 1
        if self.count >= self.window_size:
            # Substitutes a point when full
            removed_value = self._points.popleft()
            self.sum -= removed_value

        # Updates the average
        self._average = self.sum / self.count
