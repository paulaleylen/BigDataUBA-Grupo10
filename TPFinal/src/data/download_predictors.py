"""
Módulo para descarga de predictores macroeconómicos

Descarga indicadores que pueden predecir movimientos en commodities:
- VIX (volatilidad)
- DXY (dólar)
- S&P 500
- Tasas de interés
- Índices sectoriales
"""

import pandas as pd
import yfinance as yf
import json
from datetime import datetime
from pathlib import Path
import warnings

from src.config import (
    INTERIM_PREDICTORS_DIR, PREDICTORS_REGISTRY_FILE,
    PREDICTORS_TICKERS, START_DATE, FIGURES_DIR, logger
)

warnings.filterwarnings('ignore')


def load_predictors_registry():
    """
    Carga el registro de predictores descargados
    
    Returns:
        dict: Registro con metadata de predictores
    """
    if PREDICTORS_REGISTRY_FILE.exists():
        with open(PREDICTORS_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            'last_updated': None,
            'predictors': {}
        }


def save_predictor_metadata(name, metadata):
    """
    Guarda metadata de un predictor en el registro
    
    Args:
        name (str): Nombre del predictor
        metadata (dict): Metadata del predictor
    """
    registry = load_predictors_registry()
    
    registry['last_updated'] = datetime.now().isoformat()
    registry['predictors'][name] = metadata
    
    with open(PREDICTORS_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  ✓ Metadata guardada: {name}")


def download_predictor(ticker, name, start_date=START_DATE):
    """
    Descarga un predictor desde Yahoo Finance
    
    Args:
        ticker (str): Ticker de Yahoo Finance
        name (str): Nombre del predictor
        start_date (str): Fecha de inicio
        
    Returns:
        pd.DataFrame: Datos descargados
    """
    logger.info(f"Descargando {name} ({ticker})...")
    
    try:
        df = yf.download(ticker, start=start_date, progress=False).reset_index()
        
        # Manejar MultiIndex si existe
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
        
        if 'date' not in df.columns:
            df = df.rename(columns={'index': 'date'})
        
        df['predictor'] = name
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"  ✓ {len(df):,} observaciones | {df['date'].min().date()} → {df['date'].max().date()}")
        
        # Estadísticas
        if 'close' in df.columns:
            logger.info(f"  Media: {df['close'].mean():.2f} | Min: {df['close'].min():.2f} | Max: {df['close'].max():.2f}")
        
        return df
        
    except Exception as e:
        logger.error(f"  ✗ Error descargando {name}: {e}")
        return None


def clean_predictor_data(df, name):
    """
    Limpia datos de un predictor
    
    Args:
        df (pd.DataFrame): Datos crudos
        name (str): Nombre del predictor
        
    Returns:
        pd.DataFrame: Datos limpios
    """
    df = df.copy()
    
    # Eliminar valores negativos si es necesario (VIX no puede ser negativo)
    if name in ['VIX']:
        if 'close' in df.columns:
            df['close'] = df['close'].clip(lower=0)
    
    # Imputar valores faltantes
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    # Eliminar duplicados
    df = df.drop_duplicates(subset='date', keep='first').reset_index(drop=True)
    
    return df


def save_predictor(df, name, ticker):
    """
    Guarda un predictor descargado
    
    Args:
        df (pd.DataFrame): Datos del predictor
        name (str): Nombre del predictor
        ticker (str): Ticker original
    """
    # Guardar CSV
    output_path = INTERIM_PREDICTORS_DIR / f'{name.lower()}.csv'
    df.to_csv(output_path, index=False)
    
    file_size_kb = output_path.stat().st_size / 1024
    logger.info(f"  ✓ Exportado: {output_path.name} ({file_size_kb:.1f} KB)")
    
    # Guardar metadata
    metadata = {
        'ticker': ticker,
        'name': name,
        'source': 'Yahoo Finance',
        'frequency': 'Daily',
        'period': {
            'start': df['date'].min().isoformat(),
            'end': df['date'].max().isoformat()
        },
        'observations': len(df),
        'file': f'{name.lower()}.csv',
        'downloaded_at': datetime.now().isoformat()
    }
    
    # Agregar estadísticas si existe columna close
    if 'close' in df.columns:
        metadata['stats'] = {
            'mean': float(df['close'].mean()),
            'min': float(df['close'].min()),
            'max': float(df['close'].max()),
            'std': float(df['close'].std())
        }
    
    save_predictor_metadata(name, metadata)


def download_all_predictors():
    """
    Descarga todos los predictores configurados
    
    Returns:
        dict: {predictor_name: DataFrame}
    """
    logger.info("=" * 60)
    logger.info("DESCARGA DE PREDICTORES")
    logger.info("=" * 60)
    
    predictors_data = {}
    
    for name, ticker in PREDICTORS_TICKERS.items():
        logger.info(f"\n[{name}]")
        
        # Descargar
        df = download_predictor(ticker, name)
        
        if df is not None:
            # Limpiar
            df_clean = clean_predictor_data(df, name)
            
            # Guardar
            save_predictor(df_clean, name, ticker)
            
            predictors_data[name] = df_clean
        
        logger.info("")
    
    logger.info("=" * 60)
    logger.info(f"✓ {len(predictors_data)}/{len(PREDICTORS_TICKERS)} predictores descargados")
    logger.info("=" * 60)
    
    return predictors_data


def main():
    """
    Pipeline principal de descarga de predictores
    """
    logger.info("=" * 80)
    logger.info("INICIO - DESCARGA DE PREDICTORES")
    logger.info("=" * 80)
    
    # Descargar todos los predictores
    predictors_data = download_all_predictors()
    
    # Mostrar resumen
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN")
    logger.info("=" * 60)
    
    registry = load_predictors_registry()
    
    for name, meta in registry['predictors'].items():
        logger.info(f"\n{name}:")
        logger.info(f"  Ticker: {meta['ticker']}")
        logger.info(f"  Observaciones: {meta['observations']:,}")
        logger.info(f"  Período: {meta['period']['start'][:10]} → {meta['period']['end'][:10]}")
        logger.info(f"  Archivo: {meta['file']}")
    
    logger.info(f"\n📁 Archivos guardados en: {INTERIM_PREDICTORS_DIR}/")
    
    logger.info("\n" + "=" * 80)
    logger.info("FIN - DESCARGA DE PREDICTORES")
    logger.info("=" * 80)
    
    return predictors_data


if __name__ == '__main__':
    main()
