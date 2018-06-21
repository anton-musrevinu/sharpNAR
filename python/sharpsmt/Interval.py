import math

class Interval(object):
        def __init__(self,low = -math.inf, high = math.inf):
            self.setInterval(low, high)

        def asFloat(self):
            return self._interval

        def asList(self):
            return [self.min, self.max]

        def isNeg(self):
            return self._interval < 0

        def setInterval(self,low,high):
            self.min = low
            self.max = high
            self._setInterval()

        def _setInterval(self):
            if self.min > self.max:
                self._interval = -1
            else:
                self._interval = self.max - self.min


        def combine(self,other):
            if self.isNeg() or other.isNeg() or not self.intersect(other):
                self._interval = -1
                return

            self.min = (max(self.min,other.min))
            self.max = (min(self.max,other.max))
            self._setInterval()

        def intersect(self,other):
            if self.isNeg() or other.isNeg():
                return False
            if self.min < other.min and self.max >= other.min:
                return True
            elif self.min >= other.min and other.max > self.min:
                return True
            else:
                return False

        def __str__(self):
            if self.isNeg():
                return '[]'
            else:
                return '[{},{}]'.format(self.min,self.max)

        def __eq__(self,other):
            if self.min == other.min and self.max == other.max:
                return True
            else:
                return False