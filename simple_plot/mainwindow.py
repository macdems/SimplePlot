# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import csv
import re

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from scipy.stats import linregress

from . import simpleplot_rc  # noqa
from .mainwindow_ui import Ui_MainWindow
from .util import BlockQtSignals

HEADER_RE = re.compile(r"^(?P<name>.+?)\s*(?:\((?P<symbol>.+?)\))?\s*(?:\[(?P<unit>.+?)\])?$")
SYMBOL_RE = re.compile(r"[a-zA-Z_]\w*")


class DoubleValidator(QDoubleValidator):

    def validate(self, input, pos):
        if not input:
            return QValidator.Acceptable, input, pos
        return super().validate(input, pos)


class FloatDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(DoubleValidator())
        editor.setAlignment(Qt.AlignRight)
        return editor


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self):
        super().__init__()
        self.filename = ""

        self.setupUi(self)

        self.retranslateUi(self)

        symbol_regex = QRegExp(r"[a-zA-Z_]\w*")
        self.xsymbol.setValidator(QRegExpValidator(symbol_regex, self))
        self.ysymbol.setValidator(QRegExpValidator(symbol_regex, self))

        self.data_table.setItemDelegate(FloatDelegate(self))
        dataitem = QTableWidgetItem()
        dataitem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.data_table.setItemPrototype(dataitem)

        self.insert_row_action = QAction(self.tr("Insert Row"), self)
        self.data_context_menu = QMenu(self)
        self.data_context_menu.addAction(self.insert_row_action)
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.add_plot()
        self.connect_signals()
        self.process_data()

    def connect_signals(self):
        self.xsymbol.textChanged.connect(self.on_xsymbol_changed)
        self.ysymbol.textChanged.connect(self.on_ysymbol_changed)
        self.xunit.textChanged.connect(self.on_unit_or_name_changed)
        self.yunit.textChanged.connect(self.on_unit_or_name_changed)
        self.xname.textChanged.connect(self.on_unit_or_name_changed)
        self.yname.textChanged.connect(self.on_unit_or_name_changed)
        self.data_table.itemChanged.connect(self.on_data_changed)
        self.load_action.triggered.connect(self.load)
        self.save_action.triggered.connect(self.save)
        self.export_action.triggered.connect(self.figure_toolbar.save_figure)
        self.data_table.customContextMenuRequested.connect(self.on_data_context_menu)

    def add_plot(self):
        self.figure = Figure(figsize=(5, 3))
        static_canvas = FigureCanvas(self.figure)
        self.figure_toolbar = NavigationToolbar(static_canvas, self)
        self.plot_layout.addWidget(self.figure_toolbar)
        self.plot_layout.addWidget(static_canvas)

    def on_data_context_menu(self, pos):
        index = self.data_table.indexAt(pos)
        if not index.isValid(): return
        action = self.data_context_menu.exec_(self.data_table.viewport().mapToGlobal(pos))

        if action == self.insert_row_action:
            row = index.row()
            self.data_table.insertRow(row)
            index = self.data_table.model().index(row, 0)
            self.data_table.setCurrentIndex(index)
            self.data_table.edit(index)

    def on_xsymbol_changed(self, text):
        self.data_table.setHorizontalHeaderItem(0, QTableWidgetItem(self.xsymbol.text()))

    def on_ysymbol_changed(self, text):
        self.data_table.setHorizontalHeaderItem(1, QTableWidgetItem(self.ysymbol.text()))

    def on_unit_or_name_changed(self, text):
        self.process_data()

    def on_data_changed(self, item):
        row = item.row()
        cols = self.data_table.columnCount()
        lrow = self.data_table.rowCount() - 1

        if row != lrow:
            if not any(self.data_table.item(row, i) and self.data_table.item(row, i).text() for i in range(cols)):
                with BlockQtSignals(self.data_table):
                    self.data_table.removeRow(row)
        else:
            if any(self.data_table.item(lrow, i) and self.data_table.item(lrow, i).text() for i in range(cols)):
                with BlockQtSignals(self.data_table):
                    self.data_table.insertRow(lrow + 1)

        self.process_data()

    def get_data(self):
        rows = self.data_table.rowCount() - 1
        x = (x and x.text() or 'nan' for x in (self.data_table.item(i, 0) for i in range(rows)))
        x = np.fromiter((float(x) for x in x), dtype=float)
        y = (y and y.text() or 'nan' for y in (self.data_table.item(i, 1) for i in range(rows)))
        y = np.fromiter((float(y) for y in y), dtype=float)

        return x, y

    def process_data(self, rows=None):
        self.figure.clear()

        x, y = self.get_data()

        if len(x) < 2:
            self.slope.setText("")
            self.intercept.setText("")
            return

        result = linregress(x, y)
        a, b, da, db = result.slope, result.intercept, result.stderr, result.intercept_stderr

        xu = self.xunit.text()
        yu = self.yunit.text()
        yu = f" {yu}" if yu else ""
        unit = f"{yu} / {xu}" if xu and yu else yu if yu else f" / {xu}" if xu else ""
        self.slope.setText(f"({a:.3f} ± {da:.3f}){unit}")
        self.intercept.setText(f"({b:.3f} ± {db:.3f}){yu}")

        ax = self.figure.add_subplot(111)
        ax.plot(x, y, "o")

        xx = np.array(ax.get_xlim())
        ax.plot(xx, a * xx + b)
        ax.set_xlim(xx)

        ax.set_xlabel(f"{self.xname.text() or f'${self.xsymbol.text()}$'} {f'[{xu}]' if xu else ''}")
        ax.set_ylabel(f"{self.yname.text() or f'${self.ysymbol.text()}$'} {f'[{yu.strip()}]' if yu else ''}")

        self.figure.tight_layout()
        self.figure.canvas.draw()

    def load(self):
        self.filename, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open File"),
            self.filename,
            self.tr("CSV Files (*.csv)"),
        )
        if not self.filename:
            return

        with open(self.filename, "r", newline="") as file:
            reader = csv.reader(file)
            header = next(reader)
            xheader, yheader = header
            xmatch = HEADER_RE.match(xheader)
            ymatch = HEADER_RE.match(yheader)
            if xmatch:
                self.xname.setText(xmatch.group("name") if xmatch.group("symbol") else "")
                self.xsymbol.setText(xmatch.group("symbol") or xmatch.group("name"))
                self.xunit.setText(xmatch.group("unit") or "")
            if ymatch:
                self.yname.setText(ymatch.group("name") if ymatch.group("symbol") else "")
                self.ysymbol.setText(ymatch.group("symbol") or ymatch.group("name"))
                self.yunit.setText(ymatch.group("unit") or "")

            data = list(reader)
            ld = len(data)
            self.data_table.setRowCount(ld + 1)
            with BlockQtSignals(self.data_table):
                for i, (xi, yi) in enumerate(data):
                    xitem = QTableWidgetItem(xi)
                    yitem = QTableWidgetItem(yi)
                    xitem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    yitem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.data_table.setItem(i, 0, xitem)
                    self.data_table.setItem(i, 1, yitem)
                self.data_table.setItem(ld, 0, QTableWidgetItem())
                self.data_table.setItem(ld, 1, QTableWidgetItem())

        self.process_data()

    @staticmethod
    def _make_header(name, symbol, unit):
        if not name:
            return f"{symbol} [{unit}]" if unit else f"{symbol}" if symbol else ""
        else:
            return f"{name} ({symbol}) [{unit}]" if unit else f"{name} ({symbol})" if symbol else name

    def save(self):
        self.filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save File"),
            self.filename,
            self.tr("CSV Files (*.csv)"),
        )
        if not self.filename:
            return

        with open(self.filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                self._make_header(self.xname.text(), self.xsymbol.text(), self.xunit.text()),
                self._make_header(self.yname.text(), self.ysymbol.text(), self.yunit.text())
            ])

            x, y = self.get_data()
            for xi, yi in zip(x, y):
                writer.writerow([xi, yi])
