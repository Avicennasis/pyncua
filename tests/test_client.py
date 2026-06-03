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
            "latitude": 0,
            "longitude": 0,
            "valid": False,
            "list": [],
            "totalResults": 0,
            "statusCode": 1,
        }
        respx.post("https://mapping.ncua.gov/api/Search/GetSearchLocations").mock(
            return_value=httpx.Response(200, json=bad_response)
        )
        with pytest.raises(NCUAValidationError, match="valid"):
            client.find_offices_by_address("not-a-real-place")


class TestGetCreditUnion:
    @respx.mock
    def test_returns_details(self, client, credit_union_details_json):
        respx.get(
            "https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/5536"
        ).mock(return_value=httpx.Response(200, json=credit_union_details_json))
        details = client.get_credit_union(5536)
        assert details.name == "NAVY FEDERAL CREDIT UNION"
        assert details.charter_number == 5536

    @respx.mock
    def test_not_found_raises(self, client, error_details_json):
        respx.get(
            "https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/99999"
        ).mock(return_value=httpx.Response(200, json=error_details_json))
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
        respx.get(
            url__startswith="https://mapping.ncua.gov/api/CreditUnionDetails/GetDownloadCallReport/5536"
        ).mock(return_value=httpx.Response(200, json=pdf_json))
        result = client.download_call_report(5536, cycle_date="03/31/2026")
        assert result == b"%PDF"

    @respx.mock
    def test_profile_returns_bytes(self, client):
        pdf_json = {"fileContents": [37, 80, 68, 70]}
        respx.get(
            url__startswith="https://mapping.ncua.gov/api/CreditUnionDetails/GetDownloadProfile/5536"
        ).mock(return_value=httpx.Response(200, json=pdf_json))
        result = client.download_profile(5536, cycle_date="03/31/2026")
        assert result == b"%PDF"


class TestErrorHandling:
    @respx.mock
    def test_400_raises_validation_error(self, client):
        respx.get("https://mapping.ncua.gov/api/CreditUnionDetails/GetCreditUnionDetails/-1").mock(
            return_value=httpx.Response(
                400, json={"title": "Bad Request", "status": 400, "errors": {}}
            )
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
