import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from utils import Utils
from langs import Langs

class ScopeWidget():
    def __init__(self, master, this, panel, lang, m2k):
        super().__init__()
        self.panel = panel
        self.lang = lang
        self.m2k = m2k

        # const
        self.xdiv = 10
        self.ydiv = 8
        self.samplerate = self.m2k.rate_in
        self.langs = Langs(lang).get_all()
        self.MENU_NONE = 0
        self.MENU_CH1 = 1
        self.MENU_CH2 = 2
        self.MENU_TRIG = 3
        self.FINDER_PLOT_COLOR = 'yellow'
        self.TRIG_TICK_COLOR = '#01a000'
        self.HPOS_TICK_COLOR = 'red'
        self.TICK_SIZE = 10

        # setting values
        self.vdivs = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10]
        self.tdivs = [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1]
        self.vdiv_index = [0, 0]
        self.tdiv_index = 0
        self.input_range = [0, 0]
        self.offset = [0, 0]
        self.offset_count = [0, 0]
        self.hpos = 0
        self.hpos_count = 0
        self.trig_level = 0
        self.trig_level_count = 0
        self.trig_hyst = 0.6
        self.trig_hyst_count = 6
        self.trig_mode = 0
        self.trig_cond = 0
        self.trig_src = 0
        self.holdoff = 0
        self.holdoff_count = 0
        self.enable_ch = [True, True]
        self.running = False
        self.colors = ['orange', 'blue']
        self.now_menu = self.MENU_NONE

        self.stopped_hpos = 0
        self.triggered_count = 0
        self.single_waiting = False

        # get widgets
        self.scope_graph = this.findChild(pg.GraphicsLayoutWidget, 'scope_graph')
        self.scopebar1_label_trig_level = this.findChild(QtWidgets.QLabel, 'scopebar1_label_trig_level')
        self.scopebar1_label_holdoff = this.findChild(QtWidgets.QLabel, 'scopebar1_label_holdoff')
        self.scopebar1_label_trig_hyst = this.findChild(QtWidgets.QLabel, 'scopebar1_label_trig_hyst')
        self.scopebar1_label_trig_status = this.findChild(QtWidgets.QLabel, 'scopebar1_label_trig_status')
        self.scopebar1_label_tdiv = this.findChild(QtWidgets.QLabel, 'scopebar1_label_tdiv')
        self.scopebar1_label_hpos = this.findChild(QtWidgets.QLabel, 'scopebar1_label_hpos')
        self.scopebar1_label = []
        for i in range(1, 3):
            self.scopebar1_label.append(this.findChild(QtWidgets.QLabel, 'scopebar1_label' + str(i)))

        self.scopebar1_label_vdiv = []
        for i in range(1, 3):
            self.scopebar1_label_vdiv.append(this.findChild(QtWidgets.QLabel, 'scopebar1_label_vdiv' + str(i)))

        self.scopebar1_label_offset = []
        for i in range(1, 3):
            self.scopebar1_label_offset.append(this.findChild(QtWidgets.QLabel, 'scopebar1_label_offset' + str(i)))

        self.scope_button = []
        for i in range(1, 7):
            self.scope_button.append(this.findChild(QtWidgets.QPushButton, 'scope_button' + str(i)))
            self.hide_widget(self.scope_button[i - 1])

        # graph settings
        pg.setConfigOptions(antialias=True)

        # layout
        self.scope_graph.ci.layout.setSpacing(0)
        self.scope_graph.ci.layout.setRowMaximumHeight(0, 20)

        # ticks
        self.vtick = pg.TickSliderItem(orientation='left', allowAdd=False, allowRemove=False)
        self.htick = pg.TickSliderItem(orientation='top', allowAdd=False, allowRemove=False)
        self.vtick.tickSize = self.TICK_SIZE
        self.htick.tickSize = self.TICK_SIZE
        self.trig_tick = self.vtick.addTick(0, color=self.TRIG_TICK_COLOR, movable=False)
        self.offset_tick = []
        self.offset_tick.append(self.vtick.addTick(0, color=self.colors[0], movable=False))
        self.offset_tick.append(self.vtick.addTick(0, color=self.colors[1], movable=False))
        self.hpos_tick = self.htick.addTick(0, color=self.HPOS_TICK_COLOR, movable=False)
        self.scope_graph.addItem(self.vtick, row=2, col=0)
        self.scope_graph.addItem(self.htick, row=1, col=1)

        # dual plot area
        self.p1axl = pg.AxisItem(orientation='left', showValues=False)
        self.p1axb = pg.AxisItem(orientation='bottom', showValues=False)
        self.p1 = self.scope_graph.addPlot(row=2, col=1, axisItems={'left': self.p1axl, 'bottom': self.p1axb})
        self.p2 = pg.ViewBox()
        self.p1.scene().addItem(self.p2)
        self.p2.setXLink(self.p1)

        # beam finder
        self.p0axl = pg.AxisItem(orientation='left', showValues=False)
        self.p0axb = pg.AxisItem(orientation='bottom', showValues=False)
        self.p0 = self.scope_graph.addPlot(row=0, col=1, axisItems={'left': self.p0axl, 'bottom': self.p0axb})
        self.p0.hideAxis('left')
        self.p0.hideAxis('bottom')
        self.region = pg.LinearRegionItem(movable=False)
        self.region.setZValue(10)
        self.p0.addItem(self.region)
        self.p0.setYRange(-1, 1, padding=0)

        self.p1.showGrid(x=True, y=True)
        self.p0.setMouseEnabled(x=False, y=False)
        self.p1.setMouseEnabled(x=False, y=False)
        self.p2.setMouseEnabled(x=False, y=False)
        self.p0.hideButtons()
        self.p1.hideButtons()
        self.p0.setMenuEnabled(False)
        self.p1.setMenuEnabled(False)
        self.p2.setMenuEnabled(False)

        # adjust item size
        self.scope_graph.ci.layout.itemAt(2, 1).setContentsMargins(self.TICK_SIZE / 2, self.TICK_SIZE / 2, self.TICK_SIZE / 2 + 1, self.TICK_SIZE / 2)
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())

        # calculated values
        self.calc_numbers()

        # label settings
        self.update_vdiv(0)
        self.update_vdiv(1)
        self.update_tdiv()
        self.step_offset(0)
        self.step_offset(1)
        self.step_trig_level()
        self.step_holdoff()
        self.step_trig_hyst()
        self.set_trig_src()
        self.set_trig_mode()
        self.set_trig_cond()
        self.set_input_range(0)
        self.set_input_range(1)

        # run
        self.m2k.acquired.connect(self.plot)

    def calc_numbers(self):
        self.xrange = [-self.tdivs[self.tdiv_index] * self.xdiv / 2, self.tdivs[self.tdiv_index] * self.xdiv / 2]
        self.yrange = [
            [
                -self.vdivs[self.vdiv_index[0]] * self.ydiv / 2,
                self.vdivs[self.vdiv_index[0]] * self.ydiv / 2
            ],
            [
                -self.vdivs[self.vdiv_index[1]] * self.ydiv / 2,
                self.vdivs[self.vdiv_index[1]] * self.ydiv / 2
            ]
        ]
        self.samplecount = int(self.samplerate * self.tdivs[self.tdiv_index] * self.xdiv)
        self.timer_interval_ms = int(self.tdivs[self.tdiv_index] * 1000 * self.xdiv)
        self.region_range = [-self.tdivs[self.tdiv_index] * self.xdiv * 5 + self.hpos, self.tdivs[self.tdiv_index] * self.xdiv * 5 + self.hpos]
        self.update_vtick()
        self.update_htick()

    def run_acquisition(self):
        self.running = True
        self.m2k.set_loop(True)
        self.m2k.set_enable_in(True)

    def stop_acquisition(self):
        self.running = False
        self.m2k.set_loop(False)

    def plot(self, data, triggered):
        if (not self.single_waiting) or (self.single_waiting and triggered):
            x = np.linspace(self.xrange[0], self.xrange[1], num=len(data[0]))
            ch1_array = np.array(data[0]) + self.offset[0]
            ch2_array = np.array(data[1]) + self.offset[1]

            if self.enable_ch[0]:
                self.p1.plot(x=x, y=ch1_array, pen=self.colors[0], clear=True)

            if self.enable_ch[1]:
                self.p2.clear()
                self.p2.addItem(pg.PlotCurveItem(x=x, y=ch2_array, pen=self.colors[1]))

        # to avoid chattering
        if self.trig_mode:
            self.on_triggered(triggered)
        else:
            if not triggered:
                self.triggered_count = 0
                self.on_triggered(False)
            elif self.triggered_count + 1 > 3:
                self.on_triggered(True)
            else:
                self.triggered_count += 1

    def hide_widget(self, widget):
        sp = widget.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        widget.setSizePolicy(sp)
        widget.hide()

    def update_vtick(self):
        self.vtick.setTickValue(
            self.trig_tick,
            Utils.map(self.trig_level, self.yrange[self.trig_src][0], self.yrange[self.trig_src][1], 0, 1)
        )
        for i, tick in enumerate(self.offset_tick):
            if tick != None:
                self.vtick.setTickValue(
                    tick,
                    Utils.map(self.offset[i], self.yrange[i][0], self.yrange[i][1], 0, 1)
                )

    def update_htick(self):
        self.htick.setTickValue(self.hpos_tick, Utils.map(self.hpos, self.xrange[0], self.xrange[1], 0, 1))

    def update_vdiv(self, ch):
        self.calc_numbers()
        self.scopebar1_label_vdiv[ch].setText(Utils.conv_num_str(self.vdivs[self.vdiv_index[ch]]) + 'V/div')
        self.p1.setYRange(self.yrange[0][0], self.yrange[0][1], padding=0)
        self.p2.setYRange(self.yrange[1][0], self.yrange[1][1], padding=0)
        self.p1axl.setTickSpacing(self.vdivs[self.vdiv_index[0]] * self.ydiv / 2, self.vdivs[self.vdiv_index[0]])
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())

    def update_tdiv(self):
        self.calc_numbers()
        self.scopebar1_label_tdiv.setText(Utils.conv_num_str(self.tdivs[self.tdiv_index]) + 's/div')
        self.region.setRegion([self.xrange[0], self.xrange[1]])
        self.p0.setXRange(self.region_range[0], self.region_range[1], padding=0)
        self.p0.plot(x=[self.region_range[0], self.region_range[1]], y=[0, 0], pen=self.FINDER_PLOT_COLOR, clear=True)
        self.p0.addItem(self.region)
        self.p1.setXRange(self.xrange[0], self.xrange[1], padding=0)
        self.p1axb.setTickSpacing(self.tdivs[self.tdiv_index] * self.xdiv / 2, self.tdivs[self.tdiv_index])
        self.m2k.set_interval(self.timer_interval_ms)
        self.m2k.set_timeout_in(self.timer_interval_ms + 100)
        self.m2k.set_delay_trig(int(-(self.tdivs[self.tdiv_index] * self.xdiv / 2 + self.hpos) * self.samplerate))
        self.m2k.set_count_in(self.samplecount)

    def on_triggered(self, triggered):
        if triggered:
            self.scopebar1_label_trig_status.setStyleSheet('QLabel { background-color: #01a000; border-color: #016700; }')
            if self.single_waiting:
                self.single_waiting = False
                self.panel.get_widget('panel3_toggle_button').setChecked(False)
                self.update_tdiv()
                self.stop_acquisition()
        else:
            self.scopebar1_label_trig_status.setStyleSheet('')

    def set_trig_src(self, src=None):
        if src != None:
            self.trig_src = src
            self.m2k.src_trig(src)

        if self.now_menu == self.MENU_TRIG:
            self.scope_button[0].setText(self.langs['scope.source'] + '\n' + self.langs['scope.ch'] + str(self.trig_src + 1))

        self.step_trig_level()
        self.update_vtick()

    def set_trig_mode(self, mode=None):
        if mode != None:
            self.trig_mode = mode
            self.triggered_count = 0

        self.m2k.set_mode_trig(self.trig_mode)

        if self.now_menu == self.MENU_TRIG:
            self.scope_button[1].setText(self.langs['scope.mode'] + '\n' + self.langs['scope.mode_' + str(int(self.trig_mode))])

        self.scopebar1_label_trig_status.setText(self.langs['scope.mode_' + str(int(self.trig_mode))])

    def set_trig_cond(self, cond=None):
        if cond != None:
            self.trig_cond = cond
            self.m2k.set_cond_trig(0, cond)
            self.m2k.set_cond_trig(1, cond)

        if self.now_menu == self.MENU_TRIG:
            if self.trig_cond == 0:
                cond_str = self.langs['scope.rising_edge']
            else:
                cond_str = self.langs['scope.falling_edge']
            self.scope_button[2].setText(self.langs['scope.edge'] + '\n' + cond_str)

    def set_enable_ch(self, ch, enable=None):
        if enable != None:
            self.enable_ch[ch] = enable
            if enable:
                self.offset_tick[ch] = self.vtick.addTick(Utils.map(self.offset[ch], self.yrange[ch][0], self.yrange[ch][1], 0, 1), color=self.colors[ch])
                self.scopebar1_label[ch].show()
                self.scopebar1_label_vdiv[ch].show()
                self.scopebar1_label_offset[ch].show()
            else:
                if ch == 0:
                    self.p1.clear()
                else:
                    self.p2.clear()
                self.vtick.removeTick(self.offset_tick[ch])
                self.offset_tick[ch] = None

                self.hide_widget(self.scopebar1_label[ch])
                self.hide_widget(self.scopebar1_label_vdiv[ch])
                self.hide_widget(self.scopebar1_label_offset[ch])

        if self.now_menu == self.MENU_CH1 or self.now_menu == self.MENU_CH2:
            dic = [self.langs['scope.off'], self.langs['scope.on']]
            self.scope_button[0].setText(self.langs['scope.ch'] + str(ch + 1) + '\n' + dic[int(self.enable_ch[ch])])

    def set_input_range(self, ch, input_range=None):
        if input_range != None:
            self.input_range[ch] = input_range

        if self.input_range[ch] == 0:
            self.scopebar1_label_vdiv[ch].setStyleSheet('')
        else:
            self.scopebar1_label_vdiv[ch].setStyleSheet('QLabel{ color: red; }')

        self.m2k.set_range_in(ch, self.input_range[ch])

        if self.now_menu == self.MENU_CH1 or self.now_menu == self.MENU_CH2:
            dic = [self.langs['scope.plus_minus_25v'], self.langs['scope.plus_minus_2_5v']]
            self.scope_button[1].setText(self.langs['scope.range'] + '\n' + dic[self.input_range[ch]])

    def step_vdiv(self, ch, incr): # bool incr: increase or decrease
        if incr:
            if self.vdiv_index[ch] + 1 < len(self.vdivs):
                self.vdiv_index[ch] += 1
        else:
            if self.vdiv_index[ch] - 1 >= 0:
                self.vdiv_index[ch] -= 1

        self.step_offset(ch)
        self.step_trig_level()
        self.update_vdiv(ch)

    def step_tdiv(self, incr):
        if incr:
            if self.tdiv_index + 1 < len(self.vdivs):
                self.tdiv_index += 1
        else:
            if self.tdiv_index - 1 >= 0:
                self.tdiv_index -= 1

        self.step_hpos()
        self.update_tdiv()

    def step_offset(self, ch, incr=None):
        if incr != None:
            if incr:
                self.offset_count[ch] += 1
            else:
                self.offset_count[ch] -= 1

        self.offset[ch] = self.vdivs[self.vdiv_index[ch]] * 0.1 * self.offset_count[ch]
        self.scopebar1_label_offset[ch].setText(Utils.conv_num_str(self.offset[ch]) + 'V')
        self.update_vtick()
        self.m2k.set_offset_in(ch, self.offset[ch])

    def step_hpos(self, incr=None):
        if incr != None:
            if incr:
                self.hpos_count += 1
            else:
                self.hpos_count -= 1

        self.hpos = self.tdivs[self.tdiv_index] / 5 * self.hpos_count
        self.update_tdiv()
        self.scopebar1_label_hpos.setText(Utils.conv_num_str(self.hpos) + 's')
        if not self.running:
            self.p1.setXRange(self.xrange[0] - self.hpos + self.stopped_hpos, self.xrange[1] - self.hpos + self.stopped_hpos, padding=0)
            self.p1axb.setTickSpacing(levels=[(self.tdivs[self.tdiv_index] * self.xdiv / 2, -self.hpos + self.stopped_hpos), (self.tdivs[self.tdiv_index], -self.hpos + self.stopped_hpos)])

    def step_trig_level(self, incr=None):
        if incr != None:
            if incr:
                self.trig_level_count += 1
            else:
                self.trig_level_count -= 1

        self.trig_level = self.vdivs[self.vdiv_index[self.trig_src]] * 0.1 * self.trig_level_count
        self.scopebar1_label_trig_level.setText(Utils.conv_num_str(self.trig_level) + 'V')
        self.update_vtick()
        self.m2k.set_level_trig(0, self.trig_level)
        self.m2k.set_level_trig(1, self.trig_level)

    def step_holdoff(self, incr=None):
        if incr != None:
            if incr:
                self.holdoff_count += 1
            elif self.holdoff_count > 0:
                self.holdoff_count -= 1

        self.holdoff = self.tdivs[self.tdiv_index] / 2 * self.holdoff_count
        self.scopebar1_label_holdoff.setText(Utils.conv_num_str(self.holdoff) + 's')
        self.m2k.set_holdoff_trig(int(self.timer_interval_ms + self.holdoff * 1000))

    def step_trig_hyst(self, incr=None):
        if incr != None:
            if incr:
                self.trig_hyst_count += 1
            elif self.trig_hyst_count > 0:
                self.trig_hyst_count -= 1

        self.trig_hyst = 0.1 * self.trig_hyst_count
        self.scopebar1_label_trig_hyst.setText(Utils.conv_num_str(self.trig_hyst) + 'V')
        self.m2k.set_hyst_trig(0, self.trig_hyst)
        self.m2k.set_hyst_trig(1, self.trig_hyst)

    def toggle_trig_src(self):
        self.set_trig_src(not self.trig_src)

    def toggle_trig_mode(self):
        self.set_trig_mode(not self.trig_mode)

    def toggle_trig_cond(self):
        self.set_trig_cond(not self.trig_cond)

    def toggle_enable_ch(self, ch):
        self.set_enable_ch(ch, not self.enable_ch[ch])

    def toggle_input_range(self, ch):
        self.set_input_range(ch, not self.input_range[ch])

    def show_buttons(self, count):
        for i in range(count):
            try:
                self.scope_button[i].disconnect()
            except:
                pass

            self.scope_button[i].show()

        for i in range(count, 6):
            self.hide_widget(self.scope_button[i])

    def change_menu(self, index):
        if index != self.now_menu:
            self.now_menu = index
            if index == self.MENU_CH1:
                self.set_enable_ch(0)
                self.set_input_range(0)

                self.show_buttons(2)
                self.scope_button[0].pressed.connect(lambda: self.toggle_enable_ch(0))
                self.scope_button[1].pressed.connect(lambda: self.toggle_input_range(0))
            if index == self.MENU_CH2:
                self.set_enable_ch(1)
                self.set_input_range(1)

                self.show_buttons(2)
                self.scope_button[0].pressed.connect(lambda: self.toggle_enable_ch(1))
                self.scope_button[1].pressed.connect(lambda: self.toggle_input_range(1))
            elif index == self.MENU_TRIG:
                self.set_trig_src()
                self.set_trig_mode()
                self.set_trig_cond()

                self.show_buttons(3)
                self.scope_button[0].pressed.connect(self.toggle_trig_src)
                self.scope_button[1].pressed.connect(self.toggle_trig_mode)
                self.scope_button[2].pressed.connect(self.toggle_trig_cond)

    def control(self, name, value):
        if name == 'panel1_dial1':
            self.step_tdiv(not value)
        elif name == 'panel1_dial2':
            self.step_hpos(value)
        elif name == 'panel2_1_dial1':
            self.step_vdiv(0, not value)
        elif name == 'panel2_2_dial1':
            self.step_vdiv(1, not value)
        elif name == 'panel2_1_dial2':
            self.step_offset(0, value)
        elif name == 'panel2_2_dial2':
            self.step_offset(1, value)
        elif name == 'panel2_1_button':
            self.change_menu(self.MENU_CH1)
        elif name == 'panel2_2_button':
            self.change_menu(self.MENU_CH2)
        elif name == 'panel3_toggle_button':
            if value:
                self.single_waiting = False
                self.run_acquisition()
            else:
                self.stopped_hpos = self.hpos
                self.stop_acquisition()
        elif name == 'panel3_button':
            self.single_waiting = True
            self.p1.clear()
            self.p2.clear()
            self.run_acquisition()
        elif name == 'panel4_dial1':
            self.step_trig_level(value)
        elif name == 'panel4_dial2':
            self.step_holdoff(value)
        elif name == 'panel4_dial3':
            self.step_trig_hyst(value)
        elif name == 'panel4_button1':
            self.change_menu(self.MENU_TRIG)
        elif name == 'show':
            self.update_tdiv()
            self.run_acquisition()
        elif name == 'hide':
            self.stop_acquisition()
        else:
            print('WARN: control command "' + name + '" is not found')

