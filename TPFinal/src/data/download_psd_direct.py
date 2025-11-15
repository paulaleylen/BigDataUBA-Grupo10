"""
Descargador directo de archivos PSD ZIP

Estrategia definitiva: Descargar directamente el ZIP con TODOS los datos
desde los enlaces estáticos de PSD Online.

URL encontrada en el HTML:
/psdonline/downloads/psd_alldata_csv.zip

Autor: BigDataUBA-GrupoJLP
Fecha: Noviembre 2025
"""

import sys
from pathlib import Path
import requests
import zipfile
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import EXTERNAL_DIR, PSD_START_YEAR, PSD_END_YEAR

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('src.config')

# Directorios
MANUAL_PSD_DIR = EXTERNAL_DIR / 'psd_manual'
MANUAL_PSD_DIR.mkdir(parents=True, exist_ok=True)

# URLs de descarga directa
PSD_ZIP_URLS = {
    'all_csv': 'https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip',
    'all_raw': 'https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_raw.zip'
}


def download_psd_zip(url, output_filename):
    """
    Descarga archivo ZIP directamente
    
    Args:
        url: URL del ZIP
        output_filename: Nombre del archivo local
    
    Returns:
        Path del archivo descargado o None si falla
    """
    output_path = MANUAL_PSD_DIR / output_filename
    
    logger.info(f"\n{'='*80}")
    logger.info(f"DESCARGANDO: {output_filename}")
    logger.info(f"{'='*80}")
    logger.info(f"\nURL: {url}")
    
    try:
        logger.info("⏬ Iniciando descarga...")
        
        # Stream download para archivos grandes
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        total_mb = total_size / (1024 * 1024)
        
        logger.info(f"   Tamaño: {total_mb:.2f} MB")
        
        # Escribir en chunks
        downloaded = 0
        chunk_size = 8192
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Mostrar progreso cada 5 MB
                    if downloaded % (5 * 1024 * 1024) == 0 or downloaded == total_size:
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        logger.info(f"   Progreso: {progress:.1f}% ({downloaded/(1024*1024):.1f}/{total_mb:.1f} MB)")
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"\n✓ Descargado: {output_path.name} ({size_mb:.2f} MB)")
        
        return output_path
    
    except requests.RequestException as e:
        logger.error(f"\n❌ Error en descarga: {e}")
        if output_path.exists():
            output_path.unlink()  # Eliminar archivo parcial
        return None


