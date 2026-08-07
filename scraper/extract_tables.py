"""
Extract Tables Module.

Extracts statistical tables from raw BPS API JSON payloads, HTML static tables,
XLSX files, and CSV exports into clean pandas DataFrames per indicator.
"""

import json
import html
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd

from scraper.utils import (
    EAST_JAVA_REGIONS, VERVAR_REGION_MAP, normalize_regency_name, ensure_directories
)
from scraper.clean import clean_numeric_value

logger = logging.getLogger("BPS_ExtractTables")

def parse_bps_api_json(payload: Dict[str, Any], year: int) -> Dict[str, Dict[str, Optional[float]]]:
    """Parse BPS API JSON payload into region -> {turvar_label: value} mapping."""
    if not payload or payload.get("status") != "OK":
        return {}

    datacontent = payload.get("datacontent", {})
    vervar_list = payload.get("vervar", [])
    turvar_list = payload.get("turvar", [])

    turvar_map = {}
    if turvar_list:
        for t in turvar_list:
            t_val = str(t.get("val"))
            t_label = t.get("label", "value")
            turvar_map[t_val] = t_label
    else:
        turvar_map["0"] = "value"

    vervar_map = {}
    for v in vervar_list:
        v_code = str(v.get("val"))
        v_label = v.get("label")
        if v_code in VERVAR_REGION_MAP:
            vervar_map[v_code] = VERVAR_REGION_MAP[v_code]
        else:
            norm = normalize_regency_name(v_label)
            if norm in EAST_JAVA_REGIONS:
                vervar_map[v_code] = norm

    results = {reg: {} for reg in EAST_JAVA_REGIONS}

    for k, val in datacontent.items():
        matched_region = None
        sorted_codes = sorted(vervar_map.keys(), key=len, reverse=True)
        for v_code in sorted_codes:
            if k.startswith(v_code):
                if v_code in ("3500", "35000"):
                    break
                matched_region = vervar_map[v_code]
                break

        if matched_region and matched_region in results:
            t_label = "value"
            for t_code, label in turvar_map.items():
                if t_code != "0" and t_code in k:
                    t_label = label
                    break
            
            if not t_label or t_label == "value":
                if turvar_list:
                    t_label = turvar_list[0].get("label", "value")

            try:
                val_num = float(val) if val is not None and val != "" else None
            except (ValueError, TypeError):
                val_num = None

            results[matched_region][t_label] = val_num

    return results

