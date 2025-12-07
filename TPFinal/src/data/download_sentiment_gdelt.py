"""
Download News Sentiment Data from GDELT Project
================================================

Este script descarga datos de sentimiento de noticias usando GDELT Project.

**SOLUCIÓN COMPLETA:**
- GDELT 1.0: 2000-2013 (datos diarios, menos detallados)
- GDELT 2.0: 2015-2025 (datos cada 15 min, tone scores completos)
- Combinación: 25 años de datos de sentiment (2000-2025)

**Cobertura temporal:**
- GDELT 1.0: 1979-2013 (daily data, eventos + themes)
- GDELT 2.0: Feb 2015-presente (15 min intervals, tone scores detallados)
- GAP: 2014 (no cubierto por GDELT 2.0 aún en sus archives)

**Instalación:**
    pip install gdelt tqdm
    # Para BigQuery (opcional):
    pip install google-cloud-bigquery

**Uso:**
    # Descarga completa (GDELT 1.0 + 2.0)
    python src/data/download_sentiment_gdelt.py
    
    # Test rápido (1 mes)
    python src/data/download_sentiment_gdelt.py --test

**Referencias:**
- GDELT Project: https://www.gdeltproject.org/
- gdeltPyR docs: https://github.com/linwoodc3/gdeltPyR
- BigQuery: https://console.cloud.google.com/bigquery
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys
import argparse
from tqdm import tqdm
import warnings

# Suprimir warnings de gdelt (hay muchos días sin datos)
warnings.filterwarnings('ignore', message='GDELT did not return data')
warnings.filterwarnings('ignore', message='GDELT does not have a url')
warnings.filterwarnings('ignore')  # Suprimir todos los warnings

# Suprimir stdout/stderr de gdelt (imprime "here" muchas veces)
import os
import io
import contextlib

# Importar gdeltPyR suprimiendo su verbose output
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import gdelt
except ImportError:
    print("❌ ERROR: gdeltPyR no está instalado")
    print("Instalar con: pip install gdelt")
    sys.exit(1)


# ============================================================================
# Configuración
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_EXTERNAL = PROJECT_ROOT / 'data' / 'external' / 'sentiment'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'

# Crear directorios si no existen
DATA_EXTERNAL.mkdir(parents=True, exist_ok=True)

# Keywords para búsqueda (commodities agrícolas)
KEYWORDS = [
    'soybean', 'soybeans', 'corn', 'wheat', 'maize',
    'grain', 'agriculture', 'crop', 'harvest',
    'commodity', 'futures'
]

# Períodos de descarga
START_DATE_V1 = datetime(2000, 1, 1)   # GDELT 1.0 desde 2000
END_DATE_V1 = datetime(2013, 12, 31)   # GDELT 1.0 hasta 2013
START_DATE_V2 = datetime(2015, 2, 19)  # GDELT 2.0 inicia el 19 Feb 2015
END_DATE_V2 = datetime(2025, 11, 30)   # Hasta noviembre 2025


# ============================================================================
# Método 1: Download GDELT 1.0 (2000-2013) - Datos Históricos
# ============================================================================

def download_gdelt_v1_batches(start_date, end_date, batch_months=6, temp_dir=None):
    """
    Descarga GDELT 1.0 en batches para evitar timeouts.
    OPTIMIZADO: Guarda cada batch a disco inmediatamente para evitar consumir RAM.
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio
    end_date : datetime
        Fecha de fin
    batch_months : int
        Tamaño del batch en meses (default 6, optimizado para velocidad)
    temp_dir : Path
        Directorio temporal para batches (si None, usa DATA_EXTERNAL)
    
    Returns
    -------
    pd.DataFrame
        Datos descargados de GDELT 1.0
    
    Notes
    -----
    GDELT 1.0 no tiene tone scores, pero tiene:
    - AvgTone: Tone promedio de los artículos
    - GoldsteinScale: Escala de conflicto/cooperación
    - NumArticles: Número de artículos
    """
    print(f"\n🔄 Descargando GDELT 1.0 (Historical Events)...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Estrategia: Batches de {batch_months} mes(es) - guardado incremental")
    
    if temp_dir is None:
        temp_dir = DATA_EXTERNAL / 'temp_batches_v1'
    temp_dir.mkdir(exist_ok=True)
    
    gd = gdelt.gdelt(version=1)
    batch_files = []  # Lista de archivos temporales, NO DataFrames
    
    # Crear batches por mes
    current = start_date
    batch_count = 0
    
    with tqdm(total=(end_date.year - start_date.year) * 12 + (end_date.month - start_date.month), 
              desc="📥 GDELT 1.0", unit="mes") as pbar:
        
        while current < end_date:
            # Calcular fin del batch
            batch_end = current + timedelta(days=batch_months * 31)
            if batch_end > end_date:
                batch_end = end_date
            
            batch_count += 1
            batch_file = temp_dir / f'batch_{batch_count:04d}.parquet'
            
            try:
                # Descargar batch (capturar stdout/stderr para suprimir prints de gdelt)
                date_range = [
                    current.strftime('%Y %m %d'),
                    batch_end.strftime('%Y %m %d')
                ]
                
                # Capturar stdout Y stderr para suprimir verbose output de gdeltPyR
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    df_batch = gd.Search(
                        date=date_range,
                        table='events',  # GDELT 1.0 usa 'events' table
                        coverage=True,   # Todos los datos diarios
                        output='df'
                    )
                
                if df_batch is not None and len(df_batch) > 0:
                    # CRÍTICO: Guardar a disco inmediatamente, NO acumular en RAM
                    df_batch.to_parquet(batch_file, index=False)
                    batch_files.append(batch_file)
                    pbar.set_postfix({'registros': len(df_batch), 'batch': batch_count, 'RAM': 'liberada'})
                    del df_batch  # Liberar memoria explícitamente
                
            except Exception as e:
                print(f"\n⚠️  Error en batch {current.date()} - {batch_end.date()}: {e}")
            
            # Avanzar al siguiente batch
            months_processed = (batch_end.year - current.year) * 12 + (batch_end.month - current.month)
            pbar.update(months_processed)
            current = batch_end + timedelta(days=1)
    
    if len(batch_files) == 0:
        print("❌ No se descargó ningún dato de GDELT 1.0")
        return None
    
    # Concatenar desde archivos (más eficiente que desde RAM)
    print(f"\n🔄 Consolidando {len(batch_files)} batches desde disco...")
    df_combined = pd.concat([pd.read_parquet(f) for f in batch_files], ignore_index=True)
    
    # Limpiar archivos temporales
    for f in batch_files:
        f.unlink()
    temp_dir.rmdir()
    
    print(f"✅ GDELT 1.0 completado: {len(df_combined):,} registros")
    return df_combined


# ============================================================================
# Método 2: Download GDELT 2.0 (2015-2025) - Datos Modernos
# ============================================================================

def download_gdelt_v2_batches(start_date, end_date, batch_days=60, temp_dir=None):
    """
    Descarga GDELT 2.0 en batches para evitar timeouts.
    OPTIMIZADO: Guarda cada batch a disco inmediatamente para evitar consumir RAM.
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio
    end_date : datetime
        Fecha de fin
    batch_days : int
        Tamaño del batch en días (default 60, optimizado para velocidad)
    temp_dir : Path
        Directorio temporal para batches (si None, usa DATA_EXTERNAL)
    
    Returns
    -------
    pd.DataFrame
        Datos descargados de GDELT 2.0 (con tone scores)
    """
    print(f"\n🔄 Descargando GDELT 2.0 (GKG with Tone Scores)...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Estrategia: Batches de {batch_days} días - guardado incremental")
    
    if temp_dir is None:
        temp_dir = DATA_EXTERNAL / 'temp_batches_v2'
    temp_dir.mkdir(exist_ok=True)
    
    gd = gdelt.gdelt(version=2)
    batch_files = []  # Lista de archivos temporales, NO DataFrames
    
    # Crear batches por día
    current = start_date
    batch_count = 0
    total_days = (end_date - start_date).days
    
    with tqdm(total=total_days, desc="📥 GDELT 2.0", unit="día") as pbar:
        
        while current < end_date:
            # Calcular fin del batch
            batch_end = current + timedelta(days=batch_days)
            if batch_end > end_date:
                batch_end = end_date
            
            batch_count += 1
            batch_file = temp_dir / f'batch_{batch_count:04d}.parquet'
            
            try:
                # Descargar batch (capturar stdout/stderr para suprimir prints de gdelt)
                date_range = [
                    current.strftime('%Y %m %d'),
                    batch_end.strftime('%Y %m %d')
                ]
                
                # Capturar stdout Y stderr para suprimir verbose output de gdeltPyR
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    df_batch = gd.Search(
                        date=date_range,
                        table='gkg',     # Global Knowledge Graph (tiene tone)
                        coverage=False,  # Solo último intervalo del día
                        translation=False,  # Solo inglés (más rápido)
                        output='df'
                    )
                
                if df_batch is not None and len(df_batch) > 0:
                    # CRÍTICO: Guardar a disco inmediatamente, NO acumular en RAM
                    df_batch.to_parquet(batch_file, index=False)
                    batch_files.append(batch_file)
                    pbar.set_postfix({'registros': len(df_batch), 'batch': batch_count, 'RAM': 'liberada'})
                    del df_batch  # Liberar memoria explícitamente
                
            except Exception as e:
                # Silenciosamente continuar (muchos días no tienen datos)
                pass
            
            # Avanzar al siguiente batch
            days_processed = (batch_end - current).days
            pbar.update(days_processed)
            current = batch_end + timedelta(days=1)
    
    if len(batch_files) == 0:
        print("❌ No se descargó ningún dato de GDELT 2.0")
        return None
    
    # Concatenar desde archivos (más eficiente que desde RAM)
    print(f"\n🔄 Consolidando {len(batch_files)} batches desde disco...")
    df_combined = pd.concat([pd.read_parquet(f) for f in batch_files], ignore_index=True)
    
    # Limpiar archivos temporales
    for f in batch_files:
        f.unlink()
    temp_dir.rmdir()
    
    print(f"✅ GDELT 2.0 completado: {len(df_combined):,} registros")
    return df_combined


# ============================================================================
# Método 2: Download via BigQuery (MEJOR OPCIÓN)
# ============================================================================

def download_gdelt_via_bigquery(start_date, end_date, keywords):
    """
    Descarga datos de GDELT usando Google BigQuery.
    
    **VENTAJAS:**
    - Sin rate limits
    - Consultas SQL potentes
    - GRATIS hasta 1 TB/mes
    - MUCHO más rápido que HTTP
    
    **REQUISITOS:**
    1. Cuenta Google Cloud (gratuita): https://console.cloud.google.com
    2. Activar BigQuery API
    3. pip install google-cloud-bigquery
    4. Configurar credenciales:
       export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio
    end_date : datetime
        Fecha de fin
    keywords : list
        Lista de keywords para filtrar
    
    Returns
    -------
    pd.DataFrame
        Datos descargados
    """
    try:
        from google.cloud import bigquery
    except ImportError:
        print("❌ ERROR: google-cloud-bigquery no está instalado")
        print("Instalar con: pip install google-cloud-bigquery")
        return None
    
    print(f"\n🔄 Descargando GDELT via BigQuery...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Keywords: {', '.join(keywords[:3])}...")
    
    # Inicializar cliente BigQuery
    try:
        client = bigquery.Client()
    except Exception as e:
        print(f"❌ Error al inicializar BigQuery: {e}")
        print("\nSolución:")
        print("1. Crear cuenta Google Cloud: https://console.cloud.google.com")
        print("2. Crear proyecto")
        print("3. Activar BigQuery API")
        print("4. Descargar credentials.json")
        print("5. Set GOOGLE_APPLICATION_CREDENTIALS env variable")
        return None
    
    # Construir query SQL
    # Tabla: gdelt-bq.gdeltv2.gkg (Global Knowledge Graph)
    keywords_pattern = '|'.join(keywords)  # Regex OR pattern
    
    query = f"""
    SELECT 
        DATE,
        V2Tone,
        V2Locations,
        V2Themes,
        V2Persons,
        V2Organizations,
        SourceCommonName,
        DocumentIdentifier
    FROM 
        `gdelt-bq.gdeltv2.gkg`
    WHERE 
        DATE >= '{start_date.strftime('%Y%m%d')}000000'
        AND DATE <= '{end_date.strftime('%Y%m%d')}235959'
        AND REGEXP_CONTAINS(V2Themes, r'(?i){keywords_pattern}')
    LIMIT 1000000
    """
    
    print(f"\n📊 Ejecutando query BigQuery...")
    print(f"   (Esto puede tomar varios minutos para períodos largos)")
    
    try:
        # Ejecutar query
        df = client.query(query).to_dataframe()
        
        print(f"✅ Query completada: {len(df):,} registros")
        print(f"   Columnas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error en query BigQuery: {e}")
        return None


# ============================================================================
# Procesamiento de datos GDELT
# ============================================================================

def process_gdelt_sentiment(df, version='v2'):
    """
    Procesa datos crudos de GDELT para extraer features de sentiment.
    Soporta GDELT 1.0 (events) y GDELT 2.0 (GKG).
    
    Parameters
    ----------
    df : pd.DataFrame
        Datos crudos de GDELT
    version : str
        'v1' (events table) o 'v2' (GKG table)
    
    Returns
    -------
    pd.DataFrame
        Datos procesados con features diarias
    """
    if df is None or len(df) == 0:
        print("⚠️  No hay datos para procesar")
        return None
    
    print(f"\n🔧 Procesando datos GDELT {version.upper()}...")
    print(f"   Registros iniciales: {len(df):,}")
    
    # PASO 1: Parsear fecha según versión
    if version == 'v1':
        # GDELT 1.0: usa SQLDATE (formato YYYYMMDD)
        if 'SQLDATE' in df.columns:
            df['date'] = pd.to_datetime(df['SQLDATE'], format='%Y%m%d', errors='coerce')
        else:
            print(f"❌ No se encontró SQLDATE en GDELT 1.0: {df.columns.tolist()}")
            return None
    
    elif version == 'v2':
        # GDELT 2.0: usa DATE (formato YYYYMMDDHHMMSS)
        if 'DATE' in df.columns:
            df['date'] = pd.to_datetime(df['DATE'], format='%Y%m%d%H%M%S', errors='coerce')
        else:
            print(f"❌ No se encontró DATE en GDELT 2.0: {df.columns.tolist()}")
            return None
    
    # PASO 2: Extraer tone (sentiment) según versión
    if version == 'v1':
        # GDELT 1.0: AvgTone en escala -100 a +100
        if 'AvgTone' in df.columns:
            df['tone_value'] = pd.to_numeric(df['AvgTone'], errors='coerce') / 100
            df['article_count'] = 1  # Cada evento = 1 artículo (aproximación)
        else:
            print(f"❌ No se encontró AvgTone en GDELT 1.0: {df.columns.tolist()}")
            return None
    
    elif version == 'v2':
        # GDELT 2.0: V2Tone con múltiples scores
        if 'V2Tone' in df.columns:
            # V2Tone format: "Tone,PositiveScore,NegativeScore,..."
            # Nos interesa el primer valor (Tone general en escala -100 a +100)
            df['tone_value'] = df['V2Tone'].astype(str).str.split(',').str[0]
            df['tone_value'] = pd.to_numeric(df['tone_value'], errors='coerce') / 100
            
            # Contar artículos únicos
            if 'DocumentIdentifier' in df.columns:
                df['article_count'] = 1
            else:
                df['article_count'] = 1
        else:
            print(f"❌ No se encontró V2Tone en GDELT 2.0: {df.columns.tolist()}")
            return None
    
    # PASO 3: Limpiar datos
    df_clean = df.dropna(subset=['date', 'tone_value'])
    print(f"   Registros después de limpiar: {len(df_clean):,}")
    
    if len(df_clean) == 0:
        print("⚠️  No quedaron registros después de limpiar")
        return None
    
    # PASO 4: Agregar por día
    daily = df_clean.groupby(df_clean['date'].dt.date).agg({
        'tone_value': ['mean', 'std', 'count'],
        'article_count': 'sum'
    }).reset_index()
    
    # Flatten multi-index columns
    daily.columns = ['date', 'tone_mean', 'tone_std', 'tone_count', 'article_count']
    
    # Convertir date a datetime
    daily['date'] = pd.to_datetime(daily['date'])
    
    print(f"   Días con datos: {len(daily):,}")
    print(f"   Rango: {daily['date'].min().date()} a {daily['date'].max().date()}")
    print(f"   Tone medio: {daily['tone_mean'].mean():.3f} ± {daily['tone_mean'].std():.3f}")
    print(f"   Artículos/día: {daily['article_count'].mean():.0f} ± {daily['article_count'].std():.0f}")
    
    return daily


def generate_sentiment_features(df_sentiment):
    """
    Genera features de sentiment para el modelo.
    
    Parameters
    ----------
    df_sentiment : pd.DataFrame
        Datos diarios de sentiment (output de process_gdelt_sentiment)
    
    Returns
    -------
    pd.DataFrame
        Features de sentiment
    """
    if df_sentiment is None or len(df_sentiment) == 0:
        return None
    
    print(f"\n🔧 Generando features de sentiment...")
    
    df = df_sentiment.copy()
    
    # 1. Normalizar tone a [-1, 1]
    # GDELT tone range: -100 to +100
    df['news_sentiment_normalized'] = df['tone_mean'] / 100
    
    # 2. Volume metrics
    df['news_volume'] = df['article_count']
    
    # 3. Moving averages (7 días)
    df['news_sentiment_7d_ma'] = df['news_sentiment_normalized'].rolling(7, min_periods=1).mean()
    df['news_volume_7d_ma'] = df['news_volume'].rolling(7, min_periods=1).mean()
    
    # 4. Changes (day-over-day)
    df['news_sentiment_change'] = df['news_sentiment_normalized'].diff()
    df['news_volume_change'] = df['news_volume'].diff()
    
    # 5. Percentiles (rolling 252 días = 1 año de trading)
    df['news_sentiment_percentile'] = (
        df['news_sentiment_normalized']
        .rolling(252, min_periods=30)
        .apply(lambda x: (x.iloc[-1] >= x).sum() / len(x) * 100, raw=False)
    )
    
    # 6. Extreme signals
    df['news_extreme_positive'] = (df['news_sentiment_percentile'] > 90).astype(int)
    df['news_extreme_negative'] = (df['news_sentiment_percentile'] < 10).astype(int)
    
    # Seleccionar columnas finales
    feature_cols = [
        'date',
        'news_volume',
        'news_sentiment_normalized',
        'news_sentiment_7d_ma',
        'news_volume_7d_ma',
        'news_sentiment_change',
        'news_volume_change',
        'news_sentiment_percentile',
        'news_extreme_positive',
        'news_extreme_negative'
    ]
    
    df_features = df[feature_cols].copy()
    
    print(f"✅ Features generados: {len(df_features):,} días")
    print(f"   Columnas: {len(feature_cols)} features")
    
    return df_features


# ============================================================================
# Main execution
# ============================================================================

def main(test_mode=False):
    """
    Descarga y procesa datos de sentiment de GDELT 1.0 + 2.0.
    
    Parameters
    ----------
    test_mode : bool, default=False
        Si True, solo descarga 2 meses (1 de cada versión para testing)
    """
    print("="*70)
    print("GDELT SENTIMENT DATA DOWNLOAD - DUAL VERSION")
    print("="*70)
    print("Estrategia: GDELT 1.0 (2000-2013) + GDELT 2.0 (2015-2025)")
    print("Gap: 2014 (será imputado en notebook 2.6)")
    
    # Ajustar período si test mode
    if test_mode:
        start_v1 = datetime(2010, 1, 1)
        end_v1 = datetime(2010, 1, 31)
        start_v2 = datetime(2024, 1, 1)
        end_v2 = datetime(2024, 1, 31)
        print("\n⚠️  TEST MODE: Solo 1 mes por versión")
        print(f"   GDELT 1.0: {start_v1.date()} a {end_v1.date()}")
        print(f"   GDELT 2.0: {start_v2.date()} a {end_v2.date()}")
    else:
        start_v1 = START_DATE_V1
        end_v1 = END_DATE_V1
        start_v2 = START_DATE_V2
        end_v2 = END_DATE_V2
        print(f"\n📅 Cobertura completa:")
        print(f"   GDELT 1.0: {start_v1.date()} a {end_v1.date()} (14 años)")
        print(f"   GDELT 2.0: {start_v2.date()} a {end_v2.date()} (10 años)")
        print(f"   Total: 24 años de sentiment data")
    
    # ==============================================================
    # PASO 1: Descargar GDELT 1.0 (2000-2013)
    # ==============================================================
    print("\n" + "="*70)
    print("PASO 1/5: GDELT 1.0 (2000-2013)")
    print("="*70)
    
    df_v1_raw = download_gdelt_v1_batches(start_v1, end_v1, batch_months=6)
    
    if df_v1_raw is not None and len(df_v1_raw) > 0:
        raw_file_v1 = DATA_EXTERNAL / f'gdelt_v1_raw_{start_v1.year}_{end_v1.year}.csv'
        print(f"\n💾 Guardando GDELT 1.0 raw: {raw_file_v1.name}")
        df_v1_raw.to_csv(raw_file_v1, index=False)
        print(f"   Registros: {len(df_v1_raw):,}")
        print(f"   Tamaño: {raw_file_v1.stat().st_size / 1e6:.1f} MB")
    else:
        print("⚠️  GDELT 1.0 no descargó datos (continuando con v2 solamente)")
        df_v1_raw = None
    
    # ==============================================================
    # PASO 2: Descargar GDELT 2.0 (2015-2025)
    # ==============================================================
    print("\n" + "="*70)
    print("PASO 2/5: GDELT 2.0 (2015-2025)")
    print("="*70)
    
    df_v2_raw = download_gdelt_v2_batches(start_v2, end_v2, batch_days=60)
    
    if df_v2_raw is not None and len(df_v2_raw) > 0:
        raw_file_v2 = DATA_EXTERNAL / f'gdelt_v2_raw_{start_v2.year}_{end_v2.year}.csv'
        print(f"\n💾 Guardando GDELT 2.0 raw: {raw_file_v2.name}")
        df_v2_raw.to_csv(raw_file_v2, index=False)
        print(f"   Registros: {len(df_v2_raw):,}")
        print(f"   Tamaño: {raw_file_v2.stat().st_size / 1e6:.1f} MB")
    else:
        print("⚠️  GDELT 2.0 no descargó datos (continuando con v1 solamente)")
        df_v2_raw = None
    
    # Verificar que al menos una versión descargó datos
    if df_v1_raw is None and df_v2_raw is None:
        print("\n❌ Ninguna versión descargó datos. Abortando.")
        return
    
    # ==============================================================
    # PASO 3: Procesar ambas versiones
    # ==============================================================
    print("\n" + "="*70)
    print("PASO 3/5: PROCESAR Y COMBINAR")
    print("="*70)
    
    # Procesar v1
    if df_v1_raw is not None:
        df_v1_daily = process_gdelt_sentiment(df_v1_raw, version='v1')
    else:
        df_v1_daily = None
    
    # Procesar v2
    if df_v2_raw is not None:
        df_v2_daily = process_gdelt_sentiment(df_v2_raw, version='v2')
    else:
        df_v2_daily = None
    
    # Combinar v1 y v2
    daily_frames = [df for df in [df_v1_daily, df_v2_daily] if df is not None]
    
    if len(daily_frames) == 0:
        print("\n❌ No hay datos procesados para combinar. Abortando.")
        return
    
    df_combined = pd.concat(daily_frames, ignore_index=True)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    print(f"\n✅ Combinado: {len(df_combined):,} días")
    print(f"   Rango: {df_combined['date'].min().date()} a {df_combined['date'].max().date()}")
    print(f"   Gap 2014: Será imputado en notebook 2.6")
    
    # Guardar daily combinado
    daily_file = DATA_EXTERNAL / f'sentiment_daily_{start_v1.year}_{end_v2.year}.csv'
    print(f"\n💾 Guardando daily combinado: {daily_file.name}")
    df_combined.to_csv(daily_file, index=False)
    
    # ==============================================================
    # PASO 4: Generar features
    # ==============================================================
    print("\n" + "="*70)
    print("PASO 4/5: GENERAR FEATURES")
    print("="*70)
    
    df_features = generate_sentiment_features(df_combined)
    
    if df_features is None:
        print("\n❌ Generación de features falló. Abortando.")
        return
    
    # Guardar features
    features_file = DATA_EXTERNAL / f'sentiment_features_{start_v1.year}_{end_v2.year}.csv'
    print(f"\n💾 Guardando features: {features_file.name}")
    df_features.to_csv(features_file, index=False)
    print(f"   Tamaño: {features_file.stat().st_size / 1e3:.1f} KB")
    
    # ==============================================================
    # PASO 5: Resumen final
    # ==============================================================
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    if df_v1_raw is not None and df_v1_daily is not None:
        print(f"GDELT 1.0: {len(df_v1_raw):,} eventos → {len(df_v1_daily):,} días")
    else:
        print(f"GDELT 1.0: No disponible")
    
    if df_v2_raw is not None and df_v2_daily is not None:
        print(f"GDELT 2.0: {len(df_v2_raw):,} registros → {len(df_v2_daily):,} días")
    else:
        print(f"GDELT 2.0: No disponible")
    
    print(f"\nCombinado: {len(df_combined):,} días con sentiment")
    print(f"Features: {len(df_features):,} días × {len(df_features.columns)-1} features")
    
    print(f"\n📊 NaNs por feature:")
    for col in df_features.columns:
        if col != 'date':
            nans = df_features[col].isna().sum()
            pct = nans / len(df_features) * 100
            print(f"  {col}: {nans} ({pct:.1f}%)")
    
    print(f"\n✅ Proceso completado exitosamente")
    print(f"   Archivos guardados en: {DATA_EXTERNAL}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download GDELT sentiment data (v1.0 + v2.0)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: only download 1 month per version (2010-01 + 2024-01)'
    )
    
    args = parser.parse_args()
    
    main(test_mode=args.test)
