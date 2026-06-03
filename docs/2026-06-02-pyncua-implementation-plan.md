# pyncua Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python client library wrapping the NCUA Credit Union Mapping API (`mapping.ncua.gov/api`) with typed Pydantic models and httpx transport.

**Architecture:** Single package with shared request-building logic, separate sync/async clients, Pydantic v2 response models with camelCase alias mapping, and a thin exception hierarchy. Tests mock HTTP with respx; opt-in live tests hit the real API.

**Tech Stack:** Python 3.10+, httpx, Pydantic v2, uv, pytest, respx, ruff

**Design Spec:** `/tmp/pyncua/docs/2026-06-02-pyncua-design.md`

**Ticket:** Redmine #4465

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, dependencies, tool config |
| `src/pyncua/__init__.py` | Public API re-exports |
| `src/pyncua/_constants.py` | Base URL, valid radii, enums (CUType, CUStatus, Region, SearchType) |
| `src/pyncua/exceptions.py` | NCUAError hierarchy |
| `src/pyncua/models.py` | Pydantic response models (Office, CreditUnionDetails, wrappers) |
| `src/pyncua/_requests.py` | Shared request-building functions (body dicts, URL construction) |
| `src/pyncua/client.py` | NCUAClient (sync, httpx.Client) |
| `src/pyncua/async_client.py` | AsyncNCUAClient (async, httpx.AsyncClient) |
| `tests/conftest.py` | Shared fixtures, JSON response samples |
| `tests/test_models.py` | Pydantic model parsing tests |
| `tests/test_client.py` | Sync client tests with respx mocking |
| `tests/test_async_client.py` | Async client tests with respx mocking |
| `tests/test_live.py` | Opt-in integration tests against real API |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/pyncua/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create the project directory structure**

```bash
cd /tmp/pyncua
mkdir -p src/pyncua tests
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pyncua"
version = "1.0.0"
description = "Python client for the NCUA Credit Union Mapping API"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "respx>=0.21",
    "ruff>=0.4",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "live: hits the real NCUA API (deselect with '-m not live')",
]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.hatch.build.targets.wheel]
packages = ["src/pyncua"]
```

- [ ] **Step 3: Write empty __init__.py files**

`src/pyncua/__init__.py`:
```python
"""pyncua — Python client for the NCUA Credit Union Mapping API."""
```

`tests/__init__.py`: empty file.

- [ ] **Step 4: Initialize git and install dependencies**

```bash
cd /tmp/pyncua
git init
uv venv
uv pip install -e ".[dev]"
```

- [ ] **Step 5: Verify pytest runs with zero tests**

```bash
cd /tmp/pyncua && uv run pytest -v
```
Expected: `no tests ran` / exit 5 (no tests collected — OK at this stage).

- [ ] **Step 6: Create .gitignore**

```
__pycache__/
*.egg-info/
.venv/
dist/
.ruff_cache/
*.pyc
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/ tests/ .gitignore
git commit -m "chore: scaffold pyncua project with pyproject.toml and src layout"
```

---

### Task 2: Exceptions and Constants

**Files:**
- Create: `src/pyncua/exceptions.py`
- Create: `src/pyncua/_constants.py`

- [ ] **Step 1: Write exceptions.py**

```python
class NCUAError(Exception):
    """Base exception for all pyncua errors."""


class NCUANotFoundError(NCUAError):
    """Charter number not found (API returned isError=true)."""


class NCUAValidationError(NCUAError):
    """Invalid request parameters (400 or client-side validation)."""


class NCUAServerError(NCUAError):
    """NCUA API returned a 5xx error."""
```

- [ ] **Step 2: Write _constants.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/pyncua/exceptions.py src/pyncua/_constants.py
git commit -m "feat: add exception hierarchy and constants/enums"
```

---

### Task 3: Pydantic Response Models

**Files:**
- Create: `src/pyncua/models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the test fixtures in conftest.py**

