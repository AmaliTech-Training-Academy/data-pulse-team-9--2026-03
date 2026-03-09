#!/bin/bash
set -e
echo "=== DataPulse Setup ==="
if ! command -v docker; then echo "Install Docker"; exit 1; fi
if [ ! -f .env ]; then
  echo "DATABASE_URL=postgresql://datapulse:datapulse@db:5432/datapulse" > .env
  echo "SECRET_KEY=change-me" >> .env
fi
docker-compose up --build -d
sleep 10
echo "Running at http://localhost:8000"
