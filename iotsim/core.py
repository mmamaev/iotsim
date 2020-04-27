from abc import ABC, abstractmethod
from collections import namedtuple, deque
from typing import List, Dict, Callable
from .utils import to_name

def _build_namespace(myname, components, title='object', add_myname=True):
    subspaces = [obj.namespace for obj in components]
    namespace = [name for subspace in subspaces for name in subspace]
    if add_myname:
        namespace.append(myname)
    if len(set(namespace)) < len(namespace):
        raise ValueError("Non-unique names in namespace for {} {}: {}".
                         format(title, myname, namespace))
    return namespace


class Assembly:

    def __init__(self, signals, name='assembly', tick=1, history_depth=1):
        self._name = str(name)
        if tick <= 0:
            raise ValueError("Tick must be positive. Got {}".format(tick))
        self._tick = tick
        assert all([isinstance(signal, Signal) for signal in signals])
        self._namespace = _build_namespace(self._name, signals,
                                           title=self.__class__.__name__,
                                           add_myname=False
                                           )
        self._signals = signals
        self.assembly_context = AssemblyContext(self._namespace, history_depth)

    @property
    def name(self):
        return self._name

    @property
    def tick(self):
        return self._tick

    @property
    def signals(self):
        return self._signals

    def launch(self):
        signal_runners = []
        for signal in self._signals:
            signal_runners.append(signal.activate(assembly_context=self.assembly_context))

        def assembly_runner():
            while True:
                truths = []
                readings = []
                for signal in self._signals:
                    signal.update_parameters(assembly_context=self.assembly_context)
                for signal_runner in signal_runners:
                    truth, reading = next(signal_runner)
                    truths.append(truth)
                    readings.append(reading)
                yield AssemblySnapshot(self, truths, readings)

        return assembly_runner()


Reading = namedtuple('Reading', 'signal_name value arrived arrival_delay')
Truth = namedtuple('Truth', 'signal_name value')
SignalSnapshot = namedtuple('SignalSnapshot', 'truth reading')

class AssemblySnapshot:

    def __init__(self, assembly, truths, readings):
        self._truths = {truth.signal_name : truth for truth in truths}
        self._readings = {reading.signal_name : reading for reading in readings}
        self._assembly_sig_names = set([signal.name for signal in assembly.signals])
        self._assembly = assembly
        if set(self._truths.keys()) != self._assembly_sig_names:
            raise ValueError("Unexpected or missing signals in {}. "
                             "Assembly {} has signals {}.".format(
                self._truths.keys(), assembly.name, self._assembly_sig_names
            ))
        if not set(self._readings.keys()) <= self._assembly_sig_names:
            raise ValueError("Unexpected signals in readings: {}. "
                             "Assembly {} has signals {}.".format(
                self._readings.keys(), assembly.name, self._assembly_sig_names
            ))

    def __repr__(self):
        repr = "AssemblySnapshot for {!r}:\n".format(self._assembly.name)
        repr += "{:14} {:>14} {:>14} {:>14}\n".format(
            'Signal', 'True value', 'Reading', 'Delay')
        for signame in self._assembly_sig_names:
            reading_value = self._readings[signame].value
            delay = self._readings[signame].arrival_delay \
                    if self._readings[signame].arrived else "lost"
            if reading_value is None:
                repr += "{:14} {:14.4f} {:>14}\n".format(
                             signame,
                             self._truths[signame].value,
                             'None',
                         )
            elif self._readings[signame].arrived:
                repr += "{:14} {:14.4f} {:14.4f} {:14.4f}\n".format(
                            signame,
                            self._truths[signame].value,
                            reading_value,
                            self._readings[signame].arrival_delay,
                         )
            else:
                repr += "{:14} {:14.4f} {:14.4f} {:>14}\n".format(
                            signame,
                            self._truths[signame].value,
                            reading_value,
                            'lost',
                         )
            return repr

    @property
    def readings(self):
        return [reading for reading in self._readings.values()
                        if not reading is None and reading.arrived]

    @property
    def all_readings(self):
        return [reading for reading in self._readings.values()
                        if not reading is None]

    @property
    def truths(self):
        return list(self._truths.values())

    def signal(self, signal_name):
        if signal_name not in self._assembly_sig_names:
            raise ValueError('Uknown signal {}'.format(signal_name))
        reading = self._readings.get(signal_name, None)
        return SignalSnapshot(self._truths[signal_name], reading)


