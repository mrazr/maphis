from enum import IntEnum
import typing


class SIPrefix(IntEnum):
    none = 0,
    d = -1,
    c = -2,
    m = -3,
    micro = -6,
    n = -9,
    p = -12

    def __str__(self) -> str:
        if self == SIPrefix.none:
            return ''
        if self == SIPrefix.micro:
            return 'μ'
        rep = super().__str__()
        return rep.split('.')[1]

    def __repr__(self) -> str:
        if self == SIPrefix.micro:
            return f'SIPrefix.micro'
        return f'SIPrefix.{"none" if self == SIPrefix.none else str(self)}'


class BaseUnit(IntEnum):
    px = 0,
    m = 1,
    none = 2

    def __str__(self) -> str:
        if self == BaseUnit.none:
            return ''
        rep = super().__str__()
        return rep.split('.')[1]

    def __repr__(self) -> str:
        return f'BaseUnit.{"none" if self == BaseUnit.none else str(self)}'


class Unit:
    superscripts: typing.Dict[int, str] = {
        2: '²',
        3: '³'
    }

    def __init__(self, base_unit: BaseUnit, prefix: SIPrefix, dim: int):
        self.base_unit: BaseUnit = base_unit
        self.prefix: SIPrefix = prefix
        self.dim: int = dim
        if self.dim == 0:
            self.base_unit = BaseUnit.none
            self.prefix = SIPrefix.none

    def __str__(self) -> str:
        return f'{self.prefix}{self.base_unit}{"" if self.dim < 2 else self.superscripts[self.dim]}'

    def __repr__(self) -> str:
        return f'Unit(base_unit={repr(self.base_unit)}, prefix={repr(self.prefix)}, dim={repr(self.dim)})'

    def _key(self):
        return self.base_unit, self.prefix, self.dim

    def __hash__(self) -> int:
        return hash(self._key())

    def __eq__(self, other) -> bool:
        return self.__hash__() == hash(other)

    def __mul__(self, other: typing.Union['Unit', 'CompoundUnit']) -> typing.Union['CompoundUnit', 'Unit']:
        if isinstance(other, CompoundUnit):
            return other * self
        elif isinstance(other, Unit):
            if self._key()[:2] == other._key()[:2]:
                return Unit(self.base_unit, prefix=self.prefix, dim=self.dim + other.dim)
                # return CompoundUnit(numerator={unit}, denominator=set())
            return CompoundUnit(numerator={self, other}, denominator=set())
        else:
            raise ValueError(f'Not implemented for values of type {type(other)}')

    def __truediv__(self, other: typing.Union['Unit', 'CompoundUnit']) -> typing.Union['CompoundUnit', 'Unit']:
        if isinstance(other, CompoundUnit):
            recip = CompoundUnit(other.denominator, other.numerator)
            return recip * self
        elif isinstance(other, Unit):
            if self._key()[:2] == other._key()[:2]:
                return Unit(self.base_unit, prefix=self.prefix, dim=self.dim - other.dim)
            return CompoundUnit(numerator={self}, denominator={other})
        else:
            raise ValueError(f'Not implemented for values of type {type(other)}')


class CompoundUnit:
    def __init__(self, numerator: typing.Set[Unit], denominator: typing.Set[Unit]):
        self.numerator: typing.Set[Unit] = numerator
        self.denominator: typing.Set[Unit] = denominator

        self._simplify2()

    def _simplify(self):
        _num = self.numerator.difference(self.denominator)
        _den = self.denominator.difference(self.numerator)

        self.numerator = _num
        self.denominator = _den

    def _simplify2(self):
        _num_units: typing.Dict[typing.Tuple[BaseUnit, SIPrefix], int] = {}
        for unit in self.numerator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] += unit.dim
        for unit in self.denominator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] -= unit.dim

        self.numerator = {Unit(base_unit=base_unit, prefix=prefix, dim=dim) for (base_unit, prefix), dim in _num_units.items() if dim > 0}
        self.denominator = {Unit(base_unit=base_unit, prefix=prefix, dim=abs(dim)) for (base_unit, prefix), dim in _num_units.items() if dim < 0}

    def _multiply(self, other: 'CompoundUnit') -> 'CompoundUnit':
        _num_units: typing.Dict[typing.Tuple[BaseUnit, SIPrefix], int] = {}
        for unit in self.numerator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] += unit.dim
        for unit in other.numerator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] += unit.dim

        for unit in self.denominator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] -= unit.dim
        for unit in other.denominator:
            _num_units.setdefault(unit._key()[:2], 0)
            _num_units[unit._key()[:2]] -= unit.dim

        num = {Unit(base_unit=base_unit, prefix=prefix, dim=dim) for (base_unit, prefix), dim in _num_units.items() if dim > 0}
        den = {Unit(base_unit=base_unit, prefix=prefix, dim=abs(dim)) for (base_unit, prefix), dim in _num_units.items() if dim < 0}

        return CompoundUnit(numerator=num, denominator=den)

    def __str__(self) -> str:
        first_part = '⋅'.join([str(unit) for unit in self.numerator])
        sec_part = '⋅'.join([str(unit) for unit in self.denominator])

        final_part = first_part
        if len(sec_part) > 0:
            final_part += ' / '
            final_part += sec_part
        return final_part

    def __repr__(self) -> str:
        return f'CompoundUnit(numerator={repr(self.numerator)}, denominator={repr(self.denominator)})'

    def __mul__(self, other: typing.Union['CompoundUnit', Unit]) -> 'CompoundUnit':
        if isinstance(other, Unit):
            c_unit = CompoundUnit(numerator={other}, denominator=set())
            return self._multiply(c_unit)
        elif isinstance(other, CompoundUnit):
            return self._multiply(other)

        raise ValueError(f'Not implemented for values of type {type(other)}')

    def __truediv__(self, other: typing.Union['CompoundUnit', Unit]) -> 'CompoundUnit':
        if isinstance(other, CompoundUnit):
            recip = CompoundUnit(other.denominator, other.numerator)
        elif isinstance(other, Unit):
            recip = CompoundUnit(numerator=set(), denominator={other})
        else:
            raise ValueError(f"Not implemented for values of type {type(other)}")

        return self * recip

    def __eq__(self, other):
        if isinstance(other, CompoundUnit):
            return self.numerator == other.numerator and self.denominator == other.denominator
        return False


