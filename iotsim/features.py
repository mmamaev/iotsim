import iotsim.core as core
import iotsim.behaviors as behaviors
import iotsim.triggers as triggers
import iotsim.controls as controls

class PulserFeature(core.Feature):
    def __init__(self, name, level1, duration1, level2, duration2):

        bhv1 = behaviors.FlatlineBehavior('b.1', level=level1)
        bhv2 = behaviors.FlatlineBehavior('b.2', level=level2)

        trg_to_2 = triggers.CounterTrigger(
            name='',
            component=name,
            counter='b.1.duration',
            threshold=duration1,
        )

        trg_to_1 = triggers.CounterTrigger(
            name='',
            component=name,
            counter='b.2.duration',
            threshold=duration2,
        )

        ctrl_on_1 = controls.ResetCounterControl(
            name='',
            behavior='b.1',
            when='on_activation',
            trigger=triggers.Always(),
            component=name,
            counter='b.1.duration'
        )

        ctrl_with_1 = controls.IncrementCounterControl(
            name='',
            behavior='b.1',
            when='on_yield',
            trigger=triggers.Always(),
            component=name,
            counter='b.1.duration'
        )

        ctrl_to_2 = controls.UpdateParametersControl(
            name='',
            behavior='b.1',
            when='on_yield',
            trigger=trg_to_2,
            update_choices=[[(name, 'running_behavior', 'b.2')]],
            priority=1
        )

        ctrl_on_2 = controls.ResetCounterControl(
            name='',
            behavior='b.2',
            when='on_activation',
            trigger=triggers.Always(),
            component=name,
            counter='b.2.duration'
        )

        ctrl_with_2 = controls.IncrementCounterControl(
            name='',
            behavior='b.2',
            when='on_yield',
            trigger=triggers.Always(),
            component=name,
            counter='b.2.duration'
        )

        ctrl_to_1 = controls.UpdateParametersControl(
            name='',
            behavior='b.2',
            when='on_yield',
            trigger=trg_to_1,
            update_choices=[[(name, 'running_behavior', 'b.1')]],
            priority=1
        )

        super().__init__(
            name=name,
            behaviors=[bhv1, bhv2],
            controls=[ctrl_on_1, ctrl_with_1, ctrl_to_2,
                      ctrl_on_2, ctrl_with_2, ctrl_to_1]
        )
