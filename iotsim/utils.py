from collections.abc import Iterable
import numpy as np


def is_iterable(x):
    return isinstance(x, Iterable) and not isinstance(x, (str, bytes))

def is_iterable_or_None(x):
    return x is None or is_iterable(x)

def to_iterable(x):
    if x is None:
        return []
    if is_iterable(x):
        return x
    else:
        return [x]

def assert_value(x, value_render_function, value_test_function):
    if value_render_function is not None:
        x = value_render_function(x)
    if value_test_function is not None:
        assert value_test_function(x)
    return x

def equal_arrays(iterable1, iterable2):
    a = np.array(iterable1)
    b = np.array(iterable2)

    try:
        amask = np.isnan(a)
        bmask = np.isnan(b)
    except TypeError:
        try:
            amask = np.isnat(a)
            bmask = np.isnat(b)
        except TypeError:
            return (a == b).all()

    return ((a == b) | (amask & bmask)).all()

def equal_floats(a, b, accuracy=0.001):
    assert 0 < accuracy < 1
    a = np.array(to_iterable(a))
    b = np.array(to_iterable(b))
    return np.allclose(a, b, atol=accuracy, equal_nan=True)


def to_name(obj):
    if obj is None:
        return None
    elif hasattr(obj, 'name'):
        if callable(obj.name):
            return str(obj.name())
        else:
            return str(obj.name)
    else:
        return str(obj)


class RangeChoice:

    def __init__(self, v, p=None):
        self._v = sorted(to_iterable(v))
        self._p = p

    def __eq__(self, other):
        try:
            other_index = self._v.index(other)
        except ValueError:
            return False
        cast_index = np.random.choice(np.arange(len(self._v)), p=self._p)
        return cast_index <= other_index