class AssemblyContext:

    def __init__(self, namespace, history_depth=1):
        history_depth = int(history_depth)
        if history_depth < 1:
            raise ValueError("History depth must be at least one, got {}".
                             format(history_depth))
        self._depth = history_depth
        self._parameters = {to_name(name): dict() for name in namespace}
        self._counters = {to_name(name): dict() for name in namespace}
        self._history = {to_name(name): deque() for name in namespace}

    def _retrieve(self, name, store):
        try:
            return  store[to_name(name)]
        except KeyError:
            raise KeyError("Name {} not in namespace".format(to_name(name)))

    def get_parameter(self, name, parameter, default=None):
        params = self._retrieve(name, self._parameters)
        return params.get(parameter, default)

    def set_parameter(self, name, parameter, value):
        params = self._retrieve(name, self._parameters)
        params[parameter] = value
        return True

    def reset_counter(self, name, counter):
        counters_for_a_name = self._retrieve(name, self._counters)
        counters_for_a_name[counter] = 0

    def increment_counter(self, name, counter, increment=1):
        counters_for_a_name = self._retrieve(name, self._counters)
        counters_for_a_name[counter] += increment

    def read_counter(self, name, counter):
        counters_for_a_name = self._retrieve(name, self._counters)
        return counters_for_a_name.get(counter, None)

    def query(self, name, lag):
        history = self._retrieve(name, self._history)
        try:
            record = history[lag]
        except IndexError:
            return None
        return record

    def record(self, name, value):
        history = self._retrieve(name, self._history)
        history.appendleft(value)
        overflow = len(history) - self._depth
        if overflow > 0:
            for _ in range(overflow):
                history.pop()
        return True


class Signal:

    def __init__(self, name, feature, reader, network, character='continuous'):
        self._name = str(name)
        if name is None or len(self._name) == 0:
            raise ValueError("Empty name for a {}".format(self.__class__.__name__))
        assert isinstance(feature, Feature)
        self._feature = feature
        assert isinstance(reader, Reader)
        self._reader = reader
        assert isinstance(network, Network)
        self._network = network
        self._namespace = _build_namespace(self._name, [feature, reader, network],
                                           title=self.__class__.__name__)
        self._character = character

        #super().__init__()

    @property
    def name(self):
        return self._name

    @property
    def namespace(self):
        return self._namespace

    @property
    def character(self):
        return self._character

    def activate(self, assembly_context: AssemblyContext):
        feature_runner = self._feature.activate(assembly_context=assembly_context)
        reader_runner = self._reader.activate(assembly_context=assembly_context)
        network_runner = self._network.activate(assembly_context=assembly_context)

        def signal_runner():
            while True:
                true_value = next(feature_runner)
                reading_value = reader_runner(true_value)
                arrived, arrival_delay = next(network_runner)
                yield (Truth(self.name, true_value),
                       Reading(self.name, reading_value, arrived, arrival_delay))

        return signal_runner()

    def update_parameters(self, assembly_context: AssemblyContext):
        self._feature.update_parameters(assembly_context=assembly_context)
        self._reader.update_parameters(assembly_context=assembly_context)
        self._network.update_parameters(assembly_context=assembly_context)


class _AssemblyComponentTemplate(ABC):

    def __init__(self, name, **parameters):

        name = to_name(name)
        if name is None or len(name) == 0:
            self._name = None
            self._namespace = []
        else:
            self._name = name
            self._namespace = [self._name]
        self._default_parameters = parameters
        self._parameters = self._default_parameters.copy()
        super().__init__()


    @property
    def name(self):
        return self._name

    @property
    def namespace(self):
        return self._namespace

    def update_parameters(self, assembly_context: AssemblyContext, none_is_ok=False):
        for param_name, default_value in self._default_parameters.items():
            if assembly_context is None or self.name is None:
                param_value = default_value
            else:
                param_value = assembly_context.get_parameter(
                    self.name, param_name, default_value)
            if not none_is_ok and param_value is None:
                raise RuntimeError("Parameter {} undefined for {} '{}'".
                    format(param_name, self.__class__.__name__, self.name))
            self._parameters[param_name] = param_value

    @abstractmethod
    def activate(self, assembly_context: AssemblyContext):
        self.update_parameters(assembly_context=assembly_context)
        # return a component runner


class Reader(_AssemblyComponentTemplate):

    @abstractmethod
    def activate(self, assembly_context=None):
        """Return a reading of some feature's value.

           Given a true value of the feature return
           a reading  of this value (i.e. it may add some noise or bias)
           or None it no reading is to be done at this particular tick.
        """
        pass


class Network(_AssemblyComponentTemplate):

    @abstractmethod
    def activate(self, assembly_context=None):
        """Return a generator of network effects on a reading.

           The generator yields a tuple of (arrived, arrival_delay) where:
           - `arrived` shows whether the reading has made is through the network (True)
             or has been lost in transition (False)
           - `arrival_delay` is the delay of reading's arrival in seconds (must be
             ignored if `arrived` is False)
        """
        pass


