"""
Download News Sentiment Data from GDELT Project
================================================

Este script procesa y consolida datos de sentimiento de noticias de GDELT.

**MÉTODO IMPLEMENTADO (2 FUENTES):**

1. **GDELT 1.0 (1979-2013):** 
   - Archivo: MASTERREDUCEDV2.TXT (6.3 GB, descarga manual)
   - Fuente: https://www.gdeltproject.org/data.html#rawdatafiles
   - Contiene: 87M eventos con Goldstein Scale (convertido a tone)
   - Procesamiento: Notebook 2.6-gdelt-historical-merge.ipynb

2. **GDELT 2.0 (2015-2025):**
   - Fuente: Google BigQuery API
   - Dataset: `gdelt-bq.gdeltv2.gkg`
   - Descarga: ~30 segundos vía SQL agregación server-side
   - Contiene: V2Tone scores nativos

**RESULTADO FINAL:**
- Dataset consolidado: sentiment_features_1979_2025.csv
- Cobertura: 46.9 años (16,753 días)
- Features: 10 (tone_mean, tone_std, tone_ma7, tone_ma30, etc.)
- Gap 2014: No cubierto (GDELT 2.0 comienza en Feb 2015)

**Instalación:**
    pip install google-cloud-bigquery pandas numpy tqdm

**Configuración BigQuery:**
    1. Crear proyecto en https://console.cloud.google.com
    2. Habilitar BigQuery API
    3. Crear Service Account y descargar JSON credentials
    4. Configurar: export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

**Uso:**
    # Descargar GDELT 2.0 vía BigQuery (recomendado, ~30 seg)
    python src/data/download_sentiment_gdelt.py --bigquery
    
    # Procesar GDELT 1.0 manual:
    # 1. Descargar MASTERREDUCEDV2.TXT a data/external/sentiment/
    # 2. Ejecutar notebook 2.6-gdelt-historical-merge.ipynb
    
    # Test rápido (solo últimos 30 días)
    python src/data/download_sentiment_gdelt.py --bigquery --test

**Referencias:**
- GDELT Project: https://www.gdeltproject.org/
- GDELT BigQuery: https://console.cloud.google.com/marketplace/product/gdelt-bq/gdelt-2-0
- GDELT 1.0 Files: https://www.gdeltproject.org/data.html#rawdatafiles
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

def download_gdelt_v1_batches(start_date, end_date, batch_months=1, temp_dir=None):
    """
    Descarga GDELT 1.0 en batches para evitar timeouts.
    ULTRA-OPTIMIZADO: 1 mes por batch, solo columnas esenciales, pausas largas.
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio
    end_date : datetime
        Fecha de fin
    batch_months : int
        Tamaño del batch en meses (default 1, MUY reducido para bajo consumo RAM)
    temp_dir : Path
        Directorio temporal para batches (si None, usa DATA_EXTERNAL)
    
    Returns
    -------
    pd.DataFrame
        Datos descargados de GDELT 1.0 (solo columnas esenciales)
    
    Notes
    -----
    GDELT 1.0 tiene ~57 columnas pero solo necesitamos:
    - SQLDATE: Fecha
    - AvgTone: Tone promedio (-100 a +100)
    """
    import gc  # Garbage collector para liberar RAM
    
    print(f"\n🔄 Descargando GDELT 1.0 (Historical Events)...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Estrategia: Batches de {batch_months} mes - bajo consumo RAM")
    
    if temp_dir is None:
        temp_dir = DATA_EXTERNAL / 'temp_batches_v1'
    temp_dir.mkdir(exist_ok=True)
    
    gd = gdelt.gdelt(version=1)
    batch_files = []  # Lista de archivos temporales, NO DataFrames
    
    # Crear batches por mes
    current = start_date
    batch_count = 0
    
    # Columnas que REALMENTE necesitamos (de 57, solo 2)
    ESSENTIAL_COLS = ['SQLDATE', 'AvgTone']
    
    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    with tqdm(total=total_months, desc="📥 GDELT 1.0", unit="mes") as pbar:
        
        while current < end_date:
            # Calcular fin del batch (1 mes máximo)
            batch_end = current + timedelta(days=batch_months * 30)
            if batch_end > end_date:
                batch_end = end_date
            
            batch_count += 1
            batch_file = temp_dir / f'batch_{batch_count:04d}.parquet'
            
            # Si ya existe el archivo (descarga previa), skip
            if batch_file.exists():
                batch_files.append(batch_file)
                pbar.update(batch_months)
                current = batch_end + timedelta(days=1)
                continue
            
            try:
                # Forzar garbage collection ANTES de descargar
                gc.collect()
                
                # Descargar batch
                date_range = [
                    current.strftime('%Y %m %d'),
                    batch_end.strftime('%Y %m %d')
                ]
                
                # Capturar stdout Y stderr para suprimir verbose output de gdeltPyR
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    df_batch = gd.Search(
                        date=date_range,
                        table='events',
                        coverage=True,
                        output='df'
                    )
                
                if df_batch is not None and len(df_batch) > 0:
                    # INMEDIATAMENTE filtrar a solo columnas esenciales
                    available_cols = [c for c in ESSENTIAL_COLS if c in df_batch.columns]
                    if available_cols:
                        df_small = df_batch[available_cols].copy()
                        del df_batch  # Liberar el DataFrame grande ASAP
                        gc.collect()
                        
                        # Guardar versión pequeña
                        df_small.to_parquet(batch_file, index=False)
                        batch_files.append(batch_file)
                        pbar.set_postfix({'filas': len(df_small), 'cols': len(available_cols)})
                        del df_small
                    else:
                        del df_batch
                    
                    gc.collect()
                    time.sleep(2)  # Pausa de 2 segundos entre batches
                
            except MemoryError:
                print(f"\n💥 MemoryError en {current.date()}. Saltando batch...")
                gc.collect()
                time.sleep(5)  # Pausa larga para recuperar
                
            except Exception as e:
                # Solo mostrar errores que no sean de memoria
                if 'MemoryError' not in str(e):
                    print(f"\n⚠️  Error en {current.date()}: {str(e)[:50]}...")
                gc.collect()
                time.sleep(2)
            
            # Avanzar al siguiente batch
            pbar.update(batch_months)
            current = batch_end + timedelta(days=1)
            
            # Pausa cada 3 batches
            if batch_count % 3 == 0:
                gc.collect()
                time.sleep(3)
    
    if len(batch_files) == 0:
        print("❌ No se descargó ningún dato de GDELT 1.0")
        return None
    
    # NUEVA ESTRATEGIA: Procesar batch por batch, agregar a diario directamente
    # Nunca cargar todo en memoria
    print(f"\n🔄 Procesando {len(batch_files)} batches (streaming, sin cargar todo en RAM)...")
    print(f"   (Si falla, los batches quedan en {temp_dir} para resumir)")
    
    # Diccionario para acumular por fecha: {date: [tone_values]}
    daily_data = {}
    
    for i, f in enumerate(batch_files):
        try:
            chunk = pd.read_parquet(f)
            
            # Procesar este batch directamente
            if 'SQLDATE' in chunk.columns and 'AvgTone' in chunk.columns:
                for _, row in chunk.iterrows():
                    date_val = row['SQLDATE']
                    tone_val = row['AvgTone']
                    
                    if pd.notna(date_val) and pd.notna(tone_val):
                        if date_val not in daily_data:
                            daily_data[date_val] = []
                        daily_data[date_val].append(tone_val)
            
            del chunk
            gc.collect()
            
            # Progreso cada 5 batches
            if (i + 1) % 5 == 0:
                print(f"   Procesado {i+1}/{len(batch_files)} batches, {len(daily_data)} días únicos")
                
        except Exception as e:
            print(f"   ⚠️  Error leyendo batch {i}: {e}")
    
    # Convertir a DataFrame agregado por día
    print(f"   Agregando {len(daily_data)} días...")
    daily_rows = []
    for date_val, tones in daily_data.items():
        daily_rows.append({
            'date': pd.to_datetime(str(date_val), format='%Y%m%d', errors='coerce'),
            'tone_mean': np.mean(tones),
            'tone_std': np.std(tones) if len(tones) > 1 else 0,
            'tone_count': len(tones),
            'article_count': len(tones)
        })
    
    del daily_data
    gc.collect()
    
    df_daily = pd.DataFrame(daily_rows)
    df_daily = df_daily.dropna(subset=['date'])
    df_daily = df_daily.sort_values('date').reset_index(drop=True)
    
    # Limpiar archivos temporales SOLO si todo salió bien
    print(f"   Limpiando {len(batch_files)} archivos temporales...")
    for f in batch_files:
        try:
            f.unlink()
        except:
            pass
    try:
        temp_dir.rmdir()
    except:
        pass
    
    print(f"✅ GDELT 1.0 completado: {len(df_daily):,} días con datos")
    return df_daily


# ============================================================================
# Método 2: Download GDELT 2.0 (2015-2025) - Datos Modernos
# ============================================================================

def download_gdelt_v2_batches(start_date, end_date, batch_days=7, temp_dir=None):
    """
    Descarga GDELT 2.0 en batches para evitar timeouts.
    ULTRA-OPTIMIZADO: 7 días por batch, solo columnas esenciales, pausas largas.
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio
    end_date : datetime
        Fecha de fin
    batch_days : int
        Tamaño del batch en días (default 7 = 1 semana, bajo consumo RAM)
    temp_dir : Path
        Directorio temporal para batches (si None, usa DATA_EXTERNAL)
    
    Returns
    -------
    pd.DataFrame
        Datos descargados de GDELT 2.0 (solo columnas esenciales)
    """
    import gc  # Garbage collector para liberar RAM
    
    print(f"\n🔄 Descargando GDELT 2.0 (GKG with Tone Scores)...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Estrategia: Batches de {batch_days} días - bajo consumo RAM")
    
    if temp_dir is None:
        temp_dir = DATA_EXTERNAL / 'temp_batches_v2'
    temp_dir.mkdir(exist_ok=True)
    
    gd = gdelt.gdelt(version=2)
    batch_files = []  # Lista de archivos temporales, NO DataFrames
    
    # Columnas que REALMENTE necesitamos (de ~27, solo 2)
    ESSENTIAL_COLS = ['DATE', 'V2Tone']
    
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
            
            # Si ya existe el archivo (descarga previa), skip
            if batch_file.exists():
                batch_files.append(batch_file)
                days_processed = (batch_end - current).days
                pbar.update(days_processed)
                current = batch_end + timedelta(days=1)
                continue
            
            try:
                # Forzar garbage collection ANTES de descargar
                gc.collect()
                
                date_range = [
                    current.strftime('%Y %m %d'),
                    batch_end.strftime('%Y %m %d')
                ]
                
                # Capturar stdout Y stderr para suprimir verbose output
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    df_batch = gd.Search(
                        date=date_range,
                        table='gkg',
                        coverage=False,
                        translation=False,
                        output='df'
                    )
                
                if df_batch is not None and len(df_batch) > 0:
                    # INMEDIATAMENTE filtrar a solo columnas esenciales
                    available_cols = [c for c in ESSENTIAL_COLS if c in df_batch.columns]
                    if available_cols:
                        df_small = df_batch[available_cols].copy()
                        del df_batch  # Liberar el DataFrame grande ASAP
                        gc.collect()
                        
                        # Guardar versión pequeña
                        df_small.to_parquet(batch_file, index=False)
                        batch_files.append(batch_file)
                        pbar.set_postfix({'filas': len(df_small), 'cols': len(available_cols)})
                        del df_small
                    else:
                        del df_batch
                    
                    gc.collect()
                    time.sleep(1)  # Pausa de 1 segundo entre batches
                
            except MemoryError:
                print(f"\n💥 MemoryError en {current.date()}. Saltando batch...")
                gc.collect()
                time.sleep(5)  # Pausa larga para recuperar
                
            except Exception as e:
                # Solo mostrar errores que no sean de memoria ni warnings de GDELT
                if 'MemoryError' not in str(e) and 'did not return data' not in str(e):
                    pass  # Silencioso para GDELT 2.0 (muchos días sin datos)
                gc.collect()
            
            # Avanzar al siguiente batch
            days_processed = (batch_end - current).days
            pbar.update(days_processed)
            current = batch_end + timedelta(days=1)
            
            # Pausa cada 5 batches
            if batch_count % 5 == 0:
                gc.collect()
                time.sleep(3)
    
    if len(batch_files) == 0:
        print("❌ No se descargó ningún dato de GDELT 2.0")
        return None
    
    # NUEVA ESTRATEGIA: Procesar batch por batch, agregar a diario directamente
    # Nunca cargar todo en memoria
    print(f"\n🔄 Procesando {len(batch_files)} batches (streaming, sin cargar todo en RAM)...")
    print(f"   (Si falla, los batches quedan en {temp_dir} para resumir)")
    
    # Diccionario para acumular por fecha: {date: [tone_values]}
    daily_data = {}
    
    for i, f in enumerate(batch_files):
        try:
            chunk = pd.read_parquet(f)
            
            # Procesar este batch directamente
            if 'DATE' in chunk.columns and 'V2Tone' in chunk.columns:
                for _, row in chunk.iterrows():
                    date_val = row['DATE']
                    tone_str = row['V2Tone']
                    
                    if pd.notna(date_val) and pd.notna(tone_str):
                        # Parsear fecha (formato YYYYMMDDHHMMSS)
                        try:
                            date_key = str(date_val)[:8]  # Solo YYYYMMDD
                            # Parsear tone (primer valor del string separado por comas)
                            tone_val = float(str(tone_str).split(',')[0])
                            
                            if date_key not in daily_data:
                                daily_data[date_key] = []
                            daily_data[date_key].append(tone_val)
                        except:
                            pass
            
            del chunk
            gc.collect()
            
            # Progreso cada 10 batches
            if (i + 1) % 10 == 0:
                print(f"   Procesado {i+1}/{len(batch_files)} batches, {len(daily_data)} días únicos")
                
        except Exception as e:
            print(f"   ⚠️  Error leyendo batch {i}: {e}")
    
    # Convertir a DataFrame agregado por día
    print(f"   Agregando {len(daily_data)} días...")
    daily_rows = []
    for date_val, tones in daily_data.items():
        daily_rows.append({
            'date': pd.to_datetime(str(date_val), format='%Y%m%d', errors='coerce'),
            'tone_mean': np.mean(tones),
            'tone_std': np.std(tones) if len(tones) > 1 else 0,
            'tone_count': len(tones),
            'article_count': len(tones)
        })
    
    del daily_data
    gc.collect()
    
    df_daily = pd.DataFrame(daily_rows)
    df_daily = df_daily.dropna(subset=['date'])
    df_daily = df_daily.sort_values('date').reset_index(drop=True)
    
    # Limpiar archivos temporales SOLO si todo salió bien
    print(f"   Limpiando {len(batch_files)} archivos temporales...")
    for f in batch_files:
        try:
            f.unlink()
        except:
            pass
    try:
        temp_dir.rmdir()
    except:
        pass
    
    print(f"✅ GDELT 2.0 completado: {len(df_daily):,} días con datos")
    return df_daily


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
    
    # Construir query SQL - AGREGADO DIRECTAMENTE EN EL SERVIDOR
    # Tabla: gdelt-bq.gdeltv2.gkg (Global Knowledge Graph)
    keywords_pattern = '|'.join(keywords)  # Regex OR pattern
    
    query = f"""
    SELECT 
        DATE_TRUNC(
            PARSE_DATE('%Y%m%d', SUBSTR(CAST(DATE AS STRING), 1, 8)), 
            DAY
        ) as date,
        AVG(CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64)) as tone_mean,
        STDDEV(CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64)) as tone_std,
        COUNT(*) as tone_count,
        COUNT(*) as article_count
    FROM 
        `gdelt-bq.gdeltv2.gkg`
    WHERE 
        DATE >= {start_date.strftime('%Y%m%d')}000000
        AND DATE <= {end_date.strftime('%Y%m%d')}235959
        AND REGEXP_CONTAINS(V2Themes, r'(?i){keywords_pattern}')
        AND V2Tone IS NOT NULL
    GROUP BY date
    ORDER BY date
    """
    
    print(f"\n📊 Ejecutando query BigQuery (agregación en servidor)...")
    print(f"   SQL: Filtrando y agregando por día en Google Cloud")
    print(f"   Esto es MUCHO más rápido que descargar millones de filas")
    
    try:
        # Ejecutar query
        df = client.query(query).to_dataframe()
        
        print(f"✅ Query completada: {len(df):,} días con datos")
        print(f"   Rango: {df['date'].min()} a {df['date'].max()}")
        
        # Convertir tone a escala [-1, 1] (GDELT usa -100 a +100)
        df['tone_mean'] = df['tone_mean'] / 100
        df['tone_std'] = df['tone_std'] / 100
        
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

def main(test_mode=False, use_bigquery=False):
    """
    Descarga y procesa datos de sentiment de GDELT 1.0 + 2.0.
    
    Parameters
    ----------
    test_mode : bool, default=False
        Si True, solo descarga 2 meses (1 de cada versión para testing)
    use_bigquery : bool, default=False
        Si True, usa BigQuery en vez de HTTP (MUCHO más rápido)
    """
    print("="*70)
    if use_bigquery:
        print("GDELT SENTIMENT DATA DOWNLOAD - BIGQUERY MODE")
    else:
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
    # MODO BIGQUERY: Descarga TODO en 1 sola query
    # ==============================================================
    if use_bigquery:
        print("\n" + "="*70)
        print("🚀 BIGQUERY MODE - Descarga rápida")
        print("="*70)
        print("   Descargando GDELT 2.0 (2015-2025) con agregación en servidor")
        
        df_v2_raw = download_gdelt_via_bigquery(start_v2, end_v2, KEYWORDS)
        df_v1_raw = None  # BigQuery solo tiene GDELT 2.0
        
        if df_v2_raw is not None and len(df_v2_raw) > 0:
            print(f"\n✅ BigQuery descargó {len(df_v2_raw):,} días")
        else:
            print("\n❌ BigQuery falló. Abortando.")
            return
    
    # ==============================================================
    # MODO HTTP: Descarga batch por batch (más lento pero sin setup)
    # ==============================================================
    else:
        # PASO 1: Descargar GDELT 1.0 (2000-2013)
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
        
        # PASO 2: Descargar GDELT 2.0 (2015-2025)
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
    
    # Los datos ya vienen agregados por día desde las funciones de descarga
    # Solo necesitamos combinar v1 y v2
    df_v1_daily = df_v1_raw  # Ya está en formato daily
    df_v2_daily = df_v2_raw  # Ya está en formato daily
    
    # Combinar v1 y v2
    daily_frames = [df for df in [df_v1_daily, df_v2_daily] if df is not None and len(df) > 0]
    
    if len(daily_frames) == 0:
        print("\n❌ No hay datos para combinar. Abortando.")
        return
    
    df_combined = pd.concat(daily_frames, ignore_index=True)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    print(f"\n✅ Combinado: {len(df_combined):,} días")
    # Manejar tanto datetime como date
    date_min = df_combined['date'].min()
    date_max = df_combined['date'].max()
    if hasattr(date_min, 'date'):
        date_min = date_min.date()
        date_max = date_max.date()
    print(f"   Rango: {date_min} a {date_max}")
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
    
    if df_v1_daily is not None and len(df_v1_daily) > 0:
        print(f"GDELT 1.0: {len(df_v1_daily):,} días")
    else:
        print(f"GDELT 1.0: No disponible")
    
    if df_v2_daily is not None and len(df_v2_daily) > 0:
        print(f"GDELT 2.0: {len(df_v2_daily):,} días")
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
    parser.add_argument(
        '--low-memory',
        action='store_true',
        help='Low memory mode: smaller batches, more pauses (for gaming while downloading)'
    )
    parser.add_argument(
        '--v1-only',
        action='store_true',
        help='Only download GDELT 1.0 (2000-2013)'
    )
    parser.add_argument(
        '--v2-only',
        action='store_true',
        help='Only download GDELT 2.0 (2015-2025)'
    )
    parser.add_argument(
        '--bigquery',
        action='store_true',
        help='Use BigQuery instead of HTTP (MUCH faster, requires credentials)'
    )
    
    args = parser.parse_args()
    
    # Si low-memory, ajustar parámetros globales
    if args.low_memory:
        print("🎮 MODO LOW-MEMORY: Batches pequeños, pausas largas")
        print("   Podés seguir jugando tranquilo mientras descarga")
        # Monkey-patch los valores por defecto (se pasan en main)
        import functools
        original_v1 = download_gdelt_v1_batches
        original_v2 = download_gdelt_v2_batches
        download_gdelt_v1_batches = functools.partial(original_v1, batch_months=1)
        download_gdelt_v2_batches = functools.partial(original_v2, batch_days=7)
    
    # Verificar si usar BigQuery
    if args.bigquery:
        print("\n🚀 MODO BIGQUERY ACTIVADO")
        print("   Verifying credentials...")
        import os
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set")
            print("   Set it with:")
            print("   $env:GOOGLE_APPLICATION_CREDENTIALS='path/to/credentials.json'")
            sys.exit(1)
        else:
            print(f"   ✅ Credentials: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    
    main(test_mode=args.test, use_bigquery=args.bigquery)
