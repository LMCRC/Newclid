from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from geosolver.predicates import NAME_TO_PREDICATE
from geosolver.dependency.dependency import Dependency

if TYPE_CHECKING:
    from geosolver.predicates.predicate import Predicate
    from geosolver.dependency.dependency_graph import DependencyGraph


class Statement:
    """One predicate applied to a set of points and values. Comes with a proof that args are well ordered"""

    def __init__(
        self,
        predicate: type[Predicate],
        args: tuple[str, ...],
        dep_graph: DependencyGraph,
    ) -> None:
        self.predicate = predicate
        self.args: tuple[Any, ...] = self.predicate.parse(args, dep_graph)
        self.dep_graph = dep_graph
        self.why_cache: Optional[Dependency] = None

    def check(self) -> bool:
        """Symbolically check if the statement is currently considered True."""
        if self in self.dep_graph.hyper_graph:
            return True
        if not self.predicate.check_numerical(self):
            return False
        if self.predicate.check(self):
            self.dep_graph.hyper_graph[self] = set()
            return True
        return False

    def check_numerical(self) -> bool:
        """Check if the statement is numerically sound."""
        return self.predicate.check_numerical(self)

    def why(self) -> Optional[Dependency]:
        if self.why_cache is None:
            self.why_cache = self.predicate.why(self)
        return self.why_cache

    def __repr__(self) -> str:
        return self.predicate.to_repr(self)

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, Statement) and hash(self) == hash(obj)

    @classmethod
    def from_tokens(
        cls, tokens: tuple[str, ...], dep_graph: DependencyGraph
    ) -> Statement:
        return Statement(NAME_TO_PREDICATE[tokens[0]], tuple(tokens[1:]), dep_graph)

    def pretty(self) -> str:
        return self.predicate.pretty(self)

    def with_new(
        self,
        new_predicate: Optional[type[Predicate]],
        new_args: Optional[tuple[Any, ...]],
    ):
        predicate = new_predicate or self.predicate
        args = new_args or self.args
        return self.from_tokens(
            (predicate.NAME,) + predicate.to_tokens(args), self.dep_graph
        )