"""
Configuración automática de CUDA/GPU para modelos de Machine Learning.

Este módulo detecta y configura dispositivos GPU disponibles (NVIDIA, AMD, Apple Silicon)
para frameworks compatibles (PyTorch, TensorFlow, XGBoost, LightGBM).

Author: Grupo JLP - Taller de Programación UBA FCE
"""

import sys
import warnings
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CUDAConfig:
    """
    Configurador automático de GPU para diferentes frameworks de ML.
    
    Detecta hardware disponible y configura parámetros óptimos para:
    - PyTorch (CUDA, MPS para Apple Silicon)
    - TensorFlow (GPU)
    - XGBoost (gpu_hist)
    - LightGBM (gpu)
    
    Attributes:
        device_name (str): Nombre del dispositivo detectado
        device_type (str): Tipo de dispositivo ('cuda', 'mps', 'cpu')
        is_available (bool): True si GPU está disponible
        gpu_memory_gb (float): Memoria GPU disponible en GB (si aplica)
        framework_support (dict): Frameworks compatibles con GPU detectada
    """
    
    def __init__(self, verbose: bool = True):
        """
        Inicializar configurador y detectar hardware.
        
        Args:
            verbose: Si True, imprime información de detección
        """
        self.verbose = verbose
        self.device_name = "CPU"
        self.device_type = "cpu"
        self.is_available = False
        self.gpu_memory_gb = 0.0
        self.framework_support = {}
        
        # Detectar hardware
        self._detect_hardware()
        
        if self.verbose:
            self._print_summary()
    
    def _detect_hardware(self):
        """Detectar hardware GPU disponible."""
        # 1. Intentar PyTorch CUDA (NVIDIA)
        try:
            import torch
            if torch.cuda.is_available():
                self.is_available = True
                self.device_type = "cuda"
                self.device_name = torch.cuda.get_device_name(0)
                self.gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                self.framework_support['pytorch'] = True
                self.framework_support['xgboost'] = True
                self.framework_support['lightgbm'] = True
                return
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error detectando PyTorch CUDA: {e}")
        
        # 2. Intentar PyTorch MPS (Apple Silicon M1/M2/M3)
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.is_available = True
                self.device_type = "mps"
                self.device_name = "Apple Silicon GPU (MPS)"
                self.framework_support['pytorch'] = True
                # XGBoost y LightGBM no soportan MPS nativamente
                return
        except Exception as e:
            logger.warning(f"Error detectando MPS: {e}")
        
        # 3. Intentar TensorFlow GPU
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            if len(gpus) > 0:
                self.is_available = True
                self.device_type = "cuda"  # TF usa CUDA
                self.device_name = gpus[0].name
                self.framework_support['tensorflow'] = True
                return
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error detectando TensorFlow GPU: {e}")
        
        # 4. Fallback a CPU
        self.is_available = False
        self.device_type = "cpu"
        self.device_name = "CPU (No GPU detected)"
        self.framework_support = {'cpu_only': True}
    
    def _print_summary(self):
        """Imprimir resumen de detección de hardware."""
        print("=" * 80)
        print("CONFIGURACIÓN DE DISPOSITIVO GPU/CPU")
        print("=" * 80)
        
        if self.is_available:
            print(f"✓ GPU DETECTADA")
            print(f"  - Dispositivo: {self.device_name}")
            print(f"  - Tipo: {self.device_type.upper()}")
            if self.gpu_memory_gb > 0:
                print(f"  - Memoria: {self.gpu_memory_gb:.1f} GB")
            print(f"\n✓ FRAMEWORKS COMPATIBLES:")
            for fw, supported in self.framework_support.items():
                if supported:
                    print(f"  - {fw.capitalize()}: Sí")
        else:
            print(f"⚠ GPU NO DISPONIBLE - Usando CPU")
            print(f"  - Dispositivo: {self.device_name}")
            print(f"  - Modelos se entrenarán en CPU (más lento)")
        
        print("=" * 80 + "\n")
    
    def get_pytorch_device(self) -> str:
        """
        Obtener string de dispositivo para PyTorch.
        
        Returns:
            str: 'cuda', 'mps', o 'cpu'
        
        Example:
            >>> cuda_config = CUDAConfig()
            >>> device = torch.device(cuda_config.get_pytorch_device())
            >>> model.to(device)
        """
        if not self.framework_support.get('pytorch', False):
            return 'cpu'
        return self.device_type
    
    def get_xgboost_params(self) -> Dict[str, any]:
        """
        Obtener parámetros de GPU para XGBoost.
        
        Returns:
            dict: Parámetros para XGBRegressor/XGBClassifier
        
        Example:
            >>> cuda_config = CUDAConfig()
            >>> model = XGBRegressor(**cuda_config.get_xgboost_params())
        """
        if self.device_type == 'cuda':
            return {
                'tree_method': 'gpu_hist',
                'gpu_id': 0,
                'predictor': 'gpu_predictor'
            }
        else:
            return {
                'tree_method': 'hist',  # CPU optimizado
                'predictor': 'cpu_predictor'
            }
    
    def get_lightgbm_params(self) -> Dict[str, any]:
        """
        Obtener parámetros de GPU para LightGBM.
        
        Returns:
            dict: Parámetros para LGBMRegressor/LGBMClassifier
        
        Example:
            >>> cuda_config = CUDAConfig()
            >>> model = LGBMRegressor(**cuda_config.get_lightgbm_params())
        """
        if self.device_type == 'cuda':
            return {
                'device': 'gpu',
                'gpu_platform_id': 0,
                'gpu_device_id': 0
            }
        else:
            return {
                'device': 'cpu'
            }
    
    def get_tensorflow_config(self) -> Optional[any]:
        """
        Configurar TensorFlow para usar GPU con memory growth.
        
        Returns:
            tf.config o None si TF no está disponible
        
        Example:
            >>> cuda_config = CUDAConfig()
            >>> cuda_config.get_tensorflow_config()  # Auto-configura TF
        """
        try:
            import tensorflow as tf
            
            if self.framework_support.get('tensorflow', False):
                # Habilitar memory growth para evitar OOM
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    
                    if self.verbose:
                        print("✓ TensorFlow GPU configurado con memory growth")
                
                return tf.config
            else:
                return None
        except ImportError:
            return None
        except Exception as e:
            logger.warning(f"Error configurando TensorFlow: {e}")
            return None
    
    def get_sklearn_params(self) -> Dict[str, any]:
        """
        Obtener parámetros de paralelización para scikit-learn.
        
        Returns:
            dict: Parámetros n_jobs para modelos sklearn
        
        Example:
            >>> cuda_config = CUDAConfig()
            >>> model = RandomForestRegressor(**cuda_config.get_sklearn_params())
        """
        # sklearn no usa GPU, pero podemos optimizar CPU
        import os
        n_cores = os.cpu_count() or 1
        
        return {
            'n_jobs': -1  # Usar todos los cores disponibles
        }
    
    def benchmark_device(self, size: int = 10000) -> Tuple[float, str]:
        """
        Hacer benchmark simple de GPU vs CPU.
        
        Args:
            size: Tamaño de matriz para benchmark
        
        Returns:
            tuple: (tiempo_segundos, dispositivo_usado)
        """
        try:
            import torch
            import time
            
            device = torch.device(self.get_pytorch_device())
            
            # Crear datos de prueba
            x = torch.randn(size, size)
            
            # Mover a device y medir
            start = time.time()
            x = x.to(device)
            _ = torch.matmul(x, x)
            if device.type == 'cuda':
                torch.cuda.synchronize()
            elapsed = time.time() - start
            
            return elapsed, str(device)
        
        except Exception as e:
            logger.warning(f"Error en benchmark: {e}")
            return 0.0, "error"
    
    def get_device_info(self) -> Dict[str, any]:
        """
        Obtener información completa del dispositivo.
        
        Returns:
            dict: Información detallada del hardware
        """
        return {
            'device_name': self.device_name,
            'device_type': self.device_type,
            'is_available': self.is_available,
            'gpu_memory_gb': self.gpu_memory_gb,
            'framework_support': self.framework_support
        }


