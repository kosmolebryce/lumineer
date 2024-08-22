# `src/lumineer/spectacle/main.py`
import sys
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QTextEdit, QRadioButton,
                             QPushButton, QButtonGroup)
from PyQt6.QtGui import QPalette, QColor, QFont, QKeySequence, QShortcut, QColorConstants
from PyQt6.QtCore import Qt, QEvent

class NMRAnalysisHelper:
    def __init__(self):
        self.common_shifts = {
            '1H NMR': {
                'TMS': 0,
                'Alkyl (R-CH3)': (0.7, 1.3),
                'Alkyl (R-CH2-R)': (1.2, 1.4),
                'Alkyl (R3CH)': (1.4, 1.7),
                'Allylic (R-CH2-C=C)': (1.6, 2.2),
                'Alkyne (RC≡C-H)': (2.0, 3.0),
                'Ketone (R-CO-CH3)': (2.1, 2.6),
                'Aldehyde (R-CHO)': (9.5, 10.1),
                'Alcohol (R-OH)': (0.5, 5.0),
                'Alcohol (R-CH2-OH)': (3.4, 4.0),
                'Ether (R-O-CH2-R)': (3.3, 3.9),
                'Ether (R-O-CH3)': (3.3, 3.8),
                'Ester (R-COO-CH3)': (3.6, 3.8),
                'Ester (R-COO-CH2-R)': (4.1, 4.3),
                'Alkene (R2C=CH2)': (4.6, 5.0),
                'Alkene (R2C=CH-R)': (5.2, 5.7),
                'Alkene (RHC=CH2)': (5.0, 5.5),
                'Aromatic (Ar-H)': (6.5, 8.5),
                'Benzyl (Ar-CH2-R)': (2.3, 2.8),
                'Phenol (Ar-OH)': (4.5, 7.7),
                'Carboxylic Acid (R-COOH)': (10.5, 12.0),
                'Amine (R-NH2)': (1.0, 3.0),
                'Amine (R2NH)': (1.2, 2.0),
                'Amide (R-CO-NH-R)': (5.0, 6.5),
                'Amide (R-CO-NH2)': (5.5, 7.5),
                'Thiol (R-SH)': (1.0, 1.5),
                'Phosphine (R3P-H)': (2.5, 4.5),
                'Silicon (R3Si-H)': (3.5, 5.0)
            },
            '13C NMR': {
                'Alkyl (R-CH3)': (0, 40),
                'Alkyl (R-CH2-R)': (15, 55),
                'Alkyl (R3CH)': (20, 60),
                'Allylic (R-CH2-C=C)': (20, 40),
                'Alkyne (RC≡C-H)': (60, 80),
                'Aromatic (Ar-C)': (100, 160),
                'Alkene (R2C=CR2)': (100, 150),
                'Ester (R-COO-R)': (160, 185),
                'Ketone (R-CO-R)': (190, 220),
                'Aldehyde (R-CHO)': (190, 200)
            },
            'Deuterated Solvent Residuals': {
                'Chloroform-d (CDCl3)': 7.26,
                'Dimethyl sulfoxide-d6 (DMSO-d6)': 2.50,
                'Acetone-d6': 2.05,
                'Methanol-d4': 3.31,
                'Water-d2 (D2O)': 4.79,
                'Benzene-d6': 7.16,
                'Acetonitrile-d3': 1.94
            }
        }

    def identify_functional_groups(self, shift, nmr_type='1H NMR'):
        identified = []
        for group, range_val in self.common_shifts[nmr_type].items():
            if isinstance(range_val, tuple):
                if range_val[0] <= shift <= range_val[1]:
                    identified.append(group)
            elif isinstance(range_val, (int, float)):
                if abs(shift - range_val) < 0.1:
                    identified.append(group)
        return identified

    def parse_input(self, input_string):
        input_string = re.sub(r'[\n,]', ' ', input_string)
        pattern = r'(\d+\.?\d*)'
        matches = re.findall(pattern, input_string)
        try:
            return [float(match) for match in matches]
        except ValueError:
            return []

    def analyze(self, input_string, nmr_type='1H NMR'):
        shifts = self.parse_input(input_string)
        if not shifts:
            return "No valid shifts found in input."
        analysis = []
        for shift in shifts:
            groups = self.identify_functional_groups(shift, nmr_type)
            if groups:
                analysis.append(f"{shift} ppm: Possible assignments - {', '.join(groups)}")
            else:
                analysis.append(f"{shift} ppm: No common assignments found")
        return '\n'.join(analysis)

class NMRAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nmr_helper = NMRAnalysisHelper()
        self.init_ui()
        self.setup_shortcuts()
        QApplication.instance().installEventFilter(self)

    def init_ui(self):
        self.setWindowTitle("NMR Analysis Helper")
        self.setGeometry(100, 100, 600, 500)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Input section
        input_label = QLabel("Enter NMR Shifts as a comma- or line-delimited list:")
        main_layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setFixedSize(560, 100)
        main_layout.addWidget(self.input_text)

        # Radio buttons for NMR type
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(10)
        radio_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.radio_group = QButtonGroup(self)
        self.radio_1h = QRadioButton("1H NMR")
        self.radio_13c = QRadioButton("13C NMR")
        self.radio_1h.setChecked(True)
        self.radio_group.addButton(self.radio_1h)
        self.radio_group.addButton(self.radio_13c)
        radio_layout.addWidget(self.radio_1h)
        radio_layout.addWidget(self.radio_13c)
        main_layout.addLayout(radio_layout)

        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze_shifts)
        self.analyze_button.setFixedSize(100, 30)
        main_layout.addWidget(self.analyze_button)

        # Results section
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFixedSize(560, 200)
        main_layout.addWidget(self.result_text)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColorConstants.White)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColorConstants.White)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColorConstants.White)
        dark_palette.setColor(QPalette.ColorRole.Text, QColorConstants.White)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColorConstants.White)
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColorConstants.Red)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 222, 152))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColorConstants.Black)

        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QWidget {
                background-color: #353535;
                color: #FFF5E6;
                font-size: 12px;
            }
            QTextEdit, QLineEdit {
                background-color: #252525;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton {
                background-color: #FFBE98;
                color: black;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #FFE9B8;
            }
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 8px;
                height: 8px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #999999;
                background: none;
                border-radius: 7px;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #FFBE98;
                background: #FFBE98;
                border-radius: 7px;
            }
        """)

    def analyze_shifts(self):
        input_string = self.input_text.toPlainText().strip()
        nmr_type = '1H NMR' if self.radio_1h.isChecked() else '13C NMR'
        result = self.nmr_helper.analyze(input_string, nmr_type)
        formatted_result = self.format_result(result)
        self.result_text.setPlainText(formatted_result)

    def format_result(self, result):
        lines = result.split('\n')
        formatted_lines = []
        for line in lines:
            if 'ppm' in line:
                shift, assignments = line.split(' ppm: ')
                formatted_lines.append(f"[{shift.strip()} ppm]")
                if 'No common assignments found' in assignments:
                    formatted_lines.append("No common assignments found\n")
                else:
                    groups = assignments.replace('Possible assignments - ', '').split(', ')
                    formatted_lines.append("Possible assignments:")
                    for group in groups:
                        formatted_lines.append(f"> {group}")
                    formatted_lines.append("")  # Add a blank line for separation
        return "\n".join(formatted_lines)

    def setup_shortcuts(self):
        close_key = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_W)  # This will be Command+W on macOS
        self.closeWindowShortcut = QShortcut(close_key, self)
        self.closeWindowShortcut.activated.connect(self.close)

        # For compatibility, also keep the standard close shortcut
        self.closeWindowShortcutStd = QShortcut(QKeySequence.StandardKey.Close, self)
        self.closeWindowShortcutStd.activated.connect(self.close)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            if (event.modifiers() & Qt.KeyboardModifier.ControlModifier or event.modifiers() & Qt.KeyboardModifier.MetaModifier) and event.key() == Qt.Key.Key_W:
                event.accept()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Close) or (event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W):
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    ex = NMRAnalyzerApp()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()