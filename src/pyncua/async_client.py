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


class AsyncNCUAClient:
    def __init__(self, timeout: float = 30.0, base_url: str = BASE_URL, **kwargs):
        self._base_url = base_url
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": f"pyncua/{_VERSION}"},
            **kwargs,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _post(self, path: str, body: dict) -> dict:
        resp = await self._http.post(path, json=body)
        self._check_status(resp)
        return self._decode(resp)

    async def _get(self, path: str) -> dict:
        resp = await self._http.get(path)
        self._check_status(resp)
        return self._decode(resp)

    @staticmethod
    def _decode(resp: httpx.Response) -> dict:
        try:
            return resp.json()
        except Exception as e:
            raise NCUAError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}") from e

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

    async def find_offices_by_name(
        self, name: str, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(name, SearchType.NAME, skip=skip, take=take, **filters)
        data = await self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    async def find_offices_by_charter(
        self, charter: int, *, skip: int = 0, take: int = 100, **filters: bool
    ) -> LocationSearchResponse:
        body = build_search_locations_body(
            str(charter), SearchType.CHARTER, skip=skip, take=take, **filters
        )
        data = await self._post("/api/Search/GetSearchLocations", body)
        return self._parse(LocationSearchResponse, data)

    async def find_offices_by_address(
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
        data = await self._post("/api/Search/GetSearchLocations", body)
        result = self._parse(LocationSearchResponse, data)
        if not result.valid:
            raise NCUAValidationError("Search returned valid=false — address may be unresolvable")
        return result

    async def get_credit_union(self, charter: int) -> CreditUnionDetails:
        data = await self._get(f"/api/CreditUnionDetails/GetCreditUnionDetails/{charter}")
        if data.get("isError"):
            msg = data.get("errorMessage", "Charter not found")
            raise NCUANotFoundError(msg)
        return self._parse(CreditUnionDetails, data)

    async def search_names(
        self, name: str, *, skip: int = 0, take: int = 100
    ) -> SearchResponse[NameSearchResult]:
        body = build_name_search_body(name, skip=skip, take=take)
        data = await self._post("/api/Search/GetNameSearch", body)
        return self._parse(SearchResponse[NameSearchResult], data)

    async def search_credit_unions(
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
        data = await self._post("/api/ResearchCreditUnion/GetDetailSearch", body)
        return self._parse(SearchResponse[QuickSearchResult], data)

    async def get_online_credit_unions(self) -> SearchResponse[OnlineCreditUnion]:
        data = await self._get("/api/Search/GetOnlineCreditUnions")
        return self._parse(SearchResponse[OnlineCreditUnion], data)

    async def download_call_report(
        self, charter: int, cycle_date: str, is_corporate: bool = False
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadCallReport",
            charter, cycle_date, is_corporate,
        )
        data = await self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])

    async def download_profile(
        self,
        charter: int,
        cycle_date: str,
        is_corporate: bool = False,
        is_snapshot: bool = False,
    ) -> bytes:
        url = build_download_url(
            "", "/api/CreditUnionDetails/GetDownloadProfile",
            charter, cycle_date, is_corporate, is_snapshot,
        )
        data = await self._get(url)
        if "fileContents" not in data:
            raise NCUAError("Unexpected download response: missing fileContents")
        return bytes(data["fileContents"])
