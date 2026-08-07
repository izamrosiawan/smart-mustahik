"""
BPS Data Downloader Module.

Downloads statistical indicator tables from official BPS Web API / static table views
and caches raw responses in data/raw/ directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from scraper.utils import (
    BPS_API_KEY, BPS_DOMAIN_JATIM, YEAR_MAP,
    get_retry_session, ensure_directories
)

logger = logging.getLogger("BPS_Downloader")

# Key Variable ID Mapping in BPS API for domain 3500 (East Java)
INDICATOR_VAR_MAP: Dict[str, List[int]] = {
    "hdi": [36, 615],
    "unemployment_rate": [54, 462],
    "school_participation_rate": [632, 278, 37],
    "sanitation_access_percent": [486, 308],
    "drinking_water_access_percent": [308, 486],
    "proper_housing_percent": [486, 308],
    "gdp_per_capita": [327, 328],
    "poverty_data": [669, 49, 131],
    "total_population": [12, 287],
    "area_km2": [81],
    "expenditure_per_capita": [575, 34, 377]
}

# Key Official BPS Static Tables for domain 3500
STATIC_TABLE_IDS: Dict[str, List[int]] = {
    "sanitation_static": [3019],
    "drinking_water_static": [3020],
    "poverty_static": [3042, 3040, 3041],
    "housing_assets_static": [3130],
    "population_static": [2634, 2697, 2698],
    "density_static": [2635]
}

def download_var_data_for_year(var_id: int, year_val: int, raw_dir: Path) -> Optional[Dict[str, Any]]:
    """Download data for a specific BPS variable and year, caching JSON to disk."""
    if year_val not in YEAR_MAP:
        logger.warning(f"Year {year_val} not in YEAR_MAP. Skipping.")
        return None

    th_code = YEAR_MAP[year_val]
    cache_file = raw_dir / f"var_{var_id}_year_{year_val}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("status") == "OK":
                    logger.info(f"Loaded cached raw data: {cache_file.name}")
                    return data
        except Exception as e:
            logger.warning(f"Failed to read cached file {cache_file}: {e}. Re-downloading.")

    url = f"https://webapi.bps.go.id/v1/api/list/model/data/domain/{BPS_DOMAIN_JATIM}/var/{var_id}/th/{th_code}/key/{BPS_API_KEY}"
    session = get_retry_session()
    
    try:
        logger.info(f"Downloading BPS API data: var={var_id}, year={year_val}...")
        response = session.get(url, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "OK":
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(res_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved raw payload to {cache_file.name}")
                return res_json
            else:
                logger.warning(f"BPS API returned non-OK status for var={var_id}, year={year_val}: {res_json.get('message')}")
        else:
            logger.error(f"HTTP {response.status_code} error fetching var={var_id}, year={year_val}")
    except Exception as e:
        logger.error(f"Error downloading var={var_id}, year={year_val}: {e}")

    return None

def download_static_table(table_id: int, raw_dir: Path) -> Optional[Dict[str, Any]]:
    """Download official BPS static table payload by table ID and cache JSON to disk."""
    cache_file = raw_dir / f"static_table_{table_id}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("status") == "OK":
                    logger.info(f"Loaded cached static table: {cache_file.name}")
                    return data
        except Exception as e:
            logger.warning(f"Failed to read cached static table {cache_file}: {e}")

    url = f"https://webapi.bps.go.id/v1/api/view/model/statictable/domain/{BPS_DOMAIN_JATIM}/lang/ind/id/{table_id}/key/{BPS_API_KEY}"
    session = get_retry_session()

    try:
        logger.info(f"Downloading BPS static table ID {table_id}...")
        response = session.get(url, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "OK":
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(res_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved static table payload to {cache_file.name}")
                return res_json
            else:
                logger.warning(f"Static table API returned status for ID {table_id}: {res_json.get('message')}")
    except Exception as e:
        logger.error(f"Error downloading static table ID {table_id}: {e}")

    return None

def download_all_indicators(years: List[int] = [2020, 2021, 2022, 2023, 2024]) -> Dict[str, Dict[Any, Any]]:
    """Download raw JSON payloads for all target indicators, years, and static tables."""
    dirs = ensure_directories()
    raw_dir = dirs["raw"]
    
    downloaded_results: Dict[str, Dict[Any, Any]] = {}

    for ind_name, var_ids in INDICATOR_VAR_MAP.items():
        downloaded_results[ind_name] = {}
        for var_id in var_ids:
            for y in years:
                if y not in downloaded_results[ind_name]:
                    payload = download_var_data_for_year(var_id, y, raw_dir)
                    if payload and payload.get("status") == "OK":
                        datacontent = payload.get("datacontent", {})
                        if len(datacontent) > 0:
                            downloaded_results[ind_name][y] = payload

    for cat_name, t_ids in STATIC_TABLE_IDS.items():
        downloaded_results[cat_name] = {}
        for t_id in t_ids:
            payload = download_static_table(t_id, raw_dir)
            if payload and payload.get("status") == "OK":
                downloaded_results[cat_name][t_id] = payload

    logger.info("Completed downloading raw indicator data from official BPS source.")
    return downloaded_results

if __name__ == "__main__":
    download_all_indicators()
