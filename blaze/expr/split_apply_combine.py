from __future__ import absolute_import, division, print_function

from .core import common_subexpression
from .expressions import Expr, Symbol
from .reductions import Reduction, Summary, summary
from ..dispatch import dispatch
from datashape import dshape, Record, Option, Unit, var

__all__ = ['by', 'By', 'count_values']

def _names_and_types(expr):
    schema = expr.dshape.measure
    if isinstance(schema, Option):
        schema = schema.ty
    if isinstance(schema, Record):
        return schema.names, schema.types
    if isinstance(schema, Unit):
        return [expr._name], [expr.dshape.measure]
    raise ValueError("Unable to determine name and type of %s" % expr)


class By(Expr):
    """ Split-Apply-Combine Operator

    Examples
    --------

    >>> t = Symbol('t', 'var * {name: string, amount: int, id: int}')
    >>> e = by(t['name'], t['amount'].sum())

    >>> data = [['Alice', 100, 1],
    ...         ['Bob', 200, 2],
    ...         ['Alice', 50, 3]]

    >>> from blaze.compute.python import compute
    >>> sorted(compute(e, data))
    [('Alice', 150), ('Bob', 200)]
    """

    __slots__ = 'grouper', 'apply'

    @property
    def _child(self):
        return common_subexpression(self.grouper, self.apply)

    @property
    def schema(self):
        grouper_names, grouper_types = _names_and_types(self.grouper)
        apply_names, apply_types = _names_and_types(self.apply)

        names = grouper_names + apply_names
        types = grouper_types + apply_types

        return dshape(Record(list(zip(names, types))))

    @property
    def dshape(self):
        # TODO: think if this should be generalized
        return var * self.schema

@dispatch(Expr, (Summary, Reduction))
def by(grouper, apply):
    return By(grouper, apply)


@dispatch(Expr)
def by(grouper, **kwargs):
    return By(grouper, summary(**kwargs))


def count_values(expr, sort=True):
    """
    Count occurrences of elements in this column

    Sort by counts by default
    Add ``sort=False`` keyword to avoid this behavior.
    """
    result = by(expr, count=expr.count())
    if sort:
        result = result.sort('count', ascending=False)
    return result


from datashape.predicates import iscollection
from .expressions import dshape_method_list

dshape_method_list.extend([
    (lambda ds: len(ds.shape) == 1, set([count_values])),
    ])
