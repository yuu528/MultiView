from pyqtgraph.Qt import QtCore

class GetSamplesWorker(QtCore.QThread):
    plot = QtCore.pyqtSignal(tuple, tuple, int, bool) # ch1 data, ch2 data, samplecount, triggered

    def __init__(self, m2kain, m2katrig, normal, samplecount, interval):
        QtCore.QThread.__init__(self, objectName='WorkerThread')
        self.m2kain = m2kain
        self.m2katrig = m2katrig
        self.normal = normal
        self.samplecount = samplecount
        self.interval = interval
        self.loop = True

    def run(self):
        while True:
            if self.loop:
                self.do_loop()
                self.msleep(self.interval)
            else:
                break

    def do_loop(self):
        try:
            data = self.m2kain.getSamples(self.samplecount)
            self.plot.emit(data[0], data[1], self.samplecount, True)
        except:
            if not self.normal:
                self.m2kain.cancelAcquisition()
                self.m2katrig.setAnalogMode(0, 0)
                self.m2katrig.setAnalogMode(1, 0)
                delay = self.m2katrig.getAnalogDelay()
                self.m2katrig.setAnalogDelay(0)
                self.m2kain.startAcquisition(self.samplecount)
                try:
                    self.msleep(self.interval)
                    data = self.m2kain.getSamples(self.samplecount)
                    self.plot.emit(data[0], data[1], self.samplecount, False)
                except:
                    self.plot.emit((), (), 0, False)
                    pass

                self.m2katrig.setAnalogDelay(delay)
                self.m2katrig.setAnalogMode(0, 1)
                self.m2katrig.setAnalogMode(1, 1)
            else:
                self.plot.emit((), (), 0, False)

    def set_loop(self, loop):
        self.loop = loop

    def set_normal(self, normal):
        self.normal = normal

    def set_samplecount(self, samplecount):
        self.samplecount = samplecount

    def set_interval(self, interval):
        self.interval = interval
