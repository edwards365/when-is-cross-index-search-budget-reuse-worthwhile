.PHONY: setup build test smoke download-small baseline mechanism main-experiments analyze report

PYTHON ?= python

setup:
	$(PYTHON) -m pip install -e ".[analysis,test]"

build:
	cmake -S . -B build
	cmake --build build --config Release

test:
	$(PYTHON) -m pytest tests/python -q
	ctest --test-dir build -C Release --output-on-failure

smoke:
	$(PYTHON) scripts/data/generate_synthetic.py --name narrow_bridge --n 2000 --seed 7
	$(PYTHON) scripts/experiments/run_smoke.py --config configs/experiments/smoke.yaml

download-small:
	$(PYTHON) scripts/data/download.py --manifest configs/datasets/fashion_mnist.yaml

baseline:
	$(PYTHON) scripts/experiments/run_smoke.py --config configs/experiments/smoke.yaml

mechanism:
	$(PYTHON) scripts/experiments/run_mechanism.py --config configs/experiments/mechanism.yaml

main-experiments:
	@echo "Tier-gated: see reports/STATUS.md"

analyze:
	$(PYTHON) scripts/analysis/analyze_smoke.py

report:
	$(PYTHON) scripts/analysis/analyze_smoke.py --write-report

