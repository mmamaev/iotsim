import iotsim.core as core
import iotsim.behaviors as behaviors
import iotsim.triggers as triggers
import iotsim.controls as controls
from iotsim.controls import CopyFromHistory as copyhist
import iotsim.features as features
import iotsim.readers as readers
import iotsim.networks as networks


class AssemblyConstructor:

    def __init__(self, name='Assembly', tick=1, history_depth=1):
        self._name=name
        self._tick=tick
        self._history_depth=history_depth
        self._default_reader = readers.PassthroughReader('')
        self._default_network = networks.IdealNetwork('')
        self._readers = dict()
        self._networks = dict()
        self._signals = []
        self._must_signal_parameters = ['name', 'feature']
        # init must fill self._signals with parameters dicts
        # for instantiati on of core.Signal objects

    def attach_reader(self, reader, signal=None):
        assert isinstance(reader, core.Reader)
        if signal is None:
            self._default_reader = reader
        else:
            self._readers[signal] = reader

    def attach_network(self, network, signal=None):
        assert isinstance(network, core.Network)
        if signal is None:
            self._default_network = network
        else:
            self._networks[signal] = network

    @property
    def signals(self):
        return [signal['name'] for signal in self._signals]

    def __call__(self):
        signals = []
        for parameters in self._signals:
            if not all([key in parameters.keys()
                        for key in self._must_signal_parameters]):
                raise KeyError("Missing parameter(s) for a signal. Must have {}. Got {}".
                               format(self._must_signal_parameters, parameters))
            signame = parameters['name']
            parameters['reader'] = self._readers[signame] if signame in self._readers \
                else self._default_reader
            parameters['network'] = self._networks[signame] if signame in self._networks \
                else self._default_network
            signals.append(core.Signal(**parameters))
        return core.Assembly(signals=signals,
                             name=self._name,
                             tick=self._tick,
                             history_depth=self._history_depth
        )


class Flatline(AssemblyConstructor):

    def __init__(self, name='Flatline', level=0, **kwargs):

        super().__init__(name=name, **kwargs)
        self._signals = [dict(name='flatline',
                              feature=core.Feature(
                                'f', [behaviors.FlatlineBehavior('b', level=level)]),
                             )
                         ]


class Seesaw(AssemblyConstructor):

    def __init__(self, name='Seesaw',
                 forward_start=0, forward_increment=1, forward_stop=10,
                 return_start=10, return_increment=-2, return_stop=0,
                 **kwargs):

        super().__init__(name=name, **kwargs)

        forward_bhv = behaviors.LinearBehavior(
            'b.forward', bias=forward_start, increment=forward_increment)
        return_bhv = behaviors.LinearBehavior(
            'b.return', bias=return_start, increment=return_increment)

        trg_to_return = triggers.HistoryOutOfRangeTrigger(
            name='t.to_return',
            component='f', lag=0,
            v0=forward_start, v1=forward_stop,
        )
        ctrl_to_return = controls.UpdateParametersControl(
            name='c.to_return',
            behavior='b.forward',
            when='on_yield',
            trigger=trg_to_return,
            update_choices=[[('f', 'running_behavior', 'b.return')]]
        )

        trg_to_forward = triggers.HistoryOutOfRangeTrigger(
            name='t.to_forward',
            component='f', lag=0,
            v0=return_start, v1=return_stop,
        )
        ctrl_to_forward = controls.UpdateParametersControl(
            name='c.to_forward',
            behavior='b.return',
            when='on_yield',
            trigger=trg_to_forward,
            update_choices=[[('f', 'running_behavior', 'b.forward')]]
        )

        feature = core.Feature(
            name='f',
            behaviors=[forward_bhv, return_bhv],
            controls=[ctrl_to_return, ctrl_to_forward]
        )

        self._signals = [dict(name='seesaw',
                              feature=feature,
                              )
                         ]


class Pulser(AssemblyConstructor):

    def __init__(self, name='Pulser',
                 level1=0, duration1=3, level2=2, duration2=2,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self._signals = [dict(name='pulse',
                              character='discrete',
                              feature=features.PulserFeature(
                                  'f', level1, duration1, level2, duration2),
                              )
                         ]


class SimpleActuator(AssemblyConstructor):

    def __init__(self, name='Actuator',
                 control_name='control',
                 control_off_duration=5,
                 control_on_duration=2,
                 sensor_name='sensor',
                 sensor_init=0,
                 sensor_rise_rate=1,
                 sensor_fall_rate=2,
                 sensor_reaction_delay=0,
                 **kwargs
                 ):

        if (not 'history_depth' in kwargs or
            kwargs['history_depth'] < sensor_reaction_delay + 1):
                kwargs['history_depth'] = sensor_reaction_delay + 1

        super().__init__(name=name, **kwargs)

        control_off_level = 0
        control_on_level = 1

        control_feature = features.PulserFeature("f.control",
            control_off_level, control_off_duration,
            control_on_level, control_on_duration)

        flat_bhv = behaviors.FlatlineBehavior('b.flat', level=sensor_init)
        rising_bhv = behaviors.LinearBehavior(
            'b.rise', bias=sensor_init, increment=sensor_rise_rate)
        falling_bhv = behaviors.LinearBehavior(
            'b.fall', increment=-sensor_fall_rate)

        trg_to_rise = triggers.HistoryConditionTrigger(
            name='',
            component='f.control',
            lag=sensor_reaction_delay,
            condition=lambda x: x == control_on_level
        )

        trg_to_fall = triggers.HistoryConditionTrigger(
            name='',
            component='f.control',
            lag=sensor_reaction_delay,
            condition=lambda x: x == control_off_level
        )

        trg_to_flat = triggers.HistoryConditionTrigger(
            name='',
            component='f.sensor',
            lag=0,
            condition = lambda x: x <= sensor_init,
        )

        ctrl_flat_to_rise = controls.UpdateParametersControl(
            name='',
            behavior='b.flat',
            when='on_yield',
            trigger=trg_to_rise,
            update_choices=[[('f.sensor', 'running_behavior', 'b.rise'),
                             ('b.rise', 'bias', sensor_init)]],
        )

        ctrl_rise_to_fall = controls.UpdateParametersControl(
            name='',
            behavior='b.rise',
            when='on_yield',
            trigger=trg_to_fall,
            update_choices=[[('f.sensor', 'running_behavior', 'b.fall'),
                             ('b.fall', 'bias', copyhist('f.sensor', 0))]],
        )

        ctrl_fall_to_rise = controls.UpdateParametersControl(
            name='',
            behavior='b.fall',
            when='on_yield',
            trigger=trg_to_rise,
            update_choices=[[('f.sensor', 'running_behavior', 'b.rise'),
                             ('b.rise', 'bias', copyhist('f.sensor', 0))]],
        )

        ctrl_fall_to_flat = controls.UpdateParametersControl(
            name='',
            behavior='b.fall',
            when='on_yield',
            trigger=trg_to_flat,
            update_choices=[[('f.sensor', 'running_behavior', 'b.flat')]],
        )

        sensor_feature = core.Feature("f.sensor",
            behaviors=[flat_bhv, rising_bhv, falling_bhv],
            controls=[ctrl_flat_to_rise, ctrl_fall_to_rise, ctrl_rise_to_fall,
                      ctrl_fall_to_flat]
        )

        control_signal = dict(
            name=control_name,
            feature=control_feature,
            character='discrete',
        )

        sensor_signal = dict(
            name=sensor_name,
            feature=sensor_feature,
            character='continuous',
        )

        self._signals=[control_signal, sensor_signal]


