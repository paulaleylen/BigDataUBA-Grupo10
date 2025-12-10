"""
Descarga y procesa datos de sentiment de noticias para commodities
Fuente: GDELT Project (Global Database of Events, Language, and Tone)
URL: https://www.gdeltproject.org/

GDELT analiza noticias globales en tiempo real y proporciona:
- Tone (sentiment): Escala -100 (muy negativo) a +100 (muy positivo)
- Article count: Número de artículos por tema
- Cobertura geográfica global

Alternative sources consideradas:
- NewsAPI ($449/month) - DESCARTADO (pago)
- Twitter API (rate limits severos) - DESCARTADO
- Reddit (commodity-related subreddits) - DESCARTADO (sesgo retail)
"""

import pandas as pd
import numpy as np
import requests
from pathlib import Path
import sys
from datetime import datetime, timedelta
from urllib.parse import quote
import time

# Agregar directorio src al path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / 'src'))

from config import EXTERNAL_DIR, logger

# Directorio para datos de sentiment
SENTIMENT_DIR = EXTERNAL_DIR / 'sentiment'
SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)

# GDELT API endpoints
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TV_API = "https://api.gdeltproject.org/api/v2/tv/tv"

# Keywords para búsqueda de commodities
# Usar términos en inglés (GDELT tiene mejor cobertura)
COMMODITY_KEYWORDS = {
    'soybeans': 'soybean OR soybeans OR "soy bean" OR "soy futures"',
    'corn': 'corn OR maize OR "corn futures"',
    'wheat': 'wheat OR "wheat futures"',
    'agriculture': 'agriculture OR farming OR crop OR harvest'
}


