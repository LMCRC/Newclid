# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Unit tests for graph.py."""
import pytest
import pytest_check as check

from geosolver.proof_graph import ProofGraph
from geosolver.numericals import (
    check_circle,
    check_coll,
    check_cong,
    check_cyclic,
    check_eqangle,
    check_eqratio,
    check_midp,
    check_para,
    check_perp,
)
from geosolver.problem import Definition, Problem, Theorem


MAX_LEVEL = 10


class TestProofGraph:
    @pytest.fixture(autouse=True)
    def setUpClass(self):
        self.defs = Definition.from_txt_file("defs.txt", to_dict=True)
        self.rules = Theorem.from_txt_file("rules.txt", to_dict=True)

        # load a complex setup:
        txt = "a b c = triangle a b c; h = orthocenter a b c; h1 = foot a b c; h2 = foot b c a; h3 = foot c a b; g1 g2 g3 g = centroid g1 g2 g3 g a b c; o = circle a b c ? coll h g o"
        p = Problem.from_txt(txt, translate=False)
        self.graph, _ = ProofGraph.build_problem(p, self.defs)

    def test_build_graph_points(self):
        g = self.graph

        all_points = g.all_points()
        check.equal(
            {p.name for p in all_points},
            {"a", "b", "c", "g", "h", "o", "g1", "g2", "g3", "h1", "h2", "h3"},
        )

    def test_build_graph_predicates(self):
        gr = self.graph

        a, b, c, g, h, o, g1, g2, g3, h1, h2, h3 = gr.names2points(
            ["a", "b", "c", "g", "h", "o", "g1", "g2", "g3", "h1", "h2", "h3"]
        )

        # Explicit statements:
        check.is_true(gr.check_cong([b, g1, g1, c]))
        check.is_true(gr.check_cong([c, g2, g2, a]))
        check.is_true(gr.check_cong([a, g3, g3, b]))
        check.is_true(gr.check_perp([a, h1, b, c]))
        check.is_true(gr.check_perp([b, h2, c, a]))
        check.is_true(gr.check_perp([c, h3, a, b]))
        check.is_true(gr.check_cong([o, a, o, b]))
        check.is_true(gr.check_cong([o, b, o, c]))
        check.is_true(gr.check_cong([o, a, o, c]))
        check.is_true(gr.check_coll([a, g, g1]))
        check.is_true(gr.check_coll([b, g, g2]))
        check.is_true(gr.check_coll([g1, b, c]))
        check.is_true(gr.check_coll([g2, c, a]))
        check.is_true(gr.check_coll([g3, a, b]))
        check.is_true(gr.check_perp([a, h, b, c]))
        check.is_true(gr.check_perp([b, h, c, a]))

        # These are NOT part of the premises:
        check.is_false(gr.check_perp([c, h, a, b]))
        check.is_false(gr.check_coll([c, g, g3]))

        # These are automatically inferred by the graph datastructure:
        check.is_true(gr.check_eqangle([a, h1, b, c, b, h2, c, a]))
        check.is_true(gr.check_eqangle([a, h1, b, h2, b, c, c, a]))
        check.is_true(gr.check_eqratio([b, g1, g1, c, c, g2, g2, a]))
        check.is_true(gr.check_eqratio([b, g1, g1, c, o, a, o, b]))
        check.is_true(gr.check_para([a, h, a, h1]))
        check.is_true(gr.check_para([b, h, b, h2]))
        check.is_true(gr.check_coll([a, h, h1]))
        check.is_true(gr.check_coll([b, h, h2]))

    def test_enumerate_colls(self):
        g = self.graph

        for a, b, c in g.all_colls():
            check.is_true(g.check_coll([a, b, c]))
            check.is_true(check_coll([a.num, b.num, c.num]))

    def test_enumerate_paras(self):
        g = self.graph

        for a, b, c, d in g.all_paras():
            check.is_true(g.check_para([a, b, c, d]))
            check.is_true(check_para([a.num, b.num, c.num, d.num]))

    def test_enumerate_perps(self):
        g = self.graph

        for a, b, c, d in g.all_perps():
            check.is_true(g.check_perp([a, b, c, d]))
            check.is_true(check_perp([a.num, b.num, c.num, d.num]))

    def test_enumerate_congs(self):
        g = self.graph

        for a, b, c, d in g.all_congs():
            check.is_true(g.check_cong([a, b, c, d]))
            check.is_true(check_cong([a.num, b.num, c.num, d.num]))

    def test_enumerate_eqangles(self):
        g = self.graph

        for a, b, c, d, x, y, z, t in g.all_eqangles_8points():
            check.is_true(g.check_eqangle([a, b, c, d, x, y, z, t]))
            check.is_true(
                check_eqangle([a.num, b.num, c.num, d.num, x.num, y.num, z.num, t.num])
            )

    def test_enumerate_eqratios(self):
        g = self.graph

        for a, b, c, d, x, y, z, t in g.all_eqratios_8points():
            check.is_true(g.check_eqratio([a, b, c, d, x, y, z, t]))
            check.is_true(
                check_eqratio([a.num, b.num, c.num, d.num, x.num, y.num, z.num, t.num])
            )

    def test_enumerate_cyclics(self):
        g = self.graph

        for a, b, c, d, x, y, z, t in g.all_cyclics():
            check.is_true(g.check_cyclic([a, b, c, d, x, y, z, t]))
            check.is_true(check_cyclic([a.num, b.num, c.num, d.num]))

    def test_enumerate_midps(self):
        g = self.graph

        for a, b, c in g.all_midps():
            check.is_true(g.check_midp([a, b, c]))
            check.is_true(check_midp([a.num, b.num, c.num]))

    def test_enumerate_circles(self):
        g = self.graph

        for a, b, c, d in g.all_circles():
            check.is_true(g.check_circle([a, b, c, d]))
            check.is_true(check_circle([a.num, b.num, c.num, d.num]))