.PHONY: help install data clean test format lint all

help:  ## Mostrar este mensaje de ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Instalar paquete en modo editable + dependencias
	pip install -e .
	pip install -r requirements-dev.txt

install-prod:  ## Instalar solo dependencias de producción
	pip install -e .

data:  ## Descargar todos los datos (commodities + predictors + features académicas)
	@echo "=== FASE 1: Datos Core ==="
	@echo "Descargando datos de commodities..."
	python -m src.data.download_commodities
	@echo ""
	@echo "Descargando predictores macro..."
	python -m src.data.download_predictors
	@echo ""
	@echo "Descargando datos climáticos..."
	python -m src.data.download_climate
	@echo ""
	@echo "=== FASE 2: Features Académicas ==="
	@echo "Descargando CFTC Commitments of Traders..."
	python -m src.data.download_cftc_cot
	@echo ""
	@echo "Descargando GDELT sentiment (puede tardar ~10min)..."
	python -m src.data.download_sentiment_gdelt
	@echo ""
	@echo "Descargando Baltic Dry Index..."
	python -m src.data.download_bdi
	@echo ""
	@echo "Descargando Crop Conditions (NASS)..."
	python -m src.data.download_crop_conditions
	@echo ""
	@echo "Descargando Government Stocks (USDA ERS)..."
	python -m src.data.download_government_stocks_ers
	@echo ""
	@echo "Descargando indicadores FRED..."
	python -m src.data.download_fred
	@echo ""
	@echo "=== FASE 3: Procesamiento Final ==="
	@echo "Procesando y consolidando datos..."
	python -m src.data.process

clean:  ## Limpiar datos intermedios y procesados
	@echo "Limpiando datos intermedios..."
	rm -rf data/interim/commodities/*
	rm -rf data/interim/predictors/*.csv
	rm -rf data/processed/*
	@echo "Limpieza completada"

clean-all:  ## Limpiar TODO (incluyendo raw data)
	@echo "¿Estás seguro? Esto eliminará TODOS los datos descargados (raw + interim + processed)"
	@echo "Presiona Ctrl+C para cancelar, Enter para continuar..."
	@read -r
	rm -rf data/raw/*
	rm -rf data/interim/*
	rm -rf data/processed/*
	@echo "Limpieza completa finalizada"

test:  ## Ejecutar tests unitarios
	pytest tests/ -v

test-cov:  ## Ejecutar tests con coverage report
	pytest tests/ --cov=src --cov-report=html --cov-report=term

format:  ## Formatear código con black
	black src/ tests/

format-check:  ## Verificar formato sin modificar
	black src/ tests/ --check

lint:  ## Ejecutar linting con flake8
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

lint-fix:  ## Corregir problemas de linting automáticamente
	autopep8 --in-place --aggressive --aggressive src/ tests/

all: clean install data test  ## Ejecutar pipeline completo (limpieza -> instalación -> datos -> tests)

notebook:  ## Iniciar Jupyter Lab
	jupyter lab

tree:  ## Mostrar estructura de carpetas
	tree -L 3 -I '__pycache__|*.pyc|*.egg-info'

requirements:  ## Generar requirements.txt desde environment
	pip freeze > requirements.txt
