.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/etl/ratios.py

test:
	pytest tests/etl/ -v

report:
	python src/etl/report.py

dashboard:
	@echo "Dashboard target will be configured later."

api:
	python src/etl/api.py

clean:
	rm -rf __pycache__ .pytest_cache
	rm -rf src/etl/__pycache__ tests/etl/__pycache__
