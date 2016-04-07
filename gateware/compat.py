from litex.gen import *
from litex.gen.fhdl.structure import _Operator


def optree(op, operands, lb=None, ub=None, default=None):
    if lb is None:
        lb = 0
    if ub is None:
        ub = len(operands)
    l = ub - lb
    if l == 0:
        if default is None:
            raise AttributeError
        else:
            return default
    elif l == 1:
        return operands[lb]
    else:
        s = lb + l//2
        return _Operator(op,
            [optree(op, operands, lb, s, default),
            optree(op, operands, s, ub, default)])