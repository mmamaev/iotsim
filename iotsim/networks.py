from .core import Network, AssemblyContext
from itertools import repeat
from numpy.random import normal, choice

class IdealNetwork(Network):

    def __init__(self, name=None):
        super().__init__(name)

    def activate(self, assembly_context=None):
        return repeat((True, 0))


class NormalNetwork(Network):

    def __init__(self, name=None, delay=None, jitter=None, drop_rate=None):
        super().__init__(name, delay=delay, jitter=jitter, drop_rate=drop_rate)

    def activate(self, assembly_context: AssemblyContext = None):
        self.update_parameters(assembly_context=assembly_context)
        if self._parameters['delay'] < 0 or self._parameters['jitter'] < 0:
            raise ValueError("Network {} delay and jitter must be non-negative. "
                "Got delay={}, jitter={}".
                format(self.name, self._parameters['delay'], self._parameters['jitter']))
        if not 0 <= self._parameters['drop_rate'] < 1:
            raise ValueError("Network {} drop rate msu be in [0, 1). Got {} ".
                             format(self.name, self._parameters['drop_rate']))

        def runner():
            while True:
                yield (
                    choice([True, False], p=[1 - self._parameters['drop_rate'],
                                              self._parameters['drop_rate']]),
                    normal(self._parameters['delay'], self._parameters['jitter'])
                )

        return runner()