```python
import pytest


@pytest.fixture()
def office_json():
    return {
        "addressLatitude": 38.90172,
        "addressLongitude": -77.02763,
        "creditUnionName": "SIGNAL FINANCIAL",
        "creditUnionSiteName": "City Center",
        "creditUnionNumber": 5571,
        "city": "Washington",
        "cityPhysical": None,
        "country": "United States",
        "isMainOffice": False,
        "isMdi": False,
        "bilingual_Services": True,
        "credit_Builder": False,
        "financial_Counseling": True,
        "first_Time_Homebuyer_Program": False,
        "inSchoolBranch": False,
        "low_cost_wire_transfers": True,
        "no_Cost_Tax_Preparation": False,
        "no_Cost_Share_Drafts": True,
        "palS_I": False,
        "palS_II": False,
        "phone": "3019339100",
        "siteFunctions": "Member Services;ATM;;",
        "siteName": None,
        "siteId": 51878,
        "state": "DC",
        "url": "https://www.signalfinancialfcu.org",
        "zipcode": "20005-4269",
        "distance": 0.189,
        "formattedDistance": None,
        "index": 0,
        "street": "1101 New York Ave NW",
        "fieldOfMembership": False,
        "siteIdAndCUNumber": "51878_5571",
        "numericFields": None,
    }


@pytest.fixture()
def location_search_json(office_json):
    return {
        "latitude": 38.9042,
        "longitude": -77.0291,
        "valid": True,
        "list": [office_json],
        "totalResults": 90,
        "statusCode": 0,
    }


@pytest.fixture()
def credit_union_details_json():
    return {
        "creditUnionName": "NAVY FEDERAL CREDIT UNION",
        "creditUnionCharter": "5536",
        "creditUnionType": "FCU",
        "creditUnionStatus": "Active",
        "creditUnionCorp": "No",
        "creditUnionYear": "1947",
        "creditUnionIssuedDate": "07/17/1947",
        "creditUnionInsuredDate": "01/04/1971",
        "creditUnionCharterState": "",
        "creditUnionRegion": "8 - ONES",
        "creditUnionFom": "Military",
        "creditUnionIli": "No",
        "creditUnionFhlb": "Yes",
        "creditUnionAssets": "203558954708",
        "assetsFormatted": "$203,558,954,708",
        "creditUnionPeerGroup": "6 - $500,000,000 and greater",
        "creditUnionNom": "15350733",
        "membersFormatted": "15,350,733",
        "creditUnionAddress": "820 Follin Ln SE",
        "creditUnionAddress2": "",
        "creditUnionCity": "Vienna",
        "creditUnionState": "VA",
        "creditUnionZip": "22180",
        "creditUnionCountry": "United States",
        "creditUnionCounty": "Fairfax",
        "creditUnionPhone": "8888426328",
        "phoneFormatted": "888-842-6328",
        "creditUnionWebsite": "http://www.navyfcu.org",
        "creditUnionCeo": "Dietrich Kuhlmann",
        "isError": False,
        "errorMessage": None,
        "locatorButtonVisible": True,
        "isCorpCu": False,
        "callReportCycleDates": {"March-2026": "03/31/2026"},
        "profileCycleDates": {"Current profile": "3/31/2026 12:00:00 AM"},
        "urLs": {},
    }


@pytest.fixture()
def name_search_json():
    return {
        "totalResultCount": 1,
        "results": [{"charterNumber": 5536, "name": "NAVY FEDERAL CREDIT UNION"}],
    }


@pytest.fixture()
def detail_search_json():
    return {
        "totalResultCount": 1,
        "results": [
            {
                "charterNumber": 5536,
                "name": "NAVY FEDERAL CREDIT UNION",
                "city": "VIENNA",
                "state": "VA",
                "isCorporate": False,
                "isActive": True,
            }
        ],
    }


@pytest.fixture()
def online_cu_json():
    return {
        "totalResultCount": 1,
        "results": [
            {
                "charterNumber": 67955,
                "name": "ALLIANT",
                "website": "http://www.alliantcreditunion.org",
                "phone": "8003281935",
            }
        ],
    }


@pytest.fixture()
def error_details_json():
    return {
        "creditUnionName": None,
        "creditUnionCharter": None,
        "isError": True,
        "errorMessage": "Charter number not found",
    }
```

- [ ] **Step 2: Write test_models.py**

```python
from pyncua.models import (
    CreditUnionDetails,
    LocationSearchResponse,
    NameSearchResult,
    Office,
    OnlineCreditUnion,
    QuickSearchResult,
    SearchResponse,
)


class TestOffice:
    def test_parse_from_api_json(self, office_json):
        office = Office.model_validate(office_json)
        assert office.credit_union_name == "SIGNAL FINANCIAL"
        assert office.charter_number == 5571
        assert office.latitude == 38.90172
        assert office.longitude == -77.02763
        assert office.is_main_office is False
        assert office.site_id == 51878
        assert office.distance == 0.189
        assert office.state == "DC"

    def test_site_functions_parsed_from_semicolons(self, office_json):
        office = Office.model_validate(office_json)
        assert office.site_functions == ["Member Services", "ATM"]

    def test_url_can_be_none(self, office_json):
        office_json["url"] = None
        office = Office.model_validate(office_json)
        assert office.url is None

    def test_distance_none_for_non_address_search(self, office_json):
        office_json["distance"] = None
        office = Office.model_validate(office_json)
        assert office.distance is None

    def test_service_flags(self, office_json):
        office = Office.model_validate(office_json)
        assert office.bilingual_services is True
        assert office.financial_counseling is True
        assert office.is_mdi is False


class TestLocationSearchResponse:
    def test_parse_from_api_json(self, location_search_json):
        resp = LocationSearchResponse.model_validate(location_search_json)
        assert resp.latitude == 38.9042
        assert resp.valid is True
        assert resp.total_results == 90
        assert len(resp.offices) == 1
        assert resp.offices[0].credit_union_name == "SIGNAL FINANCIAL"

    def test_empty_results(self, location_search_json):
        location_search_json["list"] = []
        location_search_json["totalResults"] = 0
        resp = LocationSearchResponse.model_validate(location_search_json)
        assert resp.offices == []
        assert resp.total_results == 0


class TestCreditUnionDetails:
    def test_parse_from_api_json(self, credit_union_details_json):
        details = CreditUnionDetails.model_validate(credit_union_details_json)
        assert details.name == "NAVY FEDERAL CREDIT UNION"
        assert details.charter_number == 5536
        assert details.cu_type == "FCU"
        assert details.status == "Active"
        assert details.is_corporate is False
        assert details.charter_year == "1947"
        assert details.assets == 203558954708
        assert details.number_of_members == 15350733
        assert details.ceo == "Dietrich Kuhlmann"
        assert details.website == "http://www.navyfcu.org"

    def test_charter_number_coerced_from_string(self, credit_union_details_json):
        assert isinstance(
            CreditUnionDetails.model_validate(credit_union_details_json).charter_number, int
        )

    def test_cycle_dates_parsed(self, credit_union_details_json):
        details = CreditUnionDetails.model_validate(credit_union_details_json)
        assert "March-2026" in details.call_report_cycle_dates
        assert details.call_report_cycle_dates["March-2026"] == "03/31/2026"

    def test_low_income_and_fhlb_booleans(self, credit_union_details_json):
        details = CreditUnionDetails.model_validate(credit_union_details_json)
        assert details.low_income_designation is False
        assert details.member_of_fhlb is True


class TestSearchResponse:
    def test_name_search(self, name_search_json):
        resp = SearchResponse[NameSearchResult].model_validate(name_search_json)
        assert resp.total_result_count == 1
        assert resp.results[0].charter_number == 5536
        assert resp.results[0].name == "NAVY FEDERAL CREDIT UNION"

    def test_detail_search(self, detail_search_json):
        resp = SearchResponse[QuickSearchResult].model_validate(detail_search_json)
        assert resp.total_result_count == 1
        assert resp.results[0].is_active is True
        assert resp.results[0].city == "VIENNA"

    def test_online_cu(self, online_cu_json):
        resp = SearchResponse[OnlineCreditUnion].model_validate(online_cu_json)
        assert resp.total_result_count == 1
        assert resp.results[0].name == "ALLIANT"
        assert resp.results[0].phone == "8003281935"

    def test_empty_results(self):
        raw = {"totalResultCount": 0, "results": []}
        resp = SearchResponse[NameSearchResult].model_validate(raw)
        assert resp.total_result_count == 0
        assert resp.results == []
```

