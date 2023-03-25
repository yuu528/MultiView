import sys
from PyQt5 import QtWidgets, uic
from widget.scope import ScopeWidget
import pyqtgraph as pg

from langs import Langs
from panel import Panel
from worker.m2k import M2kWorker

class Main(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/main.ui', self)

        self.langs = Langs('en').get_all()

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
        self.m2k = M2kWorker(1, 1000, rate_in=100e3)
        if not self.m2k.ready:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle('Error 01')
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setStandardButtons(QtWidgets.QMessageBox.Close)
            msg.setText('Error 01: Please check ADALM2000 connections.')
            msg.exec_()
            exit()

        self.m2k.start()

        # control panel
        self.panel = Panel(self)

        # get instances
        self.main_widget_ins = []
        self.main_widget_ins.append(ScopeWidget(self, self.main_widget[0], self.panel, self.langs, self.m2k))

        self.send_control('show')

    def closeEvent(self, event):
        self.panel.close()
        self.main_widget_ins[0].save()
        del self.main_widget_ins[0]
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
