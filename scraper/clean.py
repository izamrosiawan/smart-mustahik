"""
Clean Data Module.

Data cleaning, standardization, numeric conversion, and normalization logic.
"""

import re
import logging
from typing import Any, Union, Optional
import pandas as pd
import numpy as np

from scraper.utils import EAST_JAVA_REGIONS, normalize_regency_name

logger = logging.getLogger("BPS_Clean")

def clean_numeric_value(val: Any) -> Optional[float]:
    """Convert raw formatted string or object into a clean numeric float.
    
    Examples:
        - "71.71%" -> 71.71
        - "1,234.50" -> 1234.50
        - "67,33" -> 67.33
        - "-" or "..." or "N/A" -> None
    """
    if pd.isna(val) or val is None:
        return None
    
    if isinstance(val, (int, float)):
        return float(val) if not np.isnan(val) else None

    val_str = str(val).strip()
    if not val_str or val_str in ("-", "...", "N/A", "n/a", "null", "None"):
        return None

    # Remove currency, percent, and extra spaces
    val_str = val_str.replace("%", "").replace("Rp", "").replace("Ribu", "").strip()

    # Handle Indonesian decimal comma vs dot separator
    # If string contains both '.' and ',', e.g., "1.234,56"
    if "." in val_str and "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str and "." not in val_str:
        # Single comma like "67,33" -> "67.33"
        val_str = val_str.replace(",", ".")

    # Remove non-numeric characters except minus sign and decimal point
    val_clean = re.sub(r"[^\d.-]", "", val_str)

    try:
        res = float(val_clean)
        return res if not np.isnan(res) else None
    except ValueError:
        return None

def clean_regency_column(series: pd.Series) -> pd.Series:
    """Standardize regency/city name column values."""
    return series.apply(lambda x: normalize_regency_name(str(x)))

def clean_year_column(series: pd.Series) -> pd.Series:
    """Standardize year column values to integer [2020-2024]."""
    def parse_year(y: Any) -> Optional[int]:
        if pd.isna(y) or y is None:
            return None
        try:
            val = int(float(str(y).strip()))
            if 2000 <= val <= 2030:
                return val
        except (ValueError, TypeError):
            pass
        return None

    return series.apply(parse_year)

def clean_indicator_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean all columns in an indicator DataFrame."""
    if df.empty:
        return df

    df_clean = df.copy()

    if "regency_city" in df_clean.columns:
        df_clean["regency_city"] = clean_regency_column(df_clean["regency_city"])

    if "year" in df_clean.columns:
        df_clean["year"] = clean_year_column(df_clean["year"])

    # Clean numeric indicator columns
    for col in df_clean.columns:
        if col not in ("regency_city", "year"):
            df_clean[col] = df_clean[col].apply(clean_numeric_value)

    # Filter only valid East Java regencies and target years
    df_clean = df_clean[
        (df_clean["regency_city"].isin(EAST_JAVA_REGIONS)) &
        (df_clean["year"].isin([2020, 2021, 2022, 2023, 2024]))
    ].reset_index(drop=True)

    return df_clean
