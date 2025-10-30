web: python scripts/initial_bootstrap.py && gunicorn --bind 0.0.0.0:$PORT wsgi:application
worker: python -m src.stockhark.core.services.background_collector