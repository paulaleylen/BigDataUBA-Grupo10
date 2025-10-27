"""
Módulo para descarga de datos de commodities

Descarga datos históricos de commodities desde:
- Kaggle (2000-2021)
- Yahoo Finance (2021-presente)

Y los empalma para crear series continuas.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
import warnings

from src.config import (
    RAW_KAGGLE_DIR, RAW_YAHOO_DIR, INTERIM_COMMODITIES_DIR,
    COMMODITIES_TICKERS, START_DATE, logger
)

warnings.filterwarnings('ignore')


def download_from_kaggle():
    """
    Descarga datos de Kaggle usando Kaggle API
    
    Requiere: ~/.kaggle/kaggle.json configurado
    """
    logger.info("Descargando datos de Kaggle...")
    
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        # Descargar dataset
        dataset = 'mattiuzc/commodity-futures-price-history'
        api.dataset_download_files(dataset, path=RAW_KAGGLE_DIR, unzip=True)
        
        logger.info(f"✓ Datos de Kaggle descargados en {RAW_KAGGLE_DIR}")
        return True
        
    except Exception as e:
        logger.error(f"Error descargando de Kaggle: {e}")
        logger.info("Continuando sin datos de Kaggle...")
        return False


def download_from_yahoo(ticker, name, start_date=START_DATE):
    """
    Descarga datos de un commodity desde Yahoo Finance
    
    Args:
        ticker (str): Ticker de Yahoo Finance (ej: 'ZC=F')
        name (str): Nombre del commodity (ej: 'Corn')
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
        
        df['commodity'] = name
        df['ticker'] = ticker
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"  ✓ {len(df):,} observaciones descargadas")
        return df
        
    except Exception as e:
        logger.error(f"  ✗ Error descargando {name}: {e}")
        return None


def download_all_yahoo_commodities():
    """
    Descarga todos los commodities configurados desde Yahoo Finance
    
    Returns:
        dict: {commodity_name: DataFrame}
    """
    logger.info("=" * 60)
    logger.info("DESCARGA DESDE YAHOO FINANCE")
    logger.info("=" * 60)
    
    yahoo_data = {}
    
    for name, ticker in COMMODITIES_TICKERS.items():
        df = download_from_yahoo(ticker, name)
        
        if df is not None:
            # Guardar en raw/yahoo
            output_path = RAW_YAHOO_DIR / f'{name.lower()}_yahoo.csv'
            df.to_csv(output_path, index=False)
            
            yahoo_data[name] = df
    
    logger.info(f"\n✓ {len(yahoo_data)}/{len(COMMODITIES_TICKERS)} commodities descargados")
    return yahoo_data


def load_kaggle_data():
    """
    Carga datos históricos de Kaggle ya descargados
    
    Returns:
        dict: {commodity_name: DataFrame}
    """
    logger.info("Cargando datos de Kaggle...")
    
    kaggle_data = {}
    
    # Mapeo de archivos Kaggle a nombres de commodities
    file_mapping = {
        'corn.csv': 'Corn',
        'soybean.csv': 'Soybeans',
        'wheat.csv': 'Wheat',
        'crude oil.csv': 'Crude_Oil',
        'brent crude oil.csv': 'Brent_Crude',
        'natural gas.csv': 'Natural_Gas',
        'gold.csv': 'Gold',
        'silver.csv': 'Silver',
        'coffee.csv': 'Coffee',
        'sugar.csv': 'Sugar',
        'cotton.csv': 'Cotton',
        'cocoa.csv': 'Cocoa',
    }
    
    for filename, commodity_name in file_mapping.items():
        filepath = RAW_KAGGLE_DIR / filename
        
        if filepath.exists():
            try:
                df = pd.read_csv(filepath)
                df.columns = df.columns.str.lower()
                
                if 'date' not in df.columns:
                    df = df.rename(columns={'index': 'date'})
                
                df['date'] = pd.to_datetime(df['date'])
                df['commodity'] = commodity_name
                df = df.sort_values('date').reset_index(drop=True)
                
                kaggle_data[commodity_name] = df
                logger.info(f"  ✓ {commodity_name}: {len(df):,} días")
                
            except Exception as e:
                logger.error(f"  ✗ Error cargando {filename}: {e}")
    
    return kaggle_data


