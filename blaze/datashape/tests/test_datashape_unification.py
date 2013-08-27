# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from blaze import error
from blaze import dshape
from blaze.datashape import unify, coretypes as T

#------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------

def symsub(ds, S):
    """Substitute type variables by name"""
    return T.DataShape([S.get(x.symbol, x) if isinstance(x, T.TypeVar) else x
                           for x in ds.parameters])

#------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------

class TestUnification(unittest.TestCase):

    def test_unify_datashape_promotion(self):
        d1 = dshape('10, T1, int32')
        d2 = dshape('T2, T2, float32')
        [result], constraints = unify([(d1, d2)], [True])
        self.assertEqual(result, dshape('10, 10, float32'))

    def test_unify_datashape_promotion2(self):
        A, B = T.TypeVar('A'), T.TypeVar('B')
        X, Y, Z = T.TypeVar('X'), T.TypeVar('Y'), T.TypeVar('Z')
        S = dict((typevar.symbol, typevar) for typevar in (A, B, X, Y, Z))

        # LHS
        d1 = dshape('A, B, int32')
        d2 = dshape('B, 10, float32')

        # RHS
        d3 = dshape('X, Y, int16')
        d4 = dshape('X, X, Z')

        # Create proper equation
        d1, d2, d3, d4 = [symsub(ds, S) for ds in (d1, d2, d3, d4)]
        constraints = [(d1, d3), (d2, d4)]

        # What we know from the above equations is:
        #   1) A coerces to X
        #   2) B coerces to Y
        #   3) 10 coerces to X
        #
        # From this we determine that X must be Fixed(10). We must retain
        # type variable B for Y, since we can only say that B must unify with
        # Fixed(10), but not whether it is actually Fixed(10) (it may also be
        # Fixed(1))

        [arg1, arg2], remaining_constraints = unify(constraints, [True, True])
        self.assertEqual(arg1, dshape('10, B, int16'))
        self.assertEqual(arg2, dshape('10, 10, float32'))

    def test_unify_broadcasting1(self):
        ds1 = dshape('A, B, int32')
        ds2 = dshape('K, M, N, float32')
        [result], constraints = unify([(ds1, ds2)], [True])
        self.assertEqual(str(result), '1, A, B, float32')

    def test_unify_broadcasting2(self):
        ds1 = dshape('A, B, C, int32')
        ds2 = dshape('M, N, float32')
        [result], constraints = unify([(ds1, ds2)], [True])
        self.assertEqual(str(result), '1, B, C, float32')

    def test_unify_ellipsis(self):
        ds1 = dshape('A, ..., B, int32')
        ds2 = dshape('M, N, ..., S, T, float32')
        [result], constraints = unify([(ds1, ds2)], [True])
        self.assertEqual(str(result), 'A, N, ..., S, B, float32')

    def test_unify_datashape_error(self):
        d1 = dshape('10, 11, int32')
        d2 = dshape('T2, T2, int32')
        self.assertRaises(error.UnificationError, unify, [(d1, d2)], [True])


if __name__ == '__main__':
    # TestUnification('test_unify_broadcasting1').debug()
    # TestNormalization('test_normalize_ellipses5').debug()
    unittest.main()