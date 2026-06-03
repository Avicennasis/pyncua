from __future__ import annotations

from pyncua._constants import VALID_RADII, SearchType
from pyncua.exceptions import NCUAValidationError

_FILTER_KWARG_TO_API = {
    "main_office_only": "is_mainOffice",
    "atm": "is_atm",
    "drive_thru": "is_drive",
    "shared_service": "is_shared",
    "bilingual": "is_bilingual",
    "credit_builder": "is_credit_builder",
    "financial_counseling": "is_fin_counseling",
    "first_time_homebuyer": "is_homebuyer",
    "in_school_branch": "is_school",
    "low_cost_wires": "is_low_wire",
    "no_cost_share_drafts": "is_no_draft",
    "no_cost_tax_prep": "is_no_tax",
    "payday_alternative": "is_payday",
    "mdi": "is_mdi",
    "member_services": "is_member",
}


def build_search_locations_body(
    search_text: str,
    search_type: SearchType,
    *,
    radius: int | None = None,
    skip: int = 0,
    take: int = 100,
    **filters: bool,
) -> dict:
    if search_type == SearchType.ADDRESS:
        if radius is not None and radius not in VALID_RADII:
            raise NCUAValidationError(
                f"radius must be one of {sorted(VALID_RADII)}, got {radius}"
            )
        rd_radius = radius if radius is not None else 25
    else:
        rd_radius = None

    body: dict = {
        "searchText": str(search_text),
        "rdSearchType": search_type.value,
        "rdSearchRadiusList": rd_radius,
        "skip": skip,
        "take": take,
        "sort_item": "distance",
        "sort_direction": "asc",
    }

    for kwarg, api_key in _FILTER_KWARG_TO_API.items():
        body[api_key] = filters.get(kwarg, False)

    return body


def build_name_search_body(name: str, *, skip: int = 0, take: int = 100) -> dict:
    return {"cuName": name, "skip": skip, "take": take}


def build_detail_search_body(
    *,
    name: str | None = None,
    cu_type: str | None = None,
    status: str | None = None,
    region: str | None = None,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    fom_type: str | None = None,
    low_income: bool | None = None,
    is_mdi: bool | None = None,
    skip: int = 0,
    take: int = 20,
) -> dict:
    return {
        "cuName": name,
        "cuType": cu_type,
        "cuStatus": status,
        "region": region,
        "state": state,
        "city": city,
        "zipCode": zip_code,
        "fomType": fom_type,
        "lowIncome": str(low_income).lower() if low_income is not None else None,
        "isMdi": str(is_mdi).lower() if is_mdi is not None else None,
        "skip": skip,
        "take": take,
    }


def build_download_url(
    base_url: str,
    endpoint: str,
    charter: int,
    cycle_date: str,
    is_corporate: bool = False,
    is_snapshot: bool | None = None,
) -> str:
    url = f"{base_url}{endpoint}/{charter}"
    params = [f"isCorpCU={str(is_corporate).lower()}", f"cycleDate={cycle_date}"]
    if is_snapshot is not None:
        params.append(f"isSnapshot={str(is_snapshot).lower()}")
    return f"{url}?{'&'.join(params)}"
