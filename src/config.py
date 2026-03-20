"""Shared constants for paper-stats analysis."""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FIG_DIR = Path(__file__).parent.parent / "figures"
LAST_FULL_YEAR = 2025

COUNTRY_NAMES = {
    "US": "United States", "CN": "China", "GB": "United Kingdom",
    "DE": "Germany", "JP": "Japan", "IN": "India", "FR": "France",
    "IT": "Italy", "CA": "Canada", "AU": "Australia", "KR": "South Korea",
    "BR": "Brazil", "ES": "Spain", "RU": "Russia", "NL": "Netherlands",
    "TR": "Turkey", "IR": "Iran", "PL": "Poland", "SE": "Sweden",
    "CH": "Switzerland", "SA": "Saudi Arabia", "ID": "Indonesia",
    "MX": "Mexico", "EG": "Egypt", "PK": "Pakistan", "MY": "Malaysia",
    "TW": "Taiwan", "PT": "Portugal", "CZ": "Czech Republic",
    "DK": "Denmark", "AT": "Austria", "BE": "Belgium", "NO": "Norway",
    "FI": "Finland", "IL": "Israel", "SG": "Singapore", "TH": "Thailand",
    "ZA": "South Africa", "NG": "Nigeria", "CL": "Chile", "CO": "Colombia",
    "AR": "Argentina", "IE": "Ireland", "RO": "Romania", "GR": "Greece",
    "NZ": "New Zealand", "HU": "Hungary", "UA": "Ukraine",
    "AE": "UAE", "BD": "Bangladesh", "IQ": "Iraq", "HK": "Hong Kong",
    "MA": "Morocco", "EC": "Ecuador", "VN": "Vietnam", "PE": "Peru",
    "PH": "Philippines", "KE": "Kenya", "GH": "Ghana", "ET": "Ethiopia",
    "LK": "Sri Lanka", "TN": "Tunisia", "JO": "Jordan",
}
