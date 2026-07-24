'''
Open the olfactometry window and the flow sensor window


7/16/2026
'''


import sys
from PyQt5.QtWidgets import *
import olfactometry
from flow_sensor_driver import flowSensor

#olfaConfigFileName = 'olfa_config.json'    # won't open python window
olfaConfigFileName = 'olfa_config_2MFC.json'


class main_window(QMainWindow):
    # Make a window where we can put stuff
    def __init__(self):
        super().__init__()
        
        self.olfas = olfactometry.Olfactometers(config_obj=olfaConfigFileName)
        self.flowsensor = flowSensor()
        self.extra_button = QPushButton('Push')
        self.extra_button.clicked.connect(self.button_push_test)
        
        layout = QVBoxLayout()
        layout.addWidget(self.flowsensor)
        layout.addWidget(self.olfas)
        layout.addWidget(self.extra_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def button_push_test(self):        
        new_setpoint = 100
        teensy_olfa = self.olfas[0]
        # get the MFC connected to VC port 2 (arduino port 1)
        for mfc in teensy_olfa.mfcs:
            if mfc.arduino_port == 2:
                mfc_i_want = mfc
                break
        mfc_i_want.mfcslider.setValue(new_setpoint)     # sets the slider and the text
        mfc_i_want._slider_changed()

        
        x=1



if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    window = main_window()
    window.show()
    sys.exit(app1.exec_())
