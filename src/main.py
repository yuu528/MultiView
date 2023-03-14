import sys
import libm2k
from PyQt5 import QtWidgets, uic
from widget.scope import ScopeWidget
import pyqtgraph as pg

from panel import Panel

class Main(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/main.ui', self)

        self.lang = 'en'

        # get widget objects
        self.main_stacked = self.findChild(QtWidgets.QStackedWidget, 'main_stacked')
        self.mainbar_combo = self.findChild(QtWidgets.QComboBox, 'mainbar_combo')
        self.main_widget = []
        for name in ['scope_widget', 'sa_widget']:
            self.main_widget.append(self.findChild(QtWidgets.QWidget, name))

        # widget settings
        self.mainbar_combo.addItem('Oscilloscope')
        self.mainbar_combo.currentIndexChanged.connect(self.change_mode)

        # connect to m2k
        self.m2kdev = libm2k.m2kOpen()
        if self.m2kdev is None:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle('Error 01')
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setStandardButtons(QtWidgets.QMessageBox.Close)
            msg.setText('Error 01: Please check ADALM2000 connections.')
            msg.exec_()
            exit()

        self.m2kain = self.m2kdev.getAnalogIn()
        self.m2kaout = self.m2kdev.getAnalogOut()
        self.m2katrig = self.m2kain.getTrigger()

        # calibrate
        self.m2kain.reset()
        self.m2kaout.reset()
        self.m2kdev.calibrateADC()
        self.m2kdev.calibrateDAC()

        # m2k settings
        self.m2kain.enableChannel(0, True)
        self.m2kain.enableChannel(1, True)
        self.m2kain.setSampleRate(100000)

        # control panel
        self.panel = Panel(self)

        # get instances
        self.main_widget_ins = []
        self.main_widget_ins.append(ScopeWidget(self, self.main_widget[0], self.panel, self.lang, self.m2kdev, self.m2kain, self.m2katrig))

    def closeEvent(self, event):
        self.panel.close()
        event.accept()

    def showEvent(self, event):
        self.panel.show()

    def change_mode(self, index):
        self.send_control('hide')
        self.main_stacked.setCurrentIndex(index)
        self.send_control('show')

    def send_control(self, name, value=None):
        self.main_widget_ins[self.main_stacked.currentIndex()].control(name, value)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
