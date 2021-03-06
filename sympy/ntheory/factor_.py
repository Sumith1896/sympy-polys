"""
Integer factorization
"""

from sympy.core import Mul
from sympy.core.numbers import igcd
from sympy.core.power import integer_nthroot, Pow
from sympy.core.mul import Mul
import random
import math
from primetest import isprime
from generate import sieve, primerange
from sympy.utilities.iterables import iff
from sympy.core.singleton import S

small_trailing = [i and max(int(not i % 2**j) and j for j in range(1,8)) \
    for i in range(256)]

def trailing(n):
    """Count the number of trailing zero digits in the binary
    representation of n, i.e. determine the largest power of 2
    that divides n."""
    if not n:
        return 0
    low_byte = n & 0xff
    if low_byte:
        return small_trailing[low_byte]
    t = 0
    p = 8
    while not n & 1:
        while not n & ((1<<p)-1):
            n >>= p
            t += p
            p *= 2
        p //= 2
    return t

def multiplicity(p, n):
    """
    Find the greatest integer m such that p**m divides n.

    Example usage
    =============
        >>> from sympy.ntheory import multiplicity
        >>> [multiplicity(5, n) for n in [8, 5, 25, 125, 250]]
        [0, 1, 2, 3, 3]

    """

    if p == 2:
        return trailing(n)

    m = 0
    n, rem = divmod(n, p)
    while not rem:
        m += 1
        if m > 5:
            # The multiplicity could be very large. Better
            # to increment in powers of two
            e = 2
            while 1:
                ppow = p**e
                if ppow < n:
                    nnew, rem = divmod(n, ppow)
                    if not rem:
                        m += e
                        e *= 2
                        n = nnew
                        continue
                return m + multiplicity(p, n)
        n, rem = divmod(n, p)
    return m

def perfect_power(n, candidates=None, recursive=True):
    """
    Return ``(a, b)`` such that ``n`` == ``a**b`` if ``n`` is a
    perfect power; otherwise return ``None``.

    By default, attempts to determine the largest possible ``b``.
    With ``recursive=False``, the smallest possible ``b`` will
    be chosen (this will be a prime number).
    """
    if n < 3:
        return None
    logn = math.log(n,2)
    max_possible = int(logn)+2
    if not candidates:
        candidates = primerange(2, max_possible)
    for b in candidates:
        if b > max_possible:
            break
        # Weed out downright impossible candidates
        if logn/b < 40:
            a = 2.0**(logn/b)
            if abs(int(a+0.5)-a) > 0.01:
                continue
        # print b
        r, exact = integer_nthroot(n, b)
        if exact:
            if recursive:
                m = perfect_power(r)
                if m:
                    return m[0], b*m[1]
            return r, b

def pollard_rho(n, retries=5, max_steps=None, seed=1234):
    """Use Pollard's rho method to try to extract a nontrivial factor
    of ``n``. The returned factor may be a composite number. If no
    factor is found, ``None`` is returned.

    The algorithm may need to take thousands of steps before
    it finds a factor or reports failure. If ``max_steps`` is
    specified, the iteration is canceled with a failure after
    the specified number of steps.

    On failure, the algorithm will self-restart (with different
    parameters) up to ``retries`` number of times.

    The rho algorithm is a Monte Carlo method whose outcome can
    be affected by changing the random seed value.

    References
    ==========
      - Richard Crandall & Carl Pomerance (2005), "Prime Numbers:
        A Computational Perspective", Springer, 2nd edition, 229-231

    """
    prng = random.Random(seed + retries)
    for i in range(retries):
        # Alternative good nonrandom choice: a = 1
        a = prng.randint(1, n-3)
        # Alternative good nonrandom choice: s = 2
        s = prng.randint(0, n-1)
        U = V = s
        F = lambda x: (x**2 + a) % n
        j = 0
        while 1:
            if max_steps and (j > max_steps):
                break
            j += 1
            U = F(U)
            V = F(F(V))
            g = igcd(abs(U-V), n)
            if g == 1:
                continue
            if g == n:
                break
            return int(g)
    return None

