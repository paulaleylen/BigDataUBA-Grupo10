"""
Configuración centralizada del proyecto

Este módulo contiene todas las constantes, paths y configuraciones
del proyecto de commodities.
"""

from pathlib import Path
from datetime import datetime

# ============================================================================
# PATHS DEL PROYECTO
# ============================================================================

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parents[1]

# Directorios de datos
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
INTERIM_DIR = DATA_DIR / 'interim'
PROCESSED_DIR = DATA_DIR / 'processed'
EXTERNAL_DIR = DATA_DIR / 'external'

# Subdirectorios de raw
RAW_KAGGLE_DIR = RAW_DIR / 'kaggle'
RAW_YAHOO_DIR = RAW_DIR / 'yahoo'

# Subdirectorios de interim
INTERIM_COMMODITIES_DIR = INTERIM_DIR / 'commodities'
INTERIM_PREDICTORS_DIR = INTERIM_DIR / 'predictors'
INTERIM_CLIMATE_DIR = INTERIM_DIR / 'climate'
INTERIM_BDI_DIR = INTERIM_DIR / 'bdi'
INTERIM_SUPPLY_DEMAND_DIR = INTERIM_DIR / 'supply_demand'
INTERIM_FRED_DIR = INTERIM_DIR / 'fred'

# Subdirectorios de external (datos de APIs externas)
EXTERNAL_CFTC_DIR = EXTERNAL_DIR / 'cftc'
EXTERNAL_GDELT_DIR = EXTERNAL_DIR / 'gdelt'

# Otros directorios
MODELS_DIR = BASE_DIR / 'models'
REPORTS_DIR = BASE_DIR / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'
REFERENCES_DIR = BASE_DIR / 'references'

# Crear directorios si no existen
for directory in [RAW_DIR, INTERIM_DIR, PROCESSED_DIR, EXTERNAL_DIR,
                  RAW_KAGGLE_DIR, RAW_YAHOO_DIR,
                  INTERIM_COMMODITIES_DIR, INTERIM_PREDICTORS_DIR,
                  INTERIM_CLIMATE_DIR, INTERIM_BDI_DIR, INTERIM_SUPPLY_DEMAND_DIR, INTERIM_FRED_DIR,
                  EXTERNAL_CFTC_DIR, EXTERNAL_GDELT_DIR,
                  MODELS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE DATOS
# ============================================================================

# Fechas
START_DATE = '2000-01-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')

# Commodities - Tickers de Yahoo Finance
COMMODITIES_TICKERS = {
    # Granos
    'Corn': 'ZC=F',
    'Soybeans': 'ZS=F',
    'Wheat': 'ZW=F',
    'Oat': 'ZO=F',
    
    # Energía
    'Crude_Oil': 'CL=F',
    'Brent_Crude': 'BZ=F',
    'Natural_Gas': 'NG=F',
    'Heating_Oil': 'HO=F',
    'RBOB_Gasoline': 'RB=F',
    
    # Metales preciosos
    'Gold': 'GC=F',
    'Silver': 'SI=F',
    'Platinum': 'PL=F',
    'Palladium': 'PA=F',
    
    # Metales industriales
    'Copper': 'HG=F',
    
    # Softs
    'Coffee': 'KC=F',
    'Sugar': 'SB=F',
    'Cotton': 'CT=F',
    'Cocoa': 'CC=F',
    
    # Ganado
    'Live_Cattle': 'LE=F',
    'Feeder_Cattle': 'GF=F',
    'Lean_Hogs': 'HE=F',
    
    # Madera
    'Lumber': 'LBS=F'
}

# Predictores - Tickers de Yahoo Finance
PREDICTORS_TICKERS = {
    'VIX': '^VIX',                    # Volatilidad
    'DXY': 'DX-Y.NYB',                # Dollar Index
    'SP500': '^GSPC',                 # S&P 500
    'Treasury_10Y': '^TNX',           # Tasas 10 años
    'Treasury_2Y': '^IRX',            # Tasas 2 años (proxy Fed Funds)
    'Energy_Index': '^GSPE',          # Índice sector energía
    'Materials_Index': '^GSPMS',      # Índice sector materiales
}

# Kaggle Dataset
KAGGLE_DATASET = 'mattiuzc/commodity-futures-price-history'

# USDA ERS Yearbooks (Government Stocks)
ERS_FEED_GRAINS_CSV = 'https://www.ers.usda.gov/webdocs/DataFiles/50048/FeedGrainsYearbook.csv'
ERS_SOYBEANS_CSV = 'https://www.ers.usda.gov/webdocs/DataFiles/50594/oilcropsyearbook.csv'
ERS_WHEAT_XLSX = 'https://www.ers.usda.gov/webdocs/DataFiles/53786/WheatYearbookTable04.xlsx'

# ============================================================================
# CONFIGURACIÓN DE VISUALIZACIONES
# ============================================================================

# Colores institucionales
UBA_BLUE = '#003D7A'
FCE_BURGUNDY = '#8B0000'

# Estilo de gráficos
PLOT_STYLE = 'seaborn-v0_8-darkgrid'
PLOT_DPI = 150
PLOT_FIGSIZE = (14, 6)

# ============================================================================
# CONFIGURACIÓN DE MODELOS
# ============================================================================

# Semilla para reproducibilidad
RANDOM_STATE = 42

# Train/test split
TEST_SIZE = 0.2

# ============================================================================
# ARCHIVOS DE SALIDA
# ============================================================================

# Datos procesados
COMMODITIES_PROCESSED_FILE = PROCESSED_DIR / 'commodities_base_daily.csv'
PREDICTORS_PROCESSED_FILE = PROCESSED_DIR / 'predictors_consolidated.csv'
FULL_DATASET_FILE = PROCESSED_DIR / 'full_dataset.csv'
FINAL_MODELING_FILE = PROCESSED_DIR / 'features_final_modeling.csv'

# Features académicas (outputs intermedios)
CFTC_FEATURES_FILE = EXTERNAL_CFTC_DIR / 'cftc_features_2000_2025.csv'
GDELT_FEATURES_FILE = EXTERNAL_GDELT_DIR / 'sentiment_features_2000_2025.csv'
BDI_FEATURES_FILE = INTERIM_BDI_DIR / 'bdi_features.csv'
CROP_CONDITIONS_FILE = INTERIM_SUPPLY_DEMAND_DIR / 'crop_conditions_all_features.csv'
GOV_STOCKS_FILE = INTERIM_SUPPLY_DEMAND_DIR / 'government_stocks_ers_all_features.csv'
FRED_FEATURES_FILE = INTERIM_FRED_DIR / 'fred_all_features.csv'

# Metadata
METADATA_FILE = PROCESSED_DIR / 'metadata.json'
PREDICTORS_REGISTRY_FILE = INTERIM_PREDICTORS_DIR / 'predictors_registry.json'

# ============================================================================
# LOGGING
# ============================================================================

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