class Value:
    def __init__(self, value: typing.Any, unit: typing.Union[Unit, CompoundUnit]):
        self._value: typing.Any = value
        self.unit: typing.Union[Unit, CompoundUnit] = unit
        self._str_rep: str = ''
        self._update_str_rep()

    @property
    def value(self) -> typing.Any:
        return self._value

    @value.setter
    def value(self, val: typing.Any):
        self._value = val
        self._update_str_rep()

    def _update_str_rep(self):
        if type(self._value) == float:
            val_str = f'{self._value:.2f} {self.unit}'
        else:
            val_str = f'{self.value} {self.unit}'
        self._str_rep = val_str

    def __str__(self) -> str:
        return self._str_rep

    def __repr__(self) -> str:
        return f'Value(value={repr(self.value)}, unit={repr(self.unit)})'

    def __mul__(self, other) -> 'Value':
        if isinstance(other, float):
            return Value(other * self.value, self.unit)
        elif isinstance(other, int):
            return Value(other * self.value, self.unit)
        elif isinstance(other, Value):
            new_unit = self.unit * other.unit
            return Value(self.value * other.value, new_unit)
        raise ValueError(f'Not implemented for values of type {(type(other))}')

    def __truediv__(self, other) -> 'Value':
        if isinstance(other, float):
            return self * (1.0/other)
        elif isinstance(other, int):
            return self * (1.0 / other)
        elif isinstance(other, Value):
            new_unit = self.unit / other.unit
            return Value(self.value / other.value, new_unit)
        raise ValueError(f'Not implemented for values of type {(type(other))}')


class UnitStore:
    def __init__(self):
        self.units: typing.Dict[str, typing.Union[Unit, CompoundUnit]] = {
            'px': Unit(BaseUnit.px, prefix=SIPrefix.none, dim=1),
            'm' : Unit(BaseUnit.m,  prefix=SIPrefix.none, dim=1),
            'cm': Unit(BaseUnit.m,  prefix=SIPrefix.c, dim=1),
            'mm': Unit(BaseUnit.m,  prefix=SIPrefix.m, dim=1),
            'um': Unit(BaseUnit.m,  prefix=SIPrefix.micro, dim=1),
            'nm': Unit(BaseUnit.m,  prefix=SIPrefix.n, dim=1),
            'pm': Unit(BaseUnit.m,  prefix=SIPrefix.p, dim=1),
            ' ': Unit(BaseUnit.none, prefix=SIPrefix.none, dim=0),
        }
        self.units['px/m']  = CompoundUnit({self.units['px']},  {self.units['m']})
        self.units['px/cm'] = CompoundUnit({self.units['px']}, {self.units['cm']})
        self.units['px/mm'] = CompoundUnit({self.units['px']}, {self.units['mm']})
        self.units['px/um'] = CompoundUnit({self.units['px']}, {self.units['um']})
        self.units['px/nm'] = CompoundUnit({self.units['px']}, {self.units['nm']})
        self.units['px/pm'] = CompoundUnit({self.units['px']}, {self.units['pm']})

        self.default_prefixes: typing.Dict[BaseUnit, SIPrefix] = {
            BaseUnit.m: SIPrefix.m,
            BaseUnit.px: SIPrefix.none,
            BaseUnit.none: SIPrefix.none
        }

    def get_default_unit(self, unit: typing.Union[Unit, CompoundUnit]) -> typing.Union[Unit, CompoundUnit]:
        if isinstance(unit, Unit):
            return Unit(unit.base_unit, prefix=self.default_prefixes[unit.base_unit], dim=unit.dim)

        num_units = {Unit(unit_.base_unit, prefix=self.default_prefixes[unit_.base_unit], dim=unit_.dim) for unit_ in unit.numerator}
        den_units = {Unit(unit_.base_unit, prefix=self.default_prefixes[unit_.base_unit], dim=unit_.dim) for unit_ in unit.denominator}

        return CompoundUnit(num_units, den_units)


