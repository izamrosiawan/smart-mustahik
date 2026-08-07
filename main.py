"""
Main ETL Pipeline Orchestrator for BPS East Java (Jawa Timur) Data Collection.

Collects, parses, cleans, validates, and exports statistical data for all 38 regencies/cities
in East Java from 2020 to 2024 (190 rows x 13 indicator columns).
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.utils import (
    ensure_directories, validate_dataset, EAST_JAVA_REGIONS
)
from scraper.download import download_all_indicators
from scraper.extract_tables import extract_indicator_dataframes
from scraper.clean import clean_indicator_dataframe
from scraper.merge import (
    merge_all_indicators, generate_missing_and_dtype_report, build_data_dictionary
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BPS_Main_ETL")

def run_pipeline():
    """Execute complete end-to-end ETL pipeline."""
    logger.info("==========================================================")
    logger.info("Starting BPS East Java (Jawa Timur) 2020-2024 ETL Pipeline")
    logger.info("==========================================================")

    dirs = ensure_directories(PROJECT_ROOT)
    outputs_dir = dirs["outputs"]
    processed_dir = dirs["processed"]

    # 1. Download data automatically & cache raw files
    logger.info("[STEP 1/5] Downloading raw BPS API & table data...")
    raw_data = download_all_indicators([2020, 2021, 2022, 2023, 2024])

    # 2. Extract DataFrames per indicator
    logger.info("[STEP 2/5] Extracting and parsing indicator DataFrames...")
    indicator_dfs = extract_indicator_dataframes(raw_data)

    # 3. Merge indicators onto standard master grid (190 rows)
    logger.info("[STEP 3/5] Merging all indicators into master dataset (190 rows)...")
    master_df = merge_all_indicators(indicator_dfs)

    # Calculate population density where area and population exist
    if "total_population" in master_df.columns and "area_km2" in indicator_dfs:
        area_df = indicator_dfs["area_km2"]
        area_map = {}
        for _, row in area_df.iterrows():
            area_map[row["regency_city"]] = row.get("value")
        
        def calc_density(row):
            pop = row.get("total_population")
            reg = row.get("regency_city")
            area = area_map.get(reg)
            if pd.notna(pop) and area and area > 0:
                return round(pop / area, 2)
            return row.get("population_density")

        master_df["population_density"] = master_df.apply(calc_density, axis=1)

    # 4. Validate row counts and dataset integrity
    logger.info("[STEP 4/5] Validating dataset integrity...")
    is_valid, validation_errors = validate_dataset(master_df)

    if not is_valid:
        logger.warning("Dataset validation warnings/errors:")
        for err in validation_errors:
            logger.warning(f"  - {err}")
    else:
        logger.info("Dataset validation PASSED cleanly! (190 rows, 38 regencies, 5 years [2020-2024]).")

    # Generate Missing Value & Data Type Reports
    dtype_report, missing_report = generate_missing_and_dtype_report(master_df)
    logger.info("\n--- MISSING VALUE REPORT ---")
    logger.info("\n" + missing_report.to_string(index=False))

    # 5. Export deliverables
    logger.info("[STEP 5/5] Exporting final CSV, Excel, and Data Dictionary deliverables...")
    
    csv_file = outputs_dir / "dataset_jatim_2020_2024.csv"
    xlsx_file = outputs_dir / "dataset_jatim_2020_2024.xlsx"
    dict_file = outputs_dir / "data_dictionary.xlsx"

    # Save to processed directory as well
    processed_csv = processed_dir / "dataset_jatim_2020_2024.csv"
    master_df.to_csv(processed_csv, index=False)

    # Export CSV
    master_df.to_csv(csv_file, index=False)
    logger.info(f"Exported CSV dataset: {csv_file}")

    # Export Excel with formatting
    with pd.ExcelWriter(xlsx_file, engine="openpyxl") as writer:
        master_df.to_excel(writer, sheet_name="Data 2020-2024", index=False)
        missing_report.to_excel(writer, sheet_name="Missing Value Report", index=False)
        dtype_report.to_excel(writer, sheet_name="Data Type Report", index=False)
    logger.info(f"Exported Excel dataset: {xlsx_file}")

    # Export Data Dictionary
    data_dict_df = build_data_dictionary()
    with pd.ExcelWriter(dict_file, engine="openpyxl") as writer:
        data_dict_df.to_excel(writer, sheet_name="Data Dictionary", index=False)
    logger.info(f"Exported Data Dictionary Excel: {dict_file}")

    logger.info("==========================================================")
    logger.info("ETL Pipeline completed successfully!")
    logger.info("==========================================================")
    return master_df

if __name__ == "__main__":
    run_pipeline()
