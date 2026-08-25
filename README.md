# pyncua

[![CI](https://github.com/Avicennasis/pyncua/actions/workflows/test.yml/badge.svg)](https://github.com/Avicennasis/pyncua/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Python client for the [NCUA Credit Union Mapping API](https://mapping.ncua.gov). Search credit union offices by name, charter number, or address; retrieve full institutional profiles; run advanced filtered searches; download call reports and profiles as PDF.

Provides both synchronous and asynchronous clients with typed [Pydantic v2](https://docs.pydantic.dev/) response models.

> **Inspired by** [ContinuityControl/ncua](https://github.com/ContinuityControl/ncua), a Ruby gem that wrapped NCUA's now-retired ASP.NET endpoint. **pyncua is not a fork** — it is a complete rewrite in Python targeting NCUA's current JSON API at `mapping.ncua.gov/api`.

## Install

```bash
pip install pyncua
```

Requires Python 3.10+.

## Quick Start

```python
from pyncua import NCUAClient

with NCUAClient() as client:
    # Search offices by name
    result = client.find_offices_by_name("Navy Federal")
    for office in result.offices:
        print(f"{office.credit_union_name} — {office.city}, {office.state}")

    # Get full credit union details
    details = client.get_credit_union(5536)
    print(
        f"{details.name}: {details.assets_formatted} in assets, {details.members_formatted} members"
    )

    # Advanced filtered search
    from pyncua import CUType, CUStatus

    results = client.search_credit_unions(
        cu_type=CUType.FEDERAL,
        status=CUStatus.ACTIVE,
        state="VA",
    )
    for cu in results.results:
        print(f"  {cu.name} (#{cu.charter_number}) — {cu.city}, {cu.state}")
```

## API Coverage

| Method | Description |
|--------|-------------|
| `find_offices_by_name(name)` | Search office locations by credit union name |
| `find_offices_by_charter(charter)` | Search office locations by charter number |
| `find_offices_by_address(address, radius)` | Search offices near an address/zip |
| `get_credit_union(charter)` | Full institutional profile by charter number |
| `search_names(name)` | Lightweight name autocomplete |
| `search_credit_unions(...)` | Advanced filtered search (type, status, region, state, etc.) |
| `get_online_credit_unions()` | List online-only credit unions |
| `download_call_report(charter, cycle_date)` | Download call report PDF |
| `download_profile(charter, cycle_date)` | Download profile PDF |
| `get_api_version()` | NCUA API version string |
| `get_current_cycle()` | Current reporting cycle date |
| `get_cycle_years()` | Available years for event data |
| `get_merger_query_years()` | Available years for merger data |

`find_offices_by_*` methods accept boolean filter kwargs (`atm`, `drive_thru`, `bilingual`, etc.).

### Choosing a search method

`find_offices_by_address` geocodes server-side and returns **branch locations** near a point.
`search_credit_unions` filters on the credit union's **headquarters city**. These give
materially different answers: a search for `city="Pittsburgh"` misses Clearview
(#9007, $2.2B in assets) because its charter address is Moon Township, even though it
operates numerous Pittsburgh branches. For "who serves this area," use the office search.

### Pagination

All search methods take `skip`/`take`. **`take` is capped at 100** — the NCUA API
silently truncates anything larger while still reporting the true count in
`total_result_count`, so pyncua raises `NCUAValidationError` rather than hand back a
short result set you might mistake for the whole answer. Page with `skip`:

```python
from pyncua import NCUAClient

with NCUAClient() as client:
    first = client.search_credit_unions(state="PA", take=100)
    rows = list(first.results)
    while len(rows) < first.total_result_count:
        page = client.search_credit_unions(state="PA", skip=len(rows), take=100)
        if not page.results:
            break
        rows.extend(page.results)
```

## Async

```python
from pyncua import AsyncNCUAClient

async with AsyncNCUAClient() as client:
    result = await client.find_offices_by_name("Navy Federal")
```

The async client mirrors the sync API exactly.

## Error Handling

```python
from pyncua import NCUAClient, NCUANotFoundError, NCUAValidationError

with NCUAClient() as client:
    try:
        details = client.get_credit_union(9999999)
    except NCUANotFoundError:
        print("Charter number not found")
    except NCUAValidationError:
        print("Invalid request")
```

`NCUAValidationError` also covers client-side guards that fire before any request is
made — an out-of-range `radius` or a `take` above 100.

**A search that matches nothing is not an error.** NCUA returns `valid=True` with an
empty list for an address it cannot resolve, so check the results rather than relying
on an exception:

```python
result = client.find_offices_by_address("Pittsburgh, PA", radius=10)
if not result.offices:
    print("No offices found")
```

## Acknowledgments

This project was inspired by [ContinuityControl/ncua](https://github.com/ContinuityControl/ncua), a Ruby gem by [ContinuityControl](https://github.com/ContinuityControl) that provided the original idea for wrapping the NCUA's credit union data API. While pyncua is an independent, ground-up implementation in Python (not a fork or port), the ContinuityControl team's work demonstrated the value of a clean client library for this data and motivated this project.

## License

[MIT](LICENSE)
