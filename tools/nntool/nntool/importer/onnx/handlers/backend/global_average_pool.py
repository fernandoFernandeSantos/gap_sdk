# Copyright (C) 2020  GreenWaves Technologies, SAS

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..backend_handler import BackendHandler
from ..handler import onnx_op

from .global_pool_mixin import GlobalPoolMixin

@onnx_op("GlobalAveragePool")
class GlobalAveragePool(GlobalPoolMixin, BackendHandler):

    @classmethod
    def version_1(cls, node, **kwargs):
        return cls._common(node, pool_type="average", **kwargs)