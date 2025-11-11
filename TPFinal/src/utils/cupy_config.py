"""
CuPy Configuration & GPU Acceleration Utilities
================================================

Módulo para configurar y verificar disponibilidad de CuPy para aceleración GPU.
Maneja automáticamente la carga de DLLs CUDA en Windows (conda environments).

Uso:
    from utils.cupy_config import get_cupy_config, CUPY_AVAILABLE
    
    # Opción 1: Configuración completa con diagnóstico
    cupy_config = get_cupy_config(verbose=True)
    if cupy_config['available']:
        import cupy as cp
        # usar CuPy normalmente
    
    # Opción 2: Variable global simple
    if CUPY_AVAILABLE:
        import cupy as cp
        # usar CuPy
    else:
        # usar CPU fallback

Autor: Grupo JLP - UBA FCE
Fecha: 2025-01-10
"""

import os
import sys
from pathlib import Path
import warnings


def _configure_cuda_dll_paths():
    """
    Configura paths de CUDA DLLs en Windows para conda environments.
    
    Debe ejecutarse ANTES de importar CuPy.
    
    Returns:
        list: Paths agregados exitosamente
    """
    if sys.platform != 'win32':
        return []  # Solo necesario en Windows
    
    python_exe = Path(sys.executable)
    conda_env_root = python_exe.parent  # De python.exe -> envs/ds/
    
    # Ubicaciones posibles de DLLs CUDA en conda
    cuda_paths = [
        conda_env_root / 'Library' / 'bin',  # Anaconda/Miniconda estándar
        conda_env_root / 'Lib' / 'site-packages' / 'nvidia' / 'cu13' / 'bin' / 'x86_64',
        conda_env_root / 'Lib' / 'site-packages' / 'nvidia' / 'cuda_runtime' / 'lib',
        conda_env_root / 'Lib' / 'site-packages' / 'nvidia' / 'cuda_nvrtc' / 'lib',
    ]
    
    paths_added = []
    for cuda_bin_path in cuda_paths:
        if cuda_bin_path.exists():
            # Método 1: Agregar al PATH (al principio)
            os.environ['PATH'] = str(cuda_bin_path) + os.pathsep + os.environ['PATH']
            
            # Método 2: Windows-specific - agregar al DLL search path (más efectivo)
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(str(cuda_bin_path))
                except (OSError, FileNotFoundError):
                    pass  # Puede fallar si el path ya está agregado
            
            paths_added.append(str(cuda_bin_path))
    
    return paths_added


