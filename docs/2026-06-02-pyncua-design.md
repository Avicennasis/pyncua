# pyncua — Design Spec

**Date:** 2026-06-02
**Ticket:** Redmine #4465
**Status:** Approved

## Summary

Python client library wrapping the NCUA Credit Union Mapping API at `mapping.ncua.gov/api`. Replaces the defunct Ruby gem `ContinuityControl/ncua` (which targeted the now-404'd ASP.NET endpoint). The new NCUA backend is a pure JSON API — no HTML scraping needed.

Stack: httpx + Pydantic v2 + uv packaging. Sync and async interfaces.

## Background

The original Ruby gem (v0.11.0, last commit 2020) wrapped two endpoints:
- `POST mapping.ncua.gov/findCUByRadius.aspx` — search by name/charter/address
- `GET mapping.ncua.gov/SingleResult.aspx?ID=<charter>` — HTML scrape for CU details

NCUA retired the ASP.NET app and replaced it with an Angular SPA backed by a proper JSON REST API at `mapping.ncua.gov/api`. No authentication required. `Content-Type: application/json` on POSTs. No CORS headers (server-side only).

## Scope

### Phase 1 (this spec)

Original gem parity plus useful new endpoints:
- **find_offices_by_name** — search office locations by CU name
- **find_offices_by_charter** — search office locations by charter number
- **find_offices_by_address** — search office locations by address/zip with radius
- **get_credit_union** — full institutional details by charter number
- **search_names** — lightweight name autocomplete (charter + name)
- **search_credit_unions** — advanced filtered search (type, status, region, state, FOM, MDI, low-income)
- **get_online_credit_unions** — list online-only CUs
- **download_call_report** — PDF call report by charter + cycle date
- **download_profile** — PDF profile by charter + cycle date

### Phase 2 (filed for later)

Full API coverage: data query emails, cycle dates, merger queries.

## API Mapping

Base URL: `https://mapping.ncua.gov` (client default). All endpoint paths below are appended to this base.

| pyncua method | HTTP | NCUA endpoint | Returns |
|---|---|---|---|
| `find_offices_by_name(name)` | POST | `/api/Search/GetSearchLocations` (rdSearchType=cuname) | `LocationSearchResponse` |
| `find_offices_by_charter(charter)` | POST | `/api/Search/GetSearchLocations` (rdSearchType=cunumber) | `LocationSearchResponse` |
| `find_offices_by_address(address, radius)` | POST | `/api/Search/GetSearchLocations` (rdSearchType=address) | `LocationSearchResponse` |
| `get_credit_union(charter)` | GET | `/api/CreditUnionDetails/GetCreditUnionDetails/{charter}` | `CreditUnionDetails` |
| `search_names(name)` | POST | `/api/Search/GetNameSearch` | `SearchResponse[NameSearchResult]` |
| `search_credit_unions(...)` | POST | `/api/ResearchCreditUnion/GetDetailSearch` | `SearchResponse[QuickSearchResult]` |
| `get_online_credit_unions()` | GET | `/api/Search/GetOnlineCreditUnions` | `SearchResponse[OnlineCreditUnion]` |
| `download_call_report(charter, cycle_date)` | GET | `/api/CreditUnionDetails/GetDownloadCallReport/{charter}?isCorpCU={bool}&cycleDate={date}` | `bytes` |
| `download_profile(charter, cycle_date)` | GET | `/api/CreditUnionDetails/GetDownloadProfile/{charter}?isCorpCU={bool}&cycleDate={date}&isSnapshot={bool}` | `bytes` |

### POST Request Body Schemas

**GetSearchLocations** (used by `find_offices_by_*`):
```json
{
  "searchText": "<query>",
  "rdSearchType": "address" | "cuname" | "cunumber",
  "rdSearchRadiusList": 25,
  "is_mainOffice": false, "is_mdi": false, "is_member": false,
  "is_drive": false, "is_atm": false, "is_shared": false,
  "is_bilingual": false, "is_credit_builder": false,
  "is_fin_counseling": false, "is_homebuyer": false,
  "is_school": false, "is_low_wire": false, "is_no_draft": false,
  "is_no_tax": false, "is_payday": false,
  "skip": 0, "take": 100,
  "sort_item": "distance", "sort_direction": "asc"
}
```
`rdSearchRadiusList` is only used for address searches (must be one of `{2, 5, 10, 15, 25, 60}`); set to `null` for name/charter searches.

**GetNameSearch** (used by `search_names`):
```json
{"cuName": "<query>", "skip": 0, "take": 100}
```

**GetDetailSearch** (used by `search_credit_unions`):
```json
{
  "cuName": "<name>", "cuType": "1"|"2"|null, "cuStatus": "A"|"I"|null,
  "region": "1"|"2"|"3"|"8"|null, "state": "<2-letter>"|null,
  "city": "<city>"|null, "zipCode": "<zip>"|null,
  "fomType": "<string>"|null, "lowIncome": "true"|"false"|null,
  "isMdi": "true"|"false"|null,
  "skip": 0, "take": 20
}
```
All filter fields accept `null` to skip that filter. `lowIncome` and `isMdi` are strings, not booleans.

### Error Response Shapes

- **200 with error flag** (details endpoint): `{"isError": true, "errorMessage": "..."}` with all other fields null. Client must check `isError` before parsing → raises `NCUANotFoundError`.
- **400 Bad Request**: ASP.NET problem details: `{"type": "...", "title": "...", "status": 400, "errors": {...}}` → raises `NCUAValidationError`.
- **500 Server Error**: `{"title": "Server error", "status": 500}` → raises `NCUAServerError`.

### PDF Download Response Format

Both download endpoints return `application/json` containing a JSON object with a `fileContents` field — an array of unsigned byte integers representing the raw PDF:
```json
{"fileContents": [37, 80, 68, 70, ...]}
```
Client converts with `bytes(response_json["fileContents"])`.

## Architecture

```
pyncua/
├── src/pyncua/
│   ├── __init__.py          # Re-exports: NCUAClient, AsyncNCUAClient, all models, all enums, all exceptions
│   ├── client.py            # NCUAClient (sync)
│   ├── async_client.py      # AsyncNCUAClient (async)
│   ├── models.py            # Pydantic response/request models
│   ├── exceptions.py        # Error hierarchy
│   └── _constants.py        # Base URL, defaults, enums
├── tests/
│   ├── test_client.py       # Unit tests with respx mocking
│   ├── test_models.py       # Model validation tests
│   ├── test_live.py         # Opt-in integration tests (--live flag)
│   └── conftest.py          # Shared fixtures, response samples
├── pyproject.toml
└── README.md
```

## Client Design

### NCUAClient (sync)

```python
from pyncua import NCUAClient

# Supports context manager (closes httpx.Client on exit)
with NCUAClient(timeout=30.0) as client:
    # Original gem parity
    offices = client.find_offices_by_name("Navy Federal", skip=0, take=100)
    offices = client.find_offices_by_charter(5536)
    offices = client.find_offices_by_address("20005", radius=25, skip=0, take=100)
    details = client.get_credit_union(5536)

    # New endpoints
    matches = client.search_names("Navy", skip=0, take=100)
    results = client.search_credit_unions(
        name="Navy",
        cu_type=CUType.FEDERAL,
        status=CUStatus.ACTIVE,
        state="VA",
        skip=0, take=20,
    )
    online = client.get_online_credit_unions()
    pdf_bytes = client.download_call_report(5536, cycle_date="03/31/2026")
    pdf_bytes = client.download_profile(5536, cycle_date="03/31/2026")
```

Both `NCUAClient` and `AsyncNCUAClient` implement context managers (`__enter__`/`__exit__` and `__aenter__`/`__aexit__`). Also usable without `with` — call `client.close()` when done. Not thread-safe; use one instance per thread.

Sets `User-Agent: pyncua/<version>` on all requests.

All search methods accept `skip`/`take` for pagination, defaulting to `skip=0, take=100`.

`find_offices_by_address` accepts `radius` (int, miles, default 25). Must be one of `{2, 5, 10, 15, 25, 60}` — client validates and raises `NCUAValidationError` for invalid values.

**`find_offices_by_*` boolean filter kwargs** (all default `False`):
- `main_office_only` → `is_mainOffice`
- `atm` → `is_atm`
- `drive_thru` → `is_drive`
- `shared_service` → `is_shared`
- `bilingual` → `is_bilingual`
- `credit_builder` → `is_credit_builder`
- `financial_counseling` → `is_fin_counseling`
- `first_time_homebuyer` → `is_homebuyer`
- `in_school_branch` → `is_school`
- `low_cost_wires` → `is_low_wire`
- `no_cost_share_drafts` → `is_no_draft`
- `no_cost_tax_prep` → `is_no_tax`
- `payday_alternative` → `is_payday`
- `mdi` → `is_mdi`
- `member_services` → `is_member`

Note: API field names use inconsistent casing (e.g., `is_mainOffice` is mixed case, not pure camelCase). Request models must use exact API field names as aliases — do not normalize.

**`search_credit_unions` full signature:**
```python
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
) -> SearchResponse[QuickSearchResult]: ...
```
`low_income` and `is_mdi` accept Python `bool` but are serialized as `"true"`/`"false"` strings per the API's expectations.

**`download_call_report` and `download_profile` full signatures:**
```python
def download_call_report(
    self,
    charter: int,
    cycle_date: str,       # format: "MM/DD/YYYY" (e.g., "03/31/2026")
    is_corporate: bool = False,
) -> bytes: ...

def download_profile(
    self,
    charter: int,
    cycle_date: str,       # format: "MM/DD/YYYY" (e.g., "03/31/2026")
    is_corporate: bool = False,
    is_snapshot: bool = False,
) -> bytes: ...
```
Large call reports can be tens of MB; the JSON byte-array wire format inflates this 3-5x in transit. No streaming is provided — callers should be aware of memory usage for large reports.

### AsyncNCUAClient

Mirrors the sync API exactly, using `httpx.AsyncClient`:

```python
from pyncua import AsyncNCUAClient

async with AsyncNCUAClient() as client:
    offices = await client.find_offices_by_name("Navy Federal")
```

### Implementation pattern

Both clients share request-building logic via a private `_build_*` mixin or module. The sync client uses `httpx.Client`, the async client uses `httpx.AsyncClient`. Response parsing is identical — Pydantic `model_validate()` on the JSON.

## Models

### Pydantic Configuration

All models use:
```python
model_config = ConfigDict(
    frozen=True,
    populate_by_name=True,
    alias_generator=to_camel,  # from pydantic.alias_generators
    extra="ignore",            # tolerate new API fields without breaking
)
```

API responses use camelCase field names (e.g., `creditUnionName`, `charterNumber`). Models use snake_case with `alias_generator=to_camel` for automatic mapping. Fields with non-standard API names (e.g., `is_mainOffice`) use explicit `Field(alias="...")`.

All `charter_number` fields across all models are typed as `int`. The API sometimes returns charter numbers as strings; Pydantic coerces these automatically in lax mode.

Pydantic `ValidationError` is caught by the client and re-raised as `NCUAError` with the original error attached, so users only need to catch the pyncua exception hierarchy.

### Response models

**Office** — location search result:
- `credit_union_name: str`
- `credit_union_site_name: str`
- `charter_number: int`
- `street: str`, `city: str`, `state: str`, `zipcode: str`, `country: str`
- `latitude: float`, `longitude: float`
- `is_main_office: bool`
- `phone: str`, `url: str | None`
- `site_functions: list[str]` (parsed from semicolon-delimited string)
- `site_id: int`
- `distance: float | None` (present for address searches)
- Service flags: `is_mdi`, `bilingual`, `credit_builder`, `financial_counseling`, `first_time_homebuyer`, `in_school_branch`, `low_cost_wires`, `no_cost_tax_prep`, `no_cost_share_drafts`, `payday_alternative_1`, `payday_alternative_2`

**CreditUnionDetails** — full institutional profile:
- `name: str`, `charter_number: int`, `cu_type: str` (API returns values like `"FCU"`, `"FISCU"` — not the request enum values), `status: str` (API returns `"Active"`/`"Inactive"` — not the request enum codes)
- `is_corporate: bool`, `charter_year: str`
- `charter_issue_date: str`, `insured_date: str`
- `charter_state: str`, `region: str`
- `field_of_membership: str`, `low_income_designation: bool`, `member_of_fhlb: bool`
- `assets: int`, `assets_formatted: str`
- `number_of_members: int`, `members_formatted: str`
- `peer_group: str`
- `address: str`, `address2: str`, `city: str`, `state: str`, `zip: str`, `country: str`, `county: str`
- `phone: str`, `phone_formatted: str`
- `website: str | None`, `ceo: str`
- `call_report_cycle_dates: dict[str, str]` (e.g., `{"March-2026": "03/31/2026"}` — valid dates for `download_call_report`)
- `profile_cycle_dates: dict[str, str]` (valid dates for `download_profile`)

**NameSearchResult**: `charter_number: int`, `name: str`

**QuickSearchResult**: `charter_number: int`, `name: str`, `city: str`, `state: str`, `is_corporate: bool`, `is_active: bool`

**OnlineCreditUnion**: `charter_number: int`, `name: str`, `website: str`, `phone: str`

### Wrapper models

**LocationSearchResponse**: `latitude: float`, `longitude: float`, `valid: bool`, `status_code: int`, `total_results: int` (alias `totalResults`), `offices: list[Office]` (alias `list` — explicit `Field(alias="list")` required since `list` shadows the Python builtin)

If `valid` is `False`, client raises `NCUAValidationError` (e.g., unresolvable address).

**SearchResponse[T]** (generic): `total_result_count: int` (alias `totalResultCount`), `results: list[T]`

### Enums

These enums are for **request parameters** only (e.g., `search_credit_unions(cu_type=CUType.FEDERAL)`). Response models use plain `str` for fields like `cu_type` and `status` because the API returns different value formats in responses (e.g., `"FCU"` vs `"1"`, `"Active"` vs `"A"`).

```python
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
    ONES = "8"  # Office of National Examinations and Supervision

class SearchType(str, Enum):
    ADDRESS = "address"
    NAME = "cuname"
    CHARTER = "cunumber"
```

## Error Handling

```python
class NCUAError(Exception): ...
class NCUANotFoundError(NCUAError): ...       # charter not found (isError=true)
class NCUAValidationError(NCUAError): ...     # 400 bad request
class NCUAServerError(NCUAError): ...         # 5xx
```

httpx timeout/connection errors are not wrapped — they pass through as `httpx.TimeoutException`, `httpx.ConnectError`, etc. HTTP 429 (rate limiting) also passes through as `httpx.HTTPStatusError` — no automatic retry. The client constructor accepts `timeout: float` (default 30.0) and `**kwargs` forwarded to `httpx.Client`/`httpx.AsyncClient` (e.g., `proxy`, `verify`, `cert`).

## Dependencies

### Runtime
- `httpx >= 0.27`
- `pydantic >= 2.0`

### Dev
- `pytest`
- `respx` (httpx request mocking)
- `ruff` (lint + format)
- `pytest-asyncio` (async test support)

## Testing

### Unit tests (default, no network)

- Mock all HTTP with `respx` using fixture JSON captured from live API responses
- Test each client method: correct URL, method, headers, body sent
- Test response parsing: each model validates against fixture data
- Test error paths: 400, 500, not-found responses
- Test edge cases: empty results, pagination, special characters in search

### Model tests

- Validate each Pydantic model against real response fixtures
- Test field aliases (API uses camelCase, models use snake_case)
- Test computed fields (site_functions list parsing, bytes conversion for PDFs)

### Integration tests (opt-in)

- Gated behind `--live` pytest marker or `PYNCUA_LIVE_TESTS=1` env var
- Hit real NCUA API with known charter numbers (5536 = Navy Federal)
- Detect schema drift early

## Packaging

`pyproject.toml` with uv, targeting Python >= 3.10. Package name `pyncua`. Publishable to PyPI.

```toml
[project]
name = "pyncua"
version = "1.0.0"
description = "Python client for the NCUA Credit Union Mapping API"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "respx",
    "ruff",
    "pytest-asyncio",
]
```
