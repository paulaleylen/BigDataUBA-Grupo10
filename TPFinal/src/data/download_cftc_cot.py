"""
Descarga y procesa CFTC Commitments of Traders (COT) Reports
Fuente: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm

ACTUALIZACIÓN: Usa librería cot_reports para descargar datos históricos
Repositorio: https://github.com/NDelventhal/cot_reports

Datos semanales de posiciones de especuladores en futuros de soja
"""

import pandas as pd
import numpy as np
import requests
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
import sys

# Agregar directorio src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import EXTERNAL_DIR, logger

try:
    import cot_reports as cot
    COT_LIBRARY_AVAILABLE = True
except ImportError:
    COT_LIBRARY_AVAILABLE = False
    logger.warning("⚠️  Librería cot_reports no instalada. Instalar con: pip install cot-reports")

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


def download_cftc_legacy_with_library():
    """
    Descarga formato Legacy (1986-2016) usando librería cot_reports
    
    Esta librería gestiona automáticamente:
    - Descarga del archivo histórico bulk (FUT86_16.txt)
    - Parsing de formato Legacy con todas las columnas
    - Compatibilidad con diferentes estructuras de datos
    
    Formato: Legacy Futures-Only
    Contiene: Commercial, Non-Commercial, Non-Reportable
    Periodo disponible: 1986-01-15 a 2016-12-31
    """
    
    logger.info("="*80)
    logger.info("DESCARGA CFTC COT LEGACY FORMAT (1986-2016) - LIBRERÍA cot_reports")
    logger.info("="*80)
    
    if not COT_LIBRARY_AVAILABLE:
        logger.error("❌ Librería cot_reports no disponible")
        logger.error("   Instalar con: pip install cot-reports")
        return None
    
    try:
        logger.info("\nDescargando archivo histórico bulk (Legacy Futures Only)...")
        df_legacy = cot.cot_hist(cot_report_type='legacy_fut')
        
        logger.info(f"✓ Descarga exitosa!")
        logger.info(f"  Registros totales: {len(df_legacy):,}")
        logger.info(f"  Periodo: {df_legacy['As of Date in Form YYYY-MM-DD'].min()} a {df_legacy['As of Date in Form YYYY-MM-DD'].max()}")
        
        # Convertir fecha a datetime
        df_legacy['Report_Date'] = pd.to_datetime(df_legacy['As of Date in Form YYYY-MM-DD'])
        
        # Filtrar solo años 2000-2009 (pre-Disaggregated)
        # Disaggregated format comienza en 2006, pero solo es confiable desde 2010
        df_legacy_filtered = df_legacy[
            (df_legacy['Report_Date'] >= '2000-01-01') & 
            (df_legacy['Report_Date'] <= '2009-12-31')
        ].copy()
        
        logger.info(f"\n✓ Datos filtrados 2000-2009: {len(df_legacy_filtered):,} registros")
        logger.info(f"  Periodo: {df_legacy_filtered['Report_Date'].min()} a {df_legacy_filtered['Report_Date'].max()}")
        logger.info(f"  Columnas disponibles: {len(df_legacy_filtered.columns)}")
        
        return df_legacy_filtered
        
    except Exception as e:
        logger.error(f"❌ Error descargando Legacy format: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_legacy_data(df, commodity_name, commodity_code):
    """
    Procesa datos Legacy format (1986-2016) para un commodity
    
    Args:
        df: DataFrame con datos raw Legacy
        commodity_name: Nombre del commodity (ej: 'Corn')
        commodity_code: Código CFTC (ej: '002602')
    
    Formato Legacy contiene:
    - Commercial Positions (hedgers/productores)
    - Non-Commercial Positions (especuladores/managed money)
    - Non-Reportable Positions (pequeños traders)
    
    Retorna DataFrame con estructura compatible con formato Disaggregated
    """
    
    logger.info(f"\nFiltrando datos de {commodity_name} (código {commodity_code})...")
    
    # Filtrar por código del commodity
    df_filtered = df[df['CFTC Contract Market Code'] == commodity_code].copy()
    
    if len(df_filtered) == 0:
        logger.error(f"❌ No se encontraron datos para código {commodity_code}")
        logger.error(f"   Códigos disponibles: {df['CFTC Contract Market Code'].unique()[:10]}")
        return pd.DataFrame()
    
    logger.info(f"✓ {len(df_filtered):,} registros de {commodity_name} encontrados")
    logger.info(f"  Período: {df_filtered['Report_Date'].min()} a {df_filtered['Report_Date'].max()}")
    
    # Extraer columnas relevantes y mapear a formato común
    # En Legacy: Commercial = Hedgers/Producers, NonCommercial = Speculators/Managed Money
    df_processed = pd.DataFrame({
        'date': df_filtered['Report_Date'],
        
        # Open Interest
        'open_interest': df_filtered['Open Interest (All)'],
        
        # Managed Money (NonCommercial en Legacy)
        'managed_long': df_filtered['Noncommercial Positions-Long (All)'],
        'managed_short': df_filtered['Noncommercial Positions-Short (All)'],
        
        # Producer/Merchant (Commercial en Legacy)  
        'producer_long': df_filtered['Commercial Positions-Long (All)'],
        'producer_short': df_filtered['Commercial Positions-Short (All)'],
        
        # Swap Dealers (no existe en Legacy - agregar NaN para compatibilidad)
        'swap_long': np.nan,
        'swap_short': np.nan,
        
        # Other Reportables (aproximación con Non-Reportable)
        'other_long': df_filtered['Nonreportable Positions-Long (All)'],
        'other_short': df_filtered['Nonreportable Positions-Short (All)'],
    })
    
    # Calcular posiciones netas
    df_processed['managed_net'] = df_processed['managed_long'] - df_processed['managed_short']
    df_processed['producer_net'] = df_processed['producer_long'] - df_processed['producer_short']
    df_processed['swap_net'] = np.nan
    df_processed['other_net'] = df_processed['other_long'] - df_processed['other_short']
    
    # Calcular porcentajes del Open Interest
    df_processed['managed_net_pct'] = (df_processed['managed_net'] / df_processed['open_interest']) * 100
    df_processed['producer_net_pct'] = (df_processed['producer_net'] / df_processed['open_interest']) * 100
    df_processed['swap_net_pct'] = np.nan
    
    # Agregar columna para identificar formato
    df_processed['format'] = 'Legacy'
    
    return df_processed


def download_cftc_historical():
    """
    Descarga datos históricos CFTC Disaggregated format (2006-presente)
    
    Formato más detallado con 4 categorías de traders:
    - Producer/Merchant/Processor/User (hedgers)
    - Swap Dealers
    - Managed Money (especuladores profesionales)
    - Other Reportables
    """
    
    logger.info("\n" + "="*80)
    logger.info("DESCARGA CFTC COMMITMENTS OF TRADERS (COT) - DISAGGREGATED FORMAT")
    logger.info("="*80)
    
    all_data = []
    
    # Descargar años individuales desde 2010 (Disaggregated comenzó en 2006, pero más confiable desde 2010)
    # Usar Disaggregated para 2010-2025
    for year in range(2010, 2026):
        try:
            # URL para Disaggregated Futures-Only
            url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
            logger.info(f"\nDescargando {year}...")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Descomprimir
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                # Buscar archivo .txt
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if txt_files:
                    with z.open(txt_files[0]) as f:
                        # Leer con encoding correcto
                        df_year = pd.read_csv(f, low_memory=False)
                        all_data.append(df_year)
                        logger.info(f"✓ {year}: {len(df_year):,} registros")
                        
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  Error en {year}: {e}")
            continue
    
    if not all_data:
        logger.error("❌ No se pudieron descargar datos Disaggregated")
        return None
        
    df = pd.concat(all_data, ignore_index=True)
    logger.info(f"\n✓ Total: {len(df):,} registros históricos (2006-2025)")
    
    return df


def process_disaggregated_data(df, commodity_name, commodity_code):
    """
    Procesa datos Disaggregated format para un commodity
    
    Args:
        df: DataFrame con datos COT Disaggregated
        commodity_name: Nombre del commodity
        commodity_code: Código CFTC
        
    Returns:
        DataFrame con datos procesados del commodity
    """
    
    logger.info(f"\nFiltrando datos de {commodity_name}...")
    
    # Filtrar por código del commodity
    df_filtered = df[df['CFTC_Contract_Market_Code'] == commodity_code].copy()
    
    logger.info(f"✓ {len(df_filtered):,} registros de {commodity_name} encontrados")
    
    # Convertir fecha
    df_filtered['date'] = pd.to_datetime(df_filtered['Report_Date_as_YYYY-MM-DD'])
    
    logger.info(f"  Período: {df_filtered['date'].min()} a {df_filtered['date'].max()}")
    
    # Extraer columnas relevantes
    # NOTA: Swap_Positions tiene nombre inconsistente en CFTC (doble guion bajo)
    df_processed = df_filtered[[
        'date',
        'Open_Interest_All',
        'Prod_Merc_Positions_Long_All',
        'Prod_Merc_Positions_Short_All',
        'Swap_Positions_Long_All', 
        'Swap__Positions_Short_All',  # Doble guion bajo en CFTC data
        'M_Money_Positions_Long_All',
        'M_Money_Positions_Short_All',
        'Other_Rept_Positions_Long_All',
        'Other_Rept_Positions_Short_All'
    ]].copy()
    
    # Renombrar columnas para consistencia
    df_processed.columns = [
        'date',
        'open_interest',
        'producer_long',
        'producer_short',
        'swap_long',
        'swap_short', 
        'managed_long',
        'managed_short',
        'other_long',
        'other_short'
    ]
    
    # Calcular posiciones netas
    df_processed['managed_net'] = df_processed['managed_long'] - df_processed['managed_short']
    df_processed['producer_net'] = df_processed['producer_long'] - df_processed['producer_short']
    df_processed['swap_net'] = df_processed['swap_long'] - df_processed['swap_short']
    df_processed['other_net'] = df_processed['other_long'] - df_processed['other_short']
    
    # Calcular porcentajes del Open Interest
    df_processed['managed_net_pct'] = (df_processed['managed_net'] / df_processed['open_interest']) * 100
    df_processed['producer_net_pct'] = (df_processed['producer_net'] / df_processed['open_interest']) * 100
    df_processed['swap_net_pct'] = (df_processed['swap_net'] / df_processed['open_interest']) * 100
    
    # Agregar columna para identificar formato
    df_processed['format'] = 'Disaggregated'
    
    return df_processed


def expand_weekly_to_daily(df_weekly):
    """
    Expande datos semanales a frecuencia diaria usando forward-fill
    
    COT se publica semanalmente (martes), pero necesitamos datos diarios
    para merge con precios diarios de commodities
    
    Args:
        df_weekly: DataFrame con datos semanales
        
    Returns:
        DataFrame con datos diarios (forward-filled)
    """
    
    logger.info("\nExpandiendo datos semanales a diarios...")
    
    # Asegurar que date es datetime
    df_weekly['date'] = pd.to_datetime(df_weekly['date'])
    
    # Crear rango de fechas diarias
    date_range = pd.date_range(
        start=df_weekly['date'].min(),
        end=df_weekly['date'].max(),
        freq='D'
    )
    
    # Crear DataFrame con todas las fechas
    df_daily = pd.DataFrame({'date': date_range})
    
    # Merge con datos semanales y forward-fill
    df_daily = df_daily.merge(df_weekly, on='date', how='left')
    
    # Forward-fill para llenar días sin reporte
    numeric_cols = df_daily.select_dtypes(include=[np.number]).columns
    df_daily[numeric_cols] = df_daily[numeric_cols].fillna(method='ffill')
    
    # Forward-fill para columna 'format'
    df_daily['format'] = df_daily['format'].fillna(method='ffill')
    
    logger.info(f"✓ {len(df_daily):,} días generados")
    logger.info(f"  Período: {df_daily['date'].min()} a {df_daily['date'].max()}")
    
    return df_daily


def process_commodity(commodity_name, commodity_code):
    """
    Procesa un commodity individual
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"PROCESANDO {commodity_name.upper()} (Código: {commodity_code})")
    logger.info(f"{'='*80}\n")
    
    # 1. Descargar Legacy format (2000-2009) CON LIBRERÍA
    df_legacy = download_cftc_legacy_with_library()
    
    df_legacy_filtered = None
    if df_legacy is not None:
        df_legacy_filtered = process_legacy_data(df_legacy, commodity_name, commodity_code)
    
    # 2. Descargar Disaggregated format (2010-2025)
    df_disagg = download_cftc_historical()
    
    df_disagg_filtered = None
    if df_disagg is not None:
        df_disagg_filtered = process_disaggregated_data(df_disagg, commodity_name, commodity_code)
    
    # 3. Combinar ambos formatos
    logger.info("\n" + "="*80)
    logger.info("COMBINANDO FORMATOS LEGACY + DISAGGREGATED")
    logger.info("="*80)
    
    dfs_to_combine = []
    
    if df_legacy_filtered is not None and len(df_legacy_filtered) > 0:
        logger.info(f"\n✓ Legacy format: {len(df_legacy_filtered):,} registros (2000-2009)")
        logger.info(f"  Período: {df_legacy_filtered['date'].min()} a {df_legacy_filtered['date'].max()}")
        dfs_to_combine.append(df_legacy_filtered)
    else:
        logger.warning("⚠️  Sin datos Legacy format - continuando solo con Disaggregated")
    
    if df_disagg_filtered is not None and len(df_disagg_filtered) > 0:
        logger.info(f"\n✓ Disaggregated format: {len(df_disagg_filtered):,} registros (2010-2025)")
        logger.info(f"  Período: {df_disagg_filtered['date'].min()} a {df_disagg_filtered['date'].max()}")
        dfs_to_combine.append(df_disagg_filtered)
    else:
        logger.error("❌ Sin datos Disaggregated format")
        return
    
    if not dfs_to_combine:
        logger.error("❌ No hay datos para combinar")
        return
    
    # Combinar DataFrames
    df_combined = pd.concat(dfs_to_combine, ignore_index=True)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    logger.info(f"\n✓ Total combinado: {len(df_combined):,} registros")
    logger.info(f"  Período completo: {df_combined['date'].min()} a {df_combined['date'].max()}")
    logger.info(f"  Formatos incluidos: {df_combined['format'].value_counts().to_dict()}")
    
    # 4. Expandir a diario
    df_daily = expand_weekly_to_daily(df_combined)
    
    # 5. Guardar archivos
    logger.info("\n" + "="*80)
    logger.info("GUARDANDO ARCHIVOS")
    logger.info("="*80)
    
    # Archivo semanal
    output_file_weekly = CFTC_DIR / f'cftc_{commodity_name.lower()}_weekly.csv'
    df_combined.to_csv(output_file_weekly, index=False)
    logger.info(f"\n✓ Archivo semanal guardado: {output_file_weekly}")
    logger.info(f"  {len(df_combined):,} registros semanales")
    
    # Archivo diario
    output_file_daily = CFTC_DIR / f'cftc_{commodity_name.lower()}_daily.csv'
    df_daily.to_csv(output_file_daily, index=False)
    logger.info(f"\n✓ Archivo diario guardado: {output_file_daily}")
    logger.info(f"  {len(df_daily):,} registros diarios")
    
    return df_daily


def main():
    """
    Proceso principal para TODOS los commodities
    """
    logger.info("Iniciando descarga CFTC COT data para Corn, Soybeans y Wheat...")
    
    # Commodities a procesar
    commodities_to_process = {
        'Corn': '002602',
        'Soybeans': '005602',
        'Wheat': '001602'
    }
    
    all_dfs = []
    
    for commodity_name, commodity_code in commodities_to_process.items():
        try:
            df = process_commodity(commodity_name, commodity_code)
            if df is not None:
                df['commodity'] = commodity_name
                all_dfs.append(df)
        except Exception as e:
            logger.error(f"❌ Error procesando {commodity_name}: {e}")
            continue
    
    # Consolidar todos los commodities
    if all_dfs:
        logger.info("\n" + "="*80)
        logger.info("CONSOLIDANDO TODOS LOS COMMODITIES")
        logger.info("="*80)
        
        df_all = pd.concat(all_dfs, ignore_index=True)
        output_file_all = CFTC_DIR / 'cftc_features_2000_2025.csv'
        df_all.to_csv(output_file_all, index=False)
        
        logger.info(f"\n✓ Archivo consolidado guardado: {output_file_all}")
        logger.info(f"  {len(df_all):,} registros totales")
        logger.info(f"  Commodities: {df_all['commodity'].unique().tolist()}")
        logger.info(f"  Período: {df_all['date'].min()} a {df_all['date'].max()}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ PROCESO COMPLETADO EXITOSAMENTE")
    logger.info("="*80)


if __name__ == '__main__':
    main()
