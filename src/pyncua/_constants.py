from enum import Enum

BASE_URL = "https://mapping.ncua.gov"

VALID_RADII = frozenset({2, 5, 10, 15, 25, 60})


class CUType(str, Enum):
    FEDERAL = "1"
    STATE = "2"


class CUStatus(str, Enum):
    ACTIVE = "A"
    INACTIVE = "I"


class Region(str, Enum):
    EASTERN = "1"
    SOUTHERN = "2"
    WESTERN = "3"
    ONES = "8"


class SearchType(str, Enum):
    ADDRESS = "address"
    NAME = "cuname"
    CHARTER = "cunumber"