- [ ] **Step 3: Run tests — they should all fail (models don't exist yet)**

```bash
cd /tmp/pyncua && uv run pytest tests/test_models.py -v
```
Expected: ImportError / FAIL on every test.

- [ ] **Step 4: Write models.py**

```python
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class _BaseModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        alias_generator=to_camel,
        extra="ignore",
    )


class Office(_BaseModel):
    credit_union_name: str
    credit_union_site_name: str = Field(alias="creditUnionSiteName")
    charter_number: int = Field(alias="creditUnionNumber")
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    latitude: float = Field(alias="addressLatitude")
    longitude: float = Field(alias="addressLongitude")
    is_main_office: bool
    phone: str
    url: str | None = None
    site_functions: list[str] = Field(alias="siteFunctions")
    site_id: int
    distance: float | None = None

    is_mdi: bool = Field(alias="isMdi")
    bilingual_services: bool = Field(alias="bilingual_Services")
    credit_builder: bool = Field(alias="credit_Builder")
    financial_counseling: bool = Field(alias="financial_Counseling")
    first_time_homebuyer: bool = Field(alias="first_Time_Homebuyer_Program")
    in_school_branch: bool = Field(alias="inSchoolBranch")
    low_cost_wires: bool = Field(alias="low_cost_wire_transfers")
    no_cost_tax_prep: bool = Field(alias="no_Cost_Tax_Preparation")
    no_cost_share_drafts: bool = Field(alias="no_Cost_Share_Drafts")
    payday_alternative_1: bool = Field(alias="palS_I")
    payday_alternative_2: bool = Field(alias="palS_II")

    @field_validator("site_functions", mode="before")
    @classmethod
    def _parse_site_functions(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(";") if s.strip()]
        return v


def _yes_no_to_bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    return v.strip().lower() == "yes"


class CreditUnionDetails(_BaseModel):
    name: str = Field(alias="creditUnionName")
    charter_number: int = Field(alias="creditUnionCharter")
    cu_type: str = Field(alias="creditUnionType")
    status: str = Field(alias="creditUnionStatus")
    is_corporate: bool = Field(alias="creditUnionCorp")
    charter_year: str = Field(alias="creditUnionYear")
    charter_issue_date: str = Field(alias="creditUnionIssuedDate")
    insured_date: str = Field(alias="creditUnionInsuredDate")
    charter_state: str = Field(alias="creditUnionCharterState")
    region: str = Field(alias="creditUnionRegion")
    field_of_membership: str = Field(alias="creditUnionFom")
    low_income_designation: bool = Field(alias="creditUnionIli")
    member_of_fhlb: bool = Field(alias="creditUnionFhlb")
    assets: int = Field(alias="creditUnionAssets")
    assets_formatted: str
    peer_group: str = Field(alias="creditUnionPeerGroup")
    number_of_members: int = Field(alias="creditUnionNom")
    members_formatted: str
    address: str = Field(alias="creditUnionAddress")
    address2: str = Field(alias="creditUnionAddress2")
    city: str = Field(alias="creditUnionCity")
    state: str = Field(alias="creditUnionState")
    zip: str = Field(alias="creditUnionZip")
    country: str = Field(alias="creditUnionCountry")
    county: str = Field(alias="creditUnionCounty")
    phone: str = Field(alias="creditUnionPhone")
    phone_formatted: str
    website: str | None = Field(alias="creditUnionWebsite", default=None)
    ceo: str = Field(alias="creditUnionCeo")
    call_report_cycle_dates: dict[str, str] = Field(default_factory=dict)
    profile_cycle_dates: dict[str, str] = Field(default_factory=dict)

    @field_validator("call_report_cycle_dates", "profile_cycle_dates", mode="before")
    @classmethod
    def _coerce_null_dict(cls, v):
        return v if v is not None else {}

    @field_validator("is_corporate", "low_income_designation", "member_of_fhlb", mode="before")
    @classmethod
    def _coerce_yes_no(cls, v: str | bool) -> bool:
        return _yes_no_to_bool(v)


class NameSearchResult(_BaseModel):
    charter_number: int
    name: str


class QuickSearchResult(_BaseModel):
    charter_number: int
    name: str
    city: str
    state: str
    is_corporate: bool
    is_active: bool


class OnlineCreditUnion(_BaseModel):
    charter_number: int
    name: str
    website: str
    phone: str


class LocationSearchResponse(_BaseModel):
    latitude: float
    longitude: float
    valid: bool
    status_code: int = Field(alias="statusCode")
    total_results: int = Field(alias="totalResults")
    offices: list[Office] = Field(alias="list")


class SearchResponse(_BaseModel, Generic[T]):
    total_result_count: int = Field(alias="totalResultCount")
    results: list[T]
```

- [ ] **Step 5: Run tests — they should all pass**

```bash
cd /tmp/pyncua && uv run pytest tests/test_models.py -v
```
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/pyncua/models.py tests/conftest.py tests/test_models.py
git commit -m "feat: add Pydantic response models with tests"
```

---

### Task 4: Request Builders

**Files:**
- Create: `src/pyncua/_requests.py`

- [ ] **Step 1: Write _requests.py**

This module builds the raw dicts/URLs that both sync and async clients use. No HTTP calls here.

```python
from __future__ import annotations

from pyncua._constants import VALID_RADII, SearchType
from pyncua.exceptions import NCUAValidationError

_FILTER_KWARG_TO_API = {
    "main_office_only": "is_mainOffice",
    "atm": "is_atm",
    "drive_thru": "is_drive",
    "shared_service": "is_shared",
    "bilingual": "is_bilingual",
    "credit_builder": "is_credit_builder",
    "financial_counseling": "is_fin_counseling",
    "first_time_homebuyer": "is_homebuyer",
    "in_school_branch": "is_school",
    "low_cost_wires": "is_low_wire",
    "no_cost_share_drafts": "is_no_draft",
    "no_cost_tax_prep": "is_no_tax",
    "payday_alternative": "is_payday",
    "mdi": "is_mdi",
    "member_services": "is_member",
}


def build_search_locations_body(
    search_text: str,
    search_type: SearchType,
    *,
    radius: int | None = None,
    skip: int = 0,
    take: int = 100,
    **filters: bool,
) -> dict:
    if search_type == SearchType.ADDRESS:
        if radius is not None and radius not in VALID_RADII:
            raise NCUAValidationError(
                f"radius must be one of {sorted(VALID_RADII)}, got {radius}"
            )
        rd_radius = radius if radius is not None else 25
    else:
        rd_radius = None

    body: dict = {
        "searchText": str(search_text),
        "rdSearchType": search_type.value,
        "rdSearchRadiusList": rd_radius,
        "skip": skip,
        "take": take,
        "sort_item": "distance",
        "sort_direction": "asc",
    }

    for kwarg, api_key in _FILTER_KWARG_TO_API.items():
        body[api_key] = filters.get(kwarg, False)

    return body


def build_name_search_body(name: str, *, skip: int = 0, take: int = 100) -> dict:
    return {"cuName": name, "skip": skip, "take": take}


def build_detail_search_body(
    *,
    name: str | None = None,
    cu_type: str | None = None,
    status: str | None = None,
    region: str | None = None,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    fom_type: str | None = None,
    low_income: bool | None = None,
    is_mdi: bool | None = None,
    skip: int = 0,
    take: int = 20,
) -> dict:
    return {
        "cuName": name,
        "cuType": cu_type,
        "cuStatus": status,
        "region": region,
        "state": state,
        "city": city,
        "zipCode": zip_code,
        "fomType": fom_type,
        "lowIncome": str(low_income).lower() if low_income is not None else None,
        "isMdi": str(is_mdi).lower() if is_mdi is not None else None,
        "skip": skip,
        "take": take,
    }


def build_download_url(
    base_url: str,
    endpoint: str,
    charter: int,
    cycle_date: str,
    is_corporate: bool = False,
    is_snapshot: bool | None = None,
) -> str:
    url = f"{base_url}{endpoint}/{charter}"
    params = [f"isCorpCU={str(is_corporate).lower()}", f"cycleDate={cycle_date}"]
    if is_snapshot is not None:
        params.append(f"isSnapshot={str(is_snapshot).lower()}")
    return f"{url}?{'&'.join(params)}"
```

- [ ] **Step 2: Commit**

```bash
git add src/pyncua/_requests.py
git commit -m "feat: add request builder functions"
```

---

### Task 5: Sync Client

**Files:**
- Create: `src/pyncua/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write test_client.py with core search tests**

```python
import httpx
import pytest
import respx

from pyncua.client import NCUAClient
from pyncua.exceptions import (
    NCUANotFoundError,
    NCUAServerError,
    NCUAValidationError,
)


@pytest.fixture()
def client():
    c = NCUAClient(timeout=5.0)
    yield c
    c.close()


class TestFindOfficesByName:
    @respx.mock
    def test_returns_location_search_response(self, client, location_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        result = client.find_offices_by_name("SIGNAL")
        assert result.total_results == 90
        assert result.offices[0].credit_union_name == "SIGNAL FINANCIAL"

    @respx.mock
    def test_sends_correct_body(self, client, location_search_json):
        route = respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        client.find_offices_by_name("Test", skip=10, take=50)
        body = route.calls[0].request.content
        import json

        parsed = json.loads(body)
        assert parsed["searchText"] == "Test"
        assert parsed["rdSearchType"] == "cuname"
        assert parsed["rdSearchRadiusList"] is None
        assert parsed["skip"] == 10
        assert parsed["take"] == 50


class TestFindOfficesByCharter:
    @respx.mock
    def test_returns_results(self, client, location_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        result = client.find_offices_by_charter(5571)
        assert result.total_results == 90

    @respx.mock
    def test_sends_correct_body(self, client, location_search_json):
        route = respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        client.find_offices_by_charter(5571)
        import json

        parsed = json.loads(route.calls[0].request.content)
        assert parsed["searchText"] == "5571"
        assert parsed["rdSearchType"] == "cunumber"
        assert parsed["rdSearchRadiusList"] is None


class TestFindOfficesByAddress:
    @respx.mock
    def test_with_valid_radius(self, client, location_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        result = client.find_offices_by_address("20005", radius=5)
        assert result.total_results == 90

    def test_invalid_radius_raises(self, client):
        with pytest.raises(NCUAValidationError, match="radius"):
            client.find_offices_by_address("20005", radius=7)

    @respx.mock
    def test_invalid_search_raises_on_valid_false(self, client):
        bad_response = {
            "latitude": 0, "longitude": 0, "valid": False,
            "list": [], "totalResults": 0, "statusCode": 1,
        }
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=bad_response)
        )
        with pytest.raises(NCUAValidationError, match="valid"):
            client.find_offices_by_address("not-a-real-place")


class TestGetCreditUnion:
    @respx.mock
    def test_returns_details(self, client, credit_union_details_json):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/5536").mock(
            return_value=httpx.Response(200, json=credit_union_details_json)
        )
        details = client.get_credit_union(5536)
        assert details.name == "NAVY FEDERAL CREDIT UNION"
        assert details.charter_number == 5536

    @respx.mock
    def test_not_found_raises(self, client, error_details_json):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/99999").mock(
            return_value=httpx.Response(200, json=error_details_json)
        )
        with pytest.raises(NCUANotFoundError):
            client.get_credit_union(99999)


class TestSearchNames:
    @respx.mock
    def test_returns_search_response(self, client, name_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetNameSearch").mock(
            return_value=httpx.Response(200, json=name_search_json)
        )
        result = client.search_names("Navy")
        assert result.total_result_count == 1
        assert result.results[0].name == "NAVY FEDERAL CREDIT UNION"


class TestSearchCreditUnions:
    @respx.mock
    def test_returns_quick_search_results(self, client, detail_search_json):
        respx.post("https://mapping.ncua.gov/api/ResearchCreditUnion/GetDetailSearch").mock(
            return_value=httpx.Response(200, json=detail_search_json)
        )
        result = client.search_credit_unions(name="Navy", state="VA")
        assert result.total_result_count == 1
        assert result.results[0].is_active is True


class TestGetOnlineCreditUnions:
    @respx.mock
    def test_returns_online_cus(self, client, online_cu_json):
        respx.get("https://mapping.ncua.gov/api/Search/GetOnlineCreditUnions").mock(
            return_value=httpx.Response(200, json=online_cu_json)
        )
        result = client.get_online_credit_unions()
        assert result.total_result_count == 1
        assert result.results[0].name == "ALLIANT"


class TestDownloads:
    @respx.mock
    def test_call_report_returns_bytes(self, client):
        pdf_json = {"fileContents": [37, 80, 68, 70]}
        respx.get(url__startswith="https://mapping.ncua.gov/api/CreditUnionDetails/GetDownloadCallReport/5536").mock(
            return_value=httpx.Response(200, json=pdf_json)
        )
        result = client.download_call_report(5536, cycle_date="03/31/2026")
        assert result == b"%PDF"

    @respx.mock
    def test_profile_returns_bytes(self, client):
        pdf_json = {"fileContents": [37, 80, 68, 70]}
        respx.get(url__startswith="https://mapping.ncua.gov/api/CreditUnionDetails/GetDownloadProfile/5536").mock(
            return_value=httpx.Response(200, json=pdf_json)
        )
        result = client.download_profile(5536, cycle_date="03/31/2026")
        assert result == b"%PDF"


class TestErrorHandling:
    @respx.mock
    def test_400_raises_validation_error(self, client):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/-1").mock(
            return_value=httpx.Response(400, json={"title": "Bad Request", "status": 400, "errors": {}})
        )
        with pytest.raises(NCUAValidationError):
            client.get_credit_union(-1)

    @respx.mock
    def test_500_raises_server_error(self, client):
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(500, json={"title": "Server error", "status": 500})
        )
        with pytest.raises(NCUAServerError):
            client.find_offices_by_name("test")


class TestContextManager:
    def test_with_statement(self):
        with NCUAClient() as client:
            assert client._http is not None
```

- [ ] **Step 2: Run tests — they should all fail**

```bash
cd /tmp/pyncua && uv run pytest tests/test_client.py -v
```
Expected: ImportError / FAIL.

- [ ] **Step 3: Write client.py**

```python
from __future__ import annotations

import importlib.metadata

import httpx
from pydantic import ValidationError

from pyncua._constants import BASE_URL, CUStatus, CUType, Region, SearchType
from pyncua._requests import (
    build_detail_search_body,
    build_download_url,
    build_name_search_body,
    build_search_locations_body,
)
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
    OnlineCreditUnion,
    QuickSearchResult,
    SearchResponse,
)

try:
    _VERSION = importlib.metadata.version("pyncua")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "0.0.0"


class NCUAClient:
    def __init__(self, timeout: float = 30.0, base_url: str = BASE_URL, **kwargs):
        self._base_url = base_url
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": f"pyncua/{_VERSION}"},
            **kwargs,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _post(self, path: str, body: dict) -> dict:
        resp = self._http.post(path, json=body)
        self._check_status(resp)
        return self._decode(resp)

    def _get(self, path: str) -> dict:
        resp = self._http.get(path)
        self._check_status(resp)
        return self._decode(resp)

    @staticmethod
    def _decode(resp: httpx.Response) -> dict:
        try:
            return resp.json()
        except Exception as e:
            raise NCUAError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}") from e

    def _check_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 500:
            raise NCUAServerError(f"NCUA API error {resp.status_code}")
        if resp.status_code >= 400:
            raise NCUAValidationError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    def _parse(self, model_cls, data):
        try:
            return model_cls.model_validate(data)
        except ValidationError as e:
            raise NCUAError(f"Failed to parse response: {e}") from e

    def find_offices_by_name(
        self, name: str, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(name, SearchType.NAME, skip=skip, take=take, **filters)
        data = self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        return result

    def find_offices_by_charter(
        self, charter: int, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            str(charter), SearchType.CHARTER, skip=skip, take=take, **filters
        )
        data = self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    def find_offices_by_address(
        self,
        address: str,
        *,
        radius: int = 25,
        skip: int = 0,
        take: int = 100,
        **filters: bool,
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            address, SearchType.ADDRESS, radius=radius, skip=skip, take=take, **filters
        )
        data = self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        if not result.valid:
            raise NCUAValidationError("Search returned valid=false — address may be unresolvable")
        return result

    def get_credit_union(self, charter: int) -> CreditUnionDetails:
        data = self._get(f"/api/CreditUnionDetails/GetCreditUnionDetails/{charter}")
        if data.get("isError"):
            msg = data.get("errorMessage", "Charter not found")
            raise NCUANotFoundError(msg)
        return self._parse(CreditUnionDetails, data)

    def search_names(
        self, name: str, *, skip: int = 0, take: int = 100
    ) -> SearchResponse[NameSearchResult]:
        body = build_name_search_body(name, skip=skip, take=take)
        data = self._post("/api/Search/GetNameSearch", body)
        return self._parse(SearchResponse[NameSearchResult], data)

    def search_credit_unions(
        self,
        name: str | None = None,
        cu_type: CUType | None = None,
        status: CUStatus | None = None,
        region: Region | None = None,
        state: str | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        fom_type: str | None = None,
        low_income: bool | None = None,
        is_mdi: bool | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> SearchResponse[QuickSearchResult]:
        body = build_detail_search_body(
            name=name,
            cu_type=cu_type.value if cu_type else None,
            status=status.value if status else None,
            region=region.value if region else None,
            state=state,
            city=city,
            zip_code=zip_code,
            fom_type=fom_type,
            low_income=low_income,
            is_mdi=is_mdi,
            skip=skip,
            take=take,
        )
        data = self._post("/api/ResearchCreditUnion/GetDetailSearch", body)
        return self._parse(SearchResponse[QuickSearchResult], data)

    def get_online_credit_unions(self) -> SearchResponse[OnlineCreditUnion]:
        data = self._get("/api/Search/GetOnlineCreditUnions")
        return self._parse(SearchResponse[OnlineCreditUnion], data)

    def download_call_report(
        self, charter: int, cycle_date: str, is_corporate: bool = False
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadCallReport",
            charter, cycle_date, is_corporate,
        )
        data = self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])

    def download_profile(
        self,
        charter: int,
        cycle_date: str,
        is_corporate: bool = False,
        is_snapshot: bool = False,
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadProfile",
            charter, cycle_date, is_corporate, is_snapshot,
        )
        data = self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])
```

- [ ] **Step 4: Run tests — they should all pass**

```bash
cd /tmp/pyncua && uv run pytest tests/test_client.py -v
```
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pyncua/client.py tests/test_client.py
git commit -m "feat: add sync NCUAClient with full API coverage"
```

---

### Task 6: Async Client

**Files:**
- Create: `src/pyncua/async_client.py`
- Create: `tests/test_async_client.py`

- [ ] **Step 1: Write test_async_client.py**

```python
import httpx
import pytest
import respx

from pyncua.async_client import AsyncNCUAClient
from pyncua.exceptions import NCUANotFoundError


@pytest.fixture()
async def client():
    c = AsyncNCUAClient(timeout=5.0)
    yield c
    await c.close()


class TestAsyncFindOfficesByName:
    @respx.mock
    async def test_returns_results(self, client, location_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=location_search_json)
        )
        result = await client.find_offices_by_name("SIGNAL")
        assert result.total_results == 90
        assert result.offices[0].credit_union_name == "SIGNAL FINANCIAL"


