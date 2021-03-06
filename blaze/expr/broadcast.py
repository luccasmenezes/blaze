from datashape import *
from datashape.predicates import iscollection
import itertools
from toolz import curry

from .expressions import *
from .expressions import Field, Map
from .arithmetic import maxshape, Arithmetic, Add
from .math import Math, sin
from .datetime import DateTime

__all__ = ['broadcast', 'Broadcast', 'scalar_symbols']

def broadcast(expr, leaves, scalars=None):
    scalars = scalars or scalar_symbols(leaves)
    assert len(scalars) == len(leaves)
    return Broadcast(tuple(leaves),
                     tuple(scalars),
                     expr._subs(dict(zip(leaves, scalars))))


class Broadcast(ElemWise):
    """ Fuse scalar expressions over collections

    Given elementwise operations on collections, e.g.

    >>> a = Symbol('a', '100 * int')
    >>> t = Symbol('t', '100 * {x: int, y: int}')

    >>> expr = sin(a) + t.y**2

    It may be best to represent this as a scalar expression mapped over a
    collection

    >>> sa = Symbol('a', 'int')
    >>> st = Symbol('t', '{x: int, y: int}')

    >>> sexpr = sin(sa) + st.y**2

    >>> expr = Broadcast((a, t), (sa, st), sexpr)

    This provides opportunities for optimized computation.

    In practice, expressions are often collected into Broadcast expressions
    automatically.  This class is mainly intented for internal use.
    """
    __slots__ = '_children', '_scalars', '_scalar_expr'

    @property
    def dshape(self):
        myshape = maxshape(map(shape, self._children))
        return DataShape(*(myshape + (self._scalar_expr.schema,)))

    @property
    def _inputs(self):
        return self._children

    @property
    def _name(self):
        return self._scalar_expr._name

    @property
    def _full_expr(self):
        return self._scalar_expr._subs(dict(zip(self._scalars,
                                                self._children)))

def scalar_symbols(exprs):
    """
    Gives a sequence of scalar symbols to mirror these expressions

    Examples
    --------

    >>> x = Symbol('x', '5 * 3 * int32')
    >>> y = Symbol('y', '5 * 3 * int32')

    >>> xx, yy = scalar_symbols([x, y])

    >>> xx._name, xx.dshape
    ('x', dshape("int32"))
    >>> yy._name, yy.dshape
    ('y', dshape("int32"))
    """
    new_names = ('_%d' % i for i in itertools.count(1))

    scalars = []
    names = set()
    for expr in exprs:
        if expr._name and expr._name not in names:
            name = expr._name
            names.add(name)
        else:
            name = next(new_names)

        s = Symbol(name, expr.schema)
        scalars.append(s)
    return scalars


Broadcastable = (Arithmetic, Math, Map, Field, DateTime)
WantToBroadcast = (Arithmetic, Math, Map, DateTime)


def broadcast_collect(expr, Broadcastable=Broadcastable,
                            WantToBroadcast=WantToBroadcast):
    """ Collapse expression down using Broadcast - Tabular cases only

    Expressions of type Broadcastables are swallowed into Broadcast
    operations

    >>> t = Symbol('t', 'var * {x: int, y: int, z: int, when: datetime}')
    >>> expr = (t.x + 2*t.y).distinct()

    >>> broadcast_collect(expr)
    distinct(Broadcast(_children=(t,), _scalars=(t,), _scalar_expr=t.x + (2 * t.y)))
    """
    if (isinstance(expr, WantToBroadcast) and
        iscollection(expr.dshape)):
        leaves = leaves_of_type(Broadcastable, expr)
        expr = broadcast(expr, sorted(leaves, key=str))

    # Recurse down
    children = [broadcast_collect(i, Broadcastable, WantToBroadcast)
            for i in expr._inputs]
    return expr._subs(dict(zip(expr._inputs, children)))


@curry
def leaves_of_type(types, expr):
    """ Leaves of an expression skipping all operations of type ``types``
    """
    if not isinstance(expr, types):
        return set([expr])
    else:
        return set.union(*map(leaves_of_type(types), expr._inputs))
