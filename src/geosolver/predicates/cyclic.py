from __future__ import annotations
from typing import TYPE_CHECKING, Any
from geosolver.dependency.dependency import Dependency
from geosolver.dependency.dependency_graph import DependencyGraph
from geosolver.dependency.symbols import Circle, Point
from geosolver.numerical import close_enough
from geosolver.numerical.geometries import CircleNum, InvalidIntersectError
from geosolver.predicates.predicate import IllegalPredicate, Predicate


if TYPE_CHECKING:
    from geosolver.dependency.dependency_graph import DependencyGraph
    from geosolver.statement import Statement


class Cyclic(Predicate):
    """cyclic A B C D -
    Represent that 4 (or more) points lie on the same circle."""

    NAME = "cyclic"

    @classmethod
    def parse(
        cls, args: tuple[str, ...], dep_graph: DependencyGraph
    ) -> tuple[Any, ...]:
        if len(args) <= 3 or len(args) != len(set(args)):
            raise IllegalPredicate
        return tuple(dep_graph.symbols_graph.names2points(sorted(args)))

    @classmethod
    def check_numerical(cls, statement: Statement) -> bool:
        points: tuple[Point, ...] = statement.args
        try:
            circle = CircleNum(p1=points[0].num, p2=points[1].num, p3=points[2].num)
        except InvalidIntersectError:
            return False

        return all(
            close_enough(circle.radius, circle.center.distance(p.num))
            for p in points[3:]
        )

    @classmethod
    def check(cls, statement: Statement) -> bool:
        return Circle.check_cyclic(statement.args)

    @classmethod
    def add(cls, dep: Dependency):
        Circle.make_cyclic(dep.statement.args, dep)

    @classmethod
    def why(cls, statement: Statement) -> Dependency:
        return Circle.why_cyclic(statement)

    @classmethod
    def to_repr(cls, statement: Statement) -> str:
        return f"cyc({''.join(repr(p) for p in statement.args)})"

    @classmethod
    def to_tokens(cls, args: tuple[Any, ...]) -> tuple[str, ...]:
        return tuple(p.name for p in args)