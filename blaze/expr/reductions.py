from __future__ import absolute_import, division, print_function

import toolz
from toolz import first
import datashape
from datashape import Record, dshape, DataShape
from datashape import coretypes as ct
from datashape.predicates import isscalar, iscollection

from .core import common_subexpression
from .expressions import Expr, Symbol


class Reduction(Expr):
    """ A column-wise reduction

    Blaze supports the same class of reductions as NumPy and Pandas.

        sum, min, max, any, all, mean, var, std, count, nunique

    Examples
    --------

    >>> t = Symbol('t', 'var * {name: string, amount: int, id: int}')
    >>> e = t['amount'].sum()

    >>> data = [['Alice', 100, 1],
    ...         ['Bob', 200, 2],
    ...         ['Alice', 50, 3]]

    >>> from blaze.compute.python import compute
    >>> compute(e, data)
    350
    """
    __slots__ = '_child', 'axis', 'keepdims'
    _dtype = None

    def __init__(self, _child, axis=None, keepdims=False):
        self._child = _child
        if axis is None:
            axis = tuple(range(_child.ndim))
        if isinstance(axis, (set, list)):
            axis = tuple(axis)
        if not isinstance(axis, tuple):
            axis = (axis,)
        axis = tuple(sorted(axis))
        self.axis = axis
        self.keepdims = keepdims

    @property
    def dshape(self):
        axis = self.axis
        if self.keepdims:
            shape = tuple(1 if i in self.axis else d
                          for i, d in enumerate(self._child.shape))
        else:
            shape = tuple(d
                          for i, d in enumerate(self._child.shape)
                          if i not in self.axis)
        return DataShape(*(shape + (self._dtype,)))

    @property
    def symbol(self):
        return type(self).__name__

    @property
    def _name(self):
        try:
            return self._child._name + '_' + type(self).__name__
        except (AttributeError, ValueError, TypeError):
            return type(self).__name__

    def __str__(self):
        kwargs = list()
        if self.keepdims:
            kwargs.append('keepdims=True')
        if self.axis != tuple(range(self._child.ndim)):
            kwargs.append('axis=' + str(self.axis))
        other = sorted(set(self.__slots__) - set(['_child', 'axis', 'keepdims']))
        for slot in other:
            kwargs.append('%s=%s' % (slot, getattr(self, slot)))
        name = type(self).__name__
        if kwargs:
            return '%s(%s, %s)' % (name, self._child, ', '.join(kwargs))
        else:
            return '%s(%s)' % (name, self._child)


class any(Reduction):
    _dtype = ct.bool_

class all(Reduction):
    _dtype = ct.bool_

class sum(Reduction):
    @property
    def _dtype(self):
        schema = self._child.schema[0]
        if isinstance(schema, Record) and len(schema.types) == 1:
            return first(schema.types)
        else:
            return schema

class max(Reduction):
    @property
    def _dtype(self):
        schema = self._child.schema[0]
        if isinstance(schema, Record) and len(schema.types) == 1:
            return first(schema.types)
        else:
            return schema

class min(Reduction):
    @property
    def _dtype(self):
        schema = self._child.schema[0]
        if isinstance(schema, Record) and len(schema.types) == 1:
            return first(schema.types)
        else:
            return schema

class mean(Reduction):
    _dtype = ct.real

class var(Reduction):
    """Variance

    Parameters
    ----------
    child : Expr
        An expression
    unbiased : bool, optional
        Compute an unbiased estimate of the population variance if this is
        ``True``. In NumPy and pandas, this parameter is called ``ddof`` (delta
        degrees of freedom) and is equal to 1 for unbiased and 0 for biased.
    """
    __slots__ = '_child', 'unbiased', 'axis', 'keepdims'

    _dtype = ct.real

    def __init__(self, child, unbiased=False, *args, **kwargs):
        self.unbiased = unbiased
        Reduction.__init__(self, child, *args, **kwargs)


class std(Reduction):
    """Standard Deviation

    Parameters
    ----------
    child : Expr
        An expression
    unbiased : bool, optional
        Compute the square root of an unbiased estimate of the population
        variance if this is ``True``.

        .. warning::

            This does *not* return an unbiased estimate of the population
            standard deviation.

    See Also
    --------
    var
    """
    __slots__ = '_child', 'unbiased', 'axis', 'keepdims'

    _dtype = ct.real

    def __init__(self, child, unbiased=False, *args, **kwargs):
        self.unbiased = unbiased
        Reduction.__init__(self, child, *args, **kwargs)


class count(Reduction):
    """ The number of non-null elements """
    _dtype = ct.int_

class nunique(Reduction):
    _dtype = ct.int_


class Summary(Expr):
    """ A collection of named reductions

    Examples
    --------

    >>> t = Symbol('t', 'var * {name: string, amount: int, id: int}')
    >>> expr = summary(number=t.id.nunique(), sum=t.amount.sum())

    >>> data = [['Alice', 100, 1],
    ...         ['Bob', 200, 2],
    ...         ['Alice', 50, 1]]

    >>> from blaze.compute.python import compute
    >>> compute(expr, data)
    (2, 350)
    """
    __slots__ = '_child', 'names', 'values', 'keepdims'

    def __init__(self, _child, names, values, keepdims=False):
        self._child = _child
        self.names = names
        self.values = values
        self.keepdims = keepdims

    @property
    def dshape(self):
        measure = Record(list(zip(self.names,
                                  [v._dtype for v in self.values])))
        if self.keepdims:
            return DataShape(*((1,) * self._child.ndim + (measure,)))
        else:
            return DataShape(measure)

    def __str__(self):
        return 'summary(' + ', '.join('%s=%s' % (name, str(val))
                for name, val in zip(self.fields, self.values)) + \
                    ', keepdims=%s' % self.keepdims + ')'


def summary(keepdims=False, **kwargs):
    items = sorted(kwargs.items(), key=first)
    names = tuple(map(first, items))
    values = tuple(map(toolz.second, items))
    child = common_subexpression(*values)

    if len(kwargs) == 1 and not iscollection(child.dshape):
        while not iscollection(child.dshape):
            children = [i for i in child._inputs if isinstance(i, Expr)]
            if len(children) == 1:
                child = children[0]
            else:
                raise ValueError()

    return Summary(child, names, values, keepdims=keepdims)


summary.__doc__ = Summary.__doc__


from datashape.predicates import (iscollection, isscalar, isrecord, isboolean,
        isnumeric)
from .expressions import schema_method_list, dshape_method_list

schema_method_list.extend([
    (isboolean, set([any, all, sum])),
    (isnumeric, set([mean, sum, mean, min, max, std, var])),
    ])

dshape_method_list.extend([
    (iscollection, set([count, min, max])),
    (lambda ds: len(ds.shape) == 1, set([nunique])),
    ])
