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
