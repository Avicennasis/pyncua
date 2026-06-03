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
        respx.get(
            "https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/5536"
        ).mock(return_value=httpx.Response(200, json=credit_union_details_json))
        details = await client.get_credit_union(5536)
        assert details.name == "NAVY FEDERAL CREDIT UNION"

    @respx.mock
    async def test_not_found(self, client, error_details_json):
        respx.get(
            "https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/99999"
        ).mock(return_value=httpx.Response(200, json=error_details_json))
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


class TestAsyncGetApiVersion:
    @respx.mock
    async def test_returns_version_string(self, client):
        respx.get("https://mapping.ncua.gov/api/Search/version").mock(
            return_value=httpx.Response(200, text="2.3.26086.1")
        )
        result = await client.get_api_version()
        assert result == "2.3.26086.1"


class TestAsyncGetCurrentCycle:
    @respx.mock
    async def test_returns_cycle_date(self, client):
        respx.get("https://mapping.ncua.gov/api/DataQuery/GetCurrentCycle").mock(
            return_value=httpx.Response(200, json="2026-03-31T00:00:00")
        )
        result = await client.get_current_cycle()
        assert result == "2026-03-31T00:00:00"


class TestAsyncGetCycleYears:
    @respx.mock
    async def test_returns_year_list(self, client):
        respx.get("https://mapping.ncua.gov/api/DataQuery/GetCycleYears").mock(
            return_value=httpx.Response(200, json=["All", "2026", "2025"])
        )
        result = await client.get_cycle_years()
        assert result == ["All", "2026", "2025"]


class TestAsyncGetMergerQueryYears:
    @respx.mock
    async def test_returns_year_list(self, client):
        respx.get("https://mapping.ncua.gov/api/DataQuery/GetMergerQueryYears").mock(
            return_value=httpx.Response(200, json=["All", "2026", "2025", "2024"])
        )
        result = await client.get_merger_query_years()
        assert result == ["All", "2026", "2025", "2024"]
