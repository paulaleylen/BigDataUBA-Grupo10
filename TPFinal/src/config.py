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

# Otros directorios
MODELS_DIR = BASE_DIR / 'models'
REPORTS_DIR = BASE_DIR / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'
REFERENCES_DIR = BASE_DIR / 'references'

# Crear directorios si no existen
for directory in [RAW_DIR, INTERIM_DIR, PROCESSED_DIR, EXTERNAL_DIR,
                  RAW_KAGGLE_DIR, RAW_YAHOO_DIR,
                  INTERIM_COMMODITIES_DIR, INTERIM_PREDICTORS_DIR, INTERIM_CLIMATE_DIR,
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
    
    # Derivados de Soja (Crush Margin)
    'Soybean_Oil': 'ZL=F',            # Aceite de soja (biodiésel + alimentos)
    'Soybean_Meal': 'ZM=F',           # Harina de soja (alimento animal)
    
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
    'Lumber': 'LBS=F',
    
    # Biocombustibles
    'Ethanol': 'EH=F',                # Etanol CME (demanda maíz USA ~40%)
    
    # Cereales adicionales
    # 'Rice': 'RR=F',                 # ❌ Arroz CME delisted - datos insuficientes
    'Wheat_Kansas': 'KE=F',           # Trigo Kansas HRW (hard red winter)
    # 'Wheat_MATIF': 'EBM=F'          # ❌ Trigo Euronext - ticker inactivo en Yahoo Finance
}

# Predictores - Tickers de Yahoo Finance
PREDICTORS_TICKERS = {
    # Volatilidad y Sentimiento
    'VIX': '^VIX',                    # Volatilidad (CBOE Volatility Index)
    
    # Índices Bursátiles
    'SP500': '^GSPC',                 # S&P 500 (indicador sentimiento económico global)
    
    # Índice Dólar
    'DXY': 'DX-Y.NYB',                # Dollar Index (dólar vs canasta de monedas)
    
    # Tipos de Cambio (principales países exportadores/importadores de soja)
    'USD_BRL': 'BRL=X',               # USD/Real brasileño (Brasil = exportador #1 soja)
    'USD_CNY': 'CNY=X',               # USD/Yuan chino (China = importador #1 soja)
    'USD_ARS': 'ARS=X',               # USD/Peso argentino (Argentina = exportador #3 soja)
    'USD_RUB': 'RUB=X',               # USD/Rublo ruso (Rusia = exportador #1 trigo)
    'USD_UAH': 'UAH=X',               # USD/Grivna ucraniana (Ucrania = top 5 exportador trigo/maíz)
    'EUR_USD': 'EURUSD=X',            # EUR/USD (UE = gran exportador trigo)
    
    # Tasas de Interés
    'Treasury_10Y': '^TNX',           # Tasas bonos del Tesoro 10 años (costo de carry)
    'Treasury_2Y': '^IRX',            # Tasas bonos del Tesoro 2 años
    
    # Índices Sectoriales
    'Energy_Index': '^GSPE',          # Índice sector energía S&P 500
    'Materials_Index': 'XLB',         # Materials Select Sector SPDR Fund (alternativa a ^GSPMS delisted)
    
    # Inflación Proxy (no hay IPC directo en yfinance, usar TIP como proxy)
    'TIPS': 'TIP',                    # iShares TIPS Bond ETF (protección inflación)
}

# Kaggle Dataset
KAGGLE_DATASET = 'mattiuzc/commodity-futures-price-history'

# ============================================================================
# CONFIGURACIÓN DE DATOS CLIMÁTICOS
# ============================================================================

# Regiones clave para commodities agrícolas (lat, lon, peso producción)
# Pesos basados en producción global de soja 2024 (USDA)
CLIMATE_REGIONS = {
    'Brazil': {
        'lat': -13.5,
        'lon': -55.5,
        'name': 'Mato Grosso (Brasil)',
        'weight': 0.51,  # 51% producción mundial de soja
        'description': 'Principal región productora de Brasil (50% producción global)'
    },
    'USA': {
        'lat': 41.5,
        'lon': -93.5,
        'name': 'Corn Belt (Iowa, USA)',
        'weight': 0.29,  # 29% producción mundial
        'description': 'Corn Belt estadounidense (principal productor USA)'
    },
    'Argentina': {
        'lat': -34.5,
        'lon': -61.0,
        'name': 'Pampa Húmeda (Argentina)',
        'weight': 0.11,  # 11% producción mundial
        'description': 'Región pampeana argentina (3er exportador mundial)'
    }
}

# NASA POWER API - Parámetros climáticos
NASA_POWER_PARAMS = {
    'T2M': 'Temperature at 2 Meters (°C)',           # Temperatura media diaria
    'T2M_MAX': 'Max Temperature at 2 Meters (°C)',   # Temperatura máxima
    'T2M_MIN': 'Min Temperature at 2 Meters (°C)',   # Temperatura mínima
    'PRECTOTCORR': 'Precipitation (mm/day)',         # Precipitación corregida
    'RH2M': 'Relative Humidity at 2 Meters (%)',     # Humedad relativa
    'ALLSKY_SFC_SW_DWN': 'Solar Radiation (MJ/m²/day)',  # Radiación solar
    'WS2M': 'Wind Speed at 2 Meters (m/s)',          # Velocidad del viento
}

