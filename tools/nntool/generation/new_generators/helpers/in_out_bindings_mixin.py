# Copyright (C) 2021  GreenWaves Technologies, SAS

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

from generation.bindings import CommentBindingList, GNodeArgEdge, GNodeArgNode, NodeBindingList


class InOutBindingsMixin():
    @classmethod
    def set_in_out_bindings(cls, gen, in_eparams, out_eparams, cname, node, node_q, out_q=None):
        if out_q is None:
            out_q = node_q
        gen.bindings.append(
            CommentBindingList("Node {} inq {} outq {}", node.name,
                            str(node_q.in_qs[0]), str(out_q.out_qs[0]))
        )
        gen.bindings.append(
            NodeBindingList(cname, GNodeArgEdge(in_eparams[0]),
                            GNodeArgEdge(out_eparams[0], "GNA_OUT")))

    @classmethod
    def set_in_out_infos_bindings(cls, gen, in_eparams, out_eparams, cname, node, node_q, out_q=None):
        if out_q is None:
            out_q = node_q
        gen.bindings.append(
            CommentBindingList("Node {} inq {} outq {}", node.name,
                            str(node_q.in_qs[0]), str(out_q.out_qs[0]))
        )
        gen.bindings.append(
            NodeBindingList(cname, GNodeArgEdge(in_eparams[0]),
                            GNodeArgEdge(out_eparams[0], "GNA_OUT"), GNodeArgNode(node, "infos")))

    @classmethod
    def set_multi_in_out_bindings(cls, gen, in_eparams, out_eparams, cname, node, qrec):
        gen.bindings.append(
            CommentBindingList("Node {} in_qs [{}] out_qs [{}]", node.name,
                            ",".join(str(in_q) for in_q in qrec.in_qs),
                            ",".join(str(out_q) for out_q in qrec.out_qs))
        )

        # the input order of the generated function can vary since it passes through a set
        params = [GNodeArgEdge(in_eparams[idx]) for idx in node.input_shuffle] + \
            [GNodeArgEdge(out_eparams[idx], "GNA_OUT") for idx in node.output_shuffle]
        gen.bindings.append(
            NodeBindingList(cname, *params)
        )