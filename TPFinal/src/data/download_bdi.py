"""
Download and process Baltic Dry Index (BDI) data.

BDI es un índice crítico de costos de transporte marítimo bulk.
Según investigación académica:
- OECD 2022: Granos/oleaginosas = 39% del tráfico Capesize, 16% Panamax, 11% Supramax
- PLoS ONE 2024: Relación bidireccional BDI ↔ Commodity Prices
- Leading indicator: 2-4 semanas adelanto

Fuente: Yahoo Finance ticker ^BDI (1985-presente)
Features generadas: 5 (BDI + lags + rolling + returns)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import warnings
import pandas_datareader.data as web
warnings.filterwarnings('ignore')

# Agregar src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import INTERIM_DIR, logger

def download_bdi(start_date='2000-01-01', end_date=None):
    """
    Carga Baltic Dry Index desde archivos CSV manuales.
    
    Archivos esperados en data/external/bdry/:
    - Baltic Dry Index Historical Data_1.csv
    - Baltic Dry Index Historical Data_2.csv
    
    Formato Investing.com:
    - Columnas: "Date","Price","Open","High","Low","Vol.","Change %"
    - Date: MM/DD/YYYY
    - Price: con comas como separadores de miles
    
    Parameters:
    -----------
    start_date : str
        Fecha inicio formato YYYY-MM-DD (para filtrar después)
    end_date : str, optional
        Fecha fin formato YYYY-MM-DD (None = sin filtrar)
    
    Returns:
    --------
    pd.DataFrame
        Columns: date, bdi_close, bdi_volume
    """
    bdry_dir = BASE_DIR / 'data' / 'external' / 'bdry'
    csv_files = sorted(bdry_dir.glob('Baltic Dry Index Historical Data*.csv'))
    
    if not csv_files:
        logger.error(f"No se encontraron archivos BDI en {bdry_dir}")
        logger.error("Archivos esperados: 'Baltic Dry Index Historical Data_1.csv', etc.")
        logger.info("\n" + "="*80)
        logger.info("DESCARGAR MANUALMENTE:")
        logger.info("="*80)
        logger.info("1. Ir a: https://www.investing.com/indices/baltic-dry-historical-data")
        logger.info("2. Configurar: Time Frame = Max, Frequency = Daily")
        logger.info("3. Click 'Download Data' (botón verde)")
        logger.info(f"4. Guardar en: {bdry_dir}")
        logger.info("="*80)
        raise FileNotFoundError(f"No se encontraron archivos BDI en {bdry_dir}")
    
    logger.info(f"Cargando BDI desde archivos CSV: {len(csv_files)} archivos")
    for f in csv_files:
        logger.info(f"  - {f.name}")
    
    # Cargar y combinar todos los CSV
    dfs = []
    for csv_file in csv_files:
        logger.info(f"Procesando: {csv_file.name}")
        df = pd.read_csv(csv_file)
        
        # Limpiar nombres de columnas (quitar comillas)
        df.columns = df.columns.str.strip().str.replace('"', '')
        
        # Convertir fecha (formato MM/DD/YYYY de Investing.com)
        try:
            df['date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        except:
            try:
                # Intentar formato DD/MM/YYYY si falla
                df['date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
            except:
                # Dejar que pandas infiera
                df['date'] = pd.to_datetime(df['Date'])
        
        # Limpiar columna Price (eliminar comas, convertir a float)
        df['bdi_close'] = df['Price'].str.replace(',', '').astype(float)
        
        # Volumen (Investing.com no provee para índices)
        df['bdi_volume'] = 0
        
        df = df[['date', 'bdi_close', 'bdi_volume']]
        dfs.append(df)
        logger.info(f"  → {len(df)} observaciones")
    
    # Combinar todos los DataFrames
    df_combined = pd.concat(dfs, ignore_index=True)
    
    # Eliminar duplicados (por si hay solapamiento)
    df_combined = df_combined.drop_duplicates(subset='date', keep='first')
    
    # Ordenar por fecha
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    # Filtrar por rango de fechas si se especifica
    if start_date:
        df_combined = df_combined[df_combined['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df_combined = df_combined[df_combined['date'] <= pd.to_datetime(end_date)]
    
    logger.info(f"✓ BDI cargado: {len(df_combined)} observaciones únicas")
    logger.info(f"  Rango: {df_combined['date'].min().date()} → {df_combined['date'].max().date()}")
    logger.info(f"  BDI min: {df_combined['bdi_close'].min():.0f}, max: {df_combined['bdi_close'].max():.0f}")
    
    return df_combined

def create_bdi_features(df):
    """
    Crea features basadas en Baltic Dry Index.
    
    Features generadas:
    1. bdi - Valor actual (proxy de shipping costs)
    2. bdi_lag_7 - Lag 7 días (influencia retardada)
    3. bdi_lag_30 - Lag 30 días (tendencia mensual)
    4. bdi_lag_90 - Lag 90 días (tendencia trimestral)
    5. bdi_rolling_30d_mean - Media móvil 30 días
    6. bdi_return - Retorno diario (% cambio)
    7. bdi_volatility_30d - Volatilidad 30 días (std de returns)
    8. bdi_spike - Indicador de spike (BDI > 2 std sobre media 90d)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Debe tener columns: date, bdi_close
    
    Returns:
    --------
    pd.DataFrame
        Mismo df + features BDI
    """
    df = df.copy()
    
    # Feature 1: BDI base (renombrar)
    df['bdi'] = df['bdi_close']
    
    # Feature 2-4: Lags
    df['bdi_lag_7'] = df['bdi'].shift(7)
    df['bdi_lag_30'] = df['bdi'].shift(30)
    df['bdi_lag_90'] = df['bdi'].shift(90)
    
    # Feature 5: Rolling mean
    df['bdi_rolling_30d_mean'] = df['bdi'].rolling(window=30, min_periods=10).mean()
    
    # Feature 6: Returns
    df['bdi_return'] = df['bdi'].pct_change()
    
    # Feature 7: Volatilidad (std de returns 30 días)
    df['bdi_volatility_30d'] = df['bdi_return'].rolling(window=30, min_periods=10).std()
    
    # Feature 8: Spike indicator (BDI > 2 std sobre media 90d)
    rolling_90d_mean = df['bdi'].rolling(window=90, min_periods=30).mean()
    rolling_90d_std = df['bdi'].rolling(window=90, min_periods=30).std()
    df['bdi_spike'] = ((df['bdi'] - rolling_90d_mean) / rolling_90d_std > 2).astype(int)
    
    # Limpiar infinitos
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Contar missing
    feature_cols = ['bdi', 'bdi_lag_7', 'bdi_lag_30', 'bdi_lag_90', 
                   'bdi_rolling_30d_mean', 'bdi_return', 'bdi_volatility_30d', 'bdi_spike']
    
    missing_counts = df[feature_cols].isnull().sum()
    
    logger.info(f"✓ BDI features creadas: {len(feature_cols)} features")
    logger.info(f"  Missing values por feature:")
    for col in feature_cols:
        pct = missing_counts[col] / len(df) * 100
        logger.info(f"    {col}: {missing_counts[col]} ({pct:.1f}%)")
    
    # Seleccionar columnas finales
    output_cols = ['date'] + feature_cols
    df_final = df[output_cols]
    
    return df_final

def main():
    """
    Pipeline principal: download + feature engineering + save.
    """
    logger.info("="*80)
    logger.info("STEP 7: BALTIC DRY INDEX (BDI) DOWNLOAD & FEATURE ENGINEERING")
    logger.info("="*80)
    
    # 1. Download BDI (automático con pandas_datareader)
    df_bdi = download_bdi(start_date='2000-01-01')
    
    # Guardar raw
    output_raw = INTERIM_DIR / 'predictors' / 'bdi_raw.csv'
    output_raw.parent.mkdir(parents=True, exist_ok=True)
    df_bdi.to_csv(output_raw, index=False)
    logger.info(f"✓ BDI raw guardado: {output_raw}")
    
    # 2. Feature engineering
    df_features = create_bdi_features(df_bdi)
    
    # 3. Guardar features
    output_features = INTERIM_DIR / 'predictors' / 'bdi_features.csv'
    df_features.to_csv(output_features, index=False)
    logger.info(f"✓ BDI features guardado: {output_features}")
    
    # 4. Resumen final
    logger.info(f"\n{'='*80}")
    logger.info(f"✓ BALTIC DRY INDEX COMPLETADO")
    logger.info(f"{'='*80}")
    logger.info(f"  Observaciones: {len(df_features)}")
    logger.info(f"  Rango temporal: {df_features['date'].min()} → {df_features['date'].max()}")
    logger.info(f"  Features generadas: 8")
    logger.info(f"  Archivos guardados:")
    logger.info(f"    - {output_raw.relative_to(BASE_DIR)}")
    logger.info(f"    - {output_features.relative_to(BASE_DIR)}")
    
    return df_features

if __name__ == '__main__':
    df_bdi = main()
