"""
Descarga y procesa CFTC Commitments of Traders (COT) Reports
Fuente: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm

Datos semanales de posiciones de especuladores en futuros de soja
"""

import pandas as pd
import requests
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
import sys

# Agregar directorio src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import EXTERNAL_DIR, logger

# Directorio para datos CFTC
CFTC_DIR = EXTERNAL_DIR / 'cftc'
CFTC_DIR.mkdir(parents=True, exist_ok=True)

# Códigos CFTC para commodities agrícolas
# Fuente: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm
CFTC_COMMODITY_CODES = {
    'Soybeans': '005602',           # CBOT Soybeans
    'Soybean_Oil': '007601',        # CBOT Soybean Oil
    'Soybean_Meal': '026603',       # CBOT Soybean Meal
    'Corn': '002602',               # CBOT Corn
    'Wheat': '001602',              # CBOT Wheat
}

def download_cftc_historical():
    """
    Descarga archivos ZIP históricos de CFTC COT Reports (2000-2025)
    
    Formato: Disaggregated Futures-Only (recomendado para commodities)
    Contiene: Producer/Merchant, Swap Dealers, Managed Money (fondos), Other Reportables
    """
    
    logger.info("="*80)
    logger.info("DESCARGA CFTC COMMITMENTS OF TRADERS (COT) - SERIE HISTÓRICA")
    logger.info("="*80)
    
    # Descargar múltiples años (CFTC publica archivos anuales)
    all_data = []
    
    for year in range(2006, 2026):  # Disaggregated format existe desde 2006
        url = f'https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip'
        logger.info(f"Descargando año {year}...")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            # Extraer ZIP
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                
                if not txt_files:
                    logger.warning(f"  No se encontró archivo TXT en {year}")
                    continue
                
                with z.open(txt_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    df_year = pd.read_csv(StringIO(content), low_memory=False)
                    
                    logger.info(f"  ✓ {year}: {len(df_year)} registros descargados")
                    all_data.append(df_year)
                    
        except Exception as e:
            logger.warning(f"  Error descargando {year}: {e}")
            continue
    
    if not all_data:
        logger.error("No se pudo descargar datos de ningún año")
        return None
    
    # Concatenar todos los años
    df_combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"\n✓ Total: {len(df_combined)} registros históricos (2006-2025)")
    logger.info(f"  Columnas: {len(df_combined.columns)}")
    
    return df_combined

def filter_soybeans_cot(df):
    """
    Filtra y procesa datos de Soybeans COT
    
    Columnas clave:
    - Market_and_Exchange_Names: nombre del contrato
    - CFTC_Contract_Market_Code: código del commodity
    - Report_Date_as_YYYY-MM-DD: fecha del reporte (martes)
    - Prod_Merc_Positions_Long/Short_All: Productores/Comerciales
    - M_Money_Positions_Long/Short_All: Managed Money (especuladores)
    - Swap_Positions_Long/Short_All: Swap Dealers
    - Open_Interest_All: Open Interest total
    """
    
    logger.info("")
    logger.info("Filtrando datos de Soybeans...")
    
    # Filtrar por código de Soybeans
    soybean_code = CFTC_COMMODITY_CODES['Soybeans']
    df_soy = df[df['CFTC_Contract_Market_Code'] == soybean_code].copy()
    
    if df_soy.empty:
        logger.error(f"No se encontraron datos para Soybeans (código {soybean_code})")
        logger.info("Códigos disponibles:")
        logger.info(df['CFTC_Contract_Market_Code'].unique()[:10])
        return None
    
    logger.info(f"  ✓ {len(df_soy)} registros de Soybeans encontrados")
    
    # Seleccionar columnas relevantes
    columns_to_keep = [
        'Report_Date_as_YYYY-MM-DD',
        'Open_Interest_All',
        'Prod_Merc_Positions_Long_All',
        'Prod_Merc_Positions_Short_All',
        'M_Money_Positions_Long_All',      # Managed Money = especuladores
        'M_Money_Positions_Short_All',
        'Swap_Positions_Long_All',
        'Swap_Positions_Short_All',
        'Other_Rept_Positions_Long_All',
        'Other_Rept_Positions_Short_All',
    ]
    
    # Verificar que columnas existen
    missing_cols = [col for col in columns_to_keep if col not in df_soy.columns]
    if missing_cols:
        logger.warning(f"Columnas faltantes: {missing_cols}")
        # Usar columnas disponibles
        columns_to_keep = [col for col in columns_to_keep if col in df_soy.columns]
    
    df_soy = df_soy[columns_to_keep].copy()
    
    # Renombrar columnas dinámicamente según las disponibles
    new_columns = []
    for col in df_soy.columns:
        if 'Report_Date' in col or 'date' in col.lower():
            new_columns.append('date')
        elif 'Open_Interest' in col:
            new_columns.append('cftc_open_interest')
        elif 'Prod_Merc' in col and 'Long' in col:
            new_columns.append('cftc_producer_long')
        elif 'Prod_Merc' in col and 'Short' in col:
            new_columns.append('cftc_producer_short')
        elif 'M_Money' in col and 'Long' in col:
            new_columns.append('cftc_managed_long')
        elif 'M_Money' in col and 'Short' in col:
            new_columns.append('cftc_managed_short')
        elif 'Swap' in col and 'Long' in col:
            new_columns.append('cftc_swap_long')
        elif 'Swap' in col and 'Short' in col:
            new_columns.append('cftc_swap_short')
        elif 'Other_Rept' in col and 'Long' in col:
            new_columns.append('cftc_other_long')
        elif 'Other_Rept' in col and 'Short' in col:
            new_columns.append('cftc_other_short')
        else:
            new_columns.append(col)
    
    df_soy.columns = new_columns
    
    # Convertir fecha
    df_soy['date'] = pd.to_datetime(df_soy['date'])
    
    # Calcular posiciones netas (Long - Short) solo si ambas columnas existen
    if 'cftc_managed_long' in df_soy.columns and 'cftc_managed_short' in df_soy.columns:
        df_soy['cftc_managed_net'] = df_soy['cftc_managed_long'] - df_soy['cftc_managed_short']
    
    if 'cftc_producer_long' in df_soy.columns and 'cftc_producer_short' in df_soy.columns:
        df_soy['cftc_producer_net'] = df_soy['cftc_producer_long'] - df_soy['cftc_producer_short']
    
    if 'cftc_swap_long' in df_soy.columns and 'cftc_swap_short' in df_soy.columns:
        df_soy['cftc_swap_net'] = df_soy['cftc_swap_long'] - df_soy['cftc_swap_short']
    
    # Calcular % de Open Interest (normalización) solo si managed_net existe
    if 'cftc_managed_net' in df_soy.columns and 'cftc_open_interest' in df_soy.columns:
        df_soy['cftc_managed_net_pct'] = (df_soy['cftc_managed_net'] / df_soy['cftc_open_interest']) * 100
    
    # Ordenar por fecha
    df_soy = df_soy.sort_values('date').reset_index(drop=True)
    
    logger.info(f"  Período: {df_soy['date'].min()} a {df_soy['date'].max()}")
    logger.info(f"  {len(df_soy)} semanas de datos")
    
    # Guardar
    output_file = CFTC_DIR / 'cftc_soybeans_weekly.csv'
    df_soy.to_csv(output_file, index=False)
    logger.info(f"  Archivo guardado: {output_file}")
    
    return df_soy

