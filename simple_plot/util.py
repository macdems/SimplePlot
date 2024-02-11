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


class BlockQtSignals:
    """
        Helper class to temporary block signals emitted by qt objects, usage::

            with BlockQtSignals(obj1, obj2, ...):
                # after with signals are reverted
    """

    def __init__(self, *objects):
        super().__init__()
        self.objects = objects
        self.signals_blocked_state = tuple(o.blockSignals(True) for o in self.objects)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
            Revert objects blockSignals values.
        """
        for obj, val in zip(self.objects, self.signals_blocked_state):
            obj.blockSignals(val)
