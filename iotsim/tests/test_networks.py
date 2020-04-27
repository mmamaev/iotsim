import pytest
from iotsim.networks import IdealNetwork, NormalNetwork


class TestIdealNetwork:

    def test_ideal_network_name(self):
        nw = IdealNetwork(name=None)
        assert nw.name is None
        assert nw.namespace == []
        nw = IdealNetwork(name="")
        assert nw.name is None
        assert nw.namespace == []
        nw = IdealNetwork(name=123)
        assert nw.name == '123'
        assert nw.namespace == ['123']

    def test_ideal_network(self):
        nw = IdealNetwork('n')
        runner = nw.activate()
        for _, output in zip(range(3), runner):
            assert output == (True, 0)

class TestLinearBehavior:

    def test_normal_nw_default_prm_deterministic(self):

        delay = 10
        jitter = 0
        drop_rate = 0
        nw = NormalNetwork('n', delay=delay, jitter=jitter, drop_rate=drop_rate)
        runner = nw.activate()
        for _, output in zip(range(3), runner):
            assert output == (True, 10)

    def test_normal_nw_default_prm_stochastic_delay(self):

        delay = 10
        jitter = 1
        drop_rate = 0
        nw = NormalNetwork('n', delay=delay, jitter=jitter, drop_rate=drop_rate)
        runner = nw.activate()
        n=100
        for _, output in zip(range(n), runner):
            arrived, arrival_delay = output
            assert arrived
            assert delay - 4 * jitter <= arrival_delay <= delay + 4 * jitter


    def test_normal_nw_default_prm_stochastic_arrival(self):

        delay = 10
        jitter = 0
        drop_rate = 0.1
        nw = NormalNetwork('n', delay=delay, jitter=jitter, drop_rate=drop_rate)
        runner = nw.activate()
        arrived_counter = 0
        n = 100
        for _, output in zip(range(n), runner):
            arrived, arrival_delay = output
            arrived_counter += 1*int(arrived)
        assert n * (1 - drop_rate * 1.5) <= arrived_counter <= n * (1 - drop_rate * 0.5)


