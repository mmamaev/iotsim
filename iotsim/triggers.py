from .core import Trigger, AssemblyContext
from .utils import RangeChoice


class HistoryConditionTrigger(Trigger):

    def __init__(self, name, component, lag, condition):
        super().__init__(name, active=True, component=component,
                         lag=lag, condition=condition)

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):

        component, lag, condition = (kwargs['component'],
                                     kwargs['lag'], kwargs['condition'])
        x = assembly_context.query(component, lag)
        return None if x is None else condition(x)


class HistoryInRangeTrigger(Trigger):

    def __init__(self, name, component, lag, v0, v1):
        super().__init__(name, active=True, component=component,
                         lag=lag, v0=v0, v1=v1)

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):

        component, lag, v0, v1 = (kwargs['component'],
                                  kwargs['lag'], kwargs['v0'], kwargs['v1'])
        x = assembly_context.query(component, lag)
        return None if x is None else min(v0, v1) <= x <= max(v0, v1)


class ParameterInRangeTrigger(Trigger):

    def __init__(self, name, component, parameter, v0, v1):
        super().__init__(name, active=True, component=component,
                         parameter=parameter, v0=v0, v1=v1)

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):

        component, parameter, v0, v1 = (kwargs['component'], kwargs['parameter'],
                                        kwargs['v0'], kwargs['v1'])
        x = assembly_context.get_parameter(component, parameter)
        return None if x is None else min(v0, v1) <= x <= max(v0, v1)


class HistoryOutOfRangeTrigger(HistoryInRangeTrigger):

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):
        result = super()._evaluate_condition(assembly_context, **kwargs)
        return result if result is None else not result

class ParameterOutOfRangeTrigger(ParameterInRangeTrigger):

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):
        result = super()._evaluate_condition(assembly_context, **kwargs)
        return result if result is None else not result


class CounterTrigger(Trigger):

    def __init__(self, name, component, counter, threshold):
        super().__init__(name, active=True, component=component,
                         counter=counter, threshold=threshold)

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):
        component, counter, threshold = (kwargs['component'], kwargs['counter'],
                                     kwargs['threshold'])
        # `threshold` may be a single value or a list or values;
        # in the latter case one value will be selected from the list at random
        count = assembly_context.read_counter(component, counter)
        return None if count is None else RangeChoice(threshold) == count


class Always(Trigger):

    def __init__(self):
        super().__init__(name=None, active=True)

    def _evaluate_condition(self, assembly_context: AssemblyContext, **kwargs):
        return True

