"""
Merge Data Module.

Combines individual indicator datasets on (regency_city, year) into a unified
master dataset for all 38 East Java regencies/cities from 2020 to 2024 (190 rows).
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

from scraper.utils import (
    EAST_JAVA_REGIONS, ensure_directories, validate_dataset
)
from scraper.clean import clean_numeric_value, clean_indicator_dataframe

logger = logging.getLogger("BPS_Merge")

def create_master_grid() -> pd.DataFrame:
    """Create full grid of 38 regencies/cities x 5 years (2020-2024) = 190 rows."""
    years = [2020, 2021, 2022, 2023, 2024]
    grid_rows = []
    for reg in EAST_JAVA_REGIONS:
        for y in years:
            grid_rows.append({
                "regency_city": reg,
                "year": y
            })
    return pd.DataFrame(grid_rows)

def merge_all_indicators(indicator_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge individual indicator DataFrames into unified master DataFrame."""
    master_df = create_master_grid()
    logger.info(f"Initialized master grid with {len(master_df)} rows.")

    target_indicators = [
        "total_population",
        "number_of_poor_people",
        "poverty_percentage",
        "school_participation_rate",
        "sanitation_access_percent",
        "drinking_water_access_percent",
        "proper_housing_percent",
        "unemployment_rate",
        "gdp_per_capita",
        "population_density",
        "hdi"
    ]

    for ind in target_indicators:
        if ind not in master_df.columns:
            master_df[ind] = np.nan

    for ind_name, df_ind in indicator_dfs.items():
        if df_ind.empty:
            continue

        df_clean = clean_indicator_dataframe(df_ind)
        logger.info(f"Merging indicator '{ind_name}': {len(df_clean)} cleaned rows...")

        for col in df_clean.columns:
            if col in ("regency_city", "year"):
                continue

            col_lower = str(col).lower()
            target_cols = []

            if "ipm" in col_lower or "pembangunan manusia" in col_lower or ind_name == "hdi":
                target_cols.append("hdi")
            elif "tpt" in col_lower or "pengangguran" in col_lower or ind_name == "unemployment_rate":
                target_cols.append("unemployment_rate")
            elif "aps" in col_lower or "partisipasi" in col_lower or ind_name == "school_participation_rate":
                target_cols.append("school_participation_rate")
            elif col == "sanitation_access_percent" or "sanitasi" in col_lower or ind_name in ("sanitation", "sanitation_access_percent"):
                target_cols.append("sanitation_access_percent")
            elif col == "drinking_water_access_percent" or "air" in col_lower or ind_name in ("drinking_water", "drinking_water_access_percent"):
                target_cols.append("drinking_water_access_percent")
            elif col == "proper_housing_percent" or "hunian" in col_lower or "rumah" in col_lower or ind_name in ("proper_housing", "proper_housing_percent"):
                target_cols.append("proper_housing_percent")
            elif col == "gdp_per_capita" or "pdrb" in col_lower or ind_name == "gdp_per_capita":
                target_cols.append("gdp_per_capita")
            elif col == "number_of_poor_people" or ("jumlah" in col_lower and "miskin" in col_lower):
                target_cols.append("number_of_poor_people")
            elif col == "poverty_percentage" or ("persen" in col_lower and "miskin" in col_lower):
                target_cols.append("poverty_percentage")
            elif col == "total_population" or ("penduduk" in col_lower and "jumlah" in col_lower):
                target_cols.append("total_population")
            elif col == "population_density" or "kepadatan" in col_lower or ind_name == "population_density":
                target_cols.append("population_density")

            for target_col in target_cols:
                temp_df = df_clean[["regency_city", "year", col]].copy()
                temp_df.rename(columns={col: f"{target_col}_new"}, inplace=True)
                temp_df = temp_df.drop_duplicates(subset=["regency_city", "year"])

                master_df = master_df.merge(
                    temp_df, on=["regency_city", "year"], how="left"
                )
                master_df[target_col] = master_df[f"{target_col}_new"].combine_first(master_df[target_col])
                master_df.drop(columns=[f"{target_col}_new"], inplace=True)

    final_cols = [
        "regency_city", "year", "total_population", "number_of_poor_people",
        "poverty_percentage", "school_participation_rate", "sanitation_access_percent",
        "drinking_water_access_percent", "proper_housing_percent", "unemployment_rate",
        "gdp_per_capita", "population_density", "hdi"
    ]
    master_df = master_df[final_cols]
    return master_df

