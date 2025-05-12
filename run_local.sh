#!/bin/bash
export FLASK_ENV=development FLASK_APP=run.py DATABASE_URL="" && flask run --port=8000
