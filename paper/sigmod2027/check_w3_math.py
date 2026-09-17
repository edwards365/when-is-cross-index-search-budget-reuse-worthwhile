"""Deterministic mathematical regression checks, not scientific experiments.

No ANN data, fitted models, or empirical results are read or written.
"""
import itertools
import math
import unittest
from fractions import Fraction


def binomial_cdf(x, n, p):
    return sum(math.comb(n, k) * p**k * (1-p)**(n-k)
               for k in range(x + 1))


def cp_upper(x, n, alpha):
    if x == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(70):
        mid = (lo + hi) / 2
        if binomial_cdf(x, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def stable_index(failure):
    return next((j for j in range(len(failure)) if not any(failure[j:])), math.inf)


class WritingMathChecks(unittest.TestCase):
    def test_zero_failure_closed_form(self):
        for n in (1, 10, 58, 59, 500):
            self.assertAlmostEqual(cp_upper(0, n, .05), 1-.05**(1/n), places=12)

    def test_minimum_sample_size(self):
        self.assertGreater(cp_upper(0, 58, .05), .05)
        self.assertLessEqual(cp_upper(0, 59, .05), .05)

    def test_cp_binomial_coverage_grid(self):
        for n in (5, 20, 59):
            upper = [cp_upper(x, n, .05) for x in range(n + 1)]
            for p in (.01, .03, .05, .10, .5, .9):
                noncoverage = sum(math.comb(n, x)*p**x*(1-p)**(n-x)
                                  for x, u in enumerate(upper) if p > u)
                self.assertLessEqual(noncoverage, .05 + 1e-12)

    def test_stable_tail_with_nonmonotone_recall(self):
        for failures in itertools.product((False, True), repeat=5):
            b = stable_index(failures)
            if math.isfinite(b):
                self.assertFalse(any(failures[b:]))
                self.assertTrue(all(any(failures[j:]) for j in range(b)))
        self.assertEqual(stable_index((False, True, False)), 2)
        self.assertEqual(stable_index((False, True)), math.inf)

    def test_rank_resolution(self):
        # Rational arithmetic avoids floating point ceil at exact boundaries.
        for m, eta, expected in ((9, Fraction(1,20), 10),
                                 (19, Fraction(1,20), 19),
                                 (9, Fraction(1,10), 9)):
            self.assertEqual(math.ceil((1-eta)*(m+1)), expected)

    def test_exchangeable_rank_bound_with_ties_and_infinity(self):
        # Each orbit is an exchangeable law, including tied and censored labels.
        for n in range(2, 6):
            for multiset in itertools.combinations_with_replacement((0, 1, math.inf), n):
                permutations = set(itertools.permutations(multiset))
                for r in range(1, n):
                    failures = 0
                    for row in permutations:
                        action = sorted(row[:-1])[r-1]
                        failures += math.isfinite(action) and row[-1] > action
                    self.assertLessEqual(Fraction(failures, len(permutations)),
                                         Fraction(n-r, n))

    def test_two_point_reduction(self):
        for p0, p1 in itertools.product((0, .25, .5, .75, 1), repeat=2):
            tv = abs(p0-p1)
            for rule in itertools.product((0, 1, 2), repeat=2):
                risk0 = (1-p0)*(rule[0] != 0) + p0*(rule[1] != 0)
                risk1 = (1-p1)*(rule[0] != 1) + p1*(rule[1] != 1)
                self.assertGreaterEqual(max(risk0, risk1) + 1e-12, (1-tv)/2)

    def test_shift_is_action_order_not_cost_order(self):
        grid = (10, 20, 40, 80, 120, 160, 200)
        for j in range(len(grid)):
            actions = [grid[min(j+s, len(grid)-1)] for s in range(len(grid))]
            self.assertEqual(actions, sorted(actions))
            self.assertEqual(actions[-1], 200)

    def test_margin_selection_bound(self):
        delta, eps_r, eps_c = .05, .01, 1.0
        risks, costs = (.02, .04, .06), (7., 5., 3.)
        for er in itertools.product((-eps_r, eps_r), repeat=3):
            for ec in itertools.product((-eps_c, eps_c), repeat=3):
                rh = [r+e for r,e in zip(risks, er)]
                ch = [c+e for c,e in zip(costs, ec)]
                retained = [j for j in range(3) if rh[j]+eps_r <= delta]
                choice = min(retained, key=lambda j: ch[j])
                self.assertLessEqual(risks[choice], delta)
                self.assertLessEqual(costs[choice], costs[0]+2*eps_c)

    def test_error_budget_composition(self):
        self.assertAlmostEqual(3*(.05/3), .05)
        self.assertGreater(2*.05, .05)


if __name__ == '__main__':
    unittest.main(verbosity=2)
