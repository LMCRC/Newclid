import pytest
from geosolver.api import GeometricSolverBuilder
from geosolver.proof import DepCheckFailError


def test_construction_attempts_limit():
    """Construction should raise an error
    after failing a fixed number of attempts."""
    solver_builder = GeometricSolverBuilder().load_problem_from_txt(
        "a b c = triangle a b c ? perp a b a c"
    )
    max_attempts = 100
    with pytest.raises(DepCheckFailError, match=f"failed {max_attempts} times"):
        solver_builder.build()