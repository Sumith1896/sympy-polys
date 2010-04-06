"""Tests for the implementation of RootOf class and related tools. """

from sympy.polys.polytools import Poly

from sympy.polys.rootoftools import RootOf

from sympy.polys.polyerrors import (
    GeneratorsNeeded,
    PolynomialError,
    DomainError,
)

from sympy import raises, sqrt, I, Rational, Real

from sympy.abc import x, y

def test_RootOf___new__():
    assert RootOf(x, 0) == 0
    assert RootOf(x,-1) == 0

    assert RootOf(x - 1, 0) == 1
    assert RootOf(x - 1,-1) == 1

    assert RootOf(x + 1, 0) ==-1
    assert RootOf(x + 1,-1) ==-1

    assert RootOf(x**2 + 2*x + 3, 0) == -1 + I*sqrt(2)
    assert RootOf(x**2 + 2*x + 3, 1) == -1 - I*sqrt(2)
    assert RootOf(x**2 + 2*x + 3,-1) == -1 - I*sqrt(2)
    assert RootOf(x**2 + 2*x + 3,-2) == -1 + I*sqrt(2)

    r = RootOf(x**2 + 2*x + 3, 0, radicals=False)
    assert isinstance(r, RootOf) == True

    r = RootOf(x**2 + 2*x + 3, 1, radicals=False)
    assert isinstance(r, RootOf) == True

    r = RootOf(x**2 + 2*x + 3,-1, radicals=False)
    assert isinstance(r, RootOf) == True

    r = RootOf(x**2 + 2*x + 3,-2, radicals=False)
    assert isinstance(r, RootOf) == True

    assert RootOf((x - 1)*(x + 1), 0, radicals=False) ==-1
    assert RootOf((x - 1)*(x + 1), 1, radicals=False) == 1
    assert RootOf((x - 1)*(x + 1),-1, radicals=False) == 1
    assert RootOf((x - 1)*(x + 1),-2, radicals=False) ==-1

    assert RootOf((x - 1)*(x + 1), 0, radicals=True) ==-1
    assert RootOf((x - 1)*(x + 1), 1, radicals=True) == 1
    assert RootOf((x - 1)*(x + 1),-1, radicals=True) == 1
    assert RootOf((x - 1)*(x + 1),-2, radicals=True) ==-1

    assert RootOf((x - 1)*(x**3 + x + 3), 0) == RootOf(x**3 + x + 3, 0)
    assert RootOf((x - 1)*(x**3 + x + 3), 1) == 1
    assert RootOf((x - 1)*(x**3 + x + 3), 2) == RootOf(x**3 + x + 3, 1)
    assert RootOf((x - 1)*(x**3 + x + 3), 3) == RootOf(x**3 + x + 3, 2)
    assert RootOf((x - 1)*(x**3 + x + 3),-1) == RootOf(x**3 + x + 3, 2)
    assert RootOf((x - 1)*(x**3 + x + 3),-2) == RootOf(x**3 + x + 3, 1)
    assert RootOf((x - 1)*(x**3 + x + 3),-3) == 1
    assert RootOf((x - 1)*(x**3 + x + 3),-4) == RootOf(x**3 + x + 3, 0)

    assert RootOf(x**4 + 3*x**3, 0) ==-3
    assert RootOf(x**4 + 3*x**3, 1) == 0
    assert RootOf(x**4 + 3*x**3, 2) == 0
    assert RootOf(x**4 + 3*x**3, 3) == 0

    raises(GeneratorsNeeded, "RootOf(0, 0)")
    raises(GeneratorsNeeded, "RootOf(1, 0)")

    raises(PolynomialError, "RootOf(x - y, 0)")

    raises(DomainError, "RootOf(x**3 - x + sqrt(2), 0)")
    raises(DomainError, "RootOf(x**3 - x + I, 0)")

    raises(IndexError, "RootOf(x**2 - 1,-4)")
    raises(IndexError, "RootOf(x**2 - 1,-3)")
    raises(IndexError, "RootOf(x**2 - 1, 2)")
    raises(IndexError, "RootOf(x**2 - 1, 3)")

    assert RootOf(Poly(x - y, x), 0) == y

    assert RootOf(Poly(x**2 - y, x), 0) == +sqrt(y)
    assert RootOf(Poly(x**2 - y, x), 1) == -sqrt(y)

    assert RootOf(Poly(x**3 - y, x), 0) == y**Rational(1,3)

    raises(DomainError, "RootOf(Poly(x**3 + x - y, x), 0)")

def test_RootOf___eq__():
    assert (RootOf(x**3 + x + 3, 0) == RootOf(x**3 + x + 3, 0)) == True
    assert (RootOf(x**3 + x + 3, 0) == RootOf(x**3 + x + 3, 1)) == False
    assert (RootOf(x**3 + x + 3, 1) == RootOf(x**3 + x + 3, 1)) == True
    assert (RootOf(x**3 + x + 3, 1) == RootOf(x**3 + x + 3, 2)) == False
    assert (RootOf(x**3 + x + 3, 2) == RootOf(x**3 + x + 3, 2)) == True

def test_RootOf_is_real():
    assert RootOf(x**3 + x + 3, 0).is_real == True
    assert RootOf(x**3 + x + 3, 1).is_real == False
    assert RootOf(x**3 + x + 3, 2).is_real == False

def test_RootOf_is_complex():
    assert RootOf(x**3 + x + 3, 0).is_complex == False
    assert RootOf(x**3 + x + 3, 1).is_complex == True
    assert RootOf(x**3 + x + 3, 2).is_complex == True

def test_RootOf_evalf():
    real = RootOf(x**3 + x + 3, 0).evalf(n=20)

    assert real.epsilon_eq(Real("-1.2134116627622296341"))

    re, im = RootOf(x**3 + x + 3, 1).evalf(n=20).as_real_imag()

    assert re.epsilon_eq(Real("0.60670583138111481707"))
    assert im.epsilon_eq(Real("1.45061224918844152650"))

    re, im = RootOf(x**3 + x + 3, 2).evalf(n=20).as_real_imag()

    assert re.epsilon_eq( Real("0.60670583138111481707"))
    assert im.epsilon_eq(-Real("1.45061224918844152650"))

