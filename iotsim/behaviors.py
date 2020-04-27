from .core import Behavior
from itertools import repeat, count

class FlatlineBehavior(Behavior):

    def __init__(self, name, level=None):
        super().__init__(name, level=level)

    def activate(self, assembly_context=None):
        self.update_parameters(assembly_context=assembly_context)

        return repeat(self._parameters['level'])


class LinearBehavior(Behavior):

    def __init__(self, name, bias=None, increment=None):
        super().__init__(name, bias=bias, increment=increment)

    def activate(self, assembly_context=None):
        self.update_parameters(assembly_context=assembly_context)

        return (self._parameters['bias'] + self._parameters['increment'] * (i + 1)
                for i in count())