def parse_static_table_to_dataframe(payload: Dict[str, Any], table_id: int) -> pd.DataFrame:
    """Parse BPS static table HTML payload into clean DataFrame with (regency_city, year, value)."""
    if not payload or payload.get("status") != "OK":
        return pd.DataFrame()

    data = payload.get("data", {})
    raw_html = data.get("table", "")
    if not raw_html:
        return pd.DataFrame()

    unescaped = html.unescape(raw_html)
    soup = BeautifulSoup(unescaped, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells and any(c for c in cells):
            rows.append(cells)

    if not rows:
        return pd.DataFrame()

    extracted_data = []

    # Table 3019 (Sanitasi) or Table 3020 (Air Minum)
    if table_id in (3019, 3020):
        val_name = "sanitation_access_percent" if table_id == 3019 else "drinking_water_access_percent"
        year_headers = [2017, 2018, 2019, 2020, 2021, 2022]
        
        for r in rows:
            if not r or len(r) < 6:
                continue
            reg_candidate = normalize_regency_name(r[0])
            if reg_candidate in EAST_JAVA_REGIONS:
                vals = r[-6:]
                for idx, y in enumerate(year_headers):
                    if y in (2020, 2021, 2022):
                        v_num = clean_numeric_value(vals[idx])
                        extracted_data.append({
                            "regency_city": reg_candidate,
                            "year": y,
                            val_name: v_num
                        })

    # Table 3042 (Kemiskinan 2021-2022)
    elif table_id == 3042:
        for r in rows:
            if not r or len(r) < 7:
                continue
            reg_candidate = normalize_regency_name(r[0])
            if reg_candidate in EAST_JAVA_REGIONS:
                jml_2021 = clean_numeric_value(r[3])
                jml_2022 = clean_numeric_value(r[4])
                pct_2021 = clean_numeric_value(r[5])
                pct_2022 = clean_numeric_value(r[6])

                extracted_data.append({
                    "regency_city": reg_candidate,
                    "year": 2021,
                    "number_of_poor_people": jml_2021,
                    "poverty_percentage": pct_2021
                })
                extracted_data.append({
                    "regency_city": reg_candidate,
                    "year": 2022,
                    "number_of_poor_people": jml_2022,
                    "poverty_percentage": pct_2022
                })

    # Table 2634 (Population 2020 & 2022)
    elif table_id == 2634:
        for r in rows:
            if not r or len(r) < 3:
                continue
            reg_candidate = normalize_regency_name(r[0])
            if reg_candidate in EAST_JAVA_REGIONS:
                pop_2020_ribu = clean_numeric_value(r[1])
                pop_2022_ribu = clean_numeric_value(r[2])
                
                if pop_2020_ribu:
                    extracted_data.append({
                        "regency_city": reg_candidate,
                        "year": 2020,
                        "total_population": pop_2020_ribu * 1000.0
                    })
                if pop_2022_ribu:
                    extracted_data.append({
                        "regency_city": reg_candidate,
                        "year": 2022,
                        "total_population": pop_2022_ribu * 1000.0
                    })

    # Table 2635 (Density 2020 & 2022)
    elif table_id == 2635:
        for r in rows:
            if not r or len(r) < 5:
                continue
            reg_candidate = normalize_regency_name(r[0])
            if reg_candidate in EAST_JAVA_REGIONS:
                dens_2020 = clean_numeric_value(r[3])
                dens_2022 = clean_numeric_value(r[4])
                
                if dens_2020:
                    extracted_data.append({
                        "regency_city": reg_candidate,
                        "year": 2020,
                        "population_density": dens_2020
                    })
                if dens_2022:
                    extracted_data.append({
                        "regency_city": reg_candidate,
                        "year": 2022,
                        "population_density": dens_2022
                    })

    # Table 2697 (Jumlah Penduduk 2022)
    elif table_id == 2697:
        for r in rows:
            if not r or len(r) < 4:
                continue
            reg_candidate = normalize_regency_name(r[0])
            if reg_candidate in EAST_JAVA_REGIONS:
                pop_val = clean_numeric_value(r[3])
                extracted_data.append({
                    "regency_city": reg_candidate,
                    "year": 2022,
                    "total_population": pop_val
                })

    return pd.DataFrame(extracted_data)

def extract_indicator_dataframes(downloaded_data: Dict[str, Dict[Any, Any]]) -> Dict[str, pd.DataFrame]:
    """Convert raw downloaded payload dictionaries into interim DataFrames per indicator."""
    dirs = ensure_directories()
    interim_dir = dirs["interim"]

    indicator_dfs = {}

    for ind_name, year_payloads in downloaded_data.items():
        if ind_name.endswith("_static"):
            all_static_rows = []
            for t_id, payload in year_payloads.items():
                df_st = parse_static_table_to_dataframe(payload, t_id)
                if not df_st.empty:
                    all_static_rows.append(df_st)
            if all_static_rows:
                df_merged_static = pd.concat(all_static_rows, ignore_index=True)
                clean_name = ind_name.replace("_static", "")
                indicator_dfs[clean_name] = df_merged_static
                logger.info(f"Parsed static table indicator '{clean_name}': {len(df_merged_static)} rows.")
        else:
            rows = []
            for y, payload in year_payloads.items():
                if not isinstance(y, int):
                    continue
                parsed_year_data = parse_bps_api_json(payload, y)
                for reg in EAST_JAVA_REGIONS:
                    val_dict = parsed_year_data.get(reg, {})
                    row = {
                        "regency_city": reg,
                        "year": y
                    }
                    if val_dict:
                        for k, v in val_dict.items():
                            row[k] = v
                    rows.append(row)

            df = pd.DataFrame(rows)
            if not df.empty and len(df.columns) > 2:
                interim_file = interim_dir / f"{ind_name}_interim.csv"
                df.to_csv(interim_file, index=False)
                logger.info(f"Saved interim dataframe for '{ind_name}': {len(df)} rows -> {interim_file.name}")
                indicator_dfs[ind_name] = df

    return indicator_dfs
