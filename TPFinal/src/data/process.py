"""
Módulo para procesamiento y consolidación de datos

Funciones para:
- Cargar datos de commodities y predictores
- Consolidar en un único dataset
- Feature engineering
- Validación de calidad
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

from src.config import (
    INTERIM_COMMODITIES_DIR, INTERIM_PREDICTORS_DIR, PROCESSED_DIR,
    PREDICTORS_REGISTRY_FILE, logger
)


def load_all_commodities():
    """
    Carga todos los commodities desde data/interim/commodities/
    
    Returns:
        pd.DataFrame: Dataset consolidado de commodities
    """
    logger.info("Cargando commodities desde interim...")
    
    commodity_files = list(INTERIM_COMMODITIES_DIR.glob('*.csv'))
    
    if not commodity_files:
        logger.warning("⚠ No se encontraron archivos de commodities")
        return pd.DataFrame()
    
    dfs = []
    for file in commodity_files:
        df = pd.read_csv(file, parse_dates=['date'])
        dfs.append(df)
        logger.info(f"  ✓ {file.name}: {len(df):,} obs")
    
    df_commodities = pd.concat(dfs, ignore_index=True)
    
    logger.info(f"Total commodities: {len(df_commodities):,} observaciones")
    logger.info(f"Período: {df_commodities['date'].min().date()} → {df_commodities['date'].max().date()}")
    logger.info(f"Commodities: {df_commodities['commodity'].nunique()}")
    
    return df_commodities


def load_all_predictors():
    """
    Carga todos los predictores desde data/interim/predictors/
    
    Returns:
        pd.DataFrame: Dataset consolidado de predictores
    """
    logger.info("\nCargando predictores desde interim...")
    
    predictor_files = list(INTERIM_PREDICTORS_DIR.glob('*.csv'))
    
    if not predictor_files:
        logger.warning("⚠ No se encontraron archivos de predictores")
        return pd.DataFrame()
    
    dfs = []
    for file in predictor_files:
        df = pd.read_csv(file, parse_dates=['date'])
        dfs.append(df)
        logger.info(f"  ✓ {file.name}: {len(df):,} obs")
    
    df_predictors = pd.concat(dfs, ignore_index=True)
    
    logger.info(f"Total predictores: {len(df_predictors):,} observaciones")
    logger.info(f"Período: {df_predictors['date'].min().date()} → {df_predictors['date'].max().date()}")
    logger.info(f"Predictores: {df_predictors['predictor'].nunique()}")
    
    return df_predictors


def create_wide_format(df, id_col, value_col='close'):
    """
    Convierte formato largo a ancho
    
    Args:
        df (pd.DataFrame): Dataset en formato largo
        id_col (str): Nombre de columna identificadora ('commodity' o 'predictor')
        value_col (str): Columna de valores a pivotar
        
    Returns:
        pd.DataFrame: Dataset en formato ancho
    """
    logger.info(f"\nCreando formato ancho para {id_col}...")
    
    # Pivotar
    df_wide = df.pivot_table(
        index='date',
        columns=id_col,
        values=value_col,
        aggfunc='first'
    ).reset_index()
    
    # Renombrar columnas
    df_wide.columns.name = None
    
    logger.info(f"  ✓ Dimensiones: {df_wide.shape}")
    logger.info(f"  Período: {df_wide['date'].min().date()} → {df_wide['date'].max().date()}")
    
    return df_wide


def merge_commodities_predictors(df_commodities, df_predictors):
    """
    Combina commodities y predictores en un dataset unificado
    
    Args:
        df_commodities (pd.DataFrame): Commodities en formato ancho
        df_predictors (pd.DataFrame): Predictores en formato ancho
        
    Returns:
        pd.DataFrame: Dataset consolidado
    """
    logger.info("\nCombinando commodities y predictores...")
    
    df_base = df_commodities.merge(df_predictors, on='date', how='outer')
    df_base = df_base.sort_values('date').reset_index(drop=True)
    
    logger.info(f"  ✓ Dimensiones finales: {df_base.shape}")
    logger.info(f"  Período: {df_base['date'].min().date()} → {df_base['date'].max().date()}")
    
    return df_base


def add_temporal_features(df):
    """
    Agrega features temporales
    
    Args:
        df (pd.DataFrame): Dataset base
        
    Returns:
        pd.DataFrame: Dataset con features temporales
    """
    logger.info("\nAgregando features temporales...")
    
    df = df.copy()
    
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week
    
    logger.info(f"  ✓ 6 features temporales agregadas")
    
    return df


def add_lag_features(df, columns, lags=[1, 7, 30]):
    """
    Agrega features de lags
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas para calcular lags
        lags (list): Períodos de lag a calcular
        
    Returns:
        pd.DataFrame: Dataset con lags
    """
    logger.info(f"\nAgregando lags: {lags}")
    
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            for lag in lags:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    
    logger.info(f"  ✓ {len(columns) * len(lags)} features de lag agregadas")
    
    return df


def add_rolling_features(df, columns, windows=[7, 30, 90]):
    """
    Agrega features de rolling statistics
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas para calcular rolling stats
        windows (list): Ventanas de tiempo
        
    Returns:
        pd.DataFrame: Dataset con rolling features
    """
    logger.info(f"\nAgregando rolling features: ventanas {windows}")
    
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            for window in windows:
                df[f'{col}_ma{window}'] = df[col].rolling(window=window, min_periods=1).mean()
                df[f'{col}_std{window}'] = df[col].rolling(window=window, min_periods=1).std()
    
    features_count = len(columns) * len(windows) * 2
    logger.info(f"  ✓ {features_count} rolling features agregadas")
    
    return df


def add_return_features(df, columns, periods=[1, 7, 30]):
    """
    Calcula retornos porcentuales
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas para calcular retornos
        periods (list): Períodos de retorno
        
    Returns:
        pd.DataFrame: Dataset con retornos
    """
    logger.info(f"\nCalculando retornos: períodos {periods}")
    
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            for period in periods:
                df[f'{col}_return{period}'] = df[col].pct_change(periods=period) * 100
    
    logger.info(f"  ✓ {len(columns) * len(periods)} features de retorno agregadas")
    
    return df


def check_data_quality(df):
    """
    Valida calidad del dataset
    
    Args:
        df (pd.DataFrame): Dataset a validar
        
    Returns:
        dict: Reporte de calidad
    """
    logger.info("\n" + "=" * 60)
    logger.info("VALIDACIÓN DE CALIDAD DE DATOS")
    logger.info("=" * 60)
    
    report = {
        'shape': df.shape,
        'period': {
            'start': df['date'].min().isoformat(),
            'end': df['date'].max().isoformat(),
            'days': (df['date'].max() - df['date'].min()).days
        },
        'missing': {},
        'duplicates': df.duplicated().sum(),
        'columns': list(df.columns)
    }
    
    # Missing values por columna
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    
    logger.info(f"\n📊 Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    logger.info(f"📅 Período: {report['period']['start'][:10]} → {report['period']['end'][:10]} ({report['period']['days']:,} días)")
    logger.info(f"🔍 Duplicados: {report['duplicates']:,}")
    
    logger.info("\n📉 Missing values por columna:")
    for col in df.columns:
        if missing[col] > 0:
            logger.info(f"  {col:30s}: {missing[col]:6,} ({missing_pct[col]:5.2f}%)")
            report['missing'][col] = {
                'count': int(missing[col]),
                'percentage': float(missing_pct[col])
            }
    
    if not report['missing']:
        logger.info("  ✓ No hay valores faltantes")
    
    logger.info("=" * 60)
    
    return report


def save_processed_data(df, filename='commodities_base_daily.csv'):
    """
    Guarda dataset procesado
    
    Args:
        df (pd.DataFrame): Dataset final
        filename (str): Nombre del archivo
    """
    output_path = PROCESSED_DIR / filename
    
    logger.info(f"\nGuardando dataset procesado...")
    df.to_csv(output_path, index=False)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  ✓ Exportado: {output_path.name} ({file_size_mb:.2f} MB)")
    
    return output_path


def save_metadata(df, quality_report, filename='metadata.json'):
    """
    Guarda metadata del dataset procesado
    
    Args:
        df (pd.DataFrame): Dataset final
        quality_report (dict): Reporte de calidad
        filename (str): Nombre del archivo metadata
    """
    output_path = PROCESSED_DIR / filename
    
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'shape': [int(x) for x in quality_report['shape']],
        'period': quality_report['period'],
        'duplicates': int(quality_report['duplicates']),
        'missing_values': quality_report['missing'],
        'columns': quality_report['columns'],
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  ✓ Metadata guardada: {output_path.name}")


def main():
    """
    Pipeline principal de procesamiento
    """
    logger.info("=" * 80)
    logger.info("INICIO - PROCESAMIENTO DE DATOS")
    logger.info("=" * 80)
    
    # 1. Cargar datos
    df_commodities = load_all_commodities()
    df_predictors = load_all_predictors()
    
    if df_commodities.empty or df_predictors.empty:
        logger.error("⚠ No hay datos para procesar. Ejecutar descarga primero.")
        return None
    
    # 2. Convertir a formato ancho
    df_comm_wide = create_wide_format(df_commodities, 'commodity')
    df_pred_wide = create_wide_format(df_predictors, 'predictor')
    
    # 3. Combinar
    df_base = merge_commodities_predictors(df_comm_wide, df_pred_wide)
    
    # 4. Feature engineering
    df_base = add_temporal_features(df_base)
    
    # Identificar columnas de precios (excluir date y features temporales)
    temporal_cols = ['year', 'month', 'quarter', 'day_of_week', 'day_of_year', 'week_of_year']
    price_cols = [col for col in df_base.columns if col not in ['date'] + temporal_cols]
    
    # Agregar lags, rolling y retornos
    df_base = add_lag_features(df_base, price_cols, lags=[1, 7])
    df_base = add_rolling_features(df_base, price_cols, windows=[7, 30])
    df_base = add_return_features(df_base, price_cols, periods=[1, 7])
    
    # 5. Validar calidad
    quality_report = check_data_quality(df_base)
    
    # 6. Guardar
    output_path = save_processed_data(df_base)
    save_metadata(df_base, quality_report)
    
    logger.info("\n" + "=" * 80)
    logger.info("FIN - PROCESAMIENTO DE DATOS")
    logger.info(f"✓ Dataset final: {output_path}")
    logger.info("=" * 80)
    
    return df_base


if __name__ == '__main__':
    main()
