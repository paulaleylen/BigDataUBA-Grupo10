"""
General utilities

This package contains general utility functions used across
the commodities project.
"""

from .cuda_config import (
    CUDAConfig,
    get_cuda_config,
    get_device,
    is_cuda_available,
    get_device_name
)

__all__ = [
    'CUDAConfig',
    'get_cuda_config',
    'get_device',
    'is_cuda_available',
    'get_device_name'
]