# Parámetros a descargar (optimizado para granos + ET0)
CLIMATE_PARAMS_DOWNLOAD = [
    'T2M', 'T2M_MAX', 'T2M_MIN',           # Temperatura
    'PRECTOTCORR',                         # Precipitación
    'RH2M',                                # Humedad relativa (para ET0)
    'ALLSKY_SFC_SW_DWN',                   # Radiación solar (para ET0)
    'WS2M'                                 # Velocidad viento (para ET0)
]

# ENSO (ONI) - URL de datos mensuales
ONI_URL = 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'

# Growing Season - Períodos críticos por cultivo (month ranges)
GROWING_SEASONS = {
    'Soybeans': {
        'Brazil': {'planting': (10, 12), 'harvest': (2, 4)},      # Oct-Dic, Feb-Abr
        'USA': {'planting': (4, 6), 'harvest': (9, 11)},          # Abr-Jun, Sep-Nov
        'Argentina': {'planting': (11, 1), 'harvest': (3, 5)}     # Nov-Ene, Mar-May
    },
    'Corn': {
        'Brazil': {'planting': (9, 11), 'harvest': (2, 3)},       # Sep-Nov, Feb-Mar
        'USA': {'planting': (4, 5), 'harvest': (9, 11)},          # Abr-May, Sep-Nov
        'Argentina': {'planting': (9, 11), 'harvest': (3, 4)}     # Sep-Nov, Mar-Abr
    }
}

# Umbrales de estrés climático para granos
CLIMATE_THRESHOLDS = {
    'heat_stress': 35,      # °C - Temperatura que daña soja/maíz
    'cold_stress': 10,      # °C - Temperatura mínima para crecimiento
    'optimal_precip': 100,  # mm/month - Precipitación óptima
    'gdd_base': 10          # °C - Base para Growing Degree Days (soja)
}

# Archivo de registro de clima
CLIMATE_REGISTRY_FILE = INTERIM_CLIMATE_DIR / 'climate_registry.json'

# ============================================================================
# SUPPLY & DEMAND - USDA PSD API (No API Key Required)
# ============================================================================

# Directorio para datos de oferta-demanda
INTERIM_SUPPLY_DEMAND_DIR = INTERIM_DIR / 'supply_demand'
INTERIM_SUPPLY_DEMAND_DIR.mkdir(parents=True, exist_ok=True)

# USDA PSD API - Production, Supply and Distribution
PSD_BASE_URL = 'https://apps.fas.usda.gov/OpenData/api/psd'

# Commodity codes (USDA PSD)
PSD_COMMODITIES = {
    'Soybeans': '0440000',
    'Corn': '0440100',
    'Wheat': '0430000'
}

# Country codes principales para soja
# NOTA: Los nombres deben coincidir EXACTAMENTE con Country_Name en el CSV
PSD_COUNTRIES = {
    'World': None,              # Agregado mundial (no disponible en CSV individual)
    'Brazil': 'BR',
    'United States': 'US',      # CSV usa "United States", no "USA"
    'Argentina': 'AR',
    'China': 'CH',
    'Paraguay': 'PA',
    'India': 'IN'
}

# Attributes de interés (supply-demand fundamentals)
PSD_ATTRIBUTES = [
    'Area Harvested',           # Área cosechada (1000 HA)
    'Yield',                    # Rendimiento (MT/HA)
    'Beginning Stocks',         # Inventarios iniciales
    'Production',               # Producción (1000 MT)
    'Imports',                  # Importaciones (1000 MT)
    'Domestic Consumption',     # Consumo doméstico (1000 MT)
    'Crush',                    # Molienda/procesamiento (1000 MT)
    'Exports',                  # Exportaciones (1000 MT)
    'Ending Stocks',            # Inventarios finales (1000 MT)
    'Total Distribution',       # Total uso (1000 MT)
    'Total Supply'              # Total oferta (1000 MT)
]

# Marketing years de interés
PSD_START_YEAR = 2000
PSD_END_YEAR = 2025

# Archivo de registro
SUPPLY_DEMAND_REGISTRY_FILE = INTERIM_SUPPLY_DEMAND_DIR / 'supply_demand_registry.json'

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
CLIMATE_PROCESSED_FILE = PROCESSED_DIR / 'climate_predictors_global.csv'
FULL_DATASET_FILE = PROCESSED_DIR / 'full_dataset.csv'

# Metadata
METADATA_FILE = PROCESSED_DIR / 'metadata.json'
PREDICTORS_REGISTRY_FILE = INTERIM_PREDICTORS_DIR / 'predictors_registry.json'
CLIMATE_REGISTRY_FILE = INTERIM_CLIMATE_DIR / 'climate_registry.json'

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
