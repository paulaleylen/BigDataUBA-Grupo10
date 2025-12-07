"""
Download economic indicators from FRED (Federal Reserve Economic Data)

FRED provides high-quality macroeconomic data from the Federal Reserve.
Requires API key (free registration at https://fred.stlouisfed.org/docs/api/api_key.html)

Key indicators:
- FEDFUNDS: Federal Funds Effective Rate (%)
- DFF: Federal Funds Rate (daily)
- UNRATE: Unemployment Rate (%)
- CPIAUCSL: Consumer Price Index
- GDP: Gross Domestic Product
"""

import pandas as pd
import requests
from pathlib import Path
import sys
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# Agregar src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import INTERIM_DIR, logger

# Output directory
FRED_DIR = INTERIM_DIR / 'fred'
FRED_DIR.mkdir(parents=True, exist_ok=True)

# FRED API Configuration
FRED_API_KEY = None
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

# Series a descargar
FRED_SERIES = {
    'FEDFUNDS': {
        'name': 'Federal Funds Effective Rate',
        'units': 'Percent',
        'frequency': 'monthly',
        'description': 'Target federal funds rate set by FOMC'
    },
    'DFF': {
        'name': 'Federal Funds Rate Daily',
        'units': 'Percent',
        'frequency': 'daily',
        'description': 'Effective federal funds rate (daily)'
    },
    'UNRATE': {
        'name': 'Unemployment Rate',
        'units': 'Percent',
        'frequency': 'monthly',
        'description': 'Civilian unemployment rate'
    },
    'CPIAUCSL': {
        'name': 'Consumer Price Index',
        'units': 'Index 1982-1984=100',
        'frequency': 'monthly',
        'description': 'CPI for all urban consumers'
    },
    'GDP': {
        'name': 'Gross Domestic Product',
        'units': 'Billions of Dollars',
        'frequency': 'quarterly',
        'description': 'US GDP seasonally adjusted annual rate'
    }
}


def get_fred_api_key():
    """
    Obtiene FRED API key desde .env o interactivo.
    """
    global FRED_API_KEY
    
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        FRED_API_KEY = os.getenv('FRED_API_KEY')
    except:
        pass
    
    if FRED_API_KEY is None:
        logger.warning("FRED_API_KEY no encontrada en .env")
        logger.info("Registrate gratis en: https://fred.stlouisfed.org/docs/api/api_key.html")
        FRED_API_KEY = input("Ingresa tu FRED API key (o Enter para skip): ").strip()
        
        if FRED_API_KEY:
            # Guardar en .env
            env_file = BASE_DIR / '.env'
            with open(env_file, 'a') as f:
                f.write(f'\nFRED_API_KEY={FRED_API_KEY}\n')
            logger.info(f"✓ API key guardada en {env_file}")
    
    return FRED_API_KEY


