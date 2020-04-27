from .core import Reader, AssemblyContext
from numpy.random import random

def add_noise(x, noise, noise_type='relative'):
    factor = x if noise_type=='relative' else 1
    return x + noise * factor * 2 * (random() - 0.5)


class PassthroughReader(Reader):

    def __init__(self, name=None):
        super().__init__(name)

    def activate(self, assembly_context=None):
        return lambda x: x


class EveryNthReader(Reader):

    def __init__(self, name=None, step=None, noise=0, noise_type='relative'):
        assert noise_type in ['relative', 'absolute']
        self._noise_type = noise_type
        super().__init__(name, step=step, noise=noise)

    def activate(self, assembly_context: AssemblyContext=None):
        self.update_parameters(assembly_context=assembly_context)
        self._parameters['step'] = int(self._parameters['step'])
        if self._parameters['step'] <= 0:
            raise ValueError("Step of {} must be positive. Got {}.".format(
                              self.name, self._parameters['step']))
        counter=0

        def reader_runner(true_value):
            nonlocal counter
            if counter == 0:
                result =  add_noise(true_value,
                                    self._parameters['noise'], self._noise_type)
            else:
                result = None

            counter += 1
            if counter >= self._parameters['step']:
                   counter = 0

            return result

        return reader_runner

class OnChangeReader(Reader):

    def __init__(self, name=None, accuracy=0, step=0, noise=0, noise_type='relative'):
        assert noise_type in ['relative', 'absolute']
        self._noise_type = noise_type
        super().__init__(name, accuracy=accuracy, step=step, noise=noise)

    def activate(self, assembly_context: AssemblyContext = None):
        self.update_parameters(assembly_context=assembly_context)
        self._parameters['step'] = int(self._parameters['step'])
        if self._parameters['step'] < 0:
            raise ValueError("Step of {} must be non-negative. Got {}.".format(
                              self.name, self._parameters['step']))
        counter=0
        prev_value = None

        def reader_runner(true_value):
            nonlocal counter, prev_value

            if (prev_value is None
                or abs(true_value - prev_value) > self._parameters['accuracy']
                or self._parameters['step'] > 0 and counter == 0
            ):
                result =  add_noise(true_value,
                                    self._parameters['noise'], self._noise_type)
                counter = 0
            else:
                result = None

            prev_value = true_value
            if self._parameters['step'] > 0:
                counter += 1
                if counter == self._parameters['step']:
                    counter = 0

            return result

        return reader_runner


