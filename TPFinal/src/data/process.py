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
import sys

# Agregar directorio src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import (
    INTERIM_COMMODITIES_DIR, INTERIM_PREDICTORS_DIR, INTERIM_CLIMATE_DIR, INTERIM_DIR, PROCESSED_DIR,
    PREDICTORS_REGISTRY_FILE, CLIMATE_REGISTRY_FILE, CLIMATE_REGIONS, 
    CLIMATE_THRESHOLDS, logger
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


def load_all_climate_data():
    """
    Carga todos los datos climáticos desde data/interim/climate/
    
    Returns:
        dict: {'oni': DataFrame, 'regions': {region_name: DataFrame}}
    """
    logger.info("\nCargando datos climáticos desde interim...")
    
    climate_files = list(INTERIM_CLIMATE_DIR.glob('*.csv'))
    
    if not climate_files:
        logger.warning("⚠ No se encontraron archivos climáticos")
        return {'oni': None, 'regions': {}}
    
    climate_data = {'oni': None, 'regions': {}}
    
    for file in climate_files:
        df = pd.read_csv(file, parse_dates=['date'])
        logger.info(f"  ✓ {file.name}: {len(df):,} obs")
        
        # Identificar tipo de dato
        filename_lower = file.name.lower()
        if 'oni_daily' in filename_lower:
            climate_data['oni'] = df
        elif 'nasa_power' in filename_lower:
            # Extraer nombre de región del archivo
            region_name = file.stem.replace('nasa_power_', '').replace('NASA_POWER_', '')
            climate_data['regions'][region_name] = df
    
    if climate_data['oni'] is not None:
        logger.info(f"ONI: {len(climate_data['oni']):,} observaciones diarias")
    
    logger.info(f"Regiones NASA POWER: {len(climate_data['regions'])}")
    
    return climate_data


def load_all_supply_demand_data():
    """
    Carga datos de supply-demand (USDA PSD) desde data/interim/supply_demand/
    
    Selecciona variables clave por país para evitar explosión de features:
    - World: todas las variables (referencia global)
    - Brasil, USA, Argentina: productores principales
    - China: mayor importador (demanda)
    
    Returns:
        pd.DataFrame: Dataset consolidado con variables supply-demand por país
    """
    logger.info("\nCargando datos supply-demand desde interim...")
    
    supply_demand_dir = INTERIM_DIR / 'supply_demand'
    
    if not supply_demand_dir.exists():
        logger.warning("⚠ No se encontró directorio supply_demand/")
        return None
    
    # Cargar metadata registry
    registry_file = supply_demand_dir / 'supply_demand_registry.json'
    if not registry_file.exists():
        logger.warning("⚠ No se encontró supply_demand_registry.json")
        return None
    
    with open(registry_file, 'r') as f:
        registry = json.load(f)
    
    # Países prioritarios (ordenados por importancia)
    priority_countries = {
        'world': ['Production', 'Ending_Stocks', 'Exports', 'Imports', 'Stock_to_Use_Ratio'],
        'brazil': ['Production', 'Ending_Stocks', 'Exports', 'Stock_to_Use_Ratio'],
        'united states': ['Production', 'Ending_Stocks', 'Exports', 'Stock_to_Use_Ratio'],
        'argentina': ['Production', 'Exports', 'Stock_to_Use_Ratio'],
        'china': ['Imports', 'Crush', 'Ending_Stocks', 'Stock_to_Use_Ratio']
    }
    
    # DataFrame base con fechas
    df_supply_demand = None
    
    for country_key, variables in priority_countries.items():
        # Buscar archivo en registry
        country_file = None
        for entry in registry.values():
            if entry['country'].lower() == country_key.lower():
                country_file = supply_demand_dir / Path(entry['file_path']).name
                break
        
        if country_file is None or not country_file.exists():
            logger.warning(f"  ⚠ No se encontró archivo para {country_key}")
            continue
        
        # Cargar dataset
        df_country = pd.read_csv(country_file, parse_dates=['date'])
        logger.info(f"  ✓ {country_key.title()}: {len(df_country):,} obs")
        
        # Seleccionar solo variables clave
        cols_to_keep = ['date'] + [v for v in variables if v in df_country.columns]
        df_country = df_country[cols_to_keep].copy()
        
        # Renombrar columnas con prefijo de país
        rename_dict = {col: f'psd_{country_key.replace(" ", "_")}_{col}' 
                      for col in df_country.columns if col != 'date'}
        df_country.rename(columns=rename_dict, inplace=True)
        
        # Merge
        if df_supply_demand is None:
            df_supply_demand = df_country
        else:
            df_supply_demand = df_supply_demand.merge(df_country, on='date', how='outer')
    
    if df_supply_demand is not None:
        logger.info(f"\nSupply-Demand consolidado:")
        logger.info(f"  Observaciones: {len(df_supply_demand):,}")
        logger.info(f"  Período: {df_supply_demand['date'].min().date()} → {df_supply_demand['date'].max().date()}")
        logger.info(f"  Variables: {len(df_supply_demand.columns) - 1}")
        
        # Ordenar por fecha
        df_supply_demand = df_supply_demand.sort_values('date').reset_index(drop=True)
    
    return df_supply_demand