def splice_data(kaggle_df, yahoo_df, commodity_name):
    """
    Empalma datos de Kaggle + Yahoo Finance eliminando duplicados
    
    Args:
        kaggle_df (pd.DataFrame): Datos históricos de Kaggle
        yahoo_df (pd.DataFrame): Datos recientes de Yahoo
        commodity_name (str): Nombre del commodity
        
    Returns:
        pd.DataFrame: Datos empalmados
    """
    if kaggle_df is not None and yahoo_df is not None:
        # Empalmar
        df_combined = pd.concat([kaggle_df, yahoo_df], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset='date', keep='last').reset_index(drop=True)
        
        logger.info(f"  {commodity_name}: {len(kaggle_df):,} (Kaggle) + {len(yahoo_df):,} (Yahoo) = {len(df_combined):,} empalmados")
        return df_combined
        
    elif yahoo_df is not None:
        logger.info(f"  {commodity_name}: Solo Yahoo ({len(yahoo_df):,} días)")
        return yahoo_df
        
    elif kaggle_df is not None:
        logger.info(f"  {commodity_name}: Solo Kaggle ({len(kaggle_df):,} días)")
        return kaggle_df
    
    return None


def clean_commodity_data(df):
    """
    Limpia datos de commodities
    
    - Elimina valores negativos en precios
    - Imputa valores faltantes (forward-fill + backward-fill)
    - Elimina duplicados
    
    Args:
        df (pd.DataFrame): Datos crudos
        
    Returns:
        pd.DataFrame: Datos limpios
    """
    df = df.copy()
    
    # Limpiar precios negativos
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].clip(lower=0).ffill().bfill()
    
    # Volumen: llenar con 0
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0)
    
    # Eliminar duplicados
    df = df.drop_duplicates(subset='date', keep='first').reset_index(drop=True)
    
    return df


def main():
    """
    Pipeline principal de descarga de commodities
    """
    logger.info("=" * 80)
    logger.info("INICIO - DESCARGA DE COMMODITIES")
    logger.info("=" * 80)
    
    # Paso 1: Descargar de Kaggle (opcional)
    download_from_kaggle()
    
    # Paso 2: Descargar de Yahoo Finance
    yahoo_data = download_all_yahoo_commodities()
    
    # Paso 3: Cargar datos de Kaggle si existen
    kaggle_data = load_kaggle_data()
    
    # Paso 4: Empalmar datos
    logger.info("\n" + "=" * 60)
    logger.info("EMPALMANDO DATOS")
    logger.info("=" * 60)
    
    commodities_combined = {}
    all_commodity_names = set(list(kaggle_data.keys()) + list(yahoo_data.keys()))
    
    for commodity_name in all_commodity_names:
        kaggle_df = kaggle_data.get(commodity_name)
        yahoo_df = yahoo_data.get(commodity_name)
        
        df_spliced = splice_data(kaggle_df, yahoo_df, commodity_name)
        
        if df_spliced is not None:
            # Limpiar
            df_clean = clean_commodity_data(df_spliced)
            
            # Guardar en interim
            output_path = INTERIM_COMMODITIES_DIR / f'{commodity_name.lower()}.csv'
            df_clean.to_csv(output_path, index=False)
            
            commodities_combined[commodity_name] = df_clean
    
    logger.info(f"\n✓ {len(commodities_combined)} commodities procesados")
    logger.info(f"Archivos guardados en: {INTERIM_COMMODITIES_DIR}")
    
    logger.info("\n" + "=" * 80)
    logger.info("FIN - DESCARGA DE COMMODITIES")
    logger.info("=" * 80)
    
    return commodities_combined


if __name__ == '__main__':
    main()