def pollard_pm1(n, B=10, seed=1234):
    """
    Use Pollard's p-1 method to try to extract a nontrivial factor
    of ``n``. The returned factor may be a composite number. If no
    factor is found, ``None`` is returned.

    The search is performed up to a smoothness bound ``B``.
    Choosing a larger B increases the likelihood of finding
    a large factor.

    The p-1 algorithm is a Monte Carlo method whose outcome can
    be affected by changing the random seed value.

    Example usage
    =============
    With the default smoothness bound, this number can't be cracked:

        >>> from sympy.ntheory import pollard_pm1
        >>> pollard_pm1(21477639576571)

    Increasing the smoothness bound helps:

        >>> pollard_pm1(21477639576571, B=2000)
        4410317

    References
    ==========
      - Richard Crandall & Carl Pomerance (2005), "Prime Numbers:
        A Computational Perspective", Springer, 2nd edition, 236-238
    """
    prng = random.Random(seed + B)
    a = prng.randint(2, n-1)
    for p in sieve.primerange(2, B):
        e = int(math.log(B, p))
        a = pow(a, p**e, n)
    g = igcd(a-1, n)
    if 1 < g < n:
        return int(g)
    else:
        return None

def _trial(factors, n, candidates=None, verbose=False, force_finalize=False):
    """
    Helper function for integer factorization. Trial factors ``n`
    against all integers given in the sequence ``candidates``
    and updates the dict ``factors`` in-place. Raises
    ``StopIteration`` if ``n`` becomes equal to 1, otherwise
    returns the reduced value of ``n`` and a flag indicating
    whether any factors were found.
    """
    if not candidates:
        return n, False
    found_something = False
    for k in candidates:
        # This check is slightly faster for small n and slightly
        # slower for large n...
        if n % k:
            continue
        m = multiplicity(k, n)
        if m:
            found_something = True
            if verbose:
                print "-- %i (multiplicity %i)" % (k, m)
            n //= (k**m)
            factors[k] = m
            if n == 1:
                raise StopIteration
    return int(n), found_something

def _check_termination(factors, n, verbose=False):
    """
    Helper function for integer factorization. Checks if ``n``
    is a prime or a perfect power, and in those cases updates
    the factorization and raises ``StopIteration``.
    """
    if verbose:
        print "Checking if remaining factor terminates the factorization"
    n = int(n)
    if n == 1:
        raise StopIteration
    p = perfect_power(n)
    if p:
        base, exp = p
        if verbose:
            print "-- Remaining factor is a perfect power: %i ** %i" % (base, exp)
        for b, e in factorint(base).iteritems():
            factors[b] = exp*e
        raise StopIteration
    if isprime(n):
        if verbose:
            print "Remaining factor", n, "is prime"
        factors[n] = 1
        raise StopIteration

trial_msg = "Trial division with primes between %i and %i"
rho_msg = "Pollard's rho with retries %i, max_steps %i and seed %i"
pm1_msg = "Pollard's p-1 with smoothness bound %i and seed %i"