def calculate_et0_fao56(temp_mean, temp_max, temp_min, rh, solar_rad, wind_speed):
    """
    Calcula evapotranspiración de referencia (ET0) usando Penman-Monteith FAO-56 simplificado
    
    Args:
        temp_mean (float): Temperatura media (°C)
        temp_max (float): Temperatura máxima (°C)
        temp_min (float): Temperatura mínima (°C)
        rh (float): Humedad relativa (%)
        solar_rad (float): Radiación solar (MJ/m²/día)
        wind_speed (float): Velocidad del viento a 2m (m/s)
        
    Returns:
        float: ET0 en mm/día
    """
    if pd.isna([temp_mean, temp_max, temp_min, rh, solar_rad, wind_speed]).any():
        return np.nan
    
    # Presión de vapor saturación (kPa)
    es_tmax = 0.6108 * np.exp((17.27 * temp_max) / (temp_max + 237.3))
    es_tmin = 0.6108 * np.exp((17.27 * temp_min) / (temp_min + 237.3))
    es = (es_tmax + es_tmin) / 2
    ea = es * (rh / 100)
    
    # Pendiente curva presión vapor (kPa/°C)
    delta = 4098 * (0.6108 * np.exp((17.27 * temp_mean) / (temp_mean + 237.3))) / ((temp_mean + 237.3) ** 2)
    
    # Constante psicrométrica (kPa/°C)
    gamma = 0.067
    
    # Radiación neta (MJ/m²/día) - simplificada
    stefan_boltzmann = 4.903e-9
    rn = solar_rad * 0.77 - (stefan_boltzmann * (((temp_max + 273.16)**4 + (temp_min + 273.16)**4) / 2) * (0.34 - 0.14 * np.sqrt(ea)))
    
    # ET0 Penman-Monteith (mm/día)
    numerator = 0.408 * delta * rn + gamma * (900 / (temp_mean + 273)) * wind_speed * (es - ea)
    denominator = delta + gamma * (1 + 0.34 * wind_speed)
    et0 = numerator / denominator
    
    return max(0, et0)