class TestAsyncGetCreditUnion:
    @respx.mock
    async def test_returns_details(self, client, credit_union_details_json):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/5536").mock(
            return_value=httpx.Response(200, json=credit_union_details_json)
        )
        details = await client.get_credit_union(5536)
        assert details.name == "NAVY FEDERAL CREDIT UNION"

    @respx.mock
    async def test_not_found(self, client, error_details_json):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/99999").mock(
            return_value=httpx.Response(200, json=error_details_json)
        )
        with pytest.raises(NCUANotFoundError):
            await client.get_credit_union(99999)


class TestAsyncSearchNames:
    @respx.mock
    async def test_returns_results(self, client, name_search_json):
        respx.post("https://mapping.ncua.gov/api/Search/GetNameSearch").mock(
            return_value=httpx.Response(200, json=name_search_json)
        )
        result = await client.search_names("Navy")
        assert result.total_result_count == 1


class TestAsyncContextManager:
    async def test_async_with(self):
        async with AsyncNCUAClient() as client:
            assert client._http is not None
```

- [ ] **Step 2: Run tests — they should fail**

```bash
cd /tmp/pyncua && uv run pytest tests/test_async_client.py -v
```
Expected: ImportError / FAIL.

- [ ] **Step 3: Write async_client.py**

```python
from __future__ import annotations

