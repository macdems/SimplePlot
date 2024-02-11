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
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .mainwindow_ui import Ui_MainWindow
from .numerics import linear_fit
from .util import BlockQtSignals


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
        self.setupUi(self)
        self.connectSignals()

        self.retranslateUi(self)

        self.data_table.setItemDelegate(FloatDelegate(self))
        dataitem = QTableWidgetItem()
        dataitem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.data_table.setItemPrototype(dataitem)

        symbol_regex = QRegExp(r'[a-zA-Z_]\w*')
        self.xsymbol.setValidator(QRegExpValidator(symbol_regex, self))
        self.ysymbol.setValidator(QRegExpValidator(symbol_regex, self))

        self.add_plot()

        self.process_data()

    def connectSignals(self):
        self.xsymbol.textChanged.connect(self.on_xsymbol_changed)
        self.ysymbol.textChanged.connect(self.on_ysymbol_changed)
        self.xunit.textChanged.connect(self.on_unit_or_name_changed)
        self.yunit.textChanged.connect(self.on_unit_or_name_changed)
        self.xname.textChanged.connect(self.on_unit_or_name_changed)
        self.yname.textChanged.connect(self.on_unit_or_name_changed)
        self.data_table.itemChanged.connect(self.on_data_changed)

    def add_plot(self):
        self.figure = Figure(figsize=(5, 3))
        static_canvas = FigureCanvas(self.figure)
        self.plot_layout.addWidget(NavigationToolbar(static_canvas, self))
        self.plot_layout.addWidget(static_canvas)

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
        x = np.fromiter((x and x.text() and float(x.text()) or np.nan for x in (self.data_table.item(i, 0) for i in range(rows))),
                        dtype=float)
        y = np.fromiter((y and y.text() and float(y.text()) or np.nan for y in (self.data_table.item(i, 1) for i in range(rows))),
                        dtype=float)

        return x, y

    def process_data(self, rows=None):
        self.figure.clear()

        x, y = self.get_data()

        if len(x) < 2:
            self.slope.setText('')
            self.intercept.setText('')
            return

        a, b, da, db = linear_fit(x, y)

        xu = self.xunit.text()
        yu = self.yunit.text()
        unit = f" {yu} / {xu}" if xu and yu else f" {yu}" if yu else f" / {xu}" if xu else ""
        self.slope.setText(f"({a:.3f} ± {da:.3f}){unit}")
        self.intercept.setText(f"({b:.3f} ± {db:.3f}){f' {yu}' if yu else ''}")

        ax = self.figure.add_subplot(111)
        ax.plot(x, y, 'o')

        xx = np.array(ax.get_xlim())
        ax.plot(xx, a * xx + b)
        ax.set_xlim(xx)

        ax.set_xlabel(f"{self.xname.text()} {f'[{xu}]' if xu else ''}")
        ax.set_ylabel(f"{self.yname.text()} {f'[{yu}]' if yu else ''}")

        self.figure.tight_layout()
        self.figure.canvas.draw()
