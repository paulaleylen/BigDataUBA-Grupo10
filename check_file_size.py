#!/usr/bin/env python3
"""
Git pre-commit hook: Rechaza archivos mayores a 50MB
Instalar: copiar a .git/hooks/pre-commit y hacer chmod +x
"""
import subprocess
import sys
from pathlib import Path

MAX_SIZE_MB = 50
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

def main():
    # Obtener archivos staged
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=d'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return 0
    
    staged_files = result.stdout.strip().split('\n')
    
    for filepath in staged_files:
        if not filepath:
            continue
            
        path = Path(filepath)
        if not path.exists():
            continue
        
        size_bytes = path.stat().st_size
        
        if size_bytes > MAX_SIZE_BYTES:
            size_mb = size_bytes / (1024 * 1024)
            print(f"\n❌ ERROR: {filepath} ({size_mb:.1f} MB) supera {MAX_SIZE_MB} MB")
            print(f"Solución: git reset HEAD '{filepath}'\n")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
