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
