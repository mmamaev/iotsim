import pytest
from iotsim.behaviors import FlatlineBehavior, LinearBehavior
from iotsim.core import AssemblyContext

class TestFlatlineBehavior:

    def test_flatline_bhv_name(self):
        with pytest.raises(ValueError):
            bhv = FlatlineBehavior(name=None)
        with pytest.raises(ValueError):
            bhv = FlatlineBehavior(name="")
        bhv = FlatlineBehavior(name=123)
        assert bhv.name == '123'

    def test_flatline_bhv_default_prm(self):

        for default_level in [2, 'text']:
            bhv = FlatlineBehavior('b', level=default_level)
            runner = bhv.activate()
            for i, v in zip(range(3), runner):
                assert v == default_level

    def test_flatline_bhv_only_context_prm(self):

        bhv = FlatlineBehavior('b')
        context = AssemblyContext(['b'])
        context.set_parameter('b', 'some_other_param', 0)
        for level in [5, 'text']:
            context.set_parameter('b', 'level', level)
            runner = bhv.activate(assembly_context=context)
            for i, v in zip(range(3), runner):
                assert v == level

    def test_flatline_bhv_context_override_prm(self):

        default_level = 2
        bhv = FlatlineBehavior('b', level=default_level)
        context = AssemblyContext(['b'])
        for level in [5, 'text']:
            context.set_parameter('b', 'level', level)
            runner = bhv.activate(assembly_context=context)
            for i, v in zip(range(3), runner):
                assert v == level

    def test_flatline_bhv_missing_param(self):

        bhv = FlatlineBehavior('b')
        with pytest.raises(RuntimeError):
            runner = bhv.activate()

        context = AssemblyContext(['b'])
        with pytest.raises(RuntimeError):
            runner = bhv.activate(assembly_context=context)

        context.set_parameter('b', 'wrong_param', 1)
        with pytest.raises(RuntimeError):
            runner = bhv.activate(assembly_context=context)

    def test_flatline_bhv_bad_context(self):
        bhv = FlatlineBehavior('b')
        context = 'bad value'
        with pytest.raises(AttributeError):
            runner = bhv.activate(assembly_context=context)

        context = AssemblyContext(['other_name'])
        context.set_parameter('other_name', 'level', 1)
        with pytest.raises(KeyError):
            runner = bhv.activate(assembly_context=context)


class TestLinearBehavior:

    def test_linear_bhv_default_prm(self):

        bias = 10
        increment = 2
        bhv = LinearBehavior('b', bias=bias, increment=increment)
        runner = bhv.activate()
        for i, v in zip(range(3), runner):
            assert v == bias + (i+1) * increment

    def test_linear_bhv_only_context_prm(self):

        bhv = LinearBehavior('b')
        context = AssemblyContext(['b'])
        for bias, increment in [(10, 2), (10.5, 1.5)]:
            context.set_parameter('b', 'bias', bias)
            context.set_parameter('b', 'increment', increment)
            runner = bhv.activate(assembly_context=context)
            for i, v in zip(range(3), runner):
                assert v == bias + (i+1) * increment

    def test_flatline_bhv_context_partly_prm(self):

        default_bias = 10
        bias=20
        increment=2
        bhv = LinearBehavior('b', bias=default_bias)
        context = AssemblyContext(['b'])
        context.set_parameter('b', 'increment', increment)
        runner = bhv.activate(assembly_context=context)
        for i, v in zip(range(3), runner):
            assert v == default_bias + (i+1) * increment

        context.set_parameter('b', 'bias', bias)
        runner = bhv.activate(assembly_context=context)
        for i, v in zip(range(3), runner):
            assert v == bias + (i+1) * increment

    def test_linear_bhv_missing_param(self):
        #bias ok but increment is missing
        bhv = LinearBehavior('b', bias=10)
        with pytest.raises(RuntimeError):
            runner = bhv.activate()

        context = AssemblyContext(['b'])
        context.set_parameter('b', 'bias', 1)
        with pytest.raises(RuntimeError):
            runner = bhv.activate(assembly_context=context)