def get_cupy_config(verbose=False):
    """
    Detecta y configura CuPy para aceleración GPU.
    
    Maneja automáticamente:
    - Configuración de DLL paths en Windows
    - Detección de GPU NVIDIA
    - Verificación de compatibilidad CUDA
    - Fallback a CPU en caso de error
    
    Args:
        verbose (bool): Si True, imprime diagnóstico detallado
        
    Returns:
        dict: Configuración con keys:
            - available (bool): Si CuPy está disponible
            - device (str): 'cuda' o 'cpu'
            - cuda_version (int): Versión CUDA (ej: 13000)
            - gpu_name (str): Nombre de GPU
            - gpu_memory_gb (float): Memoria GPU en GB
            - error (str): Mensaje de error si falló
    """
    config = {
        'available': False,
        'device': 'cpu',
        'cuda_version': None,
        'gpu_name': None,
        'gpu_memory_gb': None,
        'error': None
    }
    
    try:
        if verbose:
            print("=" * 80)
            print("CONFIGURACIÓN CuPy - GPU ACCELERATION")
            print("=" * 80)
            print(f"\n1. Sistema operativo: {sys.platform}")
            print(f"2. Python executable: {sys.executable}")
        
        # PASO 1: Configurar DLL paths en Windows
        if sys.platform == 'win32':
            if verbose:
                print(f"\n3. Configurando CUDA DLL paths (Windows)...")
            
            paths_added = _configure_cuda_dll_paths()
            
            if verbose:
                if paths_added:
                    print(f"   ✓ {len(paths_added)} path(s) agregados:")
                    for p in paths_added:
                        print(f"     - {p}")
                else:
                    print(f"   ⚠️  No se encontraron paths de CUDA DLLs")
                    print(f"   Verifica que cupy-cuda13x esté instalado:")
                    print(f"   → pip install cupy-cuda13x")
        
        # PASO 2: Importar CuPy
        if verbose:
            print(f"\n4. Importando CuPy...")
        
        import cupy as cp
        
        if verbose:
            print(f"   ✓ CuPy importado exitosamente")
        
        # PASO 3: Verificar acceso a GPU
        if verbose:
            print(f"\n5. Verificando acceso a GPU...")
        
        device = cp.cuda.Device()
        meminfo = device.mem_info
        
        # Test simple de operación
        test_array = cp.array([1.0, 2.0, 3.0])
        _ = test_array + 1.0
        
        # Configuración exitosa
        config['available'] = True
        config['device'] = 'cuda'
        config['cuda_version'] = cp.cuda.runtime.runtimeGetVersion()
        config['gpu_memory_gb'] = meminfo[1] / (1024**3)
        
        # Intentar obtener nombre de GPU (puede fallar en algunos sistemas)
        try:
            config['gpu_name'] = cp.cuda.runtime.getDeviceProperties(device.id)['name'].decode()
        except:
            config['gpu_name'] = f"GPU Device {device.id}"
        
        if verbose:
            print("\n" + "=" * 80)
            print("🚀 CuPy CONFIGURADO - GPU DISPONIBLE")
            print("=" * 80)
            print(f"   GPU: {config['gpu_name']}")
            print(f"   CUDA Version: {config['cuda_version']}")
            print(f"   GPU Memory: {config['gpu_memory_gb']:.2f} GB total")
            print(f"   Free Memory: {meminfo[0] / (1024**3):.2f} GB")
            print(f"   ✓ Test de operación GPU exitoso")
            print("=" * 80 + "\n")
        
        return config
    
    except ImportError as e:
        config['error'] = f"CuPy no instalado: {e}"
        if verbose:
            print("\n⚠️  CuPy no está instalado - usando CPU")
            print(f"\nPara habilitar aceleración GPU:")
            print(f"  1. Verificar CUDA driver: nvidia-smi")
            print(f"  2. Instalar CuPy: pip install cupy-cuda13x")
            print(f"\nError: {e}\n")
        return config
    
    except Exception as e:
        config['error'] = str(e)
        if verbose:
            print(f"\n⚠️  Error al configurar CuPy: {e}")
            print(f"   Fallback: operaciones usarán CPU")
            import traceback
            print("\nStack trace:")
            traceback.print_exc()
            print()
        return config


# Variable global para uso rápido
_cupy_config = get_cupy_config(verbose=False)
CUPY_AVAILABLE = _cupy_config['available']


def get_array_module(use_gpu=True):
    """
    Retorna numpy o cupy según disponibilidad y preferencia.
    
    Patrón común para código agnóstico GPU/CPU:
        xp = get_array_module(use_gpu=True)
        arr = xp.array([1, 2, 3])  # CuPy si GPU, NumPy si CPU
    
    Args:
        use_gpu (bool): Si True y CuPy disponible, retorna cupy. Sino numpy.
        
    Returns:
        module: cupy o numpy
    """
    if use_gpu and CUPY_AVAILABLE:
        import cupy
        return cupy
    else:
        import numpy
        return numpy


def to_cpu(array):
    """
    Convierte array CuPy a NumPy (mueve de GPU a CPU).
    Si ya es NumPy, retorna sin cambios.
    
    Args:
        array: CuPy array o NumPy array
        
    Returns:
        numpy.ndarray: Array en CPU
    """
    if CUPY_AVAILABLE:
        import cupy as cp
        if isinstance(array, cp.ndarray):
            return cp.asnumpy(array)
    return array


def to_gpu(array):
    """
    Convierte array NumPy a CuPy (mueve de CPU a GPU).
    Si CuPy no disponible, retorna NumPy sin cambios.
    
    Args:
        array: NumPy array o CuPy array
        
    Returns:
        cupy.ndarray o numpy.ndarray: Array en GPU si disponible
    """
    if CUPY_AVAILABLE:
        import cupy as cp
        if not isinstance(array, cp.ndarray):
            return cp.asarray(array)
        return array
    else:
        return array


if __name__ == '__main__':
    # Test del módulo
    print("Testing cupy_config.py...\n")
    
    config = get_cupy_config(verbose=True)
    
    print(f"\nConfig dict:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print(f"\nCUPY_AVAILABLE: {CUPY_AVAILABLE}")
    
    # Test array module
    xp = get_array_module(use_gpu=True)
    print(f"\nArray module: {xp.__name__}")
    
    arr = xp.array([1, 2, 3])
    print(f"Test array: {arr}")
    print(f"Array type: {type(arr)}")
    
    arr_cpu = to_cpu(arr)
    print(f"Array en CPU: {arr_cpu} (type: {type(arr_cpu).__name__})")
