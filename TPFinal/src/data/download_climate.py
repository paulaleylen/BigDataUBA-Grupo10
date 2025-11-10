"""
Módulo para descarga de datos climáticos

Descarga datos climáticos que afectan producción de commodities agrícolas:
- ONI (Oceanic Niño Index) desde NOAA - Fenómeno ENSO
- Temperatura y precipitación desde NASA POWER API para 3 regiones clave
"""

import pandas as pd
import requests
import json
from datetime import datetime
from pathlib import Path
import warnings

from src.config import (
    INTERIM_CLIMATE_DIR, CLIMATE_REGISTRY_FILE,
    CLIMATE_REGIONS, CLIMATE_PARAMS_DOWNLOAD, ONI_URL,
    START_DATE, END_DATE, logger
)

warnings.filterwarnings('ignore')


def load_climate_registry():
    """
    Carga el registro de datos climáticos descargados
    
    Returns:
        dict: Registro con metadata de clima
    """
    if CLIMATE_REGISTRY_FILE.exists():
        with open(CLIMATE_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            'last_updated': None,
            'oni': {},
            'nasa_power': {}
        }


def save_climate_metadata(category, name, metadata):
    """
    Guarda metadata de datos climáticos en el registro
    
    Args:
        category (str): 'oni' o 'nasa_power'
        name (str): Nombre del dato climático
        metadata (dict): Metadata del dato
    """
    registry = load_climate_registry()
    
    registry['last_updated'] = datetime.now().isoformat()
    registry[category][name] = metadata
    
    with open(CLIMATE_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  ✓ Metadata guardada: {name}")


def download_oni_index():
    """
    Descarga el índice ONI (Oceanic Niño Index) desde NOAA
    
    Returns:
        pd.DataFrame: Datos ONI mensuales
    """
    logger.info("Descargando ONI (Oceanic Niño Index) desde NOAA...")
    
    try:
        # Descargar archivo de texto
        response = requests.get(ONI_URL, timeout=30)
        response.raise_for_status()
        
        # Parse del archivo (formato: SEAS YR TOTAL ANOM)
        # Ejemplo: "DJF 1950 24.72 -1.53"
        lines = response.text.strip().split('\n')
        
        # Mapeo de seasons a mes central
        season_to_month = {
            'DJF': 1,  'JFM': 2,  'FMA': 3,  'MAM': 4,
            'AMJ': 5,  'MJJ': 6,  'JJA': 7,  'JAS': 8,
            'ASO': 9,  'SON': 10, 'OND': 11, 'NDJ': 12
        }
        
        # Buscar línea de encabezado
        header_idx = 0
        for i, line in enumerate(lines):
            if 'SEAS' in line and 'YR' in line:
                header_idx = i
                break
        
        # Parsear datos
        data = []
        for line in lines[header_idx + 1:]:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    season = parts[0]
                    year = int(parts[1])
                    oni = float(parts[3])  # ANOM column (anomaly = ONI)
                    
                    # Obtener mes central del trimestre
                    if season in season_to_month:
                        month = season_to_month[season]
                        date_str = f"{year}-{month:02d}-01"
                        
                        data.append({
                            'date': date_str,
                            'year': year,
                            'month': month,
                            'season': season,
                            'ONI': oni
                        })
                except (ValueError, IndexError):
                    continue
        
        df_oni = pd.DataFrame(data)
        df_oni['date'] = pd.to_datetime(df_oni['date'])
        df_oni = df_oni[['date', 'year', 'month', 'season', 'ONI']].sort_values('date').reset_index(drop=True)
        
        logger.info(f"  ✓ {len(df_oni):,} observaciones mensuales")
        logger.info(f"  Período: {df_oni['date'].min().date()} → {df_oni['date'].max().date()}")
        logger.info(f"  ONI actual: {df_oni['ONI'].iloc[-1]:.2f} (último mes)")
        
        # Clasificar ENSO
        last_oni = df_oni['ONI'].iloc[-1]
        if last_oni >= 0.5:
            status = "El Niño"
        elif last_oni <= -0.5:
            status = "La Niña"
        else:
            status = "Neutral"
        logger.info(f"  Estado ENSO: {status}")
        
        return df_oni
        
    except Exception as e:
        logger.error(f"  ✗ Error descargando ONI: {e}")
        return None


def expand_oni_to_daily(df_oni, start_date=START_DATE, end_date=END_DATE):
    """
    Expande ONI mensual a frecuencia diaria usando forward-fill
    
    Args:
        df_oni (pd.DataFrame): ONI mensual
        start_date (str): Fecha inicio
        end_date (str): Fecha fin
        
    Returns:
        pd.DataFrame: ONI diario
    """
    logger.info("\nExpandiendo ONI mensual a diario (forward-fill)...")
    
    # Crear rango diario
    df_daily = pd.DataFrame({
        'date': pd.date_range(start=start_date, end=end_date, freq='D')
    })
    
    # Merge con ONI mensual
    df_daily = df_daily.merge(
        df_oni[['date', 'ONI']], 
        on='date', 
        how='left'
    )
    
    # Forward fill (valor del mes se mantiene hasta siguiente actualización)
    df_daily['ONI'] = df_daily['ONI'].ffill()
    
    # Backward fill para primeros días si es necesario
    df_daily['ONI'] = df_daily['ONI'].bfill()
    
    logger.info(f"  ✓ {len(df_daily):,} observaciones diarias")
    logger.info(f"  Valores faltantes: {df_daily['ONI'].isna().sum()}")
    
    return df_daily


def download_nasa_power_region(region_name, lat, lon, params=None, 
                                start_date=START_DATE, end_date=None):
    """
    Descarga datos climáticos de NASA POWER API para una región específica
    
    Args:
        region_name (str): Nombre de la región
        lat (float): Latitud
        lon (float): Longitud
        params (list): Lista de parámetros a descargar
        start_date (str): Fecha inicio
        end_date (str): Fecha fin
        
    Returns:
        pd.DataFrame: Datos climáticos diarios
    """
    if params is None:
        params = CLIMATE_PARAMS_DOWNLOAD
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    else:
        end_date = pd.to_datetime(end_date).strftime('%Y%m%d')
    
    start_date = pd.to_datetime(start_date).strftime('%Y%m%d')
    
    logger.info(f"\nDescargando datos NASA POWER para {region_name}...")
    logger.info(f"  Coordenadas: lat={lat}, lon={lon}")
    
    try:
        # Construir URL de la API
        base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        
        params_str = ",".join(params)
        
        url = (
            f"{base_url}?"
            f"parameters={params_str}&"
            f"community=AG&"
            f"longitude={lon}&"
            f"latitude={lat}&"
            f"start={start_date}&"
            f"end={end_date}&"
            f"format=JSON"
        )
        
        logger.info(f"  Descargando {len(params)} parámetros...")
        
        # Request con timeout largo (API puede ser lenta)
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraer datos
        param_data = data['properties']['parameter']
        
        # Crear DataFrame
        dfs = []
        for param, values in param_data.items():
            df_param = pd.DataFrame.from_dict(
                values, 
                orient='index', 
                columns=[param]
            )
            df_param.index = pd.to_datetime(df_param.index, format='%Y%m%d')
            dfs.append(df_param)
        
        df_climate = pd.concat(dfs, axis=1)
        df_climate = df_climate.reset_index().rename(columns={'index': 'date'})
        
        # Agregar región
        df_climate['region'] = region_name
        
        # Reemplazar valores faltantes (-999) con NaN
        for col in params:
            if col in df_climate.columns:
                df_climate[col] = df_climate[col].replace(-999.0, pd.NA)
        
        logger.info(f"  ✓ {len(df_climate):,} observaciones")
        logger.info(f"  Período: {df_climate['date'].min().date()} → {df_climate['date'].max().date()}")
        
        # Estadísticas básicas
        if 'T2M' in df_climate.columns:
            temp_mean = df_climate['T2M'].mean()
            logger.info(f"  Temperatura media: {temp_mean:.1f}°C")
        
        if 'PRECTOTCORR' in df_climate.columns:
            precip_mean = df_climate['PRECTOTCORR'].mean()
            logger.info(f"  Precipitación media: {precip_mean:.1f} mm/día")
        
        return df_climate
        
    except requests.exceptions.Timeout:
        logger.error(f"  ✗ Timeout descargando {region_name} (>120s)")
        return None
    except Exception as e:
        logger.error(f"  ✗ Error descargando {region_name}: {e}")
        return None


def save_climate_data(df, name, source, metadata_extra=None):
    """
    Guarda datos climáticos descargados
    
    Args:
        df (pd.DataFrame): Datos climáticos
        name (str): Nombre del archivo
        source (str): Fuente de datos
        metadata_extra (dict): Metadata adicional
    """
    # Guardar CSV
    output_path = INTERIM_CLIMATE_DIR / f'{name.lower()}.csv'
    df.to_csv(output_path, index=False)
    
    file_size_kb = output_path.stat().st_size / 1024
    logger.info(f"  ✓ Exportado: {output_path.name} ({file_size_kb:.1f} KB)")
    
    # Guardar metadata
    metadata = {
        'name': name,
        'source': source,
        'frequency': 'Daily',
        'period': {
            'start': df['date'].min().isoformat(),
            'end': df['date'].max().isoformat()
        },
        'observations': len(df),
        'file': f'{name.lower()}.csv',
        'downloaded_at': datetime.now().isoformat()
    }
    
    if metadata_extra:
        metadata.update(metadata_extra)
    
    # Agregar estadísticas si hay columnas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        metadata['stats'] = {}
        for col in numeric_cols:
            if col not in ['year', 'month']:
                metadata['stats'][col] = {
                    'mean': float(df[col].mean()) if df[col].notna().any() else None,
                    'min': float(df[col].min()) if df[col].notna().any() else None,
                    'max': float(df[col].max()) if df[col].notna().any() else None,
                    'missing_pct': float((df[col].isna().sum() / len(df)) * 100)
                }
    
    # Determinar categoría
    category = 'oni' if 'ONI' in name else 'nasa_power'
    save_climate_metadata(category, name, metadata)


def download_all_climate_data():
    """
    Descarga todos los datos climáticos configurados
    
    Returns:
        dict: {data_name: DataFrame}
    """
    logger.info("=" * 60)
    logger.info("DESCARGA DE DATOS CLIMÁTICOS")
    logger.info("=" * 60)
    
    climate_data = {}
    
    # 1. Descargar ONI
    logger.info("\n[ONI - Oceanic Niño Index]")
    df_oni_monthly = download_oni_index()
    
    if df_oni_monthly is not None:
        # Guardar mensual
        save_climate_data(
            df_oni_monthly, 
            'ONI_monthly', 
            'NOAA Climate Prediction Center',
            {'url': ONI_URL, 'type': 'ENSO Index'}
        )
        climate_data['ONI_monthly'] = df_oni_monthly
        
        # Expandir a diario
        df_oni_daily = expand_oni_to_daily(df_oni_monthly)
        save_climate_data(
            df_oni_daily,
            'ONI_daily',
            'NOAA Climate Prediction Center (forward-filled)',
            {'url': ONI_URL, 'type': 'ENSO Index', 'method': 'forward-fill from monthly'}
        )
        climate_data['ONI_daily'] = df_oni_daily
    
    # 2. Descargar NASA POWER para cada región
    for region_name, region_info in CLIMATE_REGIONS.items():
        logger.info(f"\n[NASA POWER - {region_info['name']}]")
        
        df_region = download_nasa_power_region(
            region_name=region_name,
            lat=region_info['lat'],
            lon=region_info['lon']
        )
        
        if df_region is not None:
            save_climate_data(
                df_region,
                f'NASA_POWER_{region_name}',
                'NASA POWER API',
                {
                    'region': region_info['name'],
                    'coordinates': {'lat': region_info['lat'], 'lon': region_info['lon']},
                    'production_weight': region_info['weight'],
                    'description': region_info['description']
                }
            )
            climate_data[f'NASA_POWER_{region_name}'] = df_region
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✓ {len(climate_data)} datasets climáticos descargados")
    logger.info("=" * 60)
    
    return climate_data


def main():
    """
    Pipeline principal de descarga de datos climáticos
    """
    logger.info("=" * 80)
    logger.info("INICIO - DESCARGA DE DATOS CLIMÁTICOS")
    logger.info("=" * 80)
    
    # Descargar todos los datos
    climate_data = download_all_climate_data()
    
    # Mostrar resumen
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN")
    logger.info("=" * 60)
    
    registry = load_climate_registry()
    
    # ONI
    if 'oni' in registry and len(registry['oni']) > 0:
        logger.info("\nONI (ENSO Index):")
        for name, meta in registry['oni'].items():
            logger.info(f"  {name}:")
            logger.info(f"    Observaciones: {meta['observations']:,}")
            logger.info(f"    Período: {meta['period']['start'][:10]} → {meta['period']['end'][:10]}")
            logger.info(f"    Archivo: {meta['file']}")
    
    # NASA POWER
    if 'nasa_power' in registry and len(registry['nasa_power']) > 0:
        logger.info("\nNASA POWER (Clima regional):")
        for name, meta in registry['nasa_power'].items():
            logger.info(f"  {name} - {meta.get('region', 'N/A')}:")
            logger.info(f"    Coordenadas: {meta.get('coordinates', {})}")
            logger.info(f"    Peso producción: {meta.get('production_weight', 0)*100:.0f}%")
            logger.info(f"    Observaciones: {meta['observations']:,}")
            logger.info(f"    Archivo: {meta['file']}")
    
    logger.info(f"\n📁 Archivos guardados en: {INTERIM_CLIMATE_DIR}/")
    
    logger.info("\n" + "=" * 80)
    logger.info("FIN - DESCARGA DE DATOS CLIMÁTICOS")
    logger.info("=" * 80)
    
    return climate_data


if __name__ == '__main__':
    main()
