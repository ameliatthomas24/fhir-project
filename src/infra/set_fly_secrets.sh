#!/usr/bin/env bash
# Example script to set Fly secrets for Postgres and HAPI JDBC (no credentials included)
set -euo pipefail

echo "Replace the <> placeholders and run this from src/infra"

flyctl secrets set \
  NONFHIR_DB_HOST=db.lrigppqtqfztybxegils.supabase.co \
  NONFHIR_DB_PORT=5432 \
  NONFHIR_DB_NAME=postgres \
  NONFHIR_DB_USER=postgres \
  NONFHIR_DB_PASSWORD=CS6440healt \
  SPRING_DATASOURCE_URL=jdbc:postgresql://db.lrigppqtqfztybxegils.supabase.co:5432/postgres \
  SPRING_DATASOURCE_USERNAME=postgres \
  SPRING_DATASOURCE_PASSWORD=CS6440healt

echo "Secrets set (example). Deploy with: flyctl deploy --config fly.toml"
