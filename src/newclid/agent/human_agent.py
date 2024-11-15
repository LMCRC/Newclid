"""Classical Breadth-First Search based agents."""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional

from newclid import webapp
from newclid.agent.agents_interface import (
    DeductiveAgent,
)
from newclid.agent.breadth_first_search import BFSDDAR
from newclid.formulations.clause import Clause
from newclid.proof import ProofState
from newclid.formulations.rule import Rule

from newclid.statement import Statement
from newclid.tools import atomize, run_static_server

if TYPE_CHECKING:
    ...


class NamedFunction(NamedTuple):
    name: str
    f: Callable[..., Any]


class HumanAgent(DeductiveAgent):
    def __init__(self, proof: ProofState, rules: list[Rule]):
        self.proof = proof
        self.rules = rules
        self.match_rules = [
            NamedFunction(
                f"match {theorem.descrption}: {theorem}", self.fn_match(theorem)
            )
            for theorem in rules
        ]
        self.bfsddar: Optional[BFSDDAR] = None
        self.server: Optional[Path] = None

    def pull_to_server(self):
        assert self.proof.problem_path
        if not self.server:
            self.server = self.proof.problem_path / "html"
            self.pull_to_server()
            run_static_server(self.server)
        else:
            webapp.pull_to_server(self.proof, server_path=self.server)

    @classmethod
    def select(
        cls,
        options: list[NamedFunction],
        apply_all: bool = False,
        apply_none: bool = False,
    ) -> Any:
        for i, option in enumerate(options):
            print(f"[{i}] {option.name}")
        if apply_all:
            print("[all]")
        if apply_none:
            print("[none]")
        choice = input("Choose:")
        if choice == "all":
            for option in options:
                option.f()
        elif choice == "none":
            return
        else:
            n = int(choice)
            return options[n].f()

    def fn_match(self, rule: Rule):
        def fn():
            deps = self.proof.match_theorem(rule)
            self.select(
                [
                    NamedFunction(
                        f"{', '.join(s.pretty() for s in dep.why)} => {dep.statement.pretty()}",
                        lambda dep=dep: self.proof.apply_dep(dep),
                    )
                    for dep in deps
                ],
                apply_all=True,
                apply_none=True,
            )

        return fn

    def match(self) -> bool:
        self.select(self.match_rules, apply_none=True)
        return True

    def update_server(self) -> bool:
        self.pull_to_server()
        return True

    def add_construction(self) -> bool:
        clauses = Clause.parse_line(input("New construction: "))
        for clause in clauses:
            self.proof.add_construction(clause)
        return True

    def exhaust_with_bfsddar(self) -> bool:
        self.bfsddar = BFSDDAR(self.proof, self.rules)
        return True

    def check(self) -> bool:
        statement = Statement.from_tokens(
            atomize(input("Check: ")), self.proof.dep_graph
        )
        if statement is None:
            print("Statement not parsed")
        else:
            print(f"Check result of {statement.pretty()}: {statement.check()}")
        return True

    def check_goals(self) -> bool:
        selects: list[NamedFunction] = []
        for goal in self.proof.goals:
            selects.append(
                NamedFunction(
                    f"check {goal.pretty()}",
                    lambda: print(f"Check result of {goal.pretty()}: {goal.check()}"),
                )
            )
        self.select(selects, apply_all=True, apply_none=True)
        return True

    def step(self) -> bool:
        res = True
        if self.bfsddar:
            if not self.bfsddar.step():
                self.bfsddar = None
        else:
            print("Premises:")
            for dep in self.proof.dep_graph.premises():
                print(f"{dep.statement.pretty()}")
            res = self.select(
                [
                    NamedFunction("match", self.match),
                    NamedFunction("update server", self.update_server),
                    NamedFunction("construction", self.add_construction),
                    NamedFunction("exhaust with bfsddar", self.exhaust_with_bfsddar),
                    NamedFunction("check statement", self.check),
                    NamedFunction("check goals", self.check_goals),
                    NamedFunction("nothing", lambda: True),
                    NamedFunction("stop", lambda: False),
                ]
            )
            if not res:
                for goal in self.proof.goals:
                    print(f"{goal.pretty()} proven? {goal.check()}")
        if self.proof.check_goals():
            print("All the goals are proven")
        return res
