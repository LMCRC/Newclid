# Some variables are there for better code reading.


# Naming in geometry is a little different
# we stick to geometry naming to better read the code.


import math
from typing import Optional, Union

from numpy.random import uniform as unif
from geosolver.numerical import ATOM, close_enough


import numpy as np


class Point:
    """Numerical point."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __lt__(self, other: "Point") -> bool:
        return (self.x, self.y) < (other.x, other.y)

    def __gt__(self, other: "Point") -> bool:
        return (self.x, self.y) > (other.x, other.y)

    def __add__(self, p: "Point") -> "Point":
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p: "Point") -> "Point":
        return Point(self.x - p.x, self.y - p.y)

    def __mul__(self, f: float) -> "Point":
        return Point(self.x * f, self.y * f)

    def __rmul__(self, f: float) -> "Point":
        return self * f

    def __truediv__(self, f: float) -> "Point":
        return Point(self.x / f, self.y / f)

    def __floordiv__(self, f: float) -> "Point":
        div = self / f  # true div
        return Point(int(div.x), int(div.y))

    def __str__(self) -> str:
        return "P({},{})".format(self.x, self.y)

    def close(self, point: "Point", tol: float = 1e-12) -> bool:
        return abs(self.x - point.x) < tol and abs(self.y - point.y) < tol

    def midpoint(self, p: "Point") -> "Point":
        return Point(0.5 * (self.x + p.x), 0.5 * (self.y + p.y))

    def distance(self, p: Union["Point", "Line", "Circle"]) -> float:
        if isinstance(p, Line):
            return p.distance(self)
        if isinstance(p, Circle):
            return abs(p.radius - self.distance(p.center))
        dx = self.x - p.x
        dy = self.y - p.y
        return np.sqrt(dx * dx + dy * dy)

    def distance2(self, p: "Point") -> float:
        if isinstance(p, Line):
            return p.distance(self)
        dx = self.x - p.x
        dy = self.y - p.y
        return dx * dx + dy * dy

    def rotatea(self, ang: float) -> "Point":
        sinb, cosb = np.sin(ang), np.cos(ang)
        return self.rotate(sinb, cosb)

    def rotate(self, sinb: float, cosb: float) -> "Point":
        x, y = self.x, self.y
        return Point(x * cosb - y * sinb, x * sinb + y * cosb)

    def flip(self) -> "Point":
        return Point(-self.x, self.y)

    def perpendicular_line(self, line: "Line") -> "Line":
        return line.perpendicular_line(self)

    def foot(self, line: "Line") -> "Point":
        if isinstance(line, Line):
            perpendicular_line = line.perpendicular_line(self)
            return line_line_intersection(perpendicular_line, line)
        elif isinstance(line, Circle):
            c, r = line.center, line.radius
            return c + (self - c) * r / self.distance(c)
        raise ValueError("Dropping foot to weird type {}".format(type(line)))

    def parallel_line(self, line: "Line") -> "Line":
        return line.parallel_line(self)

    def norm(self) -> float:
        return np.sqrt(self.x**2 + self.y**2)

    def cos(self, other: "Point") -> float:
        x, y = self.x, self.y
        a, b = other.x, other.y
        return (x * a + y * b) / self.norm() / other.norm()

    def dot(self, other: "Point") -> float:
        return self.x * other.x + self.y * other.y

    def sign(self, line: "Line") -> int:
        return line.sign(self)

    def is_same(self, other: "Point") -> bool:
        return self.distance(other) <= ATOM


class Line:
    """Numerical line."""

    def __init__(
        self,
        p1: "Point" = None,
        p2: "Point" = None,
        coefficients: tuple[int, int, int] = None,
    ):
        if p1 is None and p2 is None and coefficients is None:
            self.coefficients = None, None, None
            return

        a, b, c = coefficients or (
            p1.y - p2.y,
            p2.x - p1.x,
            p1.x * p2.y - p2.x * p1.y,
        )

        # Make sure a is always positive (or always negative for that matter)
        # With a == 0, Assuming a = +epsilon > 0
        # Then b such that ax + by = 0 with y>0 should be negative.
        if a < 0.0 or a == 0.0 and b > 0.0:
            a, b, c = -a, -b, -c

        self.coefficients = a, b, c

    def parallel_line(self, p: "Point") -> "Line":
        a, b, _ = self.coefficients
        return Line(coefficients=(a, b, -a * p.x - b * p.y))

    def perpendicular_line(self, p: "Point") -> "Line":
        a, b, _ = self.coefficients
        return Line(p, p + Point(a, b))

    def greater_than(self, other: "Line") -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        # b/a > y/x
        return b * x > a * y

    def __gt__(self, other: "Line") -> bool:
        return self.greater_than(other)

    def __lt__(self, other: "Line") -> bool:
        return other.greater_than(self)

    def same(self, other: "Line") -> bool:
        a, b, c = self.coefficients
        x, y, z = other.coefficients
        return close_enough(a * y, b * x) and close_enough(b * z, c * y)

    def equal(self, other: "Line") -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        # b/a == y/x
        return b * x == a * y

    def less_than(self, other: "Line") -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        # b/a > y/x
        return b * x < a * y

    def intersect(self, obj: Union["Line", "Circle"]) -> tuple[Point, ...]:
        if isinstance(obj, Line):
            return line_line_intersection(self, obj)
        if isinstance(obj, Circle):
            return line_circle_intersection(self, obj)

    def distance(self, p: "Point") -> float:
        a, b, c = self.coefficients
        return abs(self(p.x, p.y)) / math.sqrt(a * a + b * b)

    def __call__(self, x: "Point", y: "Point" = None) -> float:
        if isinstance(x, Point) and y is None:
            return self(x.x, x.y)
        a, b, c = self.coefficients
        return x * a + y * b + c

    def is_parallel(self, other: "Line") -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return abs(a * y - b * x) < ATOM

    def is_perp(self, other: "Line") -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return abs(a * x + b * y) < ATOM

    def cross(self, other: "Line") -> float:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return a * y - b * x

    def dot(self, other: "Line") -> float:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return a * x + b * y

    def point_at(self, x: float = None, y: float = None) -> Optional[Point]:
        """Get a point on line closest to (x, y)."""
        a, b, c = self.coefficients
        # ax + by + c = 0
        if x is None and y is not None:
            if a != 0:
                return Point((-c - b * y) / a, y)
            else:
                return None
        elif x is not None and y is None:
            if b != 0:
                return Point(x, (-c - a * x) / b)
            else:
                return None
        elif x is not None and y is not None:
            if a * x + b * y + c == 0.0:
                return Point(x, y)
        return None

    def diff_side(self, p1: "Point", p2: "Point") -> Optional[bool]:
        d1 = self(p1.x, p1.y)
        d2 = self(p2.x, p2.y)
        if d1 == 0 or d2 == 0:
            return None
        return d1 * d2 < 0

    def same_side(self, p1: "Point", p2: "Point") -> Optional[bool]:
        d1 = self(p1.x, p1.y)
        d2 = self(p2.x, p2.y)
        if d1 == 0 or d2 == 0:
            return None
        return d1 * d2 > 0

    def sign(self, point: "Point") -> int:
        s = self(point.x, point.y)
        if s > 0:
            return 1
        elif s < 0:
            return -1
        return 0

    def is_same(self, other: "Line") -> bool:
        a, b, c = self.coefficients
        x, y, z = other.coefficients
        return abs(a * y - b * x) <= ATOM and abs(b * z - c * y) <= ATOM

    def sample_within(self, points: list[Point], n: int = 5) -> list[Point]:
        """Sample a point within the boundary of points."""
        center = sum(points, Point(0.0, 0.0)) * (1.0 / len(points))
        radius = max([p.distance(center) for p in points])
        if close_enough(center.distance(self), radius):
            center = center.foot(self)
        a, b = line_circle_intersection(self, Circle(center.foot(self), radius))

        result = None
        best = -1.0
        for _ in range(n):
            rand = unif(0.0, 1.0)
            x = a + (b - a) * rand
            mind = min([x.distance(p) for p in points])
            if mind > best:
                best = mind
                result = x

        return [result]


class Circle:
    """Numerical circle."""

    def __init__(
        self,
        center: Optional[Point] = None,
        radius: Optional[float] = None,
        p1: Optional[Point] = None,
        p2: Optional[Point] = None,
        p3: Optional[Point] = None,
    ):
        if not center:
            if not (p1 and p2 and p3):
                self.center = self.radius = self.r2 = None
                return
                # raise ValueError('Circle without center need p1 p2 p3')

            l12 = _perpendicular_bisector(p1, p2)
            l23 = _perpendicular_bisector(p2, p3)
            center = line_line_intersection(l12, l23)

        self.center = center
        self.a, self.b = center.x, center.y

        if not radius:
            if not (p1 or p2 or p3):
                raise ValueError("Circle needs radius or p1 or p2 or p3")
            p = p1 or p2 or p3
            self.r2 = (self.a - p.x) ** 2 + (self.b - p.y) ** 2
            self.radius = math.sqrt(self.r2)
        else:
            self.radius = radius
            self.r2 = radius * radius

    def intersect(self, obj: Union["Line", "Circle"]) -> tuple[Point, ...]:
        if isinstance(obj, Line):
            return obj.intersect(self)
        if isinstance(obj, Circle):
            return circle_circle_intersection(self, obj)

    def sample_within(self, points: list[Point], n: int = 5) -> list[Point]:
        """Sample a point within the boundary of points."""
        result = None
        best = -1.0
        for _ in range(n):
            ang = unif(0.0, 2.0) * np.pi
            x = self.center + Point(np.cos(ang), np.sin(ang)) * self.radius
            mind = min([x.distance(p) for p in points])
            if mind > best:
                best = mind
                result = x

        return [result]


class HalfLine(Line):
    """Numerical ray."""

    def __init__(self, tail: "Point", head: "Point"):
        self.line = Line(tail, head)
        self.coefficients = self.line.coefficients
        self.tail = tail
        self.head = head

    def intersect(
        self, obj: Union["Line", "HalfLine", "Circle", "HoleCircle"]
    ) -> "Point":
        if isinstance(obj, (HalfLine, Line)):
            return line_line_intersection(self.line, obj)

        exclude = [self.tail]
        if isinstance(obj, HoleCircle):
            exclude += [obj.hole]

        a, b = line_circle_intersection(self.line, obj)
        if any([a.close(x) for x in exclude]):
            return b
        if any([b.close(x) for x in exclude]):
            return a

        v = self.head - self.tail
        va = a - self.tail
        vb = b - self.tail
        if v.dot(va) > 0:
            return a
        if v.dot(vb) > 0:
            return b
        raise InvalidLineIntersectError()

    def sample_within(self, points: list[Point], n: int = 5) -> list[Point]:
        center = sum(points, Point(0.0, 0.0)) * (1.0 / len(points))
        radius = max([p.distance(center) for p in points])
        if close_enough(center.distance(self.line), radius):
            center = center.foot(self)
        a, b = line_circle_intersection(self, Circle(center.foot(self), radius))

        if (a - self.tail).dot(self.head - self.tail) > 0:
            a, b = self.tail, a
        else:
            a, b = self.tail, b

        result = None
        best = -1.0
        for _ in range(n):
            x = a + (b - a) * unif(0.0, 1.0)
            mind = min([x.distance(p) for p in points])
            if mind > best:
                best = mind
                result = x

        return [result]


class HoleCircle(Circle):
    """Numerical circle with a missing point."""

    def __init__(self, center: "Point", radius: float, hole: "Point"):
        super().__init__(center, radius)
        self.hole = hole

    def intersect(
        self, obj: Union["Line", "HalfLine", "Circle", "HoleCircle"]
    ) -> "Point":
        if isinstance(obj, Line):
            a, b = line_circle_intersection(obj, self)
            if a.close(self.hole):
                return b
            return a
        if isinstance(obj, HalfLine):
            return obj.intersect(self)
        if isinstance(obj, Circle):
            a, b = circle_circle_intersection(obj, self)
            if a.close(self.hole):
                return b
            return a
        if isinstance(obj, HoleCircle):
            a, b = circle_circle_intersection(obj, self)
            if a.close(self.hole) or a.close(obj.hole):
                return b
            return a


def _perpendicular_bisector(p1: "Point", p2: "Point") -> "Line":
    midpoint = (p1 + p2) * 0.5
    return Line(midpoint, midpoint + Point(p2.y - p1.y, p1.x - p2.x))


class InvalidLineIntersectError(Exception):
    pass


class InvalidQuadSolveError(Exception):
    pass


def solve_quad(a: float, b: float, c: float) -> tuple[float, float]:
    """Solve a x^2 + bx + c = 0."""
    a = 2 * a
    d = b * b - 2 * a * c
    if d < 0:
        return None  # the caller should expect this result.

    y = math.sqrt(d)
    return (-b - y) / a, (-b + y) / a


def circle_circle_intersection(c1: Circle, c2: Circle) -> tuple[Point, Point]:
    """Returns a pair of Points as intersections of c1 and c2."""
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1
    x0, y0, r0 = c1.a, c1.b, c1.radius
    x1, y1, r1 = c2.a, c2.b, c2.radius

    d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    if d == 0:
        raise InvalidQuadSolveError()

    a = (r0**2 - r1**2 + d**2) / (2 * d)
    h = r0**2 - a**2
    if h < 0:
        raise InvalidQuadSolveError()
    h = np.sqrt(h)
    x2 = x0 + a * (x1 - x0) / d
    y2 = y0 + a * (y1 - y0) / d
    x3 = x2 + h * (y1 - y0) / d
    y3 = y2 - h * (x1 - x0) / d
    x4 = x2 - h * (y1 - y0) / d
    y4 = y2 + h * (x1 - x0) / d

    return Point(x3, y3), Point(x4, y4)


def line_circle_intersection(line: Line, circle: Circle) -> tuple[Point, Point]:
    """Returns a pair of points as intersections of line and circle."""
    a, b, c = line.coefficients
    r = float(circle.radius)
    center = circle.center
    p, q = center.x, center.y

    if b == 0:
        x = -c / a
        x_p = x - p
        x_p2 = x_p * x_p
        y = solve_quad(1, -2 * q, q * q + x_p2 - r * r)
        if y is None:
            raise InvalidQuadSolveError()
        y1, y2 = y
        return (Point(x, y1), Point(x, y2))

    if a == 0:
        y = -c / b
        y_q = y - q
        y_q2 = y_q * y_q
        x = solve_quad(1, -2 * p, p * p + y_q2 - r * r)
        if x is None:
            raise InvalidQuadSolveError()
        x1, x2 = x
        return (Point(x1, y), Point(x2, y))

    c_ap = c + a * p
    a2 = a * a
    y = solve_quad(
        a2 + b * b, 2 * (b * c_ap - a2 * q), c_ap * c_ap + a2 * (q * q - r * r)
    )
    if y is None:
        raise InvalidQuadSolveError()
    y1, y2 = y

    return Point(-(b * y1 + c) / a, y1), Point(-(b * y2 + c) / a, y2)


def _check_between(a: Point, b: Point, c: Point) -> bool:
    """Whether a is between b & c."""
    return (a - b).dot(c - b) > 0 and (a - c).dot(b - c) > 0


def circle_segment_intersect(circle: Circle, p1: Point, p2: Point) -> list[Point]:
    line = Line(p1, p2)
    px, py = line_circle_intersection(line, circle)

    result = []
    if _check_between(px, p1, p2):
        result.append(px)
    if _check_between(py, p1, p2):
        result.append(py)
    return result


def line_segment_intersection(line: Line, A: Point, B: Point) -> Point:
    a, b, c = line.coefficients
    x1, y1, x2, y2 = A.x, A.y, B.x, B.y
    dx, dy = x2 - x1, y2 - y1
    alpha = (-c - a * x1 - b * y1) / (a * dx + b * dy)
    return Point(x1 + alpha * dx, y1 + alpha * dy)


def line_line_intersection(line_1: Line, line_2: Line) -> Point:
    a1, b1, c1 = line_1.coefficients
    a2, b2, c2 = line_2.coefficients
    # a1x + b1y + c1 = 0
    # a2x + b2y + c2 = 0
    d = a1 * b2 - a2 * b1
    if d == 0:
        raise InvalidLineIntersectError
    return Point((c2 * b1 - c1 * b2) / d, (c1 * a2 - c2 * a1) / d)


def bring_together(
    a: Point, b: Point, c: Point, d: Point
) -> tuple[Point, Point, Point, Point]:
    ab = Line(a, b)
    cd = Line(c, d)
    x = line_line_intersection(ab, cd)
    unit = Circle(center=x, radius=1.0)
    y, _ = line_circle_intersection(ab, unit)
    z, _ = line_circle_intersection(cd, unit)
    return x, y, x, z


def reduce(
    objs: list[Union[Point, Line, Circle, HalfLine, HoleCircle]],
    existing_points: list[Point],
) -> list[Point]:
    """Reduce intersecting objects into one point of intersections."""
    if all(isinstance(o, Point) for o in objs):
        return objs

    elif len(objs) == 1:
        return objs[0].sample_within(existing_points)

    elif len(objs) == 2:
        a, b = objs
        result = a.intersect(b)
        if isinstance(result, Point):
            return [result]
        a, b = result
        a_close = any([a.close(x) for x in existing_points])
        if a_close:
            return [b]
        b_close = any([b.close(x) for x in existing_points])
        if b_close:
            return [a]
        return [np.random.choice([a, b])]

    else:
        raise ValueError(f"Cannot reduce {objs}")