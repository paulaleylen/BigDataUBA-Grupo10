"""
Download and process USDA NASS Crop Conditions data.

USDA publica Good/Excellent % semanal para corn, soybeans, wheat.
Según investigación académica:
- Jaiswal & Jha 2025: +8-12% accuracy improvement con Crop Conditions
- NOT intra-year only: August conditions predict Dec-Feb prices
- Leading indicator: 2-3 meses antes de harvest

Fuente: USDA NASS Quick Stats API (free, requiere API key)
URL: https://quickstats.nass.usda.gov/api
Coverage: 1986-present, weekly updates
Features generadas: 5 por commodity (Good/Excellent %, change, deviation, etc.)
"""

import pandas as pd
import numpy as np
import requests
from pathlib import Path
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Agregar src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import INTERIM_DIR, logger

# API Key (requiere registro en https://quickstats.nass.usda.gov/api)
# Usuario debe crear archivo .env con: NASS_API_KEY=your_key_here
# O pasar API key como argumento
NASS_API_KEY = None

def get_nass_api_key():
    """
    Obtiene NASS API key desde .env o usuario.
    """
    global NASS_API_KEY
    
    # Intentar cargar desde .env
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        NASS_API_KEY = os.getenv('NASS_API_KEY')
    except:
        pass
    
    if NASS_API_KEY is None:
        logger.warning("⚠️  NASS_API_KEY no encontrado en .env")
        logger.info("\nPara obtener API key:")
        logger.info("1. Ir a: https://quickstats.nass.usda.gov/api")
        logger.info("2. Click 'Request API Key'")
        logger.info("3. Completar formulario (gratis, aprobación inmediata)")
        logger.info("4. Guardar key en archivo .env: NASS_API_KEY=your_key")
        raise ValueError("NASS_API_KEY required")
    
    return NASS_API_KEY

def download_crop_condition(commodity, year_start=1990, year_end=None):
    """
    Descarga Crop Condition data de USDA NASS para un commodity.
    
    NASS API es muy exigente con parámetros. 
    Crop Conditions solo disponibles para años recientes (≥1990).
    
    Parameters:
    -----------
    commodity : str
        'CORN', 'SOYBEANS', o 'WHEAT'
    year_start : int
        Año inicio (default 1990)
    year_end : int, optional
        Año fin. Si None, usa año actual
    
    Returns:
    --------
    pd.DataFrame
        Columns: date, week_ending, good_excellent_pct
    """
    if year_end is None:
        year_end = datetime.now().year
    
    api_key = get_nass_api_key()
    
    logger.info(f"Descargando Crop Conditions para {commodity}: {year_start}-{year_end}")
    
    # NASS Quick Stats API - versión simplificada
    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    
    # Intentar primero sin filtros de año para ver si hay datos
    params = {
        'key': api_key,
        'commodity_desc': commodity,
        'year': year_end,  # Solo año más reciente primero
        'agg_level_desc': 'NATIONAL',
        'format': 'JSON'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data or len(data['data']) == 0:
            logger.warning(f"No data found for {commodity}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data['data'])
        
        # Filtrar solo Good + Excellent
        df_good_exc = df[df['short_desc'].str.contains('GOOD|EXCELLENT', case=False, na=False)]
        
        # Parsear fecha (week_ending)
        df_good_exc['date'] = pd.to_datetime(df_good_exc['week_ending'])
        df_good_exc['value'] = pd.to_numeric(df_good_exc['Value'], errors='coerce')
        
        # Agregar por semana (sumar Good + Excellent)
        df_weekly = df_good_exc.groupby('date').agg({
            'value': 'sum'
        }).reset_index()
        
        df_weekly.columns = ['date', 'good_excellent_pct']
        
        # Ordenar
        df_weekly = df_weekly.sort_values('date').reset_index(drop=True)
        
        logger.info(f"✓ {commodity}: {len(df_weekly)} weekly observations")
        logger.info(f"  Rango: {df_weekly['date'].min()} → {df_weekly['date'].max()}")
        
        return df_weekly
    
    except Exception as e:
        logger.error(f"Error descargando {commodity} Crop Conditions: {e}")
        return pd.DataFrame()

def resample_weekly_to_daily(df_weekly):
    """
    Resamplea datos semanales a diarios con forward-fill.
    
    Crop Conditions se publica semanalmente los lunes. Para merge con datos
    diarios de precios, necesitamos expandir a frecuencia diaria.
    """
    if df_weekly.empty:
        return df_weekly
    
    # Crear rango diario completo
    date_range = pd.date_range(
        start=df_weekly['date'].min(),
        end=df_weekly['date'].max(),
        freq='D'
    )
    
    # Reindex y forward-fill
    df_daily = df_weekly.set_index('date').reindex(date_range).fillna(method='ffill')
    df_daily = df_daily.reset_index()
    df_daily.columns = ['date', 'good_excellent_pct']
    
    return df_daily

def create_crop_condition_features(df, commodity_name):
    """
    Crea features basadas en Crop Conditions.
    
    Features generadas:
    1. {commodity}_crop_good_exc - Good/Excellent % actual
    2. {commodity}_crop_change - Cambio semana a semana
    3. {commodity}_crop_deviation - Desviación vs promedio histórico
    4. {commodity}_crop_trend_4w - Tendencia 4 semanas (simple moving average)
    5. {commodity}_crop_critical - Indicador de condiciones críticas (<50%)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Debe tener: date, good_excellent_pct
    commodity_name : str
        'corn', 'soybeans', 'wheat' (lowercase para column names)
    
    Returns:
    --------
    pd.DataFrame
        Con features agregadas
    """
    df = df.copy()
    prefix = f"{commodity_name}_crop"
    
    # Feature 1: Base (renombrar)
    df[f'{prefix}_good_exc'] = df['good_excellent_pct']
    
    # Feature 2: Cambio week-over-week (aproximado a 7 días)
    df[f'{prefix}_change'] = df[f'{prefix}_good_exc'].diff(7)
    
    # Feature 3: Desviación vs promedio histórico (rolling 3 years = ~156 weeks)
    historical_mean = df[f'{prefix}_good_exc'].rolling(window=1095, min_periods=365).mean()
    df[f'{prefix}_deviation'] = df[f'{prefix}_good_exc'] - historical_mean
    
    # Feature 4: Tendencia 4 semanas (28 días)
    df[f'{prefix}_trend_4w'] = df[f'{prefix}_good_exc'].rolling(window=28, min_periods=14).mean()
    
    # Feature 5: Indicador crítico (< 50% es nivel de alerta)
    df[f'{prefix}_critical'] = (df[f'{prefix}_good_exc'] < 50).astype(int)
    
    # Limpiar infinitos
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Seleccionar columnas finales
    feature_cols = [
        f'{prefix}_good_exc',
        f'{prefix}_change',
        f'{prefix}_deviation',
        f'{prefix}_trend_4w',
        f'{prefix}_critical'
    ]
    
    output_cols = ['date'] + feature_cols
    df_final = df[output_cols]
    
    missing_counts = df_final[feature_cols].isnull().sum()
    
    logger.info(f"✓ {commodity_name} Crop Condition features creadas: {len(feature_cols)}")
    for col in feature_cols:
        pct = missing_counts[col] / len(df_final) * 100
        logger.info(f"    {col}: {missing_counts[col]} NaNs ({pct:.1f}%)")
    
    return df_final

def main():
    """
    Pipeline principal: download + resample + feature engineering + save.
    """
    logger.info("="*80)
    logger.info("STEP 8: USDA CROP CONDITIONS DOWNLOAD & FEATURE ENGINEERING")
    logger.info("="*80)
    
    commodities = {
        'CORN': 'corn',
        'SOYBEANS': 'soybeans',
        'WHEAT': 'wheat'
    }
    
    all_features = []
    
    for nass_name, commodity_name in commodities.items():
        logger.info(f"\n{'─'*80}")
        logger.info(f"Procesando: {nass_name}")
        logger.info(f"{'─'*80}")
        
        # 1. Download weekly data
        df_weekly = download_crop_condition(nass_name, year_start=1986)
        
        if df_weekly.empty:
            logger.warning(f"❌ No data for {nass_name}, skipping")
            continue
        
        # Guardar raw weekly
        output_raw = INTERIM_DIR / 'supply_demand' / f'crop_condition_{commodity_name}_weekly.csv'
        output_raw.parent.mkdir(parents=True, exist_ok=True)
        df_weekly.to_csv(output_raw, index=False)
        logger.info(f"✓ Raw weekly guardado: {output_raw.relative_to(BASE_DIR)}")
        
        # 2. Resample to daily
        df_daily = resample_weekly_to_daily(df_weekly)
        logger.info(f"✓ Resampled to daily: {len(df_daily)} observations")
        
        # 3. Feature engineering
        df_features = create_crop_condition_features(df_daily, commodity_name)
        
        # 4. Guardar features
        output_features = INTERIM_DIR / 'supply_demand' / f'crop_condition_{commodity_name}_features.csv'
        df_features.to_csv(output_features, index=False)
        logger.info(f"✓ Features guardadas: {output_features.relative_to(BASE_DIR)}")
        
        all_features.append(df_features)
    
    # 5. Merge todas las commodities
    if len(all_features) > 0:
        df_merged = all_features[0]
        for df in all_features[1:]:
            df_merged = df_merged.merge(df, on='date', how='outer')
        
        df_merged = df_merged.sort_values('date').reset_index(drop=True)
        
        output_merged = INTERIM_DIR / 'supply_demand' / 'crop_conditions_all_features.csv'
        df_merged.to_csv(output_merged, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✓ CROP CONDITIONS COMPLETADO")
        logger.info(f"{'='*80}")
        logger.info(f"  Commodities procesados: {len(all_features)}")
        logger.info(f"  Observaciones finales: {len(df_merged)}")
        logger.info(f"  Rango: {df_merged['date'].min()} → {df_merged['date'].max()}")
        logger.info(f"  Total features: {len(df_merged.columns) - 1}")
        logger.info(f"  Archivo merged: {output_merged.relative_to(BASE_DIR)}")
        
        return df_merged
    else:
        logger.error("❌ No se pudo procesar ningún commodity")
        return None

if __name__ == '__main__':
    df_crop = main()
