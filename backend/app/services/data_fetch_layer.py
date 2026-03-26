"""
Data Fetch Layer

Fetches data from external APIs based on parsed intent.
Supports World Bank, Data Commons, and internal OSINT sources.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from functools import lru_cache

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    DataSet,
    DataSourceType,
    DomainType,
    TimeRange,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Country Code Mappings
# =============================================================================

COUNTRY_TO_ISO2 = {
    "India": "IN",
    "China": "CN",
    "United States": "US",
    "United Kingdom": "GB",
    "Russia": "RU",
    "Japan": "JP",
    "Germany": "DE",
    "France": "FR",
    "Brazil": "BR",
    "Pakistan": "PK",
    "Bangladesh": "BD",
    "Indonesia": "ID",
    "Nigeria": "NG",
    "Mexico": "MX",
    "Canada": "CA",
    "Australia": "AU",
    "South Korea": "KR",
    "North Korea": "KP",
    "Saudi Arabia": "SA",
    "Iran": "IR",
    "Turkey": "TR",
    "Egypt": "EG",
    "South Africa": "ZA",
    "Vietnam": "VN",
    "Thailand": "TH",
    "Singapore": "SG",
    "Malaysia": "MY",
    "United Arab Emirates": "AE",
    "Israel": "IL",
    "Italy": "IT",
    "Spain": "ES",
    "Poland": "PL",
    "Ukraine": "UA",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Sweden": "SE",
    "Norway": "NO",
    "Denmark": "DK",
    "Finland": "FI",
    "Switzerland": "CH",
    "Austria": "AT",
    "Greece": "GR",
    "Portugal": "PT",
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Venezuela": "VE",
    "Philippines": "PH",
    "Taiwan": "TW",
    "Sri Lanka": "LK",
    "Nepal": "NP",
    "Myanmar": "MM",
    "Afghanistan": "AF",
    "Iraq": "IQ",
    "Syria": "SY",
    "Yemen": "YE",
    "Ethiopia": "ET",
    "Kenya": "KE",
    "Ghana": "GH",
    "Morocco": "MA",
    "Algeria": "DZ",
}

COUNTRY_TO_ISO3 = {k: v + v[1] if len(v) == 2 else v for k, v in COUNTRY_TO_ISO2.items()}
# Manual corrections for ISO3
COUNTRY_TO_ISO3.update({
    "India": "IND",
    "China": "CHN",
    "United States": "USA",
    "United Kingdom": "GBR",
    "Russia": "RUS",
    "Japan": "JPN",
    "Germany": "DEU",
    "France": "FRA",
    "Brazil": "BRA",
    "Pakistan": "PAK",
    "Bangladesh": "BGD",
    "Indonesia": "IDN",
    "South Korea": "KOR",
    "Australia": "AUS",
    "Canada": "CAN",
    "Mexico": "MEX",
    "Nigeria": "NGA",
    "South Africa": "ZAF",
    "Saudi Arabia": "SAU",
    "Turkey": "TUR",
    "Iran": "IRN",
    "Egypt": "EGY",
})


# =============================================================================
# World Bank Indicator Mappings
# =============================================================================

INDICATOR_TO_WB_CODE = {
    "GDP": "NY.GDP.MKTP.CD",
    "GDP Growth": "NY.GDP.MKTP.KD.ZG",
    "GDP Per Capita": "NY.GDP.PCAP.CD",
    "Inflation Rate": "FP.CPI.TOTL.ZG",
    "Unemployment Rate": "SL.UEM.TOTL.ZS",
    "Population": "SP.POP.TOTL",
    "Exports": "NE.EXP.GNFS.CD",
    "Imports": "NE.IMP.GNFS.CD",
    "Trade Balance": "NE.RSB.GNFS.CD",
    "Foreign Direct Investment": "BX.KLT.DINV.CD.WD",
    "Government Debt": "GC.DOD.TOTL.GD.ZS",
    "Budget Deficit": "GC.BAL.CASH.GD.ZS",
    "Interest Rate": "FR.INR.RINR",
    "Life Expectancy": "SP.DYN.LE00.IN",
    "Literacy Rate": "SE.ADT.LITR.ZS",
    "Birth Rate": "SP.DYN.CBRT.IN",
    "Death Rate": "SP.DYN.CDRT.IN",
    "CO2 Emissions": "EN.ATM.CO2E.KT",
    "Energy Consumption": "EG.USE.PCAP.KG.OE",
    "Military Expenditure": "MS.MIL.XPND.CD",
    "R&D Expenditure": "GB.XPD.RSDV.GD.ZS",
    "Tourist Arrivals": "ST.INT.ARVL",
}


# =============================================================================
# World Bank Client
# =============================================================================

class WorldBankClient:
    """Client for World Bank Open Data API."""

    BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_indicator(
        self,
        country_codes: List[str],
        indicator_code: str,
        start_year: int,
        end_year: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch indicator data from World Bank API.

        Args:
            country_codes: List of ISO3 country codes
            indicator_code: World Bank indicator code
            start_year: Start year
            end_year: End year

        Returns:
            List of data points with year, value, country
        """
        if not country_codes:
            return []

        session = await self._get_session()
        countries_str = ";".join(country_codes)
        url = f"{self.BASE_URL}/country/{countries_str}/indicator/{indicator_code}"

        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 1000,
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"World Bank API returned {response.status}")
                    return []

                data = await response.json()

                # World Bank returns [metadata, data_array]
                if not data or len(data) < 2 or not data[1]:
                    return []

                results = []
                for item in data[1]:
                    if item.get("value") is not None:
                        results.append({
                            "year": int(item.get("date", 0)),
                            "value": item.get("value"),
                            "country": item.get("country", {}).get("value"),
                            "country_code": item.get("countryiso3code"),
                        })

                return sorted(results, key=lambda x: (x["country"], x["year"]))

        except asyncio.TimeoutError:
            logger.error("World Bank API timeout")
            return []
        except Exception as e:
            logger.error(f"World Bank API error: {e}")
            return []

    async def fetch_multiple_indicators(
        self,
        country_codes: List[str],
        indicator_codes: List[str],
        start_year: int,
        end_year: int,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch multiple indicators in parallel."""
        tasks = [
            self.fetch_indicator(country_codes, code, start_year, end_year)
            for code in indicator_codes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data_map = {}
        for code, result in zip(indicator_codes, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {code}: {result}")
                data_map[code] = []
            else:
                data_map[code] = result

        return data_map


# =============================================================================
# Data Commons Client
# =============================================================================

class DataCommonsClient:
    """Client for Google Data Commons API."""

    BASE_URL = "https://api.datacommons.org"

    # Data Commons variable mappings
    STAT_VAR_MAP = {
        "Population": "Count_Person",
        "Life Expectancy": "LifeExpectancy_Person",
        "Unemployment Rate": "UnemploymentRate_Person",
        "CO2 Emissions": "Amount_Emissions_CarbonDioxide",
        "GDP": "Amount_EconomicActivity_GrossDomesticProduction_Nominal",
    }

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_dcid(self, country: str) -> str:
        """Get Data Commons ID for a country."""
        iso2 = COUNTRY_TO_ISO2.get(country, "")
        return f"country/{iso2}" if iso2 else ""

    async def fetch_stats(
        self,
        countries: List[str],
        indicator: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch statistics from Data Commons.

        Args:
            countries: List of country names
            indicator: Indicator name

        Returns:
            List of data points
        """
        stat_var = self.STAT_VAR_MAP.get(indicator)
        if not stat_var:
            return []

        dcids = [self._get_dcid(c) for c in countries if self._get_dcid(c)]
        if not dcids:
            return []

        session = await self._get_session()
        url = f"{self.BASE_URL}/v2/observation"

        payload = {
            "select": ["variable", "value", "date", "entity"],
            "variable": {"dcids": [stat_var]},
            "entity": {"dcids": dcids},
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Data Commons API returned {response.status}")
                    return []

                data = await response.json()
                results = []

                # Parse Data Commons response format
                observations = data.get("byVariable", {}).get(stat_var, {}).get("byEntity", {})
                for entity, obs_data in observations.items():
                    ordered_facets = obs_data.get("orderedFacets", [])
                    for facet in ordered_facets:
                        observations_list = facet.get("observations", [])
                        for obs in observations_list:
                            results.append({
                                "year": int(obs.get("date", "0")[:4]),
                                "value": obs.get("value"),
                                "country": entity.replace("country/", ""),
                                "country_code": entity.replace("country/", ""),
                            })

                return results

        except Exception as e:
            logger.error(f"Data Commons API error: {e}")
            return []


# =============================================================================
# Fallback Data Provider
# =============================================================================

class FallbackDataProvider:
    """Provides fallback/mock data when external APIs are unavailable."""

    # Sample data for common indicators
    FALLBACK_DATA = {
        "GDP": {
            "India": [(2019, 2.87e12), (2020, 2.66e12), (2021, 3.18e12), (2022, 3.39e12), (2023, 3.57e12)],
            "China": [(2019, 14.28e12), (2020, 14.72e12), (2021, 17.73e12), (2022, 17.96e12), (2023, 17.79e12)],
            "United States": [(2019, 21.43e12), (2020, 21.06e12), (2021, 23.32e12), (2022, 25.46e12), (2023, 27.36e12)],
        },
        "GDP Growth": {
            "India": [(2019, 3.9), (2020, -5.8), (2021, 9.7), (2022, 7.0), (2023, 7.8)],
            "China": [(2019, 6.0), (2020, 2.2), (2021, 8.4), (2022, 3.0), (2023, 5.2)],
            "United States": [(2019, 2.3), (2020, -2.8), (2021, 5.9), (2022, 2.1), (2023, 2.5)],
        },
        "Population": {
            "India": [(2019, 1.37e9), (2020, 1.38e9), (2021, 1.39e9), (2022, 1.42e9), (2023, 1.43e9)],
            "China": [(2019, 1.40e9), (2020, 1.41e9), (2021, 1.41e9), (2022, 1.41e9), (2023, 1.41e9)],
            "United States": [(2019, 3.28e8), (2020, 3.31e8), (2021, 3.32e8), (2022, 3.33e8), (2023, 3.35e8)],
        },
        "Inflation Rate": {
            "India": [(2019, 3.7), (2020, 6.6), (2021, 5.1), (2022, 6.7), (2023, 5.4)],
            "China": [(2019, 2.9), (2020, 2.4), (2021, 0.9), (2022, 2.0), (2023, 0.2)],
            "United States": [(2019, 1.8), (2020, 1.2), (2021, 4.7), (2022, 8.0), (2023, 4.1)],
        },
        "Military Expenditure": {
            "India": [(2019, 71.1e9), (2020, 72.9e9), (2021, 76.6e9), (2022, 81.4e9), (2023, 83.6e9)],
            "China": [(2019, 261e9), (2020, 252e9), (2021, 293e9), (2022, 292e9), (2023, 296e9)],
            "United States": [(2019, 732e9), (2020, 778e9), (2021, 801e9), (2022, 877e9), (2023, 886e9)],
        },
    }

    def get_fallback_data(
        self,
        indicator: str,
        countries: List[str],
        start_year: int,
        end_year: int,
    ) -> List[Dict[str, Any]]:
        """Get fallback data for an indicator."""
        indicator_data = self.FALLBACK_DATA.get(indicator, {})
        results = []

        for country in countries:
            country_data = indicator_data.get(country, [])
            for year, value in country_data:
                if start_year <= year <= end_year:
                    results.append({
                        "year": year,
                        "value": value,
                        "country": country,
                        "country_code": COUNTRY_TO_ISO3.get(country, ""),
                    })

        return results


# =============================================================================
# Data Fetch Layer
# =============================================================================

class DataFetchLayer:
    """
    Intelligent data fetching layer.

    Fetches data from multiple sources based on parsed intent,
    with caching and fallback strategies.
    """

    def __init__(self):
        self._world_bank = WorldBankClient()
        self._data_commons = DataCommonsClient()
        self._fallback = FallbackDataProvider()
        self._cache: Dict[str, Any] = {}

    async def close(self):
        """Close all client sessions."""
        await self._world_bank.close()
        await self._data_commons.close()

    async def fetch_for_intent(self, intent: ParsedIntent) -> DataFetchResult:
        """
        Fetch data based on parsed intent.

        Args:
            intent: Parsed intent from user query

        Returns:
            DataFetchResult with fetched datasets
        """
        datasets: Dict[str, DataSet] = {}
        sources_used: List[str] = []
        sources_failed: List[str] = []

        countries = intent.countries
        indicators = intent.indicators
        time_range = intent.time_range or TimeRange(2018, datetime.now().year)

        # Convert country names to ISO3 codes
        country_codes = [
            COUNTRY_TO_ISO3.get(c, "")
            for c in countries
            if COUNTRY_TO_ISO3.get(c)
        ]

        # Fetch from World Bank
        for indicator in indicators:
            wb_code = INDICATOR_TO_WB_CODE.get(indicator)

            if wb_code and country_codes:
                try:
                    data = await self._world_bank.fetch_indicator(
                        country_codes,
                        wb_code,
                        time_range.start_year,
                        time_range.end_year,
                    )

                    if data:
                        datasets[indicator] = DataSet(
                            source=DataSourceType.WORLD_BANK,
                            indicator=indicator,
                            values=data,
                            unit=self._get_unit(indicator),
                            metadata={"wb_code": wb_code},
                        )
                        if "World Bank" not in sources_used:
                            sources_used.append("World Bank")
                    else:
                        # Try fallback
                        fallback_data = self._fallback.get_fallback_data(
                            indicator, countries,
                            time_range.start_year, time_range.end_year
                        )
                        if fallback_data:
                            datasets[indicator] = DataSet(
                                source=DataSourceType.WORLD_BANK,
                                indicator=indicator,
                                values=fallback_data,
                                unit=self._get_unit(indicator),
                                metadata={"fallback": True},
                            )
                            sources_used.append("Fallback Data")

                except Exception as e:
                    logger.error(f"Error fetching {indicator}: {e}")
                    sources_failed.append(f"World Bank ({indicator})")

                    # Use fallback
                    fallback_data = self._fallback.get_fallback_data(
                        indicator, countries,
                        time_range.start_year, time_range.end_year
                    )
                    if fallback_data:
                        datasets[indicator] = DataSet(
                            source=DataSourceType.WORLD_BANK,
                            indicator=indicator,
                            values=fallback_data,
                            unit=self._get_unit(indicator),
                            metadata={"fallback": True},
                        )

        # Try Data Commons for additional data
        for indicator in indicators:
            if indicator not in datasets:
                try:
                    data = await self._data_commons.fetch_stats(countries, indicator)
                    if data:
                        datasets[indicator] = DataSet(
                            source=DataSourceType.DATA_COMMONS,
                            indicator=indicator,
                            values=data,
                            unit=self._get_unit(indicator),
                        )
                        if "Data Commons" not in sources_used:
                            sources_used.append("Data Commons")
                except Exception as e:
                    logger.error(f"Data Commons error for {indicator}: {e}")

        # Calculate data quality score
        data_quality_score = self._calculate_quality_score(datasets, indicators)

        return DataFetchResult(
            datasets=datasets,
            sources_used=sources_used,
            sources_failed=sources_failed,
            data_quality_score=data_quality_score,
            time_coverage=time_range,
            geo_coverage=countries,
            metadata={
                "fetch_timestamp": datetime.now().isoformat(),
                "indicator_count": len(datasets),
            },
        )

    def _get_unit(self, indicator: str) -> str:
        """Get unit for an indicator."""
        units = {
            "GDP": "USD",
            "GDP Growth": "%",
            "GDP Per Capita": "USD",
            "Inflation Rate": "%",
            "Unemployment Rate": "%",
            "Population": "people",
            "Exports": "USD",
            "Imports": "USD",
            "Military Expenditure": "USD",
            "CO2 Emissions": "kt",
            "Life Expectancy": "years",
        }
        return units.get(indicator, "")

    def _calculate_quality_score(
        self,
        datasets: Dict[str, DataSet],
        requested_indicators: List[str],
    ) -> float:
        """Calculate data quality score based on coverage."""
        if not requested_indicators:
            return 0.5

        coverage = len(datasets) / len(requested_indicators)

        # Check data completeness
        completeness_scores = []
        for dataset in datasets.values():
            if dataset.values:
                completeness_scores.append(1.0)
            else:
                completeness_scores.append(0.0)

        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores else 0.5
        )

        # Penalize fallback data
        fallback_count = sum(
            1 for ds in datasets.values()
            if ds.metadata.get("fallback")
        )
        fallback_penalty = fallback_count * 0.1

        score = (coverage * 0.6 + avg_completeness * 0.4) - fallback_penalty
        return max(0.1, min(1.0, round(score, 2)))


# =============================================================================
# Singleton Instance
# =============================================================================

_data_fetch_layer: Optional[DataFetchLayer] = None


def get_data_fetch_layer() -> DataFetchLayer:
    """Get singleton DataFetchLayer instance."""
    global _data_fetch_layer
    if _data_fetch_layer is None:
        _data_fetch_layer = DataFetchLayer()
    return _data_fetch_layer