def generate_missing_and_dtype_report(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate summary report of data types and missing value counts/percentages."""
    dtype_rows = []
    missing_rows = []

    total_rows = len(df)
    for col in df.columns:
        dt = str(df[col].dtype)
        null_cnt = df[col].isnull().sum()
        null_pct = round((null_cnt / total_rows) * 100, 2)
        valid_cnt = total_rows - null_cnt

        dtype_rows.append({
            "Column": col,
            "Data Type": dt,
            "Non-Null Count": valid_cnt
        })

        missing_rows.append({
            "Variable Name": col,
            "Missing Count": null_cnt,
            "Missing Percentage (%)": null_pct,
            "Status": "Complete" if null_cnt == 0 else f"{null_cnt} missing"
        })

    return pd.DataFrame(dtype_rows), pd.DataFrame(missing_rows)

def build_data_dictionary() -> pd.DataFrame:
    """Build data dictionary specifications for Excel export."""
    dict_data = [
        {
            "Variable Name": "regency_city",
            "Definition": "Official name of Regency (Kabupaten) or City (Kota) in East Java Province.",
            "Unit": "Categorical",
            "Source": "Official BPS Regency/City Classification",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "year",
            "Definition": "Reference calendar year for statistical observation.",
            "Unit": "Year",
            "Source": "Official BPS Publications / BPS Web API",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "total_population",
            "Definition": "Total resident population in regency/city.",
            "Unit": "Jiwa (Persons)",
            "Source": "BPS Dynamic Data / SP2020 & Projection Tables",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "number_of_poor_people",
            "Definition": "Number of population living below the official BPS poverty line.",
            "Unit": "Ribu Jiwa (Thousand Persons)",
            "Source": "BPS Data Kemiskinan Menurut Kabupaten/Kota (Static Table 3042)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "poverty_percentage",
            "Definition": "Percentage of population living below the poverty line.",
            "Unit": "Persen (%)",
            "Source": "BPS Data Kemiskinan Menurut Kabupaten/Kota (Static Table 3042)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "school_participation_rate",
            "Definition": "School Participation Rate (Angka Partisipasi Sekolah - APS) for age group 16-18 or school age.",
            "Unit": "Persen (%)",
            "Source": "BPS Angka Partisipasi Sekolah (Var 632)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "sanitation_access_percent",
            "Definition": "Percentage of households with access to proper sanitation facilities.",
            "Unit": "Persen (%)",
            "Source": "BPS Persentase Rumah Tangga Sanitasi Layak (Static Table 3019)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "drinking_water_access_percent",
            "Definition": "Percentage of households with access to proper drinking water sources.",
            "Unit": "Persen (%)",
            "Source": "BPS Persentase Rumah Tangga Air Minum Layak (Static Table 3020)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "proper_housing_percent",
            "Definition": "Percentage of households residing in proper housing (roof/floor/wall indicators).",
            "Unit": "Persen (%)",
            "Source": "BPS Indikator Perumahan & Kesejahteraan Rakyat (Static Table 3130)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "unemployment_rate",
            "Definition": "Open Unemployment Rate (Tingkat Pengangguran Terbuka - TPT).",
            "Unit": "Persen (%)",
            "Source": "BPS Tingkat Pengangguran Terbuka Menurut Kabupaten/Kota (Var 54)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "gdp_per_capita",
            "Definition": "Gross Regional Domestic Product (PDRB) per Capita at Current Market Prices (ADHB).",
            "Unit": "Ribu Rupiah (Thousand IDR)",
            "Source": "BPS PDRB Perkapita Menurut Kabupaten/Kota (Var 327)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "population_density",
            "Definition": "Population density per square kilometer.",
            "Unit": "Jiwa/km²",
            "Source": "Calculated from Total Population / Regional Area (Var 81)",
            "Year Coverage": "2020–2024"
        },
        {
            "Variable Name": "hdi",
            "Definition": "Human Development Index (Indeks Pembangunan Manusia - IPM).",
            "Unit": "Index (0-100)",
            "Source": "BPS Indeks Pembangunan Manusia Menurut Kabupaten/Kota (Var 36)",
            "Year Coverage": "2020–2024"
        }
    ]
    return pd.DataFrame(dict_data)
