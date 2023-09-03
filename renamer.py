#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        
# Purpose:     
#
# Author:      tejada.miguel@gmail.com
#
# Created:     06/12/2021
# Licence:     GPL

# -------------------------------------------------------------------------------
# __all__ = ['project', 'qApp', 'unit', 'settings','tempDir']
__author__ = "Miguel Tejada"
__version__ = "0.0"
__email__ = "tejada.miguel@gmail.com"
__license__ = "tejada.miguel@gmail.com"
__versionHistory__ = [
    ["0.0", "210211", "MTEJADA", "START"]]

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QFileDialog, QVBoxLayout, \
    QHBoxLayout, QWidget, QListWidget, QListWidgetItem, QMessageBox, QCheckBox, QStyle, QDirModel, QTreeView


class RenameFilesWindow(QMainWindow):
    long_path_no_check = '\\\\?\\'

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rename Files')

        # Create the main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create the directory selection layout
        directory_layout = QHBoxLayout()
        main_layout.addLayout(directory_layout)

        directory_label = QLabel('Select Directory:')
        directory_layout.addWidget(directory_label)

        self.path_edit = QLineEdit()
        directory_layout.addWidget(self.path_edit)

        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.select_directory)
        directory_layout.addWidget(browse_button)

        # Create the symbol to replace layout
        symbol_layout = QHBoxLayout()
        main_layout.addLayout(symbol_layout)

        symbol_label = QLabel('Symbol to Search:')
        symbol_layout.addWidget(symbol_label)

        self.symbol_edit = QLineEdit()
        symbol_layout.addWidget(self.symbol_edit)
        symbol_layout.addWidget(QLabel("-> Symbol for replace:"))
        self.symbol_edit.textEdited.connect(lambda: self.populate_files_list(self.path_edit.text()))

        self.symbol_replace = QLineEdit()
        self.symbol_replace.textEdited.connect(lambda: self.populate_files_list(self.path_edit.text()))
        symbol_layout.addWidget(self.symbol_replace)

        _hlay = QHBoxLayout()
        self.chk_recursively = QCheckBox("Do it recursively")
        self.chk_recursively.stateChanged.connect(lambda: self.populate_files_list(self.path_edit.text()))
        _hlay.addWidget(self.chk_recursively)
        _hlay.addStretch()
        self.lbl_level = QLabel("0")
        _hlay.addWidget(self.lbl_level)
        self.root_folder = QLabel("")
        _hlay.addWidget(self.root_folder)
        main_layout.addLayout(_hlay)
        # Create the files list widget
        self.files_list = QListWidget()
        main_layout.addWidget(self.files_list)

        # Create the process files button
        process_button = QPushButton('Process Files')
        process_button.clicked.connect(self.process_files)
        main_layout.addWidget(process_button)

        # Create the status label
        self.status_label = QLabel('')
        main_layout.addWidget(self.status_label)

        # Set the default path to the current working directory
        # self.path_edit.setText(os.getcwd())
    def processed_path(self, path):
        base_path = os.path.realpath(path)
        if not base_path.startswith(self.long_path_no_check):
            if base_path.startswith("\\"): # no es un archivo del sistema
                base_path = self.long_path_no_check + "UNC" + base_path[1:]
            else:
                base_path = self.long_path_no_check + base_path
        if not os.path.exists(base_path):
            msg = QMessageBox.critical(self, "ERROR EN EL SISTEMA", "NO CAPTURA BIEN LA CARPETA RAIZ, HABLAR CON MIGUEL")
            return None
        return base_path

    def select_directory(self):
        # Display file dialog for directory selection
        path = QFileDialog.getExistingDirectory(self, 'Select Directory')
        # Set the path in the path edit widget
        self.path_edit.setText(path)
        base_path = self.processed_path(path)
        # Populate the files list widget
        self.populate_files_list(base_path)

    def populate_files_list(self, path):
        self.files_list.clear()
        if not path:
            return
        s_search = self.symbol_edit.text()
        s_replace = self.symbol_replace.text()
        dir_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        file_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        numb_of_dirs = 0
        for p in os.listdir(path):
            cur_path = os.path.join(path, p)
            is_file = os.path.isfile(cur_path)
            if is_file:
                splitedname = os.path.basename(p).rsplit(".", 1)
                fname = splitedname[0]
                extension = ("." + splitedname[1]) if len(splitedname) > 1 else ""
            else:
                fname, extension = p, ""
            if s_search in fname or (not is_file and self.chk_recursively.isChecked()):
                if not is_file:
                    numb_of_dirs += 1
                new_name = fname.replace(s_search, s_replace)

                item = QListWidgetItem("{} -> {}".format(fname + extension, new_name + extension))
                self.files_list.addItem(item)
                if not is_file:
                    item.setIcon(dir_icon)
                else:
                    item.setIcon(file_icon)
        self.root_folder.setText(" of %i" % numb_of_dirs)

    def process_files(self):
        # Confirm with user before proceeding
        if not self.symbol_edit.text() or not self.path_edit.text():
            return

        msg = QMessageBox.question(self, "RENAME FILES",
                                   "Are you sure you want to rename the files and directories?" + (
                                       "" if not self.chk_recursively.isChecked() else "\nThis will be done recursively"),
                                   QMessageBox.Ok | QMessageBox.Cancel)
        if msg != QMessageBox.Ok:
            return

        # Get the values of path and symbol from the interfac
        base_path = self.processed_path(self.path_edit.text())
        if not base_path:
            return

        # base_path = self.long_path_no_check + str(Path(self.path_edit.text()))
        self.lbl_level.setText("")
        symbol_to_search = self.symbol_edit.text()
        symbol_to_replace = self.symbol_replace.text()
        recursively = self.chk_recursively.isChecked()
        cur_level = ""

        class Counter:
            def __init__(self):
                self.v = 0

        file_counter = Counter()
        path_counter = Counter()
        path_with_problems = []
        self.rename_files(base_path, symbol_to_search, symbol_to_replace, recursively, cur_level, file_counter,
                          path_counter, path_with_problems)
        if path_with_problems:
            msg = QMessageBox.warning(self, "ERRORS ON PATHS",
                                      "The followings paths are not modified:\n" + "\n".join(path_with_problems))
        self.populate_files_list(self.path_edit.text())
        msg = QMessageBox.information(self, "DONE",
                                      "%i files and %i folders are been modified" % (file_counter.v, path_counter.v))

    def rename_files(self, path, s_search, s_replace, recursively, cur_level, file_counter, path_counter,
                     path_with_errors):
        self.lbl_level.setText(cur_level)
        app.processEvents()
        dir_counter = 0
        cur_path = path
        try:
            for p in os.listdir(path):
                cur_path = os.path.join(path, p)
                is_file = os.path.isfile(cur_path)
                if is_file:
                    splitedname = os.path.basename(p).rsplit(".",1)
                    fname = splitedname[0]
                    extension = ("." + splitedname[1]) if len(splitedname) > 1 else ""
                else:
                    fname, extension = p, ""
                if s_search in fname:
                    new_path = os.path.join(path, fname.replace(s_search, s_replace) + extension)
                    if not is_file:
                        dir_counter += 1
                        if recursively:
                            self.rename_files(cur_path, s_search, s_replace, recursively,
                                              cur_level + ".%i" % dir_counter,
                                              file_counter, path_counter, path_with_errors)
                            self.lbl_level.setText(cur_level)
                            app.processEvents()
                        path_counter.v += 1
                        os.rename(cur_path, new_path)
                    else:
                        file_counter.v += 1
                        fstat = os.stat(cur_path)
                        ctime, mtime = fstat.st_ctime, fstat.st_mtime
                        os.rename(cur_path, new_path)
                        os.utime(new_path, (ctime, mtime))

                elif recursively and not is_file:
                    dir_counter += 1
                    self.rename_files(cur_path, s_search, s_replace, recursively, cur_level + ".%i" % dir_counter,
                                      file_counter, path_counter, path_with_errors)
                    self.lbl_level.setText(cur_level)
                    app.processEvents()
        except Exception as e:
            msg = QMessageBox.warning(self, "Error", str(e) + "\n" + "On file or path: %s" % cur_path)
            path_with_errors.append(cur_path)

        # for root, dirs, files in os.walk(path, topdown=False):
        #     for name in files:
        #         file_path = os.path.join(root, name)
        #         new_name = re.sub(symbol_to_replace, '_', name)
        #         new_path = os.path.join(root, new_name)
        #         shutil.move(file_path, new_path)
        #         # Preserve file creation time
        #         creation_time = os.stat(new_path).st_ctime
        #         os.utime(new_path, (creation_time, creation_time))
        #     for name in dirs:
        #         dir_path = os.path.join(root, name)
        #         new_name = re.sub(symbol_to_replace, '_', name)
        #         new_path = os.path.join(root, new_name)
        #         os.rename(dir_path, new_path)
        #         # Preserve directory creation time
        #         creation_time = os.stat(new_path).st_ctime
        #         os.utime(new_path, (creation_time, creation_time))


# Create the application instance
app = QApplication([])

# Create the main window
main_window = RenameFilesWindow()
main_window.show()

# Run the application event loop
app.exec_()
