"""
Download and process USDA ERS Feed Grains historical stocks data.

ALTERNATIVA A NASS API:
- USDA ERS Feed Grains Yearbook Tables (CSV directo)
- Datos históricos desde 1866 hasta presente
- Incluye ending stocks (CCC + private) por año/trimestre
- NO requiere API key

Fuente: https://www.ers.usda.gov/data-products/feed-grains-database/
CSV: feed-grains-yearbook-historical.csv (actualizado septiembre 2025)

Features generadas: 3 por commodity (stocks level, change, pct_change)
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

# URLs de USDA ERS Yearbooks
# Feed Grains: Corn, Barley, Oats, Sorghum
ERS_FEED_GRAINS_CSV = "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/50048/feed-grains-yearbook-historical.csv"

# Oil Crops: Soybeans
ERS_SOYBEANS_CSV = "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/52218/Soy.csv"

# Wheat Data (XLSX - no hay CSV)
ERS_WHEAT_XLSX = "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/54282/Wheat Data-All Years.xlsx"

def download_ers_file(url, filename):
    """
    Descarga un archivo (CSV o XLSX) de USDA ERS.
    
    Parameters:
    -----------
    url : str
        URL del archivo
    filename : str
        Nombre para guardar localmente
    
    Returns:
    --------
    pd.DataFrame
        Datos crudos del archivo
    """
    logger.info(f"Descargando {filename}...")
    logger.info(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Guardar archivo localmente
        file_path = INTERIM_DIR / 'supply_demand' / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✓ Archivo descargado: {file_path.relative_to(BASE_DIR)}")
        
        # Leer según extensión
        if filename.endswith('.xlsx'):
            # XLSX: leer todas las sheets y combinar
            df = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            # Combinar todas las sheets en un solo DF
            dfs = []
            for sheet_name, sheet_df in df.items():
                sheet_df['sheet_name'] = sheet_name
                dfs.append(sheet_df)
            df = pd.concat(dfs, ignore_index=True)
            logger.info(f"✓ XLSX leído: {len(df)} filas totales, {len(df.columns)} columnas")
        else:
            # CSV
            df = pd.read_csv(file_path, encoding='latin-1', low_memory=False)
            logger.info(f"✓ CSV leído: {len(df)} filas, {len(df.columns)} columnas")
        
        return df
    
    except Exception as e:
        logger.error(f"Error descargando {filename}: {e}")
        return pd.DataFrame()

def extract_ending_stocks_wheat_xlsx(xlsx_path):
    """
    Extrae ending stocks de Wheat desde XLSX multi-sheet.
    
    Table04 tiene columnas:
    - Col 0: Marketing year (1960/61)
    - Col 3: World ending stocks (million bushels)
    - Col 8: U.S. ending stocks (million bushels)
    
    Parameters:
    -----------
    xlsx_path : Path
        Ruta al archivo XLSX
    
    Returns:
    --------
    pd.DataFrame
        Columns: date, stocks_bu
    """
    logger.info("Extrayendo ending stocks para Wheat desde XLSX...")
    
    # Leer todas las sheets
    df_dict = pd.read_excel(xlsx_path, sheet_name=None, header=None)
    
    # Buscar tabla con ending stocks (Table04 tiene U.S. ending stocks)
    target_sheets = ['Table04', 'Table03']
    
    for sheet_name in target_sheets:
        if sheet_name not in df_dict:
            continue
        
        df = df_dict[sheet_name]
        
        # Buscar columna con "ending stock" (case-insensitive)
        for col_idx in range(df.shape[1]):
            col_values = df.iloc[:, col_idx].astype(str)
            if col_values.str.contains('ending stock', case=False, na=False).any():
                # Encontrada columna de ending stocks
                header_row = col_values[col_values.str.contains('ending stock', case=False, na=False)].index[0]
                
                # Log para debug
                logger.info(f"  Found '{df.iloc[header_row, col_idx]}' in {sheet_name} col {col_idx}")
                
                # Extraer años (primera columna)
                years_col = df.iloc[header_row+1:, 0].copy()
                stocks_col = df.iloc[header_row+1:, col_idx].copy()
                
                # Limpiar
                df_stocks = pd.DataFrame({
                    'marketing_year': years_col.values,
                    'stocks_raw': stocks_col.values
                })
                
                # Filtrar filas válidas (años tipo 2020/21)
                df_stocks = df_stocks[df_stocks['marketing_year'].astype(str).str.contains(r'\d{4}/\d{2}', na=False)]
                
                # Extraer año
                df_stocks['year'] = df_stocks['marketing_year'].astype(str).str.extract(r'(\d{4})/\d{2}')[0]
                df_stocks['year'] = pd.to_numeric(df_stocks['year'], errors='coerce')
                
                # Convertir stocks a numérico (eliminar '--' y otros)
                df_stocks['stocks_raw'] = df_stocks['stocks_raw'].astype(str).str.strip()
                df_stocks = df_stocks[df_stocks['stocks_raw'] != '--']
                df_stocks['stocks_mb'] = pd.to_numeric(df_stocks['stocks_raw'], errors='coerce')
                
                # Limpiar NaNs
                df_stocks = df_stocks.dropna(subset=['stocks_mb', 'year'])
                
                if len(df_stocks) == 0:
                    logger.warning(f"  No valid data in {sheet_name} col {col_idx}, trying next...")
                    continue
                
                # Ya está en million bushels, convertir a bushels
                df_stocks['stocks_bu'] = df_stocks['stocks_mb'] * 1_000_000
                
                # Crear fecha (31 mayo = fin marketing year wheat)
                df_stocks['date'] = pd.to_datetime(df_stocks['year'].astype(int).astype(str) + '-05-31')
                
                df_final = df_stocks[['date', 'stocks_bu']].copy()
                df_final = df_final.sort_values('date').reset_index(drop=True)
                
                logger.info(f"✓ Wheat: {len(df_final)} annual observations from {sheet_name}")
                logger.info(f"  Rango: {df_final['date'].min().date()} → {df_final['date'].max().date()}")
                logger.info(f"  Stocks range: {df_final['stocks_bu'].min():,.0f} - {df_final['stocks_bu'].max():,.0f} bushels")
                
                return df_final
    
    logger.warning("No se encontró columna de ending stocks en Wheat XLSX")
    return pd.DataFrame()

def extract_ending_stocks(df, commodity, dataset_type='feed_grains'):
    """
    Extrae ending stocks de un commodity del CSV de ERS.
    
    Formatos diferentes según dataset:
    - feed_grains/wheat: columnas 'commodity', 'attribute', 'year', 'unit', 'amount'
    - oil_crops: columnas 'Attribute', 'Item', 'Year', 'Unit', 'Value'
    
    Parameters:
    -----------
    df : pd.DataFrame
        CSV crudo de ERS
    commodity : str
        'Corn', 'Soybeans', 'Wheat'
    dataset_type : str
        'feed_grains', 'oil_crops', o 'wheat'
    
    Returns:
    --------
    pd.DataFrame
        Columns: date, stocks_bu
    """
    logger.info(f"Extrayendo ending stocks para {commodity} ({dataset_type})...")
    
    # Limpiar BOM y espacios de columnas
    df.columns = df.columns.str.replace('\ufeff', '').str.replace('"', '').str.strip()
    
    # Normalizar nombres de columnas según dataset
    if dataset_type == 'oil_crops':
        # Renombrar para consistencia
        df = df.rename(columns={
            'Attribute_Desc': 'attribute',
            'Commodity': 'commodity',
            'Marketing_Year': 'year',
            'Unit_Desc': 'unit',
            'Amount': 'amount',
            'Timeperiod_Desc': 'frequency'
        })
        # Extraer solo el año (e.g., "1999/00" → 1999)
        if 'year' in df.columns:
            df['year'] = df['year'].astype(str).str.split('/').str[0]
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    # Filtrar por commodity y attribute
    # Soybeans puede estar como "Soybeans" o "Soybean"
    commodity_variants = [commodity, commodity.rstrip('s')]
    
    if 'commodity' in df.columns:
        mask_commodity = df['commodity'].isin(commodity_variants)
    else:
        mask_commodity = pd.Series([True] * len(df), index=df.index)
    
    if 'attribute' in df.columns:
        mask_attribute = df['attribute'].str.contains('Ending stocks', case=False, na=False)
    else:
        mask_attribute = pd.Series([True] * len(df), index=df.index)
    
    df_stocks = df[mask_commodity & mask_attribute].copy()
    
    if df_stocks.empty:
        logger.warning(f"No ending stocks data found for {commodity}")
        return pd.DataFrame()
    
    logger.info(f"  Filas encontradas: {len(df_stocks)}")
    if 'year' in df_stocks.columns:
        logger.info(f"  Rango años: {df_stocks['year'].min()}-{df_stocks['year'].max()}")
    if 'frequency' in df_stocks.columns:
        logger.info(f"  Frecuencias: {df_stocks['frequency'].unique()}")
    if 'unit' in df_stocks.columns:
        logger.info(f"  Unidades: {df_stocks['unit'].unique()}")
    
    # Convertir amount a numérico
    df_stocks['amount'] = pd.to_numeric(df_stocks['amount'], errors='coerce')
    
    # Convertir de million metric tons a bushels
    # Corn: 1 metric ton = 39.368 bushels
    # Soybeans: 1 metric ton = 36.744 bushels
    # Wheat: 1 metric ton = 36.744 bushels
    conversion = {
        'Corn': 39.368,
        'Soybeans': 36.744,
        'Wheat': 36.744
    }
    
    # Si está en metric tons, convertir
    if 'metric ton' in str(df_stocks['unit'].iloc[0]).lower():
        df_stocks['stocks_bu'] = df_stocks['amount'] * conversion[commodity] * 1_000_000  # millones a bushels
        logger.info(f"  ✓ Converted from MMT to bushels (factor: {conversion[commodity]})")
    else:
        # Asumir que ya está en bushels
        df_stocks['stocks_bu'] = df_stocks['amount'] * 1_000_000  # millones a bushels
    
    # Crear fecha: usar 31 de agosto como fin de marketing year
    df_stocks['date'] = pd.to_datetime(df_stocks['year'].astype(str) + '-08-31')
    
    # Seleccionar columnas (frequency puede no existir en oil_crops CSV)
    cols_to_select = ['date', 'stocks_bu']
    if 'frequency' in df_stocks.columns:
        cols_to_select.append('frequency')
    
    df_final = df_stocks[cols_to_select].copy()
    df_final = df_final.sort_values('date').reset_index(drop=True)
    df_final = df_final.dropna(subset=['stocks_bu'])
    
    # Si hay frequency, priorizar anuales sobre trimestrales
    if 'frequency' in df_final.columns:
        df_final = df_final.sort_values(['date', 'frequency'], ascending=[True, True])  # 'Annual' < 'Quarterly'
        df_final = df_final.drop_duplicates(subset=['date'], keep='first')  # Mantener Annual
        df_final = df_final[['date', 'stocks_bu']].copy()
    else:
        # Sin frequency, simplemente deduplicate por fecha
        df_final = df_final.drop_duplicates(subset=['date'], keep='first')
    
    logger.info(f"✓ {commodity}: {len(df_final)} annual observations")
    logger.info(f"  Rango: {df_final['date'].min().date()} → {df_final['date'].max().date()}")
    logger.info(f"  Stocks range: {df_final['stocks_bu'].min():,.0f} - {df_final['stocks_bu'].max():,.0f} bushels")
    
    return df_final

def resample_annual_to_daily(df_annual):
    """
    Resamplea datos anuales a diarios con forward-fill.
    """
    if df_annual.empty:
        return df_annual
    
    # Crear rango diario completo
    date_range = pd.date_range(
        start=df_annual['date'].min(),
        end=df_annual['date'].max(),
        freq='D'
    )
    
    # Reindex y forward-fill
    df_daily = df_annual.set_index('date')[['stocks_bu']].reindex(date_range).fillna(method='ffill')
    df_daily = df_daily.reset_index()
    df_daily.columns = ['date', 'stocks_bu']
    
    return df_daily

def create_stocks_features(df, commodity_name):
    """
    Crea features basadas en ending stocks.
    
    Features generadas:
    1. {commodity}_gov_stocks - Ending stocks level (bushels)
    2. {commodity}_gov_stocks_change - Cambio year-over-year
    3. {commodity}_gov_stocks_pct_change - % cambio year-over-year
    
    Parameters:
    -----------
    df : pd.DataFrame
        Debe tener: date, stocks_bu
    commodity_name : str
        'corn', 'soybeans', 'wheat'
    
    Returns:
    --------
    pd.DataFrame
        Con features agregadas
    """
    df = df.copy()
    prefix = f"{commodity_name}_gov"
    
    # Feature 1: Base level (renombrar)
    df[f'{prefix}_stocks'] = df['stocks_bu']
    
    # Feature 2: Cambio absoluto (365 días = 1 year)
    df[f'{prefix}_stocks_change'] = df[f'{prefix}_stocks'].diff(365)
    
    # Feature 3: % cambio
    df[f'{prefix}_stocks_pct_change'] = df[f'{prefix}_stocks'].pct_change(365)
    
    # Limpiar infinitos
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Seleccionar columnas finales
    feature_cols = [
        f'{prefix}_stocks',
        f'{prefix}_stocks_change',
        f'{prefix}_stocks_pct_change'
    ]
    
    output_cols = ['date'] + feature_cols
    df_final = df[output_cols]
    
    missing_counts = df_final[feature_cols].isnull().sum()
    
    logger.info(f"✓ {commodity_name} Government Stocks features creadas: {len(feature_cols)}")
    for col in feature_cols:
        pct = missing_counts[col] / len(df_final) * 100
        logger.info(f"    {col}: {missing_counts[col]} NaNs ({pct:.1f}%)")
    
    return df_final

def main():
    """
    Pipeline principal: download ERS data + extract stocks + features.
    """
    logger.info("="*80)
    logger.info("STEP 9B: USDA ERS ENDING STOCKS (Historical CSVs)")
    logger.info("="*80)
    
    # Definir datasets y commodities
    # Nota: Wheat Data XLSX tiene formato complejo multi-sheet,
    # no es compatible con el parser tabular simple.
    # Solo procesamos Corn y Soybeans.
    datasets = [
        {
            'url': ERS_FEED_GRAINS_CSV,
            'filename': 'ers_feed_grains_raw.csv',
            'type': 'feed_grains',
            'commodities': {'Corn': 'corn'}
        },
        {
            'url': ERS_SOYBEANS_CSV,
            'filename': 'ers_soybeans_raw.csv',
            'type': 'oil_crops',
            'commodities': {'Soybeans': 'soybeans'}
        },
        {
            'url': ERS_WHEAT_XLSX,
            'filename': 'ers_wheat_raw.xlsx',
            'type': 'wheat_xlsx',
            'commodities': {'Wheat': 'wheat'}
        }
    ]
    
    all_features = []
    
    # Procesar cada dataset
    for dataset in datasets:
        logger.info(f"\n{'='*80}")
        logger.info(f"DATASET: {dataset['filename']}")
        logger.info(f"{'='*80}")
        
        # Descargar archivo (CSV o XLSX)
        df_raw = download_ers_file(dataset['url'], dataset['filename'])
        
        if df_raw.empty:
            logger.warning(f"⚠️  No se pudo descargar {dataset['filename']}, skipping")
            continue
        
        # Procesar cada commodity en este dataset
        for ers_name, commodity_name in dataset['commodities'].items():
            logger.info(f"\n{'─'*80}")
            logger.info(f"Procesando: {ers_name}")
            logger.info(f"{'─'*80}")
            
            # Extraer ending stocks (usar parser específico para wheat)
            if dataset['type'] == 'wheat_xlsx':
                xlsx_path = INTERIM_DIR / 'supply_demand' / dataset['filename']
                df_annual = extract_ending_stocks_wheat_xlsx(xlsx_path)
            else:
                df_annual = extract_ending_stocks(df_raw, ers_name, dataset['type'])
            
            if df_annual.empty:
                logger.warning(f"❌ No data for {ers_name}, skipping")
                continue
            
            # Guardar datos anuales
            output_annual = INTERIM_DIR / 'supply_demand' / f'gov_stocks_ers_{commodity_name}_annual.csv'
            output_annual.parent.mkdir(parents=True, exist_ok=True)
            df_annual.to_csv(output_annual, index=False)
            logger.info(f"✓ Annual data guardado: {output_annual.relative_to(BASE_DIR)}")
            
            # Resample a diario
            df_daily = resample_annual_to_daily(df_annual)
            logger.info(f"✓ Resampled to daily: {len(df_daily)} observations")
            
            # Feature engineering
            df_features = create_stocks_features(df_daily, commodity_name)
            
            # Guardar features
            output_features = INTERIM_DIR / 'supply_demand' / f'gov_stocks_ers_{commodity_name}_features.csv'
            df_features.to_csv(output_features, index=False)
            logger.info(f"✓ Features guardadas: {output_features.relative_to(BASE_DIR)}")
            
            all_features.append(df_features)
    
    # 3. Merge todas las commodities
    if len(all_features) > 0:
        df_merged = all_features[0]
        for df in all_features[1:]:
            df_merged = df_merged.merge(df, on='date', how='outer')
        
        df_merged = df_merged.sort_values('date').reset_index(drop=True)
        
        output_merged = INTERIM_DIR / 'supply_demand' / 'government_stocks_ers_all_features.csv'
        df_merged.to_csv(output_merged, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✓ GOVERNMENT STOCKS (ERS) COMPLETADO")
        logger.info(f"{'='*80}")
        logger.info(f"  Commodities procesados: {len(all_features)}")
        logger.info(f"  Observaciones finales: {len(df_merged)}")
        logger.info(f"  Rango: {df_merged['date'].min().date()} → {df_merged['date'].max().date()}")
        logger.info(f"  Total features: {len(df_merged.columns) - 1}")
        logger.info(f"  Archivo merged: {output_merged.relative_to(BASE_DIR)}")
        
        return df_merged
    else:
        logger.error("❌ No se pudo procesar ningún commodity")
        return None

if __name__ == '__main__':
    df = main()
