from PyQt5 import QtCore, QtWidgets, uic

class Panel(QtWidgets.QWidget):
    def __init__(self, master):
        super().__init__()
        uic.loadUi('./ui/panel.ui', self)
        self.master = master

        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        # values
        self.dial_before = []

        # get widgets
        self.toggle_button_names = [
            'panel3_toggle_button'
        ]
        self.toggle_buttons = []
        for name in self.toggle_button_names:
            self.toggle_buttons.append(self.findChild(QtWidgets.QPushButton, name))

        self.button_names = [
            'panel2_1_button', 'panel2_2_button',
            'panel3_button', 'panel4_button1'
        ]
        self.buttons = []
        for name in self.button_names:
            self.buttons.append(self.findChild(QtWidgets.QPushButton, name))

        self.dial_names = [
            'panel1_dial1', 'panel1_dial2',
            'panel2_1_dial1', 'panel2_1_dial2',
            'panel2_2_dial1', 'panel2_2_dial2',
            'panel4_dial1', 'panel4_dial2', 'panel4_dial3'
        ]
        self.dials = []
        for name in self.dial_names:
            self.dials.append(self.findChild(QtWidgets.QDial, name))
            self.dial_before.append(0)

        # connect
        for i, button in enumerate(self.buttons):
            button.clicked.connect(lambda v, index=i: self.master.send_control(self.button_names[index]))

        for i, toggle_button in enumerate(self.toggle_buttons):
            toggle_button.toggled.connect(lambda v, index=i: self.master.send_control(self.toggle_button_names[index], v))

        for i, dial in enumerate(self.dials):
            dial.valueChanged.connect(lambda v, index=i: self.encode_dial(index, v))

    def showEvent(self, event):
        self.move(self.master.pos() + QtCore.QPoint(self.master.width(), 0))

    def get_widget(self, name):
        if name in self.toggle_button_names:
            return self.toggle_buttons[self.toggle_button_names.index(name)]

        if name in self.button_names:
            return self.buttons[self.button_names.index(name)]

        if name in self.dial_names:
            return self.dial[self.dial_names.index(name)]

    def encode_dial(self, index, value):
        # check direction
        if value > self.dial_before[index]:
            if value - self.dial_before[index] > 1:
                self.master.send_control(self.dial_names[index], False)
            else:
                self.master.send_control(self.dial_names[index], True)
        elif value < self.dial_before[index]:
            if self.dial_before[index] - value > 1:
                self.master.send_control(self.dial_names[index], True)
            else:
                self.master.send_control(self.dial_names[index], False)

        self.dial_before[index] = value
