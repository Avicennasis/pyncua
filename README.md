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