class Behavior(_AssemblyComponentTemplate):

    def __init__(self, name, **parameters):
        super().__init__(name, **parameters)
        if self.name is None:
            raise ValueError("Empty name for a {}".format(self.__class__.__name__))

    @abstractmethod
    def activate(self, assembly_context=None):
        """Return a generator of true values of a feature that uses this behavior."""
        pass


class Trigger(_AssemblyComponentTemplate):

    def __init__(self, name, active=True, **condition_parameters):
        super().__init__(name, active=active, **condition_parameters)

    @abstractmethod
    def _evaluate_condition(self, assembly_context: AssemblyContext,
                            **condition_parameters):
        """Return whether `condition` is True or False.
           Return None if `condition` cannot be evaluated (no data)
        """
        pass

    def activate(self, assembly_context: AssemblyContext=None):
        self.update_parameters(assembly_context=assembly_context)
        condition_parameters = self._parameters.copy()
        active = condition_parameters.pop('active')
        if not active:
            return None
        else:
            return self._evaluate_condition(assembly_context, **condition_parameters)

    check=activate


class Control(_AssemblyComponentTemplate):

    def __init__(self, name, behavior, when, trigger: Trigger,
                 action: Callable, action_parameters: Dict,
                 priority=0,
                 ):
        """add actions for the cases when trigger returns False or None?"""

        self._behavior = to_name(behavior)
        assert when in ['on_yield', 'on_activation']
        self._when = when
        assert isinstance(trigger, Trigger)
        self._trigger = trigger
        self._priority = priority
        super().__init__(name,
                         action=action,
                         action_parameters=action_parameters)
        if self._trigger.name is not None:
            self._namespace.append(self._trigger.name)

    @property
    def behavior(self):
        return self._behavior

    @property
    def when(self):
        return self._when

    @property
    def trigger(self):
        return self._trigger

    @property
    def priority(self):
        return self._priority

    def activate(self, assembly_context: AssemblyContext):
        self.update_parameters(assembly_context=assembly_context)
        if self._trigger.check(assembly_context=assembly_context):
            self._parameters['action'](assembly_context,
                                       **self._parameters['action_parameters'])

    execute=activate


class Feature(_AssemblyComponentTemplate):

    def __init__(self, name,
                 behaviors: List[Behavior], controls: List[Control] = None,
                 start_with=None):

        assert all([isinstance(bhv, Behavior) for bhv in behaviors])
        self._behaviors = {bhv.name: bhv for bhv in behaviors}
        if start_with is None:
            start_with = behaviors[0].name
        elif not start_with in self._behaviors:
            raise ValueError("`start_with` behavior '{}' is not in feature '{}' "
                             "behaviors: {}".
                             format(start_with, name, list(self._behaviors.keys())))

        if controls is None:
            controls = []
        else:
            assert all([isinstance(ctrl, Control) for ctrl in controls])
        self._controls = {bhv.name: list() for bhv in behaviors}
        for ctrl in controls:
            try:
                self._controls[ctrl.behavior].append(ctrl)
            except KeyError:
                raise ValueError("Behavior {} of control {} is not in feature {}".
                                 format(ctrl.behavior, ctrl.name, self.name))
        for ctrl_list in self._controls.values():
            ctrl_list.sort(key=lambda ctrl: ctrl.priority)

        super().__init__(name, running_behavior=start_with)
        if self.name is None:
            raise ValueError("Empty name for a {}".format(self.__class__.__name__))
        self._namespace = _build_namespace(self.name, behaviors + controls,
                                           title=self.__class__.__name__)


    def activate(self, assembly_context: AssemblyContext):
        """Return a generator of true feature's values.

           Actual values are produced by feature's behaviors.
           Feature manages activating the behaviors and switching between them.
        """

        def runner():
            current_bhv = None
            bhv_runner = iter([])
            while True:
                running_bhv_name = self._parameters['running_behavior']
                if current_bhv is None or running_bhv_name != current_bhv.name:
                    new_bhv = self._behaviors[running_bhv_name]
                    for ctrl in [c for c in self._controls[new_bhv.name]
                                 if c.when == 'on_activation']:
                        ctrl.execute(assembly_context=assembly_context)
                    bhv_runner=new_bhv.activate(assembly_context=assembly_context)
                    current_bhv = new_bhv
                feature_value = next(bhv_runner)
                assembly_context.record(self.name, feature_value)
                for ctrl in [c for c in self._controls[current_bhv.name]
                               if c.when=='on_yield']:
                    ctrl.execute(assembly_context=assembly_context)
                yield feature_value

        return runner()

