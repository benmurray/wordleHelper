# coding=utf-8
#  Copyright (c) 2022 RuddyDog - All Rights Reserved.
import sys
import signal
import pandas as pd
from qtpy import uic, QtCore, QtWidgets, QtGui
from os.path import join, dirname

UI_AppWindow, WindowType = uic.loadUiType(join(dirname(__file__), "wordle_solver.ui"))


class WSMainWindow(QtWidgets.QMainWindow, UI_AppWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, flags=QtCore.Qt.Window)
        UI_AppWindow.__init__(self)
        self.setupUi(self)

        self.cell_state_options = ['white', 'grey', 'yellow', 'green']

        self.inputs = [[self.c00, self.c01, self.c02, self.c03, self.c04],
                       [self.c10, self.c11, self.c12, self.c13, self.c14],
                       [self.c20, self.c21, self.c22, self.c23, self.c24],
                       [self.c30, self.c31, self.c32, self.c33, self.c34],
                       [self.c40, self.c41, self.c42, self.c43, self.c44]]

        # position of cell_state_options i.e. they are all white to begin with
        self.inputs_states = [[0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0]]

        # will populate with letters
        self.inputs_chars = [["", "", "", "", ""],
                             ["", "", "", "", ""],
                             ["", "", "", "", ""],
                             ["", "", "", "", ""],
                             ["", "", "", "", ""]]

        self.submit_buttons = [self.row0Submit,
                               self.row1Submit,
                               self.row2Submit,
                               self.row3Submit,
                               self.row4Submit]

        self._setup_click_actions()
        self._setup_menubar()
        self.statusBar()

    def return_pressed(self):
        lineedit = QtWidgets.QApplication.focusWidget()
        row = int(lineedit.objectName()[1])
        col = int(lineedit.objectName()[2])
        self.update_cell_bg_color(row, col)

    def update_cell_bg_color(self, row, col):
        cell = self.inputs[row][col]
        cell_bg_state = (self.inputs_states[row][col] + 1) % len(self.cell_state_options)
        self.inputs_states[row][col] = cell_bg_state
        cell.setStyleSheet("QLineEdit {background-color:" + self.cell_state_options[cell_bg_state] + "}")

    def _setup_menubar(self):
        self.actionQuit.setShortcut('Ctrl+Q')
        self.actionQuit.triggered.connect(self.close)

    def _setup_click_actions(self):
        for row in range(5):
            for col in range(5):
                self.inputs[row][col].returnPressed.connect(self.return_pressed)


def get_words(possibles, bad_chars, known_letters_bad_pos, known_letters_with_pos):
    new_possibles = []

    for w in possibles:
        # remove all words without correct known letter(s) in their correct space
        for char in known_letters_with_pos.keys():
            # adds a word with one letter in one place and 1 in another but not should only add if BOTH are in
            for known_position in known_letters_with_pos[char]:
                if w[known_position] == char and w not in new_possibles:
                    new_possibles.append(w)
            # remove ones that don't satisfy all
            for known_position in known_letters_with_pos[char]:
                if w[known_position] != char and w in new_possibles:
                    new_possibles.remove(w)

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
    # words = pd.read_csv("/home/ben/Desktop/words.csv")
    #
    # possibles = words['word'].values
    # bad_chars = ['t', 'o', 'r', 'd', 'm']
    # known_letters_bad_pos = {'s': [3,4], 'h':[0], 'e':[1]}
    # known_letters_with_pos = {'a': [2], 's':[0], 'h':[1], 'e':[4]}
    #
    # choices = get_words(possibles, bad_chars, known_letters_bad_pos, known_letters_with_pos)
    # print(f"\n\nTry \"{choices[0]}\"\n\n")
    # print(f"\n\nReturned {len(choices)} possible words with \"{choices[0]}\" being the most likely.\n")
    # print(choices)
