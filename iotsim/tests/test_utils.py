import pytest
from iotsim.utils import to_name, RangeChoice

class TestToName:

    def test_to_name_str(self):
        assert to_name('abc') == 'abc'
        assert to_name(123) == '123'

    def test_to_name_none(self):
        assert to_name(None) is None

    def test_to_name_obj_property(self):
        class Named:
            def __init__(self, name):
                self.name = name

        obj = Named('abc')
        assert to_name(obj) == 'abc'
        obj = Named(123)
        assert to_name(obj) == '123'

    def test_to_name_obj_callable(self):
        class Named:
            def __init__(self, name):
                self._name = name
            def name(self):
                return self._name

        obj = Named('abc')
        assert to_name(obj) == 'abc'
        obj = Named(123)
        assert to_name(obj) == '123'

    def test_to_name_obj_no_name_attr(self):
        class Named:
            def __init__(self, name):
                self._name = name

            def __repr__(self):
                return str(self._name)

        obj = Named('abc')
        assert to_name(obj) == 'abc'
        obj = Named(123)
        assert to_name(obj) == '123'


class TestRangeChoice:

    def test_range_choice_single_value(self):

        for v in [1, 1.5, 'abc', False]:
            rc = RangeChoice(v)
            assert rc == v
            assert v == rc
            assert rc != 3
            assert 3 != rc

    def test_range_choice_range(self):

        rc = RangeChoice([1, 2])
        count1 = 0
        count2 = 0
        for _ in range(100):
            count1 += int(rc == 1)
            count2 += int(rc == 2)
        assert 40 <= count1 <= 60
        assert count2 == 100


    def test_range_choice_range_unequal_p(self):

        rc = RangeChoice([1, 2], p=[0.3, 0.7])
        count1 = 0
        count2 = 0
        for _ in range(100):
            count1 += int(rc == 1)
            count2 += int(rc == 2)
        assert 25 <= count1 <= 35
        assert count2 == 100

    def test_range_choice_out_of_range(self):

        rc = RangeChoice([1, 2])
        count0 = 0
        count4 = 0
        for _ in range(100):
            count0 += int(rc == 0)
            count4 += int(rc == 4)
        assert count0 == 0
        assert count4 == 0

    def test_range_choice_range_not_continuous(self):

        rc = RangeChoice([1, 3], p=[0.7, 0.3])
        count1 = 0
        count2 = 0
        count3 = 0
        for _ in range(100):
            count1 += int(rc == 1)
            count2 += int(rc == 2)
            count3 += int(rc == 3)
        assert 60 <= count1 <= 80
        assert count2 == 0
        assert count3 == 100