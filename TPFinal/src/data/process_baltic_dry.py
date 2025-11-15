"""
Procesa los 2 archivos CSV de Baltic Dry Index descargados manualmente de Investing.com
Empalma las series temporales y genera formato estándar
"""

import pandas as pd
from pathlib import Path
import sys

# Agregar directorio src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import EXTERNAL_DIR, INTERIM_COMMODITIES_DIR, logger

# Directorio con archivos manuales
BDRY_DIR = EXTERNAL_DIR / 'bdry'

def parse_investing_date(date_str):
    """
    Convierte formato MM/DD/YYYY de Investing.com a YYYY-MM-DD
    """
    try:
        return pd.to_datetime(date_str, format='%m/%d/%Y')
    except:
        return pd.to_datetime(date_str)

def clean_price(price_str):
    """
    Limpia formato de precios de Investing.com: "2,104.00" -> 2104.00
    """
    if isinstance(price_str, str):
        return float(price_str.replace(',', ''))
    return float(price_str)

def process_baltic_dry():
    """
    Procesa y empalma los 2 archivos de Baltic Dry Index
    """
    
    logger.info("="*80)
    logger.info("PROCESAMIENTO BALTIC DRY INDEX - ARCHIVOS MANUALES")
    logger.info("="*80)
    
    # Leer ambos archivos
    file1 = BDRY_DIR / 'Baltic Dry Index Historical Data_1.csv'
    file2 = BDRY_DIR / 'Baltic Dry Index Historical Data_2.csv'
    
    logger.info(f"Cargando archivo 1: {file1.name}")
    df1 = pd.read_csv(file1)
    logger.info(f"  {len(df1)} registros (reciente)")
    
    logger.info(f"Cargando archivo 2: {file2.name}")
    df2 = pd.read_csv(file2)
    logger.info(f"  {len(df2)} registros (histórico)")
    
    # Procesar ambos DataFrames
    dfs = []
    for df in [df1, df2]:
        # Convertir fecha
        df['date'] = df['Date'].apply(parse_investing_date)
        
        # Limpiar precios (remover comas)
        df['close'] = df['Price'].apply(clean_price)
        df['open'] = df['Open'].apply(clean_price)
        df['high'] = df['High'].apply(clean_price)
        df['low'] = df['Low'].apply(clean_price)
        
        # Seleccionar columnas relevantes
        df_clean = df[['date', 'open', 'high', 'low', 'close']].copy()
        df_clean['volume'] = 0  # BDI es índice, no tiene volumen
        df_clean['commodity'] = 'Baltic_Dry_Index'
        
        dfs.append(df_clean)
    
    # Concatenar
    df_combined = pd.concat(dfs, ignore_index=True)
    
    # Eliminar duplicados (overlap en enero 2019)
    df_combined = df_combined.drop_duplicates(subset=['date'], keep='first')
    
    # Ordenar por fecha (más antiguo primero)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    logger.info("")
    logger.info("✓ Series empalmadas:")
    logger.info(f"  Total registros: {len(df_combined)}")
    logger.info(f"  Período: {df_combined['date'].min()} a {df_combined['date'].max()}")
    logger.info(f"  Duplicados eliminados: {len(df1) + len(df2) - len(df_combined)}")
    
    # Verificar continuidad
    df_combined['date_diff'] = df_combined['date'].diff().dt.days
    gaps = df_combined[df_combined['date_diff'] > 7]  # Gaps > 1 semana
    
    if len(gaps) > 0:
        logger.warning(f"  {len(gaps)} gaps mayores a 7 días detectados")
    else:
        logger.info("  Sin gaps significativos en la serie")
    
    # Guardar en formato estándar
    output_file = INTERIM_COMMODITIES_DIR / 'baltic_dry_index.csv'
    df_combined[['date', 'open', 'high', 'low', 'close', 'volume', 'commodity']].to_csv(
        output_file, index=False
    )
    
    logger.info(f"\n✓ Archivo guardado: {output_file}")
    logger.info("")
    logger.info("Estadísticas:")
    logger.info(f"  Media: {df_combined['close'].mean():.2f}")
    logger.info(f"  Máximo: {df_combined['close'].max():.2f} ({df_combined.loc[df_combined['close'].idxmax(), 'date'].date()})")
    logger.info(f"  Mínimo: {df_combined['close'].min():.2f} ({df_combined.loc[df_combined['close'].idxmin(), 'date'].date()})")
    logger.info("")
    
    return df_combined

def main():
    """
    Pipeline principal
    """
    
    df = process_baltic_dry()
    
    logger.info("="*80)
    logger.info("✓ PROCESAMIENTO COMPLETADO")
    logger.info("="*80)
    logger.info("")
    logger.info("El Baltic Dry Index está listo para integración en process.py")
    logger.info("Variable agregada: Baltic_Dry_Index (costo de fletes marítimos)")
    logger.info("")
    
    return df

if __name__ == '__main__':
    main()
