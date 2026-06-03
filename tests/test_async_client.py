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
