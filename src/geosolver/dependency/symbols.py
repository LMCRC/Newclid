"""Implements geometric objects used in the graph representation."""

from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING, Optional, Self, TypeVar

from geosolver.dependency.dependency import CONSTRUCTION, Dependency
from geosolver.numerical.geometries import CircleNum, LineNum, PointNum

if TYPE_CHECKING:
    from geosolver.statement import Statement
    from geosolver.dependency.symbols_graph import SymbolsGraph
    from geosolver.dependency.dependency import Dependency

S = TypeVar("S", bound="Symbol")


class Symbol(ABC):
    r"""Symbol in the symbols graph.

    Can be Point, Line, Circle, etc.

    Each node maintains a merge history to
    other nodes if they are (found out to be) equivalent

    ::
        a -> b -
                \
            c -> d -> e -> f -> g


    d.merged_to = e
    d.rep = g
    d.merged_from = {a, b, c, d}
    d.equivs = {a, b, c, d, e, f, g}
    d.members = {a, b, c, d}

    """

    def __init__(
        self, name: str, symbols_graph: "SymbolsGraph", dep: Optional[Dependency]
    ):
        self.name = name
        self.symbols_graph = symbols_graph
        self.dep = dep
        self.fellows: list[Self] = []
        self._rep: Self = self

    def rep(self) -> Self:
        if self._rep != self:
            self._rep = self._rep.rep()
        return self._rep

    def _merge_one(self, node: Self, dep: Dependency) -> Self:
        selfrep = self.rep()
        noderep = node.rep()
        if selfrep == noderep:
            return selfrep
        noderep._rep = selfrep

        selfrep.fellows.append(noderep)
        return selfrep

    def _merge(self, nodes: list[Self], dep: Dependency) -> Self:
        for node in nodes:
            self._merge_one(node, dep)
        return self.rep()

    def __repr__(self) -> str:
        return self.name


class Point(Symbol):
    num: PointNum


class Line(Symbol):
    """Symbol of type Line."""

    points: set[Point]
    num: LineNum

    @classmethod
    def check_coll(cls, points: list[Point] | tuple[Point]) -> bool:
        symbols_graph = points[0].symbols_graph
        s = set(points)
        for line in symbols_graph.nodes_of_type(Line):
            if s <= line.points:
                return True
        return False

    @classmethod
    def make_coll(
        cls, points: list[Point] | tuple[Point], dep: Dependency
    ) -> tuple[Line, list[Line]]:
        symbols_graph = points[0].symbols_graph
        s = set(points)
        merge: list[Line] = []
        for line in symbols_graph.nodes_of_type(Line):
            if s <= line.points:
                return line, []
            if len(s & line.points) >= 2:
                merge.append(line)
                s.update(line.points)
        line = symbols_graph.new_node(
            Line, f"line/{'-'.join(p.name for p in points)}/", dep
        )
        line.points = s
        symbols_graph.merge(line, merge, dep)
        return line, merge

    @classmethod
    def why_coll(cls, statement: Statement) -> Dependency:
        points: tuple[Point, ...] = statement.args
        symbols_graph = points[0].symbols_graph
        s = set(points)
        for line in symbols_graph.nodes_of_type(Line):
            if s <= line.points:
                target = line
                for _target in line.fellows:
                    if s <= _target.points and len(_target.points) < len(target.points):
                        target = _target
                if target.dep:
                    return target.dep.with_new(statement)
                else:
                    return Dependency.mk(statement, CONSTRUCTION, ())
        raise Exception("why_coll failed")


class Circle(Symbol):
    """Symbol of type Circle."""

    points: set[Point]
    num: CircleNum

    @classmethod
    def check_cyclic(cls, points: list[Point] | tuple[Point]) -> bool:
        symbols_graph = points[0].symbols_graph
        s = set(points)
        for c in symbols_graph.nodes_of_type(Circle):
            if s <= c.points:
                return True
        return False

    @classmethod
    def make_cyclic(cls, points: list[Point] | tuple[Point], dep: Dependency):
        symbols_graph = points[0].symbols_graph
        s = set(points)
        merge: list[Circle] = []
        for c in symbols_graph.nodes_of_type(Circle):
            if s <= c.points:
                return
            if len(s & c.points) >= 3:
                merge.append(c)
                s.update(c.points)
        c = symbols_graph.new_node(
            Circle, f"circle({''.join(p.name for p in points)})", dep
        )
        c.points = s
        symbols_graph.merge(c, merge, dep)

    @classmethod
    def why_cyclic(cls, statement: Statement) -> Dependency:
        points: tuple[Point, ...] = statement.args
        symbols_graph = points[0].symbols_graph
        s = set(points)
        for line in symbols_graph.nodes_of_type(Circle):
            if s <= line.points:
                target = line
                for _target in line.fellows:
                    if s <= _target.points and len(_target.points) < len(target.points):
                        target = _target
                if target.dep:
                    return target.dep.with_new(statement)
                else:
                    return Dependency.mk(statement, CONSTRUCTION, ())
        raise Exception("why_concyclic failed")