# coding=utf-8
#  Copyright (c) 2022 RuddyDog - All Rights Reserved.
import sys
import signal
import pandas as pd
from qtpy import uic, QtCore, QtWidgets, QtGui
from qtpy.QtGui import QPalette
from os.path import join, dirname

UI_AppWindow, WindowType = uic.loadUiType(join(dirname(__file__), "wordle_solver.ui"))


class WSMainWindow(QtWidgets.QMainWindow, UI_AppWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, flags=QtCore.Qt.Window)
        UI_AppWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Wordle Helper")

        self.known = ["", "", "", "", ""]
        self.known_letters_bad_pos = {}
        self.known_bad_chars = []

        self.cell_state_options = ['grey', 'yellow', 'green']

        self.inputs = [[self.c00, self.c01, self.c02, self.c03, self.c04],
                       [self.c10, self.c11, self.c12, self.c13, self.c14],
                       [self.c20, self.c21, self.c22, self.c23, self.c24],
                       [self.c30, self.c31, self.c32, self.c33, self.c34],
                       [self.c40, self.c41, self.c42, self.c43, self.c44]]

        # position of cell_state_options i.e. they are all white to begin with
        self.inputs_states = [[-1, -1, -1, -1, -1],
                              [-1, -1, -1, -1, -1],
                              [-1, -1, -1, -1, -1],
                              [-1, -1, -1, -1, -1],
                              [-1, -1, -1, -1, -1]]

        self.submit_buttons = [self.row0Submit,
                               self.row1Submit,
                               self.row2Submit,
                               self.row3Submit,
                               self.row4Submit]

        self._setup_click_actions()
        self._setup_menubar()
        self.statusBar()
        self.possible_words = self.get_all_possible_words()

    def get_all_possible_words(self):
        """ Reads a list of words sorted my most frequency in Holman Bible"""
        words = pd.read_csv("words.csv")
        return words['word'].values

    def return_pressed(self):
        lineedit = QtWidgets.QApplication.focusWidget()
        row = int(lineedit.objectName()[1])
        col = int(lineedit.objectName()[2])
        self.update_cell_bg_color(row, col)

    def text_changed(self, char_changed_to):
        lineedit = QtWidgets.QApplication.focusWidget()
        row = int(lineedit.objectName()[1])
        col = int(lineedit.objectName()[2])
        if self.inputs_states[row][col] == -1:
            if char_changed_to != "":
                self.inputs[row][col].setStyleSheet("QLineEdit {background-color:" + self.cell_state_options[0] + "}")
                self.inputs_states[row][col] += 1
            else:
                self.inputs[row][col].setStyleSheet("QLineEdit {background-color: white}")
                self.inputs_states[row][col] = -1

    def update_cell_bg_color(self, row, col):
        cell = self.inputs[row][col]
        cell_bg_state = (self.inputs_states[row][col] + 1) % len(self.cell_state_options)
        self.inputs_states[row][col] = cell_bg_state
        cell.setStyleSheet("QLineEdit {background-color:" + self.cell_state_options[cell_bg_state] + "}")

    def _setup_menubar(self):
        self.actionQuit.setShortcut('Ctrl+Q')
        self.actionQuit.triggered.connect(self.close)

    def _setup_click_actions(self):
        # setup color changing of LineEdits
        for row in range(5):
            for col in range(5):
                self.inputs[row][col].returnPressed.connect(self.return_pressed)
                self.inputs[row][col].textChanged.connect(self.text_changed)

        # setup Submit of row
        self.row0Submit.clicked.connect(self.submit_clicked)
        self.row1Submit.clicked.connect(self.submit_clicked)
        self.row2Submit.clicked.connect(self.submit_clicked)
        self.row3Submit.clicked.connect(self.submit_clicked)
        self.row4Submit.clicked.connect(self.submit_clicked)

    def submit_clicked(self):
        button = QtWidgets.QApplication.focusWidget()
        row = int(button.objectName()[3])
        # Get letter and status of each input and add to appropriate array
        for col in range(5):
            line_edit = self.inputs[row][col]
            char = line_edit.text()
            color = self.get_color(line_edit.palette().color(QPalette.Background))

            if color == "green":
                self.known[col] = char
            elif color == "grey":
                if char not in self.known_bad_chars and \
                        (char not in self.known and char not in self.known_letters_bad_pos.keys()):
                    self.known_bad_chars.append(char)

            elif color == "yellow":
                if char in self.known_letters_bad_pos.keys():  # Add it to its value
                    self.known_letters_bad_pos[char].append(col)
                else:
                    self.known_letters_bad_pos[char] = [col]
            else:
                return

        self.possible_words = get_words(self.possible_words,
                                        self.known_bad_chars,
                                        self.known_letters_bad_pos,
                                        self.known)

        self.update_status_labels()

        button.setEnabled(False)

    def update_status_labels(self):
        if len(self.possible_words) > 0:
            self.try_next_text.setText(f"Try: {self.possible_words[0]}")
        else:
            self.try_next_text.setText(f"Nothing Left")
        min_idx = min(len(self.possible_words), 4)

        if min_idx <= 1:
            self.top_results.setText("No More Words!")
        else:
            next_top_str = f"Next Top {min_idx - 1}:"
            for idx in range(min_idx - 1):
                next_top_str += f" {self.possible_words[idx + 1]},"
            self.top_results.setText(next_top_str[:-1])

    def get_color(self, bg):
        # bg is background of of Cell
        if bg.red() == 239 and bg.green() == 239 and bg.blue() == 239:
            return "white"
        if bg.red() == 128 and bg.green() == 128 and bg.blue() == 128:
            return "grey"
        if bg.red() == 255 and bg.green() == 255 and bg.blue() == 0:
            return "yellow"
        if bg.red() == 0 and bg.green() == 128 and bg.blue() == 0:
            return "green"


def get_words(possibles, bad_chars, known_letters_bad_pos, known_letters):
    new_possibles = []

    for w in possibles:
        # remove all words without correct known letter(s) in their correct space
        is_valid = True
        for idx, char in enumerate(known_letters):
            if char != "":
                if w[idx] != char:
                    is_valid = False
                    break
        # only add words that matched every known character
        if is_valid:
            new_possibles.append(w)

    # This is hit first time called when nothing is known
    if len(new_possibles) == 0:
        new_possibles = list(possibles)

    to_delete = []
    for w in new_possibles:
        # remove all words with known letter(s) in known wrong spaces
        for char in known_letters_bad_pos.keys():
            # remove all words that don't have that letter at all
            if char not in w and w not in to_delete:
                to_delete.append(w)
                continue
            for known_bad_pos in known_letters_bad_pos[char]:
                if w[known_bad_pos] == char and w not in to_delete:
                    to_delete.append(w)

    for d in to_delete:
        new_possibles.remove(d)

    to_delete = []
    for w in new_possibles:
        # remove all words containing known bad letters
        for char in bad_chars:
            if char in w and w not in to_delete:
                to_delete.append(w)

    for d in to_delete:
        new_possibles.remove(d)

    return new_possibles


if __name__ == '__main__':
    # Hooks up ctrl-c to stop the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication([])
    window = WSMainWindow()
    window.show()
    sys.exit(app.exec_())
