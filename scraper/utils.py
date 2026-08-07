"""
Utility functions and constants for BPS East Java (Jawa Timur) ETL Pipeline.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BPS_ETL_Utils")

# Official BPS API Key & Domain
BPS_API_KEY = "5a91eee05bb200a412fdddf3f53778a8"
BPS_DOMAIN_JATIM = "3500"

# Year mapping for BPS API (th parameter)
YEAR_MAP = {
    2020: "120",
    2021: "121",
    2022: "122",
    2023: "123",
    2024: "124"
}

# Standard 38 Regencies and Cities in Jawa Timur
EAST_JAVA_REGIONS: List[str] = [
    # 29 Regencies (Kabupaten)
    "Kabupaten Pacitan",
    "Kabupaten Ponorogo",
    "Kabupaten Trenggalek",
    "Kabupaten Tulungagung",
    "Kabupaten Blitar",
    "Kabupaten Kediri",
    "Kabupaten Malang",
    "Kabupaten Lumajang",
    "Kabupaten Jember",
    "Kabupaten Banyuwangi",
    "Kabupaten Bondowoso",
    "Kabupaten Situbondo",
    "Kabupaten Probolinggo",
    "Kabupaten Pasuruan",
    "Kabupaten Sidoarjo",
    "Kabupaten Mojokerto",
    "Kabupaten Jombang",
    "Kabupaten Nganjuk",
    "Kabupaten Madiun",
    "Kabupaten Magetan",
    "Kabupaten Ngawi",
    "Kabupaten Bojonegoro",
    "Kabupaten Tuban",
    "Kabupaten Lamongan",
    "Kabupaten Gresik",
    "Kabupaten Bangkalan",
    "Kabupaten Sampang",
    "Kabupaten Pamekasan",
    "Kabupaten Sumenep",
    # 9 Cities (Kota)
    "Kota Kediri",
    "Kota Blitar",
    "Kota Malang",
    "Kota Probolinggo",
    "Kota Pasuruan",
    "Kota Mojokerto",
    "Kota Madiun",
    "Kota Surabaya",
    "Kota Batu"
]

# Map BPS Vervar Code (e.g. 3501 -> Kabupaten Pacitan)
VERVAR_REGION_MAP: Dict[str, str] = {
    "3501": "Kabupaten Pacitan",
    "3502": "Kabupaten Ponorogo",
    "3503": "Kabupaten Trenggalek",
    "3504": "Kabupaten Tulungagung",
    "3505": "Kabupaten Blitar",
    "3506": "Kabupaten Kediri",
    "3507": "Kabupaten Malang",
    "3508": "Kabupaten Lumajang",
    "3509": "Kabupaten Jember",
    "3510": "Kabupaten Banyuwangi",
    "3511": "Kabupaten Bondowoso",
    "3512": "Kabupaten Situbondo",
    "3513": "Kabupaten Probolinggo",
    "3514": "Kabupaten Pasuruan",
    "3515": "Kabupaten Sidoarjo",
    "3516": "Kabupaten Mojokerto",
    "3517": "Kabupaten Jombang",
    "3518": "Kabupaten Nganjuk",
    "3519": "Kabupaten Madiun",
    "3520": "Kabupaten Magetan",
    "3521": "Kabupaten Ngawi",
    "3522": "Kabupaten Bojonegoro",
    "3523": "Kabupaten Tuban",
    "3524": "Kabupaten Lamongan",
    "3525": "Kabupaten Gresik",
    "3526": "Kabupaten Bangkalan",
    "3527": "Kabupaten Sampang",
    "3528": "Kabupaten Pamekasan",
    "3529": "Kabupaten Sumenep",
    "3571": "Kota Kediri",
    "3572": "Kota Blitar",
    "3573": "Kota Malang",
    "3574": "Kota Probolinggo",
    "3575": "Kota Pasuruan",
    "3576": "Kota Mojokerto",
    "3577": "Kota Madiun",
    "3578": "Kota Surabaya",
    "3579": "Kota Batu"
}

def get_retry_session(
    retries: int = 5,
    backoff_factor: float = 1.0,
    status_forcelist: Tuple[int, ...] = (429, 500, 502, 503, 504)
) -> requests.Session:
    """Create requests Session with automated retries and custom headers."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    })
    return session

def normalize_regency_name(name: str) -> str:
    """Standardize regency/city name variations to standard official BPS format.
    
    Examples:
        - "Kab. Malang" -> "Kabupaten Malang"
        - "Malang" -> "Kabupaten Malang"
        - "Kota Surabaya" -> "Kota Surabaya"
        - "Surabaya" -> "Kota Surabaya"
        - "Kabupaten Malang" -> "Kabupaten Malang"
    """
    if not name or not isinstance(name, str):
        return ""
    
    clean_name = name.strip()
    clean_name = re.sub(r"\s+", " ", clean_name)
    
    # Check exact match first
    for reg in EAST_JAVA_REGIONS:
        if clean_name.lower() == reg.lower():
            return reg

    # Handle prefixes
    upper_name = clean_name.upper()
    if upper_name.startswith("KAB. ") or upper_name.startswith("KABUPATEN "):
        base = re.sub(r"^(KAB\.|KABUPATEN)\s+", "", clean_name, flags=re.IGNORECASE).strip()
        expected = f"Kabupaten {base.title()}"
        for reg in EAST_JAVA_REGIONS:
            if reg.lower() == expected.lower():
                return reg
    elif upper_name.startswith("KOTA "):
        base = re.sub(r"^KOTA\s+", "", clean_name, flags=re.IGNORECASE).strip()
        expected = f"Kota {base.title()}"
        for reg in EAST_JAVA_REGIONS:
            if reg.lower() == expected.lower():
                return reg
    else:
        # Check without prefix
        base_title = clean_name.title()
        for reg in EAST_JAVA_REGIONS:
            reg_base = reg.replace("Kabupaten ", "").replace("Kota ", "")
            if reg_base.lower() == base_title.lower():
                return reg

    return clean_name

def ensure_directories(base_path: Optional[Path] = None) -> Dict[str, Path]:
    """Ensure all required project directories exist."""
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent

    dirs = {
        "raw": base_path / "data" / "raw",
        "interim": base_path / "data" / "interim",
        "processed": base_path / "data" / "processed",
        "outputs": base_path / "outputs",
        "notebooks": base_path / "notebooks"
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs

def validate_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate dataset structure, row counts, duplicate checks, and missing values."""
    errors = []
    
    # Expected rows
    expected_rows = 38 * 5 # 190
    if len(df) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, but got {len(df)} rows.")

    # Check required columns
    required_cols = [
        "regency_city", "year", "total_population", "number_of_poor_people",
        "poverty_percentage", "school_participation_rate", "sanitation_access_percent",
        "drinking_water_access_percent", "proper_housing_percent", "unemployment_rate",
        "gdp_per_capita", "population_density", "hdi"
    ]
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")

    if "regency_city" in df.columns and "year" in df.columns:
        # Check duplicates
        dups = df.duplicated(subset=["regency_city", "year"]).sum()
        if dups > 0:
            errors.append(f"Found {dups} duplicate (regency_city, year) rows.")

        # Check regency count
        unique_regions = df["regency_city"].nunique()
        if unique_regions != 38:
            errors.append(f"Expected 38 unique regencies/cities, but found {unique_regions}.")

        # Check year range
        unique_years = sorted(df["year"].unique())
        if unique_years != [2020, 2021, 2022, 2023, 2024]:
            errors.append(f"Expected years [2020, 2021, 2022, 2023, 2024], but found {unique_years}.")

    is_valid = len(errors) == 0
    return is_valid, errors
