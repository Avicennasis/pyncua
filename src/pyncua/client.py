from __future__ import annotations

import importlib.metadata

import httpx
from pydantic import ValidationError

from pyncua._constants import BASE_URL, CUStatus, CUType, Region, SearchType
from pyncua._requests import (
    build_detail_search_body,
    build_download_url,
    build_name_search_body,
    build_search_locations_body,
)
from pyncua.exceptions import (
    NCUAError,
    NCUANotFoundError,
    NCUAServerError,
    NCUAValidationError,
)
from pyncua.models import (
    CreditUnionDetails,
    LocationSearchResponse,
    NameSearchResult,
    OnlineCreditUnion,
    QuickSearchResult,
    SearchResponse,
)

try:
    _VERSION = importlib.metadata.version("pyncua")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "0.0.0"


class NCUAClient:
    def __init__(self, timeout: float = 30.0, base_url: str = BASE_URL, **kwargs):
        self._base_url = base_url
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": f"pyncua/{_VERSION}"},
            **kwargs,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _post(self, path: str, body: dict) -> dict:
        resp = self._http.post(path, json=body)
        self._check_status(resp)
        return self._decode(resp)

    def _get(self, path: str) -> dict:
        resp = self._http.get(path)
        self._check_status(resp)
        return self._decode(resp)

    def _get_text(self, path: str) -> str:
        resp = self._http.get(path)
        self._check_status(resp)
        return resp.text

    @staticmethod
    def _decode(resp: httpx.Response) -> dict:
        try:
            return resp.json()
        except Exception as e:
            raise NCUAError(
                f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}"
            ) from e

    def _check_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 500:
            raise NCUAServerError(f"NCUA API error {resp.status_code}")
        if resp.status_code >= 400:
            raise NCUAValidationError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    def _parse(self, model_cls, data):
        try:
            return model_cls.model_validate(data)
        except ValidationError as e:
            raise NCUAError(f"Failed to parse response: {e}") from e

    def get_api_version(self) -> str:
        return self._get_text("/api/Search/version")

    def get_current_cycle(self) -> str:
        return self._get("/api/DataQuery/GetCurrentCycle")

    def get_cycle_years(self) -> list[str]:
        return self._get("/api/DataQuery/GetCycleYears")

    def get_merger_query_years(self) -> list[str]:
        return self._get("/api/DataQuery/GetMergerQueryYears")

    def find_offices_by_name(
        self, name: str, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(name, SearchType.NAME, skip=skip, take=take, **filters)
        data = self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        return result

    def find_offices_by_charter(
        self, charter: int, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            str(charter), SearchType.CHARTER, skip=skip, take=take, **filters
        )
        data = self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    def find_offices_by_address(
        self,
        address: str,
        *,
        radius: int = 25,
        skip: int = 0,
        take: int = 100,
        **filters: bool,
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            address, SearchType.ADDRESS, radius=radius, skip=skip, take=take, **filters
        )
        data = self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        if not result.valid:
            raise NCUAValidationError("Search returned valid=false — address may be unresolvable")
        return result

    def get_credit_union(self, charter: int) -> CreditUnionDetails:
        data = self._get(f"/api/CreditUnionDetails/GetCreditUnionDetails/{charter}")
        if data.get("isError") is True:
            raise NCUANotFoundError(data.get("errorMessage") or "Charter not found")
        return self._parse(CreditUnionDetails, data)

    def search_names(
        self, name: str, *, skip: int = 0, take: int = 100
    ) -> SearchResponse[NameSearchResult]:
        body = build_name_search_body(name, skip=skip, take=take)
        data = self._post("/api/Search/GetNameSearch", body)
        return self._parse(SearchResponse[NameSearchResult], data)

    def search_credit_unions(
        self,
        name: str | None = None,
        cu_type: CUType | None = None,
        status: CUStatus | None = None,
        region: Region | None = None,
        state: str | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        fom_type: str | None = None,
        low_income: bool | None = None,
        is_mdi: bool | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> SearchResponse[QuickSearchResult]:
        body = build_detail_search_body(
            name=name,
            cu_type=cu_type.value if cu_type else None,
            status=status.value if status else None,
            region=region.value if region else None,
            state=state,
            city=city,
            zip_code=zip_code,
            fom_type=fom_type,
            low_income=low_income,
            is_mdi=is_mdi,
            skip=skip,
            take=take,
        )
        data = self._post("/api/ResearchCreditUnion/GetDetailSearch", body)
        return self._parse(SearchResponse[QuickSearchResult], data)

    def get_online_credit_unions(self) -> SearchResponse[OnlineCreditUnion]:
        data = self._get("/api/Search/GetOnlineCreditUnions")
        return self._parse(SearchResponse[OnlineCreditUnion], data)

    def download_call_report(
        self, charter: int, cycle_date: str, is_corporate: bool = False
    ) -> bytes:
        url = build_download_url(
            "",
            "/api/CreditUnionDetails/GetDownloadCallReport",
            charter,
            cycle_date,
            is_corporate,
        )
        data = self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])

    def download_profile(
        self,
        charter: int,
        cycle_date: str,
        is_corporate: bool = False,
        is_snapshot: bool = False,
    ) -> bytes:
        url = build_download_url(
            "",
            "/api/CreditUnionDetails/GetDownloadProfile",
            charter,
            cycle_date,
            is_corporate,
            is_snapshot,
        )
        data = self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])