# Instancia global para uso conveniente
_cuda_config_instance = None


def get_cuda_config(verbose: bool = True) -> CUDAConfig:
    """
    Obtener instancia singleton de CUDAConfig.
    
    Args:
        verbose: Si True, imprime información en primera llamada
    
    Returns:
        CUDAConfig: Configurador de CUDA singleton
    
    Example:
        >>> from utils.cuda_config import get_cuda_config
        >>> cuda = get_cuda_config()
        >>> device = cuda.get_pytorch_device()
    """
    global _cuda_config_instance
    
    if _cuda_config_instance is None:
        _cuda_config_instance = CUDAConfig(verbose=verbose)
    
    return _cuda_config_instance


# Funciones de conveniencia
def get_device() -> str:
    """Shortcut para obtener dispositivo PyTorch."""
    return get_cuda_config(verbose=False).get_pytorch_device()


def is_cuda_available() -> bool:
    """Shortcut para verificar si CUDA está disponible."""
    return get_cuda_config(verbose=False).is_available


def get_device_name() -> str:
    """Shortcut para obtener nombre del dispositivo."""
    return get_cuda_config(verbose=False).device_name


if __name__ == "__main__":
    # Test del módulo
    print("Testing CUDA Configuration Module\n")
    
    cuda = CUDAConfig(verbose=True)
    
    print("\nDevice Info:")
    import json
    print(json.dumps(cuda.get_device_info(), indent=2))
    
    print("\nXGBoost params:", cuda.get_xgboost_params())
    print("LightGBM params:", cuda.get_lightgbm_params())
    print("PyTorch device:", cuda.get_pytorch_device())
    
    if cuda.is_available:
        print("\nRunning benchmark...")
        time_taken, device = cuda.benchmark_device(5000)
        print(f"Benchmark: {time_taken:.4f}s on {device}")