import importlib.metadata

import httpx
from pydantic import ValidationError

from pyncua._constants import BASE_URL, CUStatus, CUType, Region, SearchType
from pyncua._requests import (
    build_detail_search_body,
    build_download_url,
    build_name_search_body,
    build_search_locations_body,
)
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
    OnlineCreditUnion,
    QuickSearchResult,
    SearchResponse,
)

try:
    _VERSION = importlib.metadata.version("pyncua")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "0.0.0"


class AsyncNCUAClient:
    def __init__(self, timeout: float = 30.0, base_url: str = BASE_URL, **kwargs):
        self._base_url = base_url
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": f"pyncua/{_VERSION}"},
            **kwargs,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _post(self, path: str, body: dict) -> dict:
        resp = await self._http.post(path, json=body)
        self._check_status(resp)
        return self._decode(resp)

    async def _get(self, path: str) -> dict:
        resp = await self._http.get(path)
        self._check_status(resp)
        return self._decode(resp)

    @staticmethod
    def _decode(resp: httpx.Response) -> dict:
        try:
            return resp.json()
        except Exception as e:
            raise NCUAError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}") from e

    def _check_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 500:
            raise NCUAServerError(f"NCUA API error {resp.status_code}")
        if resp.status_code >= 400:
            raise NCUAValidationError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    def _parse(self, model_cls, data):
        try:
            return model_cls.model_validate(data)
        except ValidationError as e:
            raise NCUAError(f"Failed to parse response: {e}") from e

    async def find_offices_by_name(
        self, name: str, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(name, SearchType.NAME, skip=skip, take=take, **filters)
        data = await self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    async def find_offices_by_charter(
        self, charter: int, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            str(charter), SearchType.CHARTER, skip=skip, take=take, **filters
        )
        data = await self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    async def find_offices_by_address(
        self,
        address: str,
        *,
        radius: int = 25,
        skip: int = 0,
        take: int = 100,
        **filters: bool,
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            address, SearchType.ADDRESS, radius=radius, skip=skip, take=take, **filters
        )
        data = await self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        if not result.valid:
            raise NCUAValidationError("Search returned valid=false — address may be unresolvable")
        return result

    async def get_credit_union(self, charter: int) -> CreditUnionDetails:
        data = await self._get(f"/api/CreditUnionDetails/GetCreditUnionDetails/{charter}")
        if data.get("isError"):
            msg = data.get("errorMessage", "Charter not found")
            raise NCUANotFoundError(msg)
        return self._parse(CreditUnionDetails, data)

    async def search_names(
        self, name: str, *, skip: int = 0, take: int = 100
    ) -> SearchResponse[NameSearchResult]:
        body = build_name_search_body(name, skip=skip, take=take)
        data = await self._post("/api/Search/GetNameSearch", body)
        return self._parse(SearchResponse[NameSearchResult], data)

    async def search_credit_unions(
        self,
        name: str | None = None,
        cu_type: CUType | None = None,
        status: CUStatus | None = None,
        region: Region | None = None,
        state: str | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        fom_type: str | None = None,
        low_income: bool | None = None,
        is_mdi: bool | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> SearchResponse[QuickSearchResult]:
        body = build_detail_search_body(
            name=name,
            cu_type=cu_type.value if cu_type else None,
            status=status.value if status else None,
            region=region.value if region else None,
            state=state,
            city=city,
            zip_code=zip_code,
            fom_type=fom_type,
            low_income=low_income,
            is_mdi=is_mdi,
            skip=skip,
            take=take,
        )
        data = await self._post("/api/ResearchCreditUnion/GetDetailSearch", body)
        return self._parse(SearchResponse[QuickSearchResult], data)

    async def get_online_credit_unions(self) -> SearchResponse[OnlineCreditUnion]:
        data = await self._get("/api/Search/GetOnlineCreditUnions")
        return self._parse(SearchResponse[OnlineCreditUnion], data)

    async def download_call_report(
        self, charter: int, cycle_date: str, is_corporate: bool = False
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadCallReport",
            charter, cycle_date, is_corporate,
        )
        data = await self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])

    async def download_profile(
        self,
        charter: int,
        cycle_date: str,
        is_corporate: bool = False,
        is_snapshot: bool = False,
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadProfile",
            charter, cycle_date, is_corporate, is_snapshot,
        )
        data = await self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])
