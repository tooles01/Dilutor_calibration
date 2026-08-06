'''
Open the olfactometry window


ST 2026
'''


import sys
from PyQt5.QtWidgets import *
import olfactometry

#olfaConfigFileName = 'olfa_config.json'    # mad slow
olfaConfigFileName = 'olfa_config_alt.json' # honestly no idea which is slower
#olfaConfigFileName = 'olfa_config_2MFC.json'
#olfaConfigFileName = 'olfa_config_1Dilutor.json'


class main_window(QMainWindow):
    # Make a window where we can put stuff
    def __init__(self):
        super().__init__()
        
        self.olfas = olfactometry.Olfactometers(config_obj=olfaConfigFileName)
        self.extra_button = QPushButton('Push')
        self.extra_button.clicked.connect(self.button_push_test)
        
        layout = QVBoxLayout()
        layout.addWidget(self.olfas)
        
        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    window = main_window()
    window.show()
    sys.exit(app1.exec_())




