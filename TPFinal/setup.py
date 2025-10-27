from setuptools import find_packages, setup

setup(
    name='commodities_project',
    version='0.1.0',
    packages=find_packages(),
    description='Base de datos de commodities + predictores para análisis cuantitativo',
    author='Grupo JLP',
    author_email='',
    url='https://github.com/paulaleylen/BigDataUBA-GrupoJLP',
    license='MIT',
    python_requires='>=3.9',
    install_requires=[
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'yfinance>=0.2.28',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0',
        'openpyxl>=3.1.0',
        'kaggle>=1.5.16',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'jupyter>=1.0.0',
            'ipykernel>=6.25.0',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
