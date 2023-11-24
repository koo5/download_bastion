#!/usr/bin/env bash

python3 -O `which uvicorn` main:app --proxy-headers --host 0.0.0.0 --port 6457  --workers 8 # --log-level trace $@

#python3 -O `which gunicorn` app/main.py  --proxy-headers --bind 0.0.0.0:7788 --workers 4 --worker-class uvicorn.workers.UvicornWorker --log-level trace $@