```

- [ ] **Step 4: Run tests — they should all pass**

```bash
cd /tmp/pyncua && uv run pytest tests/test_async_client.py -v
```
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pyncua/async_client.py tests/test_async_client.py
git commit -m "feat: add async AsyncNCUAClient mirroring sync API"
```

---

### Task 7: Public API Exports and Full Test Suite

**Files:**
- Modify: `src/pyncua/__init__.py`

- [ ] **Step 1: Update __init__.py with all public exports**

```python
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
```

- [ ] **Step 2: Run the full test suite**

```bash
cd /tmp/pyncua && uv run pytest -v
```
Expected: All tests across test_models.py, test_client.py, test_async_client.py PASS.

- [ ] **Step 3: Run ruff**

```bash
cd /tmp/pyncua && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
```
Expected: No errors. Fix any issues if found.

- [ ] **Step 4: Commit**

```bash
git add src/pyncua/__init__.py
git commit -m "feat: wire up public API exports in __init__.py"
```

---

### Task 8: Integration Tests (Opt-In)

**Files:**
- Create: `tests/test_live.py`

- [ ] **Step 1: Write test_live.py**

```python
import os

import pytest

from pyncua import NCUAClient

pytestmark = pytest.mark.live

LIVE = os.environ.get("PYNCUA_LIVE_TESTS") == "1"

if not LIVE:
    pytest.skip("Set PYNCUA_LIVE_TESTS=1 to run", allow_module_level=True)


@pytest.fixture(scope="module")
def client():
    with NCUAClient() as c:
        yield c


NAVY_FEDERAL_CHARTER = 5536


class TestLiveSearch:
    def test_find_by_name(self, client):
        result = client.find_offices_by_name("Navy Federal", take=5)
        assert result.total_results > 0
        assert any(o.charter_number == NAVY_FEDERAL_CHARTER for o in result.offices)

    def test_find_by_charter(self, client):
        result = client.find_offices_by_charter(NAVY_FEDERAL_CHARTER, take=5)
        assert result.total_results > 0

    def test_find_by_address(self, client):
        result = client.find_offices_by_address("22180", radius=10, take=5)
        assert result.valid is True
        assert result.total_results > 0


class TestLiveDetails:
    def test_get_credit_union(self, client):
        details = client.get_credit_union(NAVY_FEDERAL_CHARTER)
        assert details.name == "NAVY FEDERAL CREDIT UNION"
        assert details.charter_number == NAVY_FEDERAL_CHARTER
        assert details.assets > 0
        assert details.number_of_members > 0
        assert len(details.call_report_cycle_dates) > 0

    def test_not_found(self, client):
        from pyncua import NCUANotFoundError

        with pytest.raises(NCUANotFoundError):
            client.get_credit_union(9999999)


class TestLiveNameSearch:
    def test_search_names(self, client):
        result = client.search_names("Navy Federal")
        assert result.total_result_count >= 1
        assert any(r.charter_number == NAVY_FEDERAL_CHARTER for r in result.results)


class TestLiveAdvancedSearch:
    def test_search_credit_unions(self, client):
        from pyncua import CUStatus

        result = client.search_credit_unions(name="Navy", status=CUStatus.ACTIVE, take=5)
        assert result.total_result_count >= 1


class TestLiveOnline:
    def test_get_online_credit_unions(self, client):
        result = client.get_online_credit_unions()
        assert result.total_result_count > 0
        assert len(result.results) > 0
```

