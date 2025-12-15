@echo off
chcp 65001
set PYTHONIOENCODING=utf-8
python -m uvicorn ott_ad_builder.api:app --host 0.0.0.0 --port 4000 --reload