def factorint(n, limit=None, use_trial=True, use_rho=True, use_pm1=True,
    verbose=False, visual=False):
    """
    Given a positive integer ``n``, ``factorint(n)`` returns a dict containing
    the prime factors of ``n`` as keys and their respective multiplicities
    as values. For example:

        >>> from sympy.ntheory import factorint
        >>> factorint(2000)    # 2000 = (2**4) * (5**3)
        {2: 4, 5: 3}
        >>> factorint(65537)   # This number is prime
        {65537: 1}

    For input less than 2, factorint behaves as follows:

      - ``factorint(1)`` returns the empty factorization, ``{}``
      - ``factorint(0)`` returns ``{0:1}``
      - ``factorint(-n)`` adds ``-1:1`` to the factors and then factors ``n``

    Algorithm
    =========

    The function switches between multiple algorithms. Trial division
    quickly finds small factors (of the order 1-5 digits), and finds
    all large factors if given enough time. The Pollard rho and p-1
    algorithms are used to find large factors ahead of time; they
    will often find factors of the order of 10 digits within a few
    seconds:

        >>> factors = factorint(12345678910111213141516)
        >>> for base, exp in sorted(factors.items()):
        ...     print base, exp
        ...
        2 2
        2507191691 1
        1231026625769 1

    Any of these methods can optionally be disabled with the following
    boolean parameters:

      - ``use_trial``: Toggle use of trial division
      - ``use_rho``: Toggle use of Pollard's rho method
      - ``use_pm1``: Toggle use of Pollard's p-1 method

    ``factorint`` also periodically checks if the remaining part is
    a prime number or a perfect power, and in those cases stops.

    Partial Factorization
    =====================

    If ``limit`` (> 2) is specified, the search is stopped after performing
    trial division up to (and including) the limit (or taking a
    corresponding number of rho/p-1 steps). This is useful if one has
    a large number and only is interested in finding small factors (if
    any). Note that setting a limit does not prevent larger factors
    from being found early; it simply means that the largest factor may
    be composite.

    This number, for example, has two small factors and a huge
    semi-prime factor that cannot be reduced easily:

        >>> from sympy.ntheory import isprime
        >>> a = 1407633717262338957430697921446883
        >>> f = factorint(a, limit=10000)
        >>> f == {991: 1, 202916782076162456022877024859L: 1, 7: 1}
        True
        >>> isprime(max(f))
        False

    Visual Factorization
    ====================
    If ``visual`` is set to ``True``, then it will return a visual
    factorization of the integer.  For example:

        >>> from sympy import pprint
        >>> pprint(factorint(4200, visual=True))
         3  1  2  1
        2 *3 *5 *7

    Note that this is achieved by using the evaluate=False flag in Mul
    and Pow. If you do other manipulations with an expression where
    evaluate=False, it may evaluate.  Therefore, you should use the
    visual option only for visualization, and use the normal dictionary
    returned by visual=False if you want to perform operations on the
    factors.

    If you find that you want one from the other but you do not want to
    run expensive factorint again, you can easily switch between the two
    forms using the following list comprehensions:

        >>> from sympy import Mul, Pow
        >>> regular = factorint(1764); regular
        {2: 2, 3: 2, 7: 2}
        >>> pprint(Mul(*[Pow(*i, **{'evaluate':False}) for i in regular.items()],
        ... **{'evaluate':False}))
         2  2  2
        2 *3 *7

        >>> visual = factorint(1764, visual=True); pprint(visual)
         2  2  2
        2 *3 *7
        >>> dict([i.args for i in visual.args])
        {2: 2, 3: 2, 7: 2}

    Miscellaneous Options
    =====================

    If ``verbose`` is set to ``True``, detailed progress is printed.
    """
    if visual:
        factordict = factorint(n, limit=limit, use_trial=use_trial, use_rho=use_rho,
        use_pm1=use_pm1, verbose=verbose, visual=False)
        if factordict == {}:
            return S.One
        return Mul(*[Pow(*i, **{'evaluate':False}) for i in factordict.items()],
            **{'evaluate':False})
    assert use_trial or use_rho or use_pm1
    n = int(n)
    if not n:
        return {0:1}
    if n < 0:
        n = -n
        factors = {-1:1}
    else:
        factors = {}
    # Power of two
    t = trailing(n)
    if t:
        factors[2] = t
        n >>= t
    if n == 1:
        return factors

    low, high = 3, 250

    # It is sufficient to perform trial division up to sqrt(n)
    try:
        # add 1 to sqrt in case there is round off; add 1 overall to make
        # sure that the limit is included
        limit = iff(limit, lambda: max(limit, low), lambda: int(n**0.5) + 1) + 1
    except OverflowError:
        limit = 1e1000


    # Setting to True here forces _check_termination if first round of
    # trial division fails
    found_trial_previous = True

    if verbose and n < 1e300:
        print "Factoring", n

    while 1:
        try:
            high_ = min(high, limit)

            # Trial division
            if use_trial:
                if verbose:
                    print trial_msg % (low, high_)
                ps = sieve.primerange(low, high_)
                n, found_trial = _trial(factors, n, ps, verbose)
            else:
                found_trial = False

            if high > limit:
                factors[n] = 1
                raise StopIteration

            # Only used advanced (and more expensive) methods as long as
            # trial division fails to locate small factors
            if not found_trial:
                if found_trial_previous:
                    _check_termination(factors, n, verbose)

                # Pollard p-1
                if use_pm1 and not found_trial:
                    B = int(high_**0.7)
                    if verbose:
                        print (pm1_msg % (high_, high_))
                    ps = factorint(pollard_pm1(n, B=high_, seed=high_) or 1, \
                        limit=limit-1, verbose=verbose)
                    n, found_pm1 = _trial(factors, n, ps, verbose)
                    if found_pm1:
                        _check_termination(factors, n, verbose)

                # Pollard rho
                if use_rho and not found_trial:
                    max_steps = int(high_**0.7)
                    if verbose:
                        print (rho_msg % (1, max_steps, high_))
                    ps = factorint(pollard_rho(n, retries=1, max_steps=max_steps, \
                        seed=high_) or 1, limit=limit-1, verbose=verbose)
                    n, found_rho = _trial(factors, n, ps, verbose)
                    if found_rho:
                        _check_termination(factors, n, verbose)

        except StopIteration:
            return factors

        found_trial_previous = found_trial
        low, high = high, high*2