def download_fred_series(series_id, start_date='2000-01-01'):
    """
    Descarga una serie de FRED.
    
    Args:
        series_id (str): ID de la serie (ej: 'FEDFUNDS')
        start_date (str): Fecha inicio YYYY-MM-DD
    
    Returns:
        pd.DataFrame: Datos con columnas [date, value]
    """
    if not FRED_API_KEY:
        logger.error(f"❌ FRED API key requerida para {series_id}")
        return pd.DataFrame()
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'sort_order': 'asc'
    }
    
    try:
        response = requests.get(FRED_BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'observations' not in data:
            logger.warning(f"⚠️  No observations found for {series_id}")
            return pd.DataFrame()
        
        observations = data['observations']
        
        # Convertir a DataFrame
        df = pd.DataFrame(observations)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Eliminar valores faltantes (FRED usa '.')
        df = df[df['value'].notna()].copy()
        
        df = df[['date', 'value']].sort_values('date').reset_index(drop=True)
        
        logger.info(f"  ✓ {len(df):,} observaciones | {df['date'].min().date()} → {df['date'].max().date()}")
        logger.info(f"  Media: {df['value'].mean():.2f} | Min: {df['value'].min():.2f} | Max: {df['value'].max():.2f}")
        
        return df
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP Error para {series_id}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error descargando {series_id}: {e}")
        return pd.DataFrame()


def resample_to_daily(df, method='ffill'):
    """
    Resample monthly/quarterly data to daily (forward-fill).
    
    Args:
        df (pd.DataFrame): DataFrame con columnas [date, value]
        method (str): 'ffill' (forward-fill) o 'interpolate'
    
    Returns:
        pd.DataFrame: Daily data
    """
    if df.empty:
        return df
    
    df = df.set_index('date')
    
    # Crear rango diario
    date_range = pd.date_range(df.index.min(), df.index.max(), freq='D')
    df_daily = df.reindex(date_range)
    
    # Forward-fill (mantener último valor hasta nueva observación)
    if method == 'ffill':
        df_daily['value'] = df_daily['value'].ffill()
    elif method == 'interpolate':
        df_daily['value'] = df_daily['value'].interpolate(method='linear')
    
    df_daily = df_daily.reset_index().rename(columns={'index': 'date'})
    
    return df_daily


def create_fred_features(df, series_id, metadata):
    """
    Crea features desde serie FRED.
    
    Args:
        df (pd.DataFrame): DataFrame con [date, value]
        series_id (str): ID de la serie
        metadata (dict): Metadata de la serie
    
    Returns:
        pd.DataFrame: Features generadas
    """
    if df.empty:
        return df
    
    df_feat = df.copy()
    
    # Nombre base
    base_name = series_id.lower()
    
    # Feature principal
    df_feat[base_name] = df_feat['value']
    
    # Cambios
    df_feat[f'{base_name}_change'] = df_feat['value'].diff()
    df_feat[f'{base_name}_pct_change'] = df_feat['value'].pct_change()
    
    # Moving averages (si es daily/monthly)
    if metadata['frequency'] in ['daily', 'monthly']:
        df_feat[f'{base_name}_ma30'] = df_feat['value'].rolling(30).mean()
        df_feat[f'{base_name}_ma90'] = df_feat['value'].rolling(90).mean()
    
    # Lags
    df_feat[f'{base_name}_lag7'] = df_feat['value'].shift(7)
    df_feat[f'{base_name}_lag30'] = df_feat['value'].shift(30)
    
    # Eliminar columna 'value' original
    df_feat = df_feat.drop(columns=['value'])
    
    logger.info(f"✓ Features creadas: {len(df_feat.columns)-1} para {series_id}")
    
    return df_feat


def main():
    """
    Pipeline principal: descarga FRED series + features.
    """
    logger.info("="*80)
    logger.info("FRED ECONOMIC DATA DOWNLOAD")
    logger.info("="*80)
    
    # Get API key
    api_key = get_fred_api_key()
    
    if not api_key:
        logger.error("❌ FRED API key requerida. Saliendo...")
        return
    
    logger.info(f"✓ FRED API key encontrada")
    logger.info(f"✓ Descargando {len(FRED_SERIES)} series desde 2000-01-01\n")
    
    all_features = []
    
    for series_id, metadata in FRED_SERIES.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"[{series_id}] {metadata['name']}")
        logger.info(f"{'='*80}")
        
        # Descargar
        df_raw = download_fred_series(series_id, start_date='2000-01-01')
        
        if df_raw.empty:
            logger.warning(f"⚠️  No data for {series_id}, skipping")
            continue
        
        # Guardar raw
        output_raw = FRED_DIR / f'{series_id.lower()}_raw.csv'
        df_raw.to_csv(output_raw, index=False)
        logger.info(f"  ✓ Raw data: {output_raw.relative_to(BASE_DIR)}")
        
        # Resample a diario si no es daily
        if metadata['frequency'] != 'daily':
            logger.info(f"  Resampling {metadata['frequency']} → daily (forward-fill)...")
            df_daily = resample_to_daily(df_raw, method='ffill')
            logger.info(f"  ✓ Resampled: {len(df_daily):,} daily observations")
        else:
            df_daily = df_raw.copy()
        
        # Feature engineering
        df_features = create_fred_features(df_daily, series_id, metadata)
        
        # Guardar features
        output_features = FRED_DIR / f'{series_id.lower()}_features.csv'
        df_features.to_csv(output_features, index=False)
        logger.info(f"  ✓ Features: {output_features.relative_to(BASE_DIR)}")
        
        all_features.append(df_features)
    
    # Merge todas las series
    if len(all_features) > 0:
        logger.info(f"\n{'='*80}")
        logger.info("MERGING ALL FRED SERIES")
        logger.info(f"{'='*80}")
        
        df_merged = all_features[0]
        for df in all_features[1:]:
            df_merged = df_merged.merge(df, on='date', how='outer')
        
        df_merged = df_merged.sort_values('date').reset_index(drop=True)
        
        # Guardar merged
        output_merged = FRED_DIR / 'fred_all_features.csv'
        df_merged.to_csv(output_merged, index=False)
        
        logger.info(f"✓ FRED features merged: {output_merged.relative_to(BASE_DIR)}")
        logger.info(f"  Observaciones: {len(df_merged):,}")
        logger.info(f"  Período: {df_merged['date'].min().date()} → {df_merged['date'].max().date()}")
        logger.info(f"  Total features: {len(df_merged.columns)-1}")
        
        # Missing values summary
        missing = df_merged.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        
        if len(missing) > 0:
            logger.info(f"\n  Missing values:")
            for col, count in missing.items():
                pct = count / len(df_merged) * 100
                logger.info(f"    {col}: {count:,} ({pct:.1f}%)")
    
    logger.info(f"\n{'='*80}")
    logger.info("✓ FRED DOWNLOAD COMPLETADO")
    logger.info(f"{'='*80}")
    logger.info(f"Archivos guardados en: {FRED_DIR}")


if __name__ == '__main__':
    main()
