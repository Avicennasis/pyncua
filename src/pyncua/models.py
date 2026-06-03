from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class _BaseModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        alias_generator=to_camel,
        extra="ignore",
    )


class Office(_BaseModel):
    credit_union_name: str
    credit_union_site_name: str = Field(alias="creditUnionSiteName")
    charter_number: int = Field(alias="creditUnionNumber")
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    latitude: float = Field(alias="addressLatitude")
    longitude: float = Field(alias="addressLongitude")
    is_main_office: bool
    phone: str
    url: str | None = None
    site_functions: list[str] = Field(alias="siteFunctions")
    site_id: int
    distance: float | None = None

    is_mdi: bool = Field(alias="isMdi")
    bilingual_services: bool = Field(alias="bilingual_Services")
    credit_builder: bool = Field(alias="credit_Builder")
    financial_counseling: bool = Field(alias="financial_Counseling")
    first_time_homebuyer: bool = Field(alias="first_Time_Homebuyer_Program")
    in_school_branch: bool = Field(alias="inSchoolBranch")
    low_cost_wires: bool = Field(alias="low_cost_wire_transfers")
    no_cost_tax_prep: bool = Field(alias="no_Cost_Tax_Preparation")
    no_cost_share_drafts: bool = Field(alias="no_Cost_Share_Drafts")
    payday_alternative_1: bool = Field(alias="palS_I")
    payday_alternative_2: bool = Field(alias="palS_II")

    @field_validator("site_functions", mode="before")
    @classmethod
    def _parse_site_functions(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(";") if s.strip()]
        return v


def _yes_no_to_bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    return v.strip().lower() == "yes"


class CreditUnionDetails(_BaseModel):
    name: str = Field(alias="creditUnionName")
    charter_number: int = Field(alias="creditUnionCharter")
    cu_type: str = Field(alias="creditUnionType")
    status: str = Field(alias="creditUnionStatus")
    is_corporate: bool = Field(alias="creditUnionCorp")
    charter_year: str = Field(alias="creditUnionYear")
    charter_issue_date: str = Field(alias="creditUnionIssuedDate")
    insured_date: str = Field(alias="creditUnionInsuredDate")
    charter_state: str = Field(alias="creditUnionCharterState")
    region: str = Field(alias="creditUnionRegion")
    field_of_membership: str = Field(alias="creditUnionFom")
    low_income_designation: bool = Field(alias="creditUnionIli")
    member_of_fhlb: bool = Field(alias="creditUnionFhlb")
    assets: int = Field(alias="creditUnionAssets")
    assets_formatted: str
    peer_group: str = Field(alias="creditUnionPeerGroup")
    number_of_members: int = Field(alias="creditUnionNom")
    members_formatted: str
    address: str = Field(alias="creditUnionAddress")
    address2: str = Field(alias="creditUnionAddress2")
    city: str = Field(alias="creditUnionCity")
    state: str = Field(alias="creditUnionState")
    zip: str = Field(alias="creditUnionZip")
    country: str = Field(alias="creditUnionCountry")
    county: str = Field(alias="creditUnionCounty")
    phone: str = Field(alias="creditUnionPhone")
    phone_formatted: str
    website: str | None = Field(alias="creditUnionWebsite", default=None)
    ceo: str = Field(alias="creditUnionCeo")
    call_report_cycle_dates: dict[str, str] = Field(default_factory=dict)
    profile_cycle_dates: dict[str, str] = Field(default_factory=dict)

    @field_validator("call_report_cycle_dates", "profile_cycle_dates", mode="before")
    @classmethod
    def _coerce_null_dict(cls, v):
        return v if v is not None else {}

    @field_validator("is_corporate", "low_income_designation", "member_of_fhlb", mode="before")
    @classmethod
    def _coerce_yes_no(cls, v: str | bool) -> bool:
        return _yes_no_to_bool(v)


class NameSearchResult(_BaseModel):
    charter_number: int
    name: str


class QuickSearchResult(_BaseModel):
    charter_number: int
    name: str
    city: str
    state: str
    is_corporate: bool
    is_active: bool


class OnlineCreditUnion(_BaseModel):
    charter_number: int
    name: str
    website: str
    phone: str


class LocationSearchResponse(_BaseModel):
    latitude: float
    longitude: float
    valid: bool
    status_code: int = Field(alias="statusCode")
    total_results: int = Field(alias="totalResults")
    offices: list[Office] = Field(alias="list")


class SearchResponse(_BaseModel, Generic[T]):
    total_result_count: int = Field(alias="totalResultCount")
    results: list[T]