def primefactors(n, limit=None, verbose=False):
    """Return a sorted list of n's prime factors, ignoring multiplicity
    and any composite factor that remains if the limit was set too low
    for complete factorization. Unlike factorint(), primefactors() does
    not return -1 or 0.

    Example usage
    =============

        >>> from sympy.ntheory import primefactors, factorint, isprime
        >>> primefactors(6)
        [2, 3]
        >>> primefactors(-5)
        [5]

        >>> sorted(factorint(123456).items())
        [(2, 6), (3, 1), (643, 1)]
        >>> primefactors(123456)
        [2, 3, 643]

        >>> sorted(factorint(10000000001, limit=200).items())
        [(101, 1), (99009901, 1)]
        >>> isprime(99009901)
        False
        >>> primefactors(10000000001, limit=300)
        [101]

    """
    n = int(n)
    s = []
    factors = sorted(factorint(n, limit=limit, verbose=verbose).keys())
    s = [f for f in factors[:-1:] if f not in [-1, 0, 1]]
    if factors and isprime(factors[-1]):
        s += [factors[-1]]
    return s

def _divisors(n):
    """Helper function for divisors which generates the divisors."""

    factordict = factorint(n)
    ps = sorted(factordict.keys())

    def rec_gen(n = 0):
        if n == len(ps):
            yield 1
        else :
            pows = [1]
            for j in xrange(factordict[ps[n]]):
                pows.append(pows[-1] * ps[n])
            for q in rec_gen(n + 1):
                for p in pows:
                    yield p * q

    for p in rec_gen() :
        yield p

def divisors(n, generator=False):
    """
    Return all divisors of n sorted from 1..n by default.
    If generator is True an unordered generator is returned.

    The number of divisors of n can be quite large if there are many
    prime factors (counting repeated factors). If only the number of
    factors is desired use divisor_count(n).

    Examples::

    >>> from sympy import divisors, divisor_count
    >>> divisors(24)
    [1, 2, 3, 4, 6, 8, 12, 24]
    >>> divisor_count(24)
    8

    >>> list(divisors(120, generator=True))
    [1, 2, 4, 8, 3, 6, 12, 24, 5, 10, 20, 40, 15, 30, 60, 120]

    This is a slightly modified version of Tim Peters referenced at:
    http://stackoverflow.com/questions/1010381/python-factorization
    """

    n = abs(n)
    if isprime(n):
        return [1, n]
    elif n == 1:
        return [1]
    elif n == 0:
        return []
    else:
        rv = _divisors(n)
        if not generator:
            return sorted(rv)
        return rv

def divisor_count(n):
    """Return the number of divisors of n.

    Reference:
    http://www.mayer.dial.pipex.com/maths/formulae.htm

    >>> from sympy import divisor_count
    >>> divisor_count(6)
    4
    """

    n = abs(n)
    if n == 0:
        return 0
    return Mul(*[v+1 for k, v in factorint(n).items() if k > 1])

def totient(n):
    """Calculate the Euler totient function phi(n)

    >>> from sympy.ntheory import totient
    >>> totient(1)
    1
    >>> totient(25)
    20

    """
    if n < 1:
        raise ValueError("n must be a positive integer")
    factors = factorint(n)
    t = 1
    for p, k in factors.iteritems():
        t *= (p-1) * p**(k-1)
    return t
