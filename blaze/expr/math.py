from __future__ import absolute_import, division, print_function

from datashape import dshape, real, int_, bool_

from .expressions import Expr
from .arithmetic import UnaryOp

# Here follows a large number of unary operators.  These were selected by
# taking the intersection of the functions in ``math`` and ``numpy``

__all__ = ['sqrt', 'sin', 'sinh', 'cos', 'cosh', 'tan', 'tanh', 'exp', 'expm1',
        'log', 'log10', 'log1p', 'acos', 'acosh', 'asin', 'asinh', 'atan',
        'atanh', 'radians', 'degrees', 'ceil', 'floor', 'trunc', 'isnan',
        'RealMath', 'IntegerMath', 'BooleanMath', 'Math']

class Math(UnaryOp):
    pass

class RealMath(Math):
    """ Mathematical unary operator with real valued dshape like sin, or exp """
    _dtype = real


class sqrt(RealMath): pass

class sin(RealMath): pass
class sinh(RealMath): pass
class cos(RealMath): pass
class cosh(RealMath): pass
class tan(RealMath): pass
class tanh(RealMath): pass

class exp(RealMath): pass
class expm1(RealMath): pass
class log(RealMath): pass
class log10(RealMath): pass
class log1p(RealMath): pass

class acos(RealMath): pass
class acosh(RealMath): pass
class asin(RealMath): pass
class asinh(RealMath): pass
class atan(RealMath): pass
class atanh(RealMath): pass

class radians(RealMath): pass
class degrees(RealMath): pass


class IntegerMath(Math):
    """ Mathematical unary operator with int valued dshape like ceil, floor """
    _dtype = int_


class ceil(IntegerMath): pass
class floor(IntegerMath): pass
class trunc(IntegerMath): pass


class BooleanMath(Math):
    """ Mathematical unary operator with bool valued dshape like isnan """
    _dtype = bool_


class isnan(BooleanMath): pass


from datashape.predicates import isreal

from .expressions import schema_method_list

schema_method_list.extend([
    (isreal, set([isnan]))
        ])
