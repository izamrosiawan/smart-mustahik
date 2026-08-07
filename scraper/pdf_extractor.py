"""
PDF Extractor Module.

Extracts statistical data tables from official BPS PDF publications
(e.g., 'Provinsi Jawa Timur Dalam Angka' or 'Statistik Kesejahteraan Rakyat')
using pdfplumber and tabula-py.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

from scraper.utils import EAST_JAVA_REGIONS, normalize_regency_name

logger = logging.getLogger("BPS_PDFExtractor")

def extract_tables_with_pdfplumber(pdf_path: Path, page_numbers: List[int]) -> List[pd.DataFrame]:
    """Extract tabular data from specific PDF page numbers using pdfplumber."""
    extracted_tables = []
    try:
        import pdfplumber
        logger.info(f"Opening PDF with pdfplumber: {pdf_path.name}")
        with pdfplumber.open(pdf_path) as pdf:
            for p_num in page_numbers:
                if 1 <= p_num <= len(pdf.pages):
                    page = pdf.pages[p_num - 1]
                    tables = page.extract_tables()
                    for t in tables:
                        if t:
                            df = pd.DataFrame(t[1:], columns=t[0])
                            extracted_tables.append(df)
    except ImportError:
        logger.warning("pdfplumber package is not installed.")
    except Exception as e:
        logger.error(f"Error extracting PDF with pdfplumber from {pdf_path}: {e}")

    return extracted_tables

def extract_tables_with_tabula(pdf_path: Path, pages: str = "all") -> List[pd.DataFrame]:
    """Extract tabular data from PDF using tabula-py."""
    extracted_tables = []
    try:
        import tabula
        logger.info(f"Extracting tables with tabula from {pdf_path.name}...")
        tables = tabula.read_pdf(str(pdf_path), pages=pages, multiple_tables=True)
        for t in tables:
            if isinstance(t, pd.DataFrame) and not t.empty:
                extracted_tables.append(t)
    except ImportError:
        logger.warning("tabula-py package is not installed or Java is missing.")
    except Exception as e:
        logger.error(f"Error extracting PDF with tabula from {pdf_path}: {e}")

    return extracted_tables

def clean_pdf_extracted_table(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and match regency names from PDF extracted tables."""
    if df.empty:
        return df

    cleaned_rows = []
    # Identify regency column
    reg_col = None
    for col in df.columns:
        col_str = str(col).lower()
        if "kabupaten" in col_str or "kota" in col_str or "wilayah" in col_str or "daerah" in col_str:
            reg_col = col
            break

    if reg_col is None and len(df.columns) > 0:
        reg_col = df.columns[0]

    for idx, row in df.iterrows():
        val_name = str(row[reg_col]) if reg_col in df.columns else ""
        norm_name = normalize_regency_name(val_name)
        if norm_name in EAST_JAVA_REGIONS:
            row_dict = row.to_dict()
            row_dict["regency_city"] = norm_name
            cleaned_rows.append(row_dict)

    return pd.DataFrame(cleaned_rows)
