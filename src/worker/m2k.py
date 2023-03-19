import libm2k
from pyqtgraph.Qt import QtCore

class M2kWorker(QtCore.QThread):
    acquired = QtCore.pyqtSignal(tuple, bool) # input data, triggered

    def __init__(self, interval, count_in, rate_in=100e6, range_in=[0, 0], offset_in=[0, 0],
        timeout_in=0, src_trig=0, mode_trig=0, delay_trig=0, cond_trig=[0, 0],
        level_trig=[0, 0], hyst_trig=[0, 0], holdoff_trig=0):

        QtCore.QThread.__init__(self, objectName='M2kWorker')

        self.loop = True
        self.ready = False
        self.enable_in = False

        self.interval = interval
        self.count_in = count_in
        self.rate_in = rate_in
        self.range_in = range_in
        self.offset_in = offset_in
        self.timeout_in = timeout_in # 0=inf
        self.src_trig = src_trig
        self.mode_trig = mode_trig # 0=auto, 1=normal
        self.delay_trig = delay_trig
        self.cond_trig = cond_trig # 0=rising edge, 1=falling
        self.level_trig = level_trig
        self.hyst_trig = hyst_trig
        self.holdoff_trig = holdoff_trig

        self.change_count_in = False
        self.change_range_in = [False, False]
        self.change_offset_in = [False, False]
        self.change_timeout_in = False
        self.change_src_trig = False
        self.change_delay_trig = False
        self.change_cond_trig = [False, False]
        self.change_level_trig = [False, False]
        self.change_hyst_trig = [False, False]

        self.volts_raw_in = [[0, 0], [0, 0]]

        self.m2kdev = libm2k.m2kOpen()
        if not self.m2kdev == None:
            self.m2kain = self.m2kdev.getAnalogIn()
            self.m2kaout = self.m2kdev.getAnalogOut()
            self.m2ktrig = self.m2kain.getTrigger()

            self.m2kain.reset()
            self.m2kaout.reset()
            self.m2kdev.calibrateADC()
            self.m2kdev.calibrateDAC()

            self.m2kdev.setTimeout(self.timeout_in)

            self.m2kain.enableChannel(0, True)
            self.m2kain.enableChannel(1, True)

            self.m2kain.setSampleRate(self.rate_in)
            self.m2kain.setRange(0, self.range_in[0])
            self.m2kain.setRange(1, self.range_in[1])
            self.m2kain.setVerticalOffset(0, self.offset_in[0])
            self.m2kain.setVerticalOffset(1, self.offset_in[1])

            self.m2ktrig.setAnalogSource(self.src_trig)
            self.m2ktrig.setAnalogMode(0, 1)
            self.m2ktrig.setAnalogMode(1, 1)
            self.m2ktrig.setAnalogDelay(self.delay_trig)
            self.m2ktrig.setAnalogCondition(0, self.cond_trig[0])
            self.m2ktrig.setAnalogCondition(1, self.cond_trig[1])
            self.m2ktrig.setAnalogLevel(0, self.level_trig[0])
            self.m2ktrig.setAnalogLevel(1, self.level_trig[1])

            self.calc_volts_raw_in(0)
            self.calc_volts_raw_in(1)

            self.m2kain.startAcquisition(self.count_in)
            self.ready = True

    def run(self):
        while True:
            self.msleep(self.interval)
            if self.loop and self.ready:
                # change parameters
                for i, change in enumerate(self.change_range_in):
                    if change:
                        self.m2kain.setRange(i, self.range_in[i])
                        self.change_range_in[i] = False
                        self.calc_volts_raw_in(i)

                for i, change in enumerate(self.change_offset_in):
                    if change:
                        self.m2kain.setVerticalOffset(i, self.offset_in[i])
                        self.change_offset_in[i] = False
                        self.calc_volts_raw_in(i)

                for i, change in enumerate(self.change_cond_trig):
                    if change:
                        self.m2ktrig.setAnalogCondition(i, self.cond_trig[i])
                        self.change_cond_trig[i] = False

                for i, change in enumerate(self.change_level_trig):
                    if change:
                        self.m2ktrig.setAnalogLevel(i, self.level_trig[i])
                        self.change_level_trig[i] = False

                for i, change in enumerate(self.change_hyst_trig):
                    if change:
                        self.m2ktrig.setAnalogHysteresis(i, self.hyst_trig[i])
                        self.change_hyst_trig[i] = False

                if self.change_count_in:
                    self.m2kain.cancelAcquisition()
                    self.m2kain.stopAcquisition()
                    self.m2kain.startAcquisition(self.count_in)
                    self.change_count_in = False

                if self.change_timeout_in:
                    self.m2kdev.setTimeout(self.timeout_in)
                    self.change_timeout_in = False

                if self.change_src_trig:
                    self.m2ktrig.setAnalogSource(self.src_trig)
                    self.change_src_trig = False

                if self.change_delay_trig:
                    self.m2ktrig.setAnalogDelay(self.delay_trig)
                    self.change_delay_trig = False

                # analog input
                if self.enable_in:
                    self.msleep(self.holdoff_trig)
                    try:
                        data = self.m2kain.getSamples(self.count_in)
                        self.acquired.emit(data, True)
                    except Exception as e:
                        if self.mode_trig == 0:
                            self.m2kain.cancelAcquisition()
                            self.m2kain.startAcquisition(self.count_in)
                            self.msleep(self.interval)
                            self.m2ktrig.setAnalogMode(0, 0) # disable triggering
                            self.m2ktrig.setAnalogMode(1, 0) # disable triggering
                            try:
                                data = self.m2kain.getSamples(self.count_in)
                                self.acquired.emit(data, False)
                                self.m2ktrig.setAnalogMode(0, 1)
                                self.m2ktrig.setAnalogMode(1, 1)
                            except Exception as e:
                                pass

    def calc_volts_raw_in(self, ch):
        if self.range_in[ch] == 0:
            self.volts_raw_in[ch] = [
                self.m2kain.convertVoltsToRaw(ch, -25), self.m2kain.convertVoltsToRaw(ch, 25)
            ]
        else:
            self.volts_raw_in[ch] = [
                self.m2kain.convertVoltsToRaw(ch, -2.5), self.m2kain.convertVoltsToRaw(ch, 2.5)
            ]

    def set_loop(self, loop):
        self.loop = loop

    def set_interval(self, interval):
        self.interval = interval

    def set_enable_in(self, enable_in):
        self.enable_in = enable_in

    def set_count_in(self, count_in):
        self.count_in = count_in
        self.change_count_in = True

    def set_rate_in(self, rate_in):
        self.rate_in = rate_in

    def set_range_in(self, ch, range_in):
        self.range_in[ch] = range_in
        self.change_range_in[ch] = True

    def set_offset_in(self, ch, offset_in):
        self.offset_in[ch] = offset_in
        self.change_offset_in[ch] = True

    def set_timeout_in(self, timeout_in):
        self.timeout_in = timeout_in
        self.change_timeout_in = True

    def set_src_trig(self, src_trig):
        self.src_trig = src_trig
        self.change_src_trig = True

    def set_mode_trig(self, mode_trig):
        self.mode_trig = mode_trig

    def set_delay_trig(self, delay_trig):
        self.delay_trig = delay_trig
        self.change_delay_trig = True

    def set_cond_trig(self, ch, cond_trig):
        self.cond_trig[ch] = cond_trig
        self.change_cond_trig[ch] = True

    def set_level_trig(self, ch, level_trig):
        self.level_trig[ch] = level_trig
        self.change_level_trig[ch] = True

    def set_hyst_trig(self, ch, hyst_trig):
        self.hyst_trig[ch] = hyst_trig
        self.change_hyst_trig[ch] = True

    def set_holdoff_trig(self, holdoff_trig):
        self.holdoff_trig = holdoff_trig