def convertible(unit1: typing.Union[Unit, CompoundUnit], unit2: typing.Union[Unit, CompoundUnit]) -> bool:
    if type(unit1) != type(unit2):
        return False

    if isinstance(unit1, Unit):
        bu1, dim1 = unit1.base_unit, unit1.dim
        bu2, dim2 = unit2.base_unit, unit2.dim

        return (bu1, dim1) == (bu2, dim2)
    num1 = {(unit.base_unit, unit.dim) for unit in unit1.numerator}
    num2 = {(unit.base_unit, unit.dim) for unit in unit2.numerator}

    den1 = {(unit.base_unit, unit.dim) for unit in unit1.denominator}
    den2 = {(unit.base_unit, unit.dim) for unit in unit2.denominator}

    return num1 == num2 and den1 == den2


def convert_value(value: Value, unit: typing.Union[Unit, CompoundUnit]) -> Value:
    if not convertible(value.unit, unit):
        raise ValueError(f'Conversion unsupported for {value.unit} and {unit}')

    # if isinstance(unit, CompoundUnit):
    #     num_multiplicators: typing.Dict[typing.Tuple[BaseUnit, int], typing.Tuple[SIPrefix, SIPrefix]] = {}
    #     den_multiplicators: typing.Dict[typing.Tuple[BaseUnit, int], typing.Tuple[SIPrefix, SIPrefix]] = {}
    #
    #     for _unit in value.unit.numerator:
    #         num_multiplicators.setdefault((_unit.base_unit, _unit.dim), 0)
    #         num_multiplicators[(_unit.base_unit, _unit.dim)] += int(_unit.prefix)
    #     for _unit in unit.numerator:
    #         num_multiplicators.setdefault((_unit.base_unit, _unit.dim), 0)
    #         num_multiplicators[(_unit.base_unit, _unit.dim)] -= int(_unit.prefix)
    #     for _unit in value.unit.denominator:
    #         den_multiplicators.setdefault((_unit.base_unit, _unit.dim), 0)
    #         den_multiplicators[(_unit.base_unit, _unit.dim)] += int(_unit.prefix)
    #     for _unit in unit.denominator:
    #         den_multiplicators.setdefault((_unit.base_unit, _unit.dim), 0)
    #         den_multiplicators[(_unit.base_unit, _unit.dim)] -= int(_unit.prefix)
    #
    #     numerator: typing.Set[Unit] = set()
    #     new_value = value.value
    #     for (base_unit, dim), mult in num_multiplicators.items():
    #         # diffs = [(int(prefix) - mult, prefix) for prefix in list(SIPrefix)]
    #         # exponent, prefix = min(diffs, key=lambda t: abs(t[0]))
    #         unit_ = Unit(base_unit, prefix, dim)
    #         new_value /= 10**exponent
    #         numerator.add(unit_)
    #
    #     denominator: typing.Set[Unit] = set()
    #     for (base_unit, dim), mult in den_multiplicators.items():
    #         diffs = [(int(prefix) - mult, prefix) for prefix in list(SIPrefix)]
    #         exponent, prefix = min(diffs, key=lambda t: abs(t[0]))
    #         unit_ = Unit(base_unit, prefix, dim)
    #         new_value *= 10**exponent
    #         denominator.add(unit_)
    #     return Value(new_value, CompoundUnit(numerator, denominator))
    if isinstance(unit, CompoundUnit):
        num_target_units: typing.Dict[typing.Tuple[BaseUnit, int], Unit] = {(_unit.base_unit, _unit.dim): _unit for _unit in unit.numerator}
        den_target_units: typing.Dict[typing.Tuple[BaseUnit, int], Unit] = {(_unit.base_unit, _unit.dim): _unit for _unit in
                                                                            unit.denominator}
        new_value = value.value
        for _unit in value.unit.numerator:
            target = num_target_units[(_unit.base_unit, _unit.dim)]
            exponent = int(_unit.prefix) - int(target.prefix)
            new_value *= (10**exponent) ** _unit.dim
        for _unit in value.unit.denominator:
            target = den_target_units[(_unit.base_unit, _unit.dim)]
            exponent = int(_unit.prefix) - int(target.prefix)
            new_value /= (10 ** exponent) ** _unit.dim
        return Value(new_value, CompoundUnit(set(num_target_units.values()), set(den_target_units.values())))
    elif isinstance(unit, Unit):
        new_value = value.value * (10 ** (int(value.unit.prefix) - int(unit.prefix))) ** unit.dim
        return Value(new_value, unit)
    raise ValueError(f'Not implemented for types {type(value)} and {type(unit)}')

