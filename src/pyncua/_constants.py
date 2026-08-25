from enum import Enum

BASE_URL = "https://mapping.ncua.gov"

VALID_RADII = frozenset({2, 5, 10, 15, 25, 60})

# NCUA silently truncates any `take` above this to 100 rows while still
# reporting the true unpaginated count in totalResultCount, so a caller who
# asks for 500 gets 100 back with no error and no indication of the loss.
# Measured identical across all four paginated endpoints (GetSearchLocations,
# GetNameSearch, GetDetailSearch, and address search) on 2026-08-25.
MAX_TAKE = 100


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
