from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Type, TypeVar, cast

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Name(Enum):
    ALLIANCE = "ALLIANCE"
    FB = "FB"
    SGD = "SGD"
    WB = "WB"
    XB = "XB"
    ZFIN = "ZFIN"


@dataclass
class DataProvider:
    environments: List[str]
    name: Name

    @staticmethod
    def from_dict(obj: Any) -> "DataProvider":
        assert isinstance(obj, dict)
        environments = from_list(from_str, obj.get("environments"))
        name = Name(obj.get("name"))
        return DataProvider(environments, name)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environments"] = from_list(from_str, self.environments)
        result["name"] = to_enum(Name, self.name)
        return result


@dataclass
class Global:
    data_providers: List[DataProvider]

    @staticmethod
    def from_dict(obj: Any) -> "Global":
        assert isinstance(obj, dict)
        data_providers = from_list(DataProvider.from_dict, obj.get("data_providers"))
        return Global(data_providers)

    def to_dict(self) -> dict:
        result: dict = {}
        result["data_providers"] = from_list(
            lambda x: to_class(DataProvider, x), self.data_providers
        )
        return result


def global_from_dict(s: Any) -> Global:
    return Global.from_dict(s)


def global_to_dict(x: Global) -> Any:
    return to_class(Global, x)