def expand_weekly_to_daily(df_weekly):
    """
    Expande datos semanales a diarios usando forward-fill
    
    CFTC publica los martes con datos del viernes anterior.
    Forward-fill es apropiado porque posiciones cambian gradualmente.
    """
    
    logger.info("")
    logger.info("Expandiendo datos semanales a diarios...")
    
    # Crear rango diario completo
    date_range = pd.date_range(
        start=df_weekly['date'].min(),
        end=df_weekly['date'].max(),
        freq='D'
    )
    
    # Crear DataFrame diario
    df_daily = pd.DataFrame({'date': date_range})
    
    # Merge con forward-fill
    df_daily = df_daily.merge(df_weekly, on='date', how='left')
    df_daily = df_daily.ffill()  # Forward-fill
    
    logger.info(f"  ✓ {len(df_daily)} días generados")
    logger.info(f"  Período: {df_daily['date'].min()} a {df_daily['date'].max()}")
    
    # Guardar
    output_file = CFTC_DIR / 'cftc_soybeans_daily.csv'
    df_daily.to_csv(output_file, index=False)
    logger.info(f"  Archivo guardado: {output_file}")
    
    return df_daily

def main():
    """
    Pipeline completo de descarga y procesamiento CFTC COT
    """
    
    # 1. Descargar archivo histórico
    df_all = download_cftc_historical()
    if df_all is None:
        return None
    
    # 2. Filtrar y procesar Soybeans
    df_weekly = filter_soybeans_cot(df_all)
    if df_weekly is None:
        return None
    
    # 3. Expandir a datos diarios
    df_daily = expand_weekly_to_daily(df_weekly)
    
    logger.info("")
    logger.info("="*80)
    logger.info("✓ DESCARGA COMPLETADA")
    logger.info("="*80)
    logger.info(f"Datos semanales: {CFTC_DIR / 'cftc_soybeans_weekly.csv'}")
    logger.info(f"Datos diarios:   {CFTC_DIR / 'cftc_soybeans_daily.csv'}")
    logger.info("")
    logger.info("Variables clave creadas:")
    logger.info("  - cftc_managed_net: Posición neta de fondos especulativos (contratos)")
    logger.info("  - cftc_managed_net_pct: Posición neta como % de Open Interest")
    logger.info("  - cftc_open_interest: Contratos totales abiertos")
    logger.info("")
    logger.info("INTERPRETACIÓN:")
    logger.info("  - Managed Net > 0: Especuladores están LARGOS (alcistas)")
    logger.info("  - Managed Net < 0: Especuladores están CORTOS (bajistas)")
    logger.info("  - Producer Net típicamente negativo (hedgers naturales)")
    logger.info("")
    
    return df_daily

if __name__ == '__main__':
    main()