def create_global_climate_predictors(climate_data):
    """
    Crea predictores climáticos globales usando weighted average por producción
    
    Args:
        climate_data (dict): Datos climáticos por región
        
    Returns:
        pd.DataFrame: Predictores climáticos globales
    """
    logger.info("\nCreando predictores climáticos globales...")
    
    # Iniciar con ONI
    df_global = climate_data['oni'][['date', 'ONI']].copy()
    
    # Preparar datos regionales
    regions_data = {}
    for region_name, df_region in climate_data['regions'].items():
        regions_data[region_name] = df_region
    
    # Verificar que tenemos las 3 regiones esperadas
    expected_regions = ['brazil', 'usa', 'argentina']
    available_regions = [r.lower() for r in regions_data.keys()]
    
    if not all(r in available_regions for r in expected_regions):
        logger.warning(f"⚠ Faltan regiones. Esperadas: {expected_regions}, Disponibles: {available_regions}")
    
    # Crear DataFrames por región con prefijo
    dfs_to_merge = []
    
    for region_name, df_region in regions_data.items():
        df_temp = df_region[['date']].copy()
        
        # Extraer parámetros climáticos básicos
        if 'T2M' in df_region.columns:
            df_temp[f'Temp_{region_name}'] = df_region['T2M']
        
        if 'PRECTOTCORR' in df_region.columns:
            df_temp[f'Precip_{region_name}'] = df_region['PRECTOTCORR']
        
        if 'T2M_MAX' in df_region.columns:
            df_temp[f'TempMax_{region_name}'] = df_region['T2M_MAX']
        
        if 'T2M_MIN' in df_region.columns:
            df_temp[f'TempMin_{region_name}'] = df_region['T2M_MIN']
        
        # Nuevos parámetros
        if 'RH2M' in df_region.columns:
            df_temp[f'RH_{region_name}'] = df_region['RH2M']
        
        if 'ALLSKY_SFC_SW_DWN' in df_region.columns:
            df_temp[f'SolarRad_{region_name}'] = df_region['ALLSKY_SFC_SW_DWN']
        
        if 'WS2M' in df_region.columns:
            df_temp[f'WindSpeed_{region_name}'] = df_region['WS2M']
        
        # Calcular ET0 para región si tenemos todos los datos
        has_et0_params = all(col in df_region.columns for col in 
                            ['T2M', 'T2M_MAX', 'T2M_MIN', 'RH2M', 'ALLSKY_SFC_SW_DWN', 'WS2M'])
        
        if has_et0_params:
            df_temp[f'ET0_{region_name}'] = df_region.apply(
                lambda row: calculate_et0_fao56(
                    row['T2M'], row['T2M_MAX'], row['T2M_MIN'],
                    row['RH2M'], row['ALLSKY_SFC_SW_DWN'], row['WS2M']
                ), axis=1
            )
        
        dfs_to_merge.append(df_temp)
    
    # Merge todas las regiones
    for df_region in dfs_to_merge:
        df_global = df_global.merge(df_region, on='date', how='outer')
    
    df_global = df_global.sort_values('date').reset_index(drop=True)
    
    # Calcular promedios ponderados por producción
    logger.info("  Calculando weighted averages (producción mundial)...")
    
    # Mapeo de nombres de región (lowercase) a keys de CLIMATE_REGIONS
    region_key_map = {
        'brazil': 'Brazil',
        'usa': 'USA',
        'argentina': 'Argentina'
    }
    
    # Temperatura global
    temp_cols = [col for col in df_global.columns if col.startswith('Temp_') and not 'Max' in col and not 'Min' in col]
    if len(temp_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in temp_cols]
        df_global['Temp_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(temp_cols, weights)
        )
        logger.info(f"    ✓ Temp_Global_Grain (pesos: {dict(zip([c.split('_')[1] for c in temp_cols], weights))})")
    
    # Precipitación global
    precip_cols = [col for col in df_global.columns if col.startswith('Precip_')]
    if len(precip_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in precip_cols]
        df_global['Precip_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(precip_cols, weights)
        )
        logger.info(f"    ✓ Precip_Global_Grain (pesos: {dict(zip([c.split('_')[1] for c in precip_cols], weights))})")
    
    # Humedad relativa global
    rh_cols = [col for col in df_global.columns if col.startswith('RH_')]
    if len(rh_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in rh_cols]
        df_global['RH_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(rh_cols, weights)
        )
        logger.info(f"    ✓ RH_Global_Grain (humedad relativa ponderada)")
    
    # Radiación solar global
    solar_cols = [col for col in df_global.columns if col.startswith('SolarRad_')]
    if len(solar_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in solar_cols]
        df_global['SolarRad_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(solar_cols, weights)
        )
        logger.info(f"    ✓ SolarRad_Global_Grain (radiación solar ponderada)")
    
    # Velocidad del viento global
    wind_cols = [col for col in df_global.columns if col.startswith('WindSpeed_')]
    if len(wind_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in wind_cols]
        df_global['WindSpeed_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(wind_cols, weights)
        )
        logger.info(f"    ✓ WindSpeed_Global_Grain (viento ponderado)")
    
    # ET0 global (evapotranspiración de referencia)
    et0_cols = [col for col in df_global.columns if col.startswith('ET0_')]
    if len(et0_cols) >= 3:
        weights = [CLIMATE_REGIONS[region_key_map[r.split('_')[1].lower()]]['weight'] for r in et0_cols]
        df_global['ET0_Global_Grain'] = sum(
            df_global[col] * w for col, w in zip(et0_cols, weights)
        )
        logger.info(f"    ✓ ET0_Global_Grain (evapotranspiración FAO-56 ponderada)")
    
    # Calcular variables derivadas
    logger.info("  Calculando variables derivadas...")
    
    # Growing Degree Days (GDD) - suma de temperaturas sobre base
    if 'Temp_Global_Grain' in df_global.columns:
        gdd_base = CLIMATE_THRESHOLDS['gdd_base']
        df_global['GDD_Global_Grain'] = df_global['Temp_Global_Grain'].apply(
            lambda x: max(0, x - gdd_base) if pd.notna(x) else np.nan
        )
        logger.info(f"    ✓ GDD_Global_Grain (base {gdd_base}°C)")
    
    # Heat Stress Days (días con temperatura extrema) - rolling 30 días
    if 'Temp_Global_Grain' in df_global.columns:
        heat_threshold = CLIMATE_THRESHOLDS['heat_stress']
        df_global['Heat_Stress_Days'] = (
            df_global['Temp_Global_Grain'] > heat_threshold
        ).rolling(window=30, min_periods=1).sum()
        logger.info(f"    ✓ Heat_Stress_Days (>{heat_threshold}°C, rolling 30d)")
    
    # Precipitation Deficit (déficit vs óptimo) - rolling 30 días
    if 'Precip_Global_Grain' in df_global.columns:
        optimal_precip = CLIMATE_THRESHOLDS['optimal_precip']
        df_global['Precip_Deficit'] = (
            df_global['Precip_Global_Grain'].rolling(window=30, min_periods=1).sum() - optimal_precip
        )
        logger.info(f"    ✓ Precip_Deficit (vs {optimal_precip}mm/30d óptimo)")
    
    logger.info(f"  ✓ Dimensiones: {df_global.shape}")
    logger.info(f"  Período: {df_global['date'].min().date()} → {df_global['date'].max().date()}")
    
    # Seleccionar solo columnas principales para merge
    main_cols = [
        'date', 'ONI', 
        'Temp_Global_Grain', 'Precip_Global_Grain',
        'RH_Global_Grain', 'SolarRad_Global_Grain', 'WindSpeed_Global_Grain',
        'ET0_Global_Grain',
        'GDD_Global_Grain', 'Heat_Stress_Days', 'Precip_Deficit'
    ]
    
    df_final = df_global[[col for col in main_cols if col in df_global.columns]].copy()
    
    logger.info(f"  Predictores finales: {list(df_final.columns)}")
    
    return df_final


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
    Pipeline principal de procesamiento - SOLO CONSOLIDACIÓN DE DATOS
    
    Este script NO hace feature engineering (eso se hace en notebooks 2.0-feature-engineering).
    Solo consolida datos crudos de múltiples fuentes:
    - Commodities (precios + volumen)
    - Predictores macro (VIX, DXY, tasas, etc.)
    - Clima (ONI, NASA POWER) - si disponible
    - Supply-Demand (USDA PSD) - si disponible
    
    Feature engineering se realiza en notebooks separados para:
    - Exploración interactiva
    - Documentación académica
    - Reproducibilidad
    """
    logger.info("=" * 80)
    logger.info("INICIO - CONSOLIDACIÓN DE DATOS (SIN FEATURE ENGINEERING)")
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
    
    # 2b. Agregar Volume como features adicionales
    logger.info("\nAgregando Volume features...")
    df_volume_wide = df_commodities.pivot_table(
        index='date',
        columns='commodity',
        values='volume',
        aggfunc='first'
    ).reset_index()
    df_volume_wide.columns = ['date'] + [f'{col}_volume' for col in df_volume_wide.columns[1:]]
    df_volume_wide.columns.name = None
    
    # Merge volume con commodities
    df_comm_wide = df_comm_wide.merge(df_volume_wide, on='date', how='left')
    logger.info(f"  ✓ Volume agregado: {len([c for c in df_comm_wide.columns if '_volume' in c])} columnas")
    
    # 3. Combinar commodities y predictores macro
    df_base = merge_commodities_predictors(df_comm_wide, df_pred_wide)
    
    # 3b. Integrar datos climáticos (si existen)
    climate_data = load_all_climate_data()
    if climate_data['oni'] is not None and len(climate_data['regions']) > 0:
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRANDO DATOS CLIMÁTICOS")
        logger.info("=" * 60)
        
        df_climate = create_global_climate_predictors(climate_data)
        
        # Merge con dataset base
        logger.info("\nCombinando con dataset base...")
        df_base = df_base.merge(df_climate, on='date', how='left')
        logger.info(f"  ✓ Dataset con clima: {df_base.shape}")
    else:
        logger.warning("\n⚠ No se encontraron datos climáticos. Continuando sin clima.")
    
    # 3c. Integrar datos supply-demand (si existen)
    df_supply_demand = load_all_supply_demand_data()
    if df_supply_demand is not None:
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRANDO DATOS SUPPLY-DEMAND (USDA PSD)")
        logger.info("=" * 60)
        
        # Merge con dataset base
        logger.info("\nCombinando con dataset base...")
        df_base = df_base.merge(df_supply_demand, on='date', how='left')
        logger.info(f"  ✓ Dataset con supply-demand: {df_base.shape}")
        
        # Reportar variables agregadas
        sd_cols = [col for col in df_supply_demand.columns if col != 'date']
        logger.info(f"  Variables supply-demand: {len(sd_cols)}")
        logger.info(f"  Países: World, Brazil, USA, Argentina, China")
    else:
        logger.warning("\n⚠ No se encontraron datos supply-demand. Continuando sin PSD.")
    
    # 4. Validar calidad (sin feature engineering)
    quality_report = check_data_quality(df_base)
    
    # 5. Guardar dataset consolidado (SIN feature engineering)
    output_path = save_processed_data(df_base, filename='commodities_base_consolidated.csv')
    save_metadata(df_base, quality_report)
    
    logger.info("\n" + "=" * 80)
    logger.info("FIN - CONSOLIDACIÓN DE DATOS")
    logger.info(f"✓ Dataset consolidado: {output_path}")
    logger.info("")
    logger.info("PRÓXIMOS PASOS:")
    logger.info("  Feature engineering se realiza en notebooks:")
    logger.info("    - notebooks/2.0-feature-engineering/2.1-temporal-lag-features.ipynb")
    logger.info("    - notebooks/2.0-feature-engineering/2.2-rolling-statistics-features.ipynb")
    logger.info("    - notebooks/2.0-feature-engineering/2.3-return-features-volatility.ipynb")
    logger.info("    - notebooks/2.0-feature-engineering/2.4-climate-features.ipynb")
    logger.info("")
    logger.info("  Output final: data/processed/commodities_base_daily.csv")
    logger.info("=" * 80)
    
    return df_base


if __name__ == '__main__':
    main()
