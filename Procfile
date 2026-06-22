web: gunicorn app:app --timeout 120 --workers 1 --bind 0.0.0.0:10000 --max-requests 1000 --max-requests-jitter 100 --worker-class sync
