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

from PyQt5.QtCore import QLibraryInfo, QLocale, QTranslator
from PyQt5.QtWidgets import QApplication

from .mainwindow import MainWindow


def main(argv):
    app = QApplication(argv)

    # Configure Qt translations
    locale = QLocale.system()
    translator = QTranslator()
    translator.load(locale, 'qtbase', '_', QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    translator.load(locale, 'simpleplot', '_', ":/translations")
    app.installTranslator(translator)

    main_window = MainWindow()
    main_window.show()

    return app.exec()
