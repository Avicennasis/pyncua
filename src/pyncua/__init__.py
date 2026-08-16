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
    "AsyncNCUAClient",
    "CUStatus",
    "CUType",
    "CreditUnionDetails",
    "LocationSearchResponse",
    "NCUAClient",
    "NCUAError",
    "NCUANotFoundError",
    "NCUAServerError",
    "NCUAValidationError",
    "NameSearchResult",
    "Office",
    "OnlineCreditUnion",
    "QuickSearchResult",
    "Region",
    "SearchResponse",
    "SearchType",
    "__version__",
]