- [ ] **Step 2: Verify tests are skipped by default**

```bash
cd /tmp/pyncua && uv run pytest tests/test_live.py -v
```
Expected: All tests skipped (`Set PYNCUA_LIVE_TESTS=1 to run`).

- [ ] **Step 3: Run live tests (optional — requires network)**

```bash
cd /tmp/pyncua && PYNCUA_LIVE_TESTS=1 uv run pytest tests/test_live.py -v
```
Expected: All tests PASS (hitting the real NCUA API).

- [ ] **Step 4: Commit**

```bash
git add tests/test_live.py
git commit -m "feat: add opt-in live integration tests"
```

---

### Task 9: README and Final Polish

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# pyncua

Python client for the [NCUA Credit Union Mapping API](https://mapping.ncua.gov).

## Install

```bash
pip install pyncua
```

## Usage

```python
from pyncua import NCUAClient

with NCUAClient() as client:
    # Search offices by name
    result = client.find_offices_by_name("Navy Federal")
    for office in result.offices:
        print(f"{office.credit_union_name} — {office.city}, {office.state}")

    # Get full credit union details
    details = client.get_credit_union(5536)
    print(f"{details.name}: ${details.assets_formatted} in assets")

    # Advanced filtered search
    from pyncua import CUType, CUStatus
    results = client.search_credit_unions(
        cu_type=CUType.FEDERAL,
        status=CUStatus.ACTIVE,
        state="VA",
    )
```

### Async

```python
from pyncua import AsyncNCUAClient

async with AsyncNCUAClient() as client:
    result = await client.find_offices_by_name("Navy Federal")
```

## License

MIT
```

- [ ] **Step 2: Run full test suite one final time**

```bash
cd /tmp/pyncua && uv run pytest -v && uv run ruff check src/ tests/
```
Expected: All tests PASS, ruff clean.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage examples"
```

---

### Task 10: Create GitHub Repo and Push

- [ ] **Step 1: Create the repo on GitHub**

```bash
cd /tmp/pyncua && gh repo create Avicennasis/pyncua --private --source=. --push
```

- [ ] **Step 2: Verify on GitHub**

```bash
gh repo view Avicennasis/pyncua --web
```

- [ ] **Step 3: Update Redmine ticket #4465 with progress**

Add a note linking to the repo and marking progress.
