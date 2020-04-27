from .core import Control, AssemblyContext, Trigger
from .utils import to_name

import numpy as np
from typing import List, Callable

class ContextRetriever:

    def __call__(self, assembly_context: AssemblyContext):
        return None

class CopyFromParameter(ContextRetriever):
    def __init__(self, src_component, src_parameter, apply: Callable = None):
        self._src_component = to_name(src_component)
        self._src_parameter = src_parameter
        if not apply is None:
            assert callable(apply)
        self._apply = apply

    def __call__(self, assembly_context: AssemblyContext):
        x = assembly_context.get_parameter(self._src_component, self._src_parameter)
        if not self._apply is None:
            x = self._apply(x)
        return x


class CopyFromHistory(ContextRetriever):
    def __init__(self, src_component, lag, apply: Callable = None):
        self._src_component = to_name(src_component)
        self._lag = lag
        if not apply is None:
            assert callable(apply)
        self._apply = apply

    def __call__(self, assembly_context: AssemblyContext):
        x = assembly_context.query(self._src_component, self._lag)
        if not self._apply is None:
            x = self._apply(x)
        return x

class CopyFromCounter(ContextRetriever):
    def __init__(self, src_component, src_counter, apply: Callable = None):
        self._src_component = to_name(src_component)
        self._src_counter = src_counter
        if not apply is None:
            assert callable(apply)
        self._apply = apply

    def __call__(self, assembly_context: AssemblyContext):
        x = assembly_context.read_counter(self._src_component, self._src_counter)
        if not self._apply is None:
            x = self._apply(x)
        return x


class UpdateParametersControl(Control):

    def __init__(self, name, behavior, when, trigger: Trigger,
                  update_choices: List, p: List = None,
                  priority=0
    ):

        def choose_and_update(assembly_context: AssemblyContext,
                              update_choices: List, p=None):
            choice_idx = np.random.choice(np.arange(len(update_choices)), p=p)
            choice = update_choices[choice_idx]
            if choice is not None:
                for param_tuple in choice:
                    component, parameter, value = param_tuple
                    if isinstance(value, ContextRetriever):
                        value = value(assembly_context)
                    assembly_context.set_parameter(component, parameter, value)

        super().__init__(name, behavior, when, trigger,
                         action=choose_and_update,
                         action_parameters=dict(update_choices=update_choices, p=p),
                         priority=priority)


class ResetCounterControl(Control):

    def __init__(self, name, behavior, when, trigger: Trigger,
                 component, counter,
                 priority=0
                 ):
        def reset_counter(assembly_context: AssemblyContext,
                          component, counter):
            assembly_context.reset_counter(component, counter)

        super().__init__(name, behavior, when, trigger,
                         action=reset_counter,
                         action_parameters=dict(component=component,
                                                counter=counter),
                         priority=priority)


class IncrementCounterControl(Control):

    def __init__(self, name, behavior, when, trigger: Trigger,
                 component, counter, increment=1,
                 priority=0
                 ):

        def increment_counter(assembly_context: AssemblyContext,
                              component, counter, increment):
            assembly_context.increment_counter(component, counter, increment)

        super().__init__(name, behavior, when, trigger,
                         action=increment_counter,
                         action_parameters=dict(component=component,
                                                counter=counter,
                                                increment=increment),
                         priority=priority)



