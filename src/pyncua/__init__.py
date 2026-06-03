"""pyncua — Python client for the NCUA Credit Union Mapping API."""

import importlib.metadata as _meta

try:
    __version__ = _meta.version("pyncua")
except _meta.PackageNotFoundError:
    __version__ = "0.0.0"

from pyncua._constants import CUStatus, CUType, Region, SearchType
from pyncua.async_client import AsyncNCUAClient
from pyncua.client import NCUAClient
from pyncua.exceptions import (
    NCUAError,
    NCUANotFoundError,
    NCUAServerError,
    NCUAValidationError,
)
from pyncua.models import (
    CreditUnionDetails,
    LocationSearchResponse,
    NameSearchResult,
    Office,
    OnlineCreditUnion,
    QuickSearchResult,
    SearchResponse,
)

__all__ = [
    "NCUAClient",
    "AsyncNCUAClient",
    "CUType",
    "CUStatus",
    "Region",
    "SearchType",
    "NCUAError",
    "NCUANotFoundError",
    "NCUAServerError",
    "NCUAValidationError",
    "Office",
    "CreditUnionDetails",
    "LocationSearchResponse",
    "NameSearchResult",
    "OnlineCreditUnion",
    "QuickSearchResult",
    "SearchResponse",
    "__version__",
]
