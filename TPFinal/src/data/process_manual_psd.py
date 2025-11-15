"""
Procesador de datos PSD descargados manualmente

Este script procesa los archivos CSV de USDA PSD descargados manualmente
y genera los mismos outputs que download_supply_demand.py.

Input esperado:
  - data/external/psd_manual/psd_soybeans_all.csv
    (descargado desde PSD Online - Downloadable Data Sets)

Output generado:
  - data/interim/supply_demand/psd_soybeans_{country}.csv (uno por país)
  - data/interim/supply_demand/supply_demand_registry.json

Autor: BigDataUBA-GrupoJLP
Fecha: Noviembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import (
    EXTERNAL_DIR, INTERIM_DIR, PSD_COMMODITIES, PSD_COUNTRIES,
    PSD_ATTRIBUTES, PSD_START_YEAR, PSD_END_YEAR, SUPPLY_DEMAND_REGISTRY_FILE
)

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('src.config')

# Directorios
MANUAL_PSD_DIR = EXTERNAL_DIR / 'psd_manual'
INTERIM_SUPPLY_DEMAND_DIR = INTERIM_DIR / 'supply_demand'
INTERIM_SUPPLY_DEMAND_DIR.mkdir(parents=True, exist_ok=True)


def load_supply_demand_registry():
    """Carga el registro de metadata de supply-demand"""
    if SUPPLY_DEMAND_REGISTRY_FILE.exists():
        with open(SUPPLY_DEMAND_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_supply_demand_metadata(metadata):
    """Guarda metadata en el registro de supply-demand"""
    registry = load_supply_demand_registry()
    
    key = f"{metadata['commodity']}_{metadata['country']}"
    registry[key] = metadata
    
    with open(SUPPLY_DEMAND_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def load_manual_psd_csv(commodity_name='Soybeans'):
    """
    Carga el CSV descargado manualmente desde PSD Online
    
    Formato esperado:
    - Country_Name, Country_Code, Market_Year, Commodity_Code, 
      Attribute_ID, Attribute_Description, Unit_ID, Unit_Description, Value
    
    O formato alternativo:
    - Country Name, Market Year, Attribute, Value, Unit
    """
    csv_path = MANUAL_PSD_DIR / f"psd_{commodity_name.lower()}_all.csv"
    
    if not csv_path.exists():
        # Intentar con nombres alternativos
        alternatives = [
            MANUAL_PSD_DIR / f"psd_{commodity_name.lower()}_custom.csv",
            MANUAL_PSD_DIR / f"{commodity_name.lower()}.csv",
            MANUAL_PSD_DIR / "psd_download.csv"
        ]
        for alt_path in alternatives:
            if alt_path.exists():
                csv_path = alt_path
                break
        else:
            raise FileNotFoundError(
                f"No se encontró CSV para {commodity_name} en {MANUAL_PSD_DIR}\n"
                f"Archivos esperados: {[p.name for p in [csv_path] + alternatives]}"
            )
    
    logger.info(f"Cargando CSV: {csv_path.name}")
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    logger.info(f"  Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    logger.info(f"  Columnas: {list(df.columns)}")
    
    return df, csv_path.name


def standardize_psd_dataframe(df):
    """
    Estandariza el DataFrame al formato esperado
    
    Normaliza nombres de columnas independientemente del formato de descarga
    """
    # Normalizar nombres de columnas (espacios → underscores, lowercase)
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
    
    # Mapeo de posibles nombres de columnas
    column_mapping = {
        'country': 'country_name',
        'market_year': 'market_year',
        'attribute': 'attribute_name',
        'attribute_description': 'attribute_name',
        'value': 'value',
        'country_code': 'country_code'
    }
    
    # Renombrar si es necesario
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Verificar columnas esenciales
    required = ['country_name', 'market_year', 'attribute_name', 'value']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Columnas faltantes en CSV: {missing}")
    
    return df


def filter_psd_data(df, commodity_name='Soybeans', countries=None, years_range=None):
    """
    Filtra el DataFrame por países y años
    
    Args:
        df: DataFrame con datos PSD
        commodity_name: Nombre del commodity
        countries: Lista de nombres de países (None = todos)
        years_range: Tupla (start_year, end_year) (None = 2000-2025)
    """
    if years_range is None:
        years_range = (PSD_START_YEAR, PSD_END_YEAR)
    
    # Filtrar por años
    df_filtered = df[
        (df['market_year'] >= years_range[0]) & 
        (df['market_year'] <= years_range[1])
    ].copy()
    
    logger.info(f"  Filtrado por años {years_range[0]}-{years_range[1]}: {len(df_filtered):,} filas")
    
    # Filtrar por países si se especifica
    if countries:
        df_filtered = df_filtered[df_filtered['country_name'].isin(countries)]
        logger.info(f"  Filtrado por países {countries}: {len(df_filtered):,} filas")
    
    return df_filtered


def process_psd_data(df, commodity_name='Soybeans'):
    """
    Procesa datos PSD: pivotea atributos y limpia
    
    Args:
        df: DataFrame con formato: country_name, market_year, attribute_name, value
    
    Returns:
        DataFrame con atributos como columnas
    """
    # Eliminar duplicados (si existen)
    df = df.drop_duplicates(subset=['country_name', 'market_year', 'attribute_name'])
    
    # Pivotar: attribute_name → columnas
    df_pivot = df.pivot_table(
        index=['country_name', 'market_year'],
        columns='attribute_name',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Limpiar nombres de columnas (espacios → underscores)
    df_pivot.columns = [
        col.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
        if isinstance(col, str) else col
        for col in df_pivot.columns
    ]
    
    # Renombrar columnas comunes
    rename_map = {
        'country_name': 'country',
        'area_harvested': 'Area_Harvested',
        'yield': 'Yield',
        'production': 'Production',
        'beginning_stocks': 'Beginning_Stocks',
        'imports': 'Imports',
        'crush': 'Crush',
        'domestic_consumption': 'Domestic_Consumption',
        'exports': 'Exports',
        'ending_stocks': 'Ending_Stocks',
        'total_supply': 'Total_Supply',
        'total_distribution': 'Total_Distribution'
    }
    
    for old_col in df_pivot.columns:
        old_col_lower = old_col.lower() if isinstance(old_col, str) else str(old_col)
        for pattern, new_col in rename_map.items():
            if pattern in old_col_lower:
                df_pivot = df_pivot.rename(columns={old_col: new_col})
                break
    
    # Agregar columna commodity
    df_pivot['commodity'] = commodity_name
    
    # Convertir market_year a int
    df_pivot['market_year'] = df_pivot['market_year'].astype(int)
    
    # Ordenar
    df_pivot = df_pivot.sort_values(['country', 'market_year']).reset_index(drop=True)
    
    return df_pivot


def calculate_derived_metrics(df):
    """
    Calcula métricas derivadas de supply-demand
    
    Métricas:
    - Stock-to-Use Ratio: (Ending_Stocks / Total_Distribution) × 100
    - Production Growth YoY: % cambio en Production
    - Export Share: (Exports / Production) × 100
    - Import Dependency: (Imports / Domestic_Consumption) × 100
    """
    df = df.copy()
    
    # Stock-to-Use Ratio
    if 'Ending_Stocks' in df.columns and 'Total_Distribution' in df.columns:
        df['Stock_to_Use_Ratio'] = (
            df['Ending_Stocks'] / df['Total_Distribution'] * 100
        ).round(2)
    
    # Production Growth YoY
    if 'Production' in df.columns:
        df['Production_Growth_YoY'] = (
            df.groupby('country')['Production'].pct_change() * 100
        ).round(2)
    
    # Export Share
    if 'Exports' in df.columns and 'Production' in df.columns:
        df['Export_Share'] = (
            df['Exports'] / df['Production'] * 100
        ).round(2)
    
    # Import Dependency
    if 'Imports' in df.columns and 'Domestic_Consumption' in df.columns:
        df['Import_Dependency'] = (
            df['Imports'] / df['Domestic_Consumption'] * 100
        ).round(2)
    
    return df


def expand_to_daily(df_annual, commodity_name='Soybeans'):
    """
    Expande datos anuales (marketing year) a observaciones diarias
    usando forward-fill.
    
    Marketing Year para Soybeans: Septiembre 1 - Agosto 31
    Ej: MY 2020 = Sep 1, 2020 - Aug 31, 2021
    
    Args:
        df_annual: DataFrame con columna 'market_year'
    
    Returns:
        DataFrame con observaciones diarias
    """
    # Crear rango de fechas completo
    start_date = datetime(PSD_START_YEAR, 9, 1)  # Sep 1, 2000
    end_date = datetime.today()
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    df_daily = pd.DataFrame({'date': date_range})
    
    # Calcular marketing year para cada fecha
    # MY = año si mes >= 9, sino año - 1
    df_daily['marketing_year'] = df_daily['date'].apply(
        lambda x: x.year if x.month >= 9 else x.year - 1
    )
    
    # Verificar nombre de columna (puede ser 'marketing_year' o 'market_year')
    year_col = 'market_year' if 'market_year' in df_annual.columns else 'marketing_year'
    
    # Merge con datos anuales (forward-fill automático por fecha)
    df_daily = df_daily.merge(
        df_annual,
        left_on='marketing_year',
        right_on=year_col,
        how='left'
    )
    
    # Forward-fill para rellenar NaN
    # (datos de MY se repiten todos los días de ese año)
    numeric_cols = df_daily.select_dtypes(include=[np.number]).columns
    df_daily[numeric_cols] = df_daily[numeric_cols].fillna(method='ffill')
    
    return df_daily


def save_supply_demand_data(df_daily, commodity_name, country_name, source_file):
    """
    Guarda datos procesados en CSV y metadata en registry
    """
    # Guardar CSV
    output_filename = f"psd_{commodity_name.lower()}_{country_name.lower()}.csv"
    output_path = INTERIM_SUPPLY_DEMAND_DIR / output_filename
    
    df_daily.to_csv(output_path, index=False, encoding='utf-8')
    
    # Metadata
    metadata = {
        'commodity': commodity_name,
        'country': country_name,
        'source': 'USDA FAS PSD Online (manual download)',
        'source_file': source_file,
        'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_observations': len(df_daily[df_daily['marketing_year'].notna()].drop_duplicates('marketing_year')),
        'daily_observations': len(df_daily),
        'date_range': {
            'start': df_daily['date'].min().strftime('%Y-%m-%d'),
            'end': df_daily['date'].max().strftime('%Y-%m-%d')
        },
        'marketing_years': {
            'start': int(df_daily['marketing_year'].min()),
            'end': int(df_daily['marketing_year'].max())
        },
        'columns': list(df_daily.columns),
        'file_path': str(output_path),
        'file_size_mb': round(output_path.stat().st_size / (1024 * 1024), 2)
    }
    
    save_supply_demand_metadata(metadata)
    
    logger.info(f"  ✓ Exportado: {output_filename} ({metadata['file_size_mb']} MB)")
    logger.info(f"    - {metadata['original_observations']} marketing years → {metadata['daily_observations']:,} daily obs")
    
    return output_path


def create_world_aggregate(df, commodity_name='Soybeans', source_file='psd_download.csv'):
    """
    Crea agregado mundial sumando todos los países disponibles en el CSV
    
    Args:
        df: DataFrame procesado con datos de todos los países
        commodity_name: Nombre del commodity
        source_file: Nombre del archivo fuente
    
    Returns:
        Path del archivo guardado
    """
    logger.info(f"\n{'='*60}")
    logger.info("CREANDO AGREGADO MUNDIAL (WORLD)")
    logger.info(f"{'='*60}")
    
    # Agrupar por año y sumar atributos numéricos
    numeric_cols = ['Area_Harvested', 'Beginning_Stocks', 'Crush', 
                    'Domestic_Consumption', 'Ending_Stocks', 'Exports',
                    'Imports', 'Production', 'Total_Distribution', 'Total_Supply']
    
    # Verificar qué columnas existen
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    df_world = df.groupby('market_year')[available_cols].sum().reset_index()
    df_world['country'] = 'World'
    df_world['commodity'] = commodity_name
    
    # Recalcular Yield promedio ponderado por área
    if 'Yield' in df.columns and 'Area_Harvested' in df.columns:
        df_temp = df[df['Area_Harvested'] > 0].copy()
        df_temp['weighted_yield'] = df_temp['Yield'] * df_temp['Area_Harvested']
        
        df_yield = df_temp.groupby('market_year').agg({
            'weighted_yield': 'sum',
            'Area_Harvested': 'sum'
        }).reset_index()
        
        df_yield['Yield'] = df_yield['weighted_yield'] / df_yield['Area_Harvested']
        df_world = df_world.merge(df_yield[['market_year', 'Yield']], on='market_year', how='left')
    
    # Recalcular métricas derivadas para World
    df_world = calculate_derived_metrics(df_world)
    
    logger.info(f"\n  Marketing years: {df_world['market_year'].min()}-{df_world['market_year'].max()}")
    logger.info(f"  Observaciones anuales: {len(df_world)}")
    logger.info(f"  Producción total 2025: {df_world[df_world['market_year']==2025]['Production'].values[0]:,.0f} 1000 MT")
    
    # Expandir a diario
    df_daily = expand_to_daily(df_world, commodity_name)
    
    # Guardar
    output_path = save_supply_demand_data(
        df_daily, commodity_name, 'World', source_file
    )
    
    return output_path


def process_all_countries(df, commodity_name='Soybeans', source_file='psd_download.csv'):
    """
    Procesa datos para todos los países en el DataFrame
    """
    countries_in_data = df['country'].unique()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Países encontrados en CSV: {len(countries_in_data)}")
    logger.info(f"{'='*60}")
    for country in sorted(countries_in_data):
        logger.info(f"  • {country}")
    logger.info("")
    
    # Priorizar países configurados en config.py (excepto World)
    priority_countries = [c for c in PSD_COUNTRIES.keys() if c != 'World']
    
    processed_count = 0
    for country in priority_countries:
        if country not in countries_in_data:
            logger.warning(f"⚠️  País '{country}' no encontrado en CSV, saltando...")
            continue
        
        logger.info(f"\n--- {country} ---")
        
        # Filtrar por país
        df_country = df[df['country'] == country].copy()
        
        logger.info(f"  Marketing years: {df_country['market_year'].min()}-{df_country['market_year'].max()}")
        logger.info(f"  Observaciones anuales: {len(df_country)}")
        
        # Expandir a diario
        df_daily = expand_to_daily(df_country, commodity_name)
        
        # Guardar
        output_path = save_supply_demand_data(
            df_daily, commodity_name, country, source_file
        )
        
        processed_count += 1
    
    return processed_count


def main():
    """
    Pipeline principal de procesamiento
    """
    logger.info("="*80)
    logger.info("PROCESAMIENTO DE DATOS PSD MANUALES")
    logger.info("="*80)
    logger.info("")
    
    try:
        # 1. Cargar CSV manual
        commodity_name = 'Soybeans'
        df_raw, source_file = load_manual_psd_csv(commodity_name)
        
        # 2. Estandarizar formato
        logger.info("\nEstandarizando formato...")
        df_std = standardize_psd_dataframe(df_raw)
        
        # 3. Filtrar por años
        logger.info("\nFiltrando datos...")
        df_filtered = filter_psd_data(
            df_std, 
            commodity_name=commodity_name,
            years_range=(PSD_START_YEAR, PSD_END_YEAR)
        )
        
        # 4. Procesar (pivotar atributos)
        logger.info("\nProcesando atributos...")
        df_processed = process_psd_data(df_filtered, commodity_name)
        logger.info(f"  Columnas después de pivot: {list(df_processed.columns)}")
        
        # 5. Calcular métricas derivadas
        logger.info("\nCalculando métricas derivadas...")
        df_metrics = calculate_derived_metrics(df_processed)
        
        # 6. Procesar todos los países
        logger.info("\n" + "="*80)
        logger.info("GENERANDO DATASETS POR PAÍS")
        logger.info("="*80)
        
        processed_count = process_all_countries(
            df_metrics, 
            commodity_name=commodity_name,
            source_file=source_file
        )
        
        # Crear agregado mundial
        logger.info("\n" + "="*80)
        logger.info("GENERANDO AGREGADO MUNDIAL")
        logger.info("="*80)
        
        world_path = create_world_aggregate(
            df_metrics,
            commodity_name=commodity_name,
            source_file=source_file
        )
        
        if world_path:
            processed_count += 1
        
        # Resumen final
        logger.info("\n" + "="*80)
        logger.info("RESUMEN")
        logger.info("="*80)
        logger.info(f"\n✓ {processed_count} datasets procesados exitosamente (incluye World agregado)")
        logger.info(f"\n📁 Archivos guardados en: {INTERIM_SUPPLY_DEMAND_DIR.absolute()}")
        logger.info(f"📋 Metadata guardada en: {SUPPLY_DEMAND_REGISTRY_FILE.absolute()}")
        logger.info("")
        
        # Listar archivos generados
        csv_files = sorted(INTERIM_SUPPLY_DEMAND_DIR.glob("psd_*.csv"))
        if csv_files:
            logger.info("Archivos generados:")
            for csv_file in csv_files:
                size_mb = csv_file.stat().st_size / (1024 * 1024)
                logger.info(f"  • {csv_file.name} ({size_mb:.2f} MB)")
        
        logger.info("\n" + "="*80)
        logger.info("🚀 SIGUIENTE PASO: Integrar en process.py")
        logger.info("="*80)
        logger.info("\nAgregar en src/data/process.py:")
        logger.info("  - load_all_supply_demand_data()")
        logger.info("  - Merge con commodities/macro/climate por fecha")
        logger.info("  - Seleccionar variables clave para el modelo")
        logger.info("")
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.error("\nAsegúrate de haber descargado el CSV primero:")
        logger.error("  python src/data/manual_psd_download_guide.py")
        return 1
    
    except Exception as e:
        logger.error(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