def extract_soybean_data(zip_path):
    """
    Extrae datos de Soybeans del ZIP
    
    Args:
        zip_path: Path del archivo ZIP
    
    Returns:
        Path del CSV extraído o None si falla
    """
    logger.info(f"\n{'='*80}")
    logger.info("EXTRAYENDO DATOS DE SOYBEANS")
    logger.info(f"{'='*80}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Listar contenido
            file_list = zip_ref.namelist()
            logger.info(f"\nArchivos en ZIP: {len(file_list)}")
            
            # Buscar archivo de soybeans
            soybean_files = [f for f in file_list if 'soybean' in f.lower() or 'oilseed' in f.lower()]
            
            if not soybean_files:
                logger.warning("⚠️  No se encontró archivo específico de Soybeans")
                logger.info("   Intentando extraer archivo principal de commodities...")
                
                # Buscar archivo principal que contenga todos los commodities
                main_files = [f for f in file_list if 'psd' in f.lower() and f.endswith('.csv')]
                
                if main_files:
                    main_file = main_files[0]
                    logger.info(f"   Extrayendo: {main_file}")
                    
                    zip_ref.extract(main_file, MANUAL_PSD_DIR)
                    extracted_path = MANUAL_PSD_DIR / main_file
                    
                    # Renombrar
                    output_path = MANUAL_PSD_DIR / "psd_alldata.csv"
                    extracted_path.rename(output_path)
                    
                    size_mb = output_path.stat().st_size / (1024 * 1024)
                    logger.info(f"   ✓ Extraído: {output_path.name} ({size_mb:.2f} MB)")
                    
                    # Filtrar solo Soybeans
                    logger.info("\n   Filtrando datos de Soybeans...")
                    df = pd.read_csv(output_path)
                    
                    logger.info(f"   Total registros: {len(df):,}")
                    logger.info(f"   Columnas: {list(df.columns)}")
                    
                    # Filtrar por commodity
                    if 'Commodity_Description' in df.columns:
                        df_soy = df[df['Commodity_Description'].str.contains('Soybean', case=False, na=False)]
                    elif 'Commodity' in df.columns:
                        df_soy = df[df['Commodity'].str.contains('Soybean', case=False, na=False)]
                    elif 'commodity_description' in df.columns:
                        df_soy = df[df['commodity_description'].str.contains('Soybean', case=False, na=False)]
                    else:
                        logger.warning(f"   ⚠️  No se encontró columna de Commodity. Columnas disponibles: {list(df.columns)}")
                        logger.info(f"   Guardando archivo completo para análisis manual...")
                        return output_path
                    
                    logger.info(f"   Registros de Soybeans: {len(df_soy):,}")
                    
                    # Guardar filtrado
                    output_soy = MANUAL_PSD_DIR / "psd_soybeans_all.csv"
                    df_soy.to_csv(output_soy, index=False)
                    
                    size_mb = output_soy.stat().st_size / (1024 * 1024)
                    logger.info(f"   ✓ Filtrado guardado: {output_soy.name} ({size_mb:.2f} MB)")
                    
                    return output_soy
                else:
                    logger.error("❌ No se encontró archivo CSV principal en el ZIP")
                    return None
            
            else:
                # Extraer archivo específico de soybeans
                soybean_file = soybean_files[0]
                logger.info(f"\n   Extrayendo: {soybean_file}")
                
                zip_ref.extract(soybean_file, MANUAL_PSD_DIR)
                extracted_path = MANUAL_PSD_DIR / soybean_file
                
                # Renombrar
                output_path = MANUAL_PSD_DIR / "psd_soybeans_all.csv"
                if extracted_path != output_path:
                    extracted_path.rename(output_path)
                
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"   ✓ Extraído: {output_path.name} ({size_mb:.2f} MB)")
                
                return output_path
    
    except Exception as e:
        logger.error(f"\n❌ Error al extraer: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Pipeline de descarga directa
    """
    logger.info("="*80)
    logger.info("DESCARGA DIRECTA DE PSD ZIP")
    logger.info("="*80)
    logger.info(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Estrategia: Descarga directa del archivo ZIP consolidado")
    logger.info(f"Directorio: {MANUAL_PSD_DIR.absolute()}")
    logger.info("")
    
    # Verificar si ya existe CSV procesado
    existing_csv = MANUAL_PSD_DIR / "psd_soybeans_all.csv"
    if existing_csv.exists():
        logger.warning(f"⚠️  ARCHIVO EXISTENTE: {existing_csv.name}")
        size_mb = existing_csv.stat().st_size / (1024 * 1024)
        logger.info(f"   Tamaño: {size_mb:.2f} MB")
        logger.info(f"\n   Para re-descargar, eliminar el archivo")
        logger.info(f"   O ejecutar: python src/data/process_manual_psd.py")
        return 0
    
    # Paso 1: Descargar ZIP
    zip_url = PSD_ZIP_URLS['all_csv']
    zip_filename = "psd_alldata_csv.zip"
    
    zip_path = download_psd_zip(zip_url, zip_filename)
    
    if not zip_path:
        logger.error("\n❌ Descarga del ZIP falló")
        return 1
    
    # Paso 2: Extraer datos de Soybeans
    csv_path = extract_soybean_data(zip_path)
    
    if not csv_path:
        logger.error("\n❌ Extracción falló")
        return 1
    
    # Resumen
    logger.info("\n" + "="*80)
    logger.info("✅ DESCARGA Y EXTRACCIÓN EXITOSA")
    logger.info("="*80)
    logger.info(f"\n📁 Archivo CSV: {csv_path.absolute()}")
    logger.info(f"\n🚀 SIGUIENTE PASO:")
    logger.info(f"   python src/data/process_manual_psd.py")
    logger.info("")
    
    return 0


if __name__ == "__main__":
    exit(main())