def download_gdelt_sentiment_timeframe(start_date, end_date, keywords, max_records=250):
    """
    Descarga datos de sentiment de GDELT para un período específico
    
    GDELT API limitations:
    - Max 250 records per query
    - Max 1 query per second (rate limit)
    - Free tier: Sin límite de queries diarias
    
    Args:
        start_date: datetime object
        end_date: datetime object  
        keywords: string con keywords de búsqueda
        max_records: int, máximo de registros por query (default 250)
        
    Returns:
        DataFrame con sentiment data o None si falla
    """
    
    # Formatear fechas para GDELT (YYYYMMDDHHMMSS)
    start_str = start_date.strftime("%Y%m%d%H%M%S")
    end_str = end_date.strftime("%Y%m%d%H%M%S")
    
    # Construir query parameters
    params = {
        'query': keywords,
        'mode': 'timelinevol',  # Timeline volume mode
        'format': 'json',
        'timespan': f'{start_str}-{end_str}',
        'maxrecords': max_records
    }
    
    try:
        logger.info(f"   Consultando GDELT: {start_date.date()} → {end_date.date()}")
        response = requests.get(GDELT_DOC_API, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # GDELT retorna datos en formato timeline
        if 'timeline' in data and len(data['timeline']) > 0:
            timeline = data['timeline'][0]['data']
            
            # Convertir a DataFrame
            df = pd.DataFrame(timeline)
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
            
            return df
        else:
            logger.warning(f"   Sin datos para {start_date.date()} → {end_date.date()}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"   Error en request GDELT: {e}")
        return None
    except Exception as e:
        logger.error(f"   Error procesando respuesta GDELT: {e}")
        return None


def download_gdelt_sentiment_full(commodity='soybeans', start_year=2015, end_year=2025):
    """
    Descarga sentiment data de GDELT para commodity específico
    
    GDELT tiene datos desde 2015 con buena cobertura.
    Para períodos anteriores, usar proxy de búsquedas de Google Trends.
    
    Args:
        commodity: str, commodity a buscar
        start_year: int, año inicial
        end_year: int, año final
        
    Returns:
        DataFrame con sentiment diario
    """
    
    logger.info("="*80)
    logger.info(f"DESCARGA GDELT SENTIMENT DATA: {commodity.upper()}")
    logger.info("="*80)
    
    keywords = COMMODITY_KEYWORDS.get(commodity, commodity)
    logger.info(f"\nKeywords: {keywords}")
    logger.info(f"Período: {start_year} → {end_year}")
    
    all_data = []
    
    # Iterar por meses (GDELT funciona mejor con queries de 1 mes)
    current_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    month_count = 0
    total_months = (end_year - start_year + 1) * 12
    
    while current_date <= end_date:
        # Calcular fin del mes
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        month_end = min(month_end, end_date)
        
        # Descargar datos del mes
        df_month = download_gdelt_sentiment_timeframe(
            start_date=current_date,
            end_date=month_end,
            keywords=keywords
        )
        
        if df_month is not None and len(df_month) > 0:
            all_data.append(df_month)
            logger.info(f"   ✓ {current_date.strftime('%Y-%m')}: {len(df_month)} registros")
        else:
            logger.warning(f"   ⚠️  {current_date.strftime('%Y-%m')}: Sin datos")
        
        month_count += 1
        
        # Avanzar al siguiente mes
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        # Rate limit: 1 query per second
        time.sleep(1.1)
        
        # Progress update cada 12 meses
        if month_count % 12 == 0:
            logger.info(f"\n   Progreso: {month_count}/{total_months} meses procesados")
    
    if not all_data:
        logger.error("\n❌ No se pudieron descargar datos de GDELT")
        return None
    
    # Combinar todos los meses
    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    logger.info(f"\n✓ Total de registros: {len(df_combined):,}")
    logger.info(f"  Período: {df_combined['date'].min()} → {df_combined['date'].max()}")
    
    return df_combined


def process_sentiment_features(df_raw):
    """
    Procesa datos raw de GDELT y crea features de sentiment
    
    GDELT proporciona:
    - volume: Número de artículos
    - tone: Sentiment promedio (-100 a +100)
    
    Args:
        df_raw: DataFrame con datos raw de GDELT
        
    Returns:
        DataFrame con features procesadas
    """
    
    logger.info("\n" + "="*80)
    logger.info("PROCESANDO SENTIMENT FEATURES")
    logger.info("="*80)
    
    # Agregar por día (GDELT puede tener múltiples registros por día)
    df_daily = df_raw.groupby(df_raw['date'].dt.date).agg({
        'volume': 'sum',      # Total de artículos
        'tone': 'mean'        # Sentiment promedio
    }).reset_index()
    
    df_daily['date'] = pd.to_datetime(df_daily['date'])
    df_daily = df_daily.set_index('date')
    
    # Renombrar columnas
    df_daily = df_daily.rename(columns={
        'volume': 'news_volume',
        'tone': 'news_sentiment'
    })
    
    # Normalizar sentiment a escala -1 a +1 (GDELT usa -100 a +100)
    df_daily['news_sentiment_normalized'] = df_daily['news_sentiment'] / 100
    
    # Calcular moving averages para suavizar ruido
    df_daily['news_sentiment_7d_ma'] = df_daily['news_sentiment_normalized'].rolling(window=7, min_periods=1).mean()
    df_daily['news_volume_7d_ma'] = df_daily['news_volume'].rolling(window=7, min_periods=1).mean()
    
    # Calcular cambios day-over-day
    df_daily['news_sentiment_change'] = df_daily['news_sentiment_normalized'].diff()
    df_daily['news_volume_change'] = df_daily['news_volume'].diff()
    
    # Señales de extremos (percentiles)
    df_daily['news_sentiment_percentile'] = (
        df_daily['news_sentiment_normalized']
        .rolling(window=252, min_periods=50)
        .apply(lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100, raw=False)
    )
    
    df_daily['news_extreme_positive'] = (df_daily['news_sentiment_percentile'] > 90).astype(int)
    df_daily['news_extreme_negative'] = (df_daily['news_sentiment_percentile'] < 10).astype(int)
    
    logger.info(f"\n✓ Features creadas: {len(df_daily.columns)}")
    logger.info(f"  - news_volume: Número de artículos")
    logger.info(f"  - news_sentiment_normalized: Sentiment (-1 a +1)")
    logger.info(f"  - news_sentiment_7d_ma: MA 7 días")
    logger.info(f"  - news_volume_7d_ma: MA 7 días")
    logger.info(f"  - news_sentiment_change: Cambio diario")
    logger.info(f"  - news_volume_change: Cambio diario")
    logger.info(f"  - news_sentiment_percentile: Percentil histórico")
    logger.info(f"  - news_extreme_positive: Señal extremo positivo")
    logger.info(f"  - news_extreme_negative: Señal extremo negativo")
    
    logger.info(f"\nEstadísticas de sentiment:")
    print(df_daily[['news_sentiment_normalized', 'news_volume']].describe())
    
    return df_daily


def main():
    """
    Proceso principal:
    1. Descargar datos de GDELT (2015-2025)
    2. Procesar y crear features de sentiment
    3. Guardar archivo CSV
    
    Nota: Para datos pre-2015, considerar:
    - Google Trends (proxy de interés)
    - Web scraping de archivos históricos de noticias
    - Sentiment analysis manual de headlines almacenados
    """
    
    logger.info("Iniciando descarga de sentiment data...")
    
    # Descargar datos de GDELT
    df_raw = download_gdelt_sentiment_full(
        commodity='soybeans',
        start_year=2015,
        end_year=2025
    )
    
    if df_raw is None:
        logger.error("❌ No se pudieron descargar datos. Terminando.")
        return
    
    # Procesar features
    df_features = process_sentiment_features(df_raw)
    
    # Guardar archivos
    logger.info("\n" + "="*80)
    logger.info("GUARDANDO ARCHIVOS")
    logger.info("="*80)
    
    # Archivo raw (backup)
    output_file_raw = SENTIMENT_DIR / 'gdelt_soybeans_raw.csv'
    df_raw.to_csv(output_file_raw, index=False)
    logger.info(f"\n✓ Raw data guardada: {output_file_raw}")
    logger.info(f"  {len(df_raw):,} registros")
    
    # Archivo procesado (features)
    output_file_features = SENTIMENT_DIR / 'sentiment_soybeans_daily.csv'
    df_features.to_csv(output_file_features)
    logger.info(f"\n✓ Features guardadas: {output_file_features}")
    logger.info(f"  {len(df_features):,} días")
    logger.info(f"  {len(df_features.columns)} features")
    
    logger.info("\n" + "="*80)
    logger.info("✅ PROCESO COMPLETADO EXITOSAMENTE")
    logger.info("="*80)
    logger.info(f"\nCobertura temporal:")
    logger.info(f"  Sentiment data: 2015-2025 ({len(df_features)} días)")
    logger.info(f"  Gap 2000-2014: Será NaN (imputación en pipeline)")
    logger.info(f"\nSiguiente paso:")
    logger.info(f"  Ejecutar notebook 2.7-sentiment-features.ipynb")


if __name__ == '__main__':
    main()
