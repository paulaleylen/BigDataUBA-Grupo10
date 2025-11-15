"""
Módulo de Feature Engineering para Commodities

Funciones reutilizables para generación de features sobre datos de commodities:
- Temporal features
- Lag features  
- Rolling statistics
- Return features
- Volatility features
- Climate features

Todas las funciones siguen el patrón: reciben DataFrame, retornan DataFrame.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Agregar src al path para imports
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import CLIMATE_REGIONS, CLIMATE_THRESHOLDS, logger


# ============================================================================
# TEMPORAL FEATURES
# ============================================================================

def add_temporal_features(df):
    """
    Agrega features temporales extraídas de la columna date
    
    Args:
        df (pd.DataFrame): Dataset con columna 'date'
        
    Returns:
        pd.DataFrame: Dataset con 6 features temporales adicionales
    """
    df = df.copy()
    
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week
    
    logger.info(f"✓ Temporal features agregadas: 6 columnas")
    
    return df


# ============================================================================
# LAG FEATURES
# ============================================================================

def add_lag_features(df, columns, lags=[1, 7, 30]):
    """
    Agrega features de lags (variables rezagadas)
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas para calcular lags
        lags (list): Períodos de lag a calcular (días)
        
    Returns:
        pd.DataFrame: Dataset con lags agregados
    """
    df = df.copy()
    
    features_added = 0
    
    for col in columns:
        if col in df.columns:
            for lag in lags:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
                features_added += 1
    
    logger.info(f"✓ Lag features agregadas: {features_added} columnas ({len(columns)} vars × {len(lags)} lags)")
    
    return df


# ============================================================================
# ROLLING STATISTICS
# ============================================================================

def add_rolling_features(df, columns, windows=[7, 30, 90]):
    """
    Agrega features de rolling statistics (media móvil y desviación estándar)
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas para calcular rolling stats
        windows (list): Ventanas de tiempo (días)
        
    Returns:
        pd.DataFrame: Dataset con rolling features agregadas
    """
    df = df.copy()
    
    features_added = 0
    
    for col in columns:
        if col in df.columns:
            for window in windows:
                # Media móvil
                df[f'{col}_ma{window}'] = df[col].rolling(
                    window=window, 
                    min_periods=1
                ).mean()
                
                # Desviación estándar
                df[f'{col}_std{window}'] = df[col].rolling(
                    window=window, 
                    min_periods=1
                ).std()
                
                features_added += 2
    
    logger.info(f"✓ Rolling features agregadas: {features_added} columnas ({len(columns)} vars × {len(windows)} windows × 2 stats)")
    
    return df


# ============================================================================
# RETURN FEATURES
# ============================================================================

def add_return_features(df, columns, periods=[1, 7, 30]):
    """
    Calcula retornos porcentuales
    
    Args:
        df (pd.DataFrame): Dataset base
        columns (list): Columnas de precios para calcular retornos
        periods (list): Períodos de retorno (días)
        
    Returns:
        pd.DataFrame: Dataset con retornos agregados
    """
    df = df.copy()
    
    features_added = 0
    
    for col in columns:
        if col in df.columns:
            for period in periods:
                df[f'{col}_return{period}'] = df[col].pct_change(periods=period) * 100
                features_added += 1
    
    logger.info(f"✓ Return features agregadas: {features_added} columnas ({len(columns)} vars × {len(periods)} periods)")
    
    return df


def add_realized_volatility(df, price_columns, window=30):
    """
    Calcula volatilidad realizada (desviación estándar de retornos diarios en ventana móvil)
    
    Args:
        df (pd.DataFrame): Dataset con retornos diarios
        price_columns (list): Columnas de precios originales
        window (int): Ventana para calcular volatilidad (días)
        
    Returns:
        pd.DataFrame: Dataset con volatilidad realizada
    """
    df = df.copy()
    
    features_added = 0
    
    for col in price_columns:
        return_col = f'{col}_return1'
        if return_col in df.columns:
            df[f'{col}_volatility{window}'] = df[return_col].rolling(
                window=window,
                min_periods=1
            ).std()
            features_added += 1
    
    logger.info(f"✓ Volatilidad realizada agregada: {features_added} columnas (window={window}d)")
    
    return df


# ============================================================================
# CLIMATE FEATURES
# ============================================================================

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
        climate_data (dict): {'oni': DataFrame, 'regions': {region_name: DataFrame}}
        
    Returns:
        pd.DataFrame: Predictores climáticos globales
    """
    logger.info("\nCreando predictores climáticos globales...")
    
    # Verificar datos disponibles
    if climate_data['oni'] is None or len(climate_data['regions']) == 0:
        logger.warning("⚠ Datos climáticos insuficientes. Retornando DataFrame vacío.")
        return pd.DataFrame()
    
    # Iniciar con ONI
    df_global = climate_data['oni'][['date', 'ONI']].copy()
    
    # Preparar datos regionales
    regions_data = climate_data['regions']
    
    # Verificar regiones esperadas
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
