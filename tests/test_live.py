import os

import pytest

from pyncua import NCUAClient, NCUAValidationError
from pyncua._constants import MAX_TAKE
from pyncua._requests import build_detail_search_body

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


class TestLivePaginationCap:
    """Characterization tests for the server-side `take` cap.

    The client-side guard in `_requests._validate_pagination` exists only
    because NCUA truncates oversized `take` values without saying so. These
    tests bypass the guard and talk to the API directly, so if NCUA ever
    raises, lowers, or starts reporting the cap, they fail and tell us the
    guard's constant needs revisiting.
    """

    def test_server_still_truncates_oversized_take(self, client):
        # Build the body the normal way, then override `take` past the guard so
        # this exercises the real server behaviour rather than a hand-copied
        # body that could drift from build_detail_search_body.
        body = build_detail_search_body(state="PA", take=MAX_TAKE)
        body["take"] = 500

        data = client._post("/api/ResearchCreditUnion/GetDetailSearch", body)
        assert len(data["results"]) == MAX_TAKE, (
            f"NCUA returned {len(data['results'])} rows for take=500; the "
            f"server-side cap is no longer {MAX_TAKE} and MAX_TAKE needs updating."
        )
        # The true count is still reported, which is what makes the truncation
        # silent rather than obvious.
        assert data["totalResultCount"] > MAX_TAKE

    def test_client_rejects_oversized_take(self, client):
        with pytest.raises(NCUAValidationError, match="take must be <= 100"):
            client.search_credit_unions(state="PA", take=MAX_TAKE + 1)

    def test_skip_pagination_walks_the_whole_set(self, client):
        first = client.search_credit_unions(state="PA", take=MAX_TAKE)
        total = first.total_result_count
        assert total > MAX_TAKE, "PA should have more than one page of credit unions"

        rows = list(first.results)
        while len(rows) < total:
            page = client.search_credit_unions(state="PA", skip=len(rows), take=MAX_TAKE)
            if not page.results:
                break
            rows.extend(page.results)

        assert len(rows) == total
        assert len({r.charter_number for r in rows}) == total, "pages overlapped"
