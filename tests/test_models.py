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
