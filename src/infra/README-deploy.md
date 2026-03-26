Deployment notes — HAPI FHIR on Fly.io + Supabase Postgres

Quick overview
- HAPI FHIR server runs from the official Docker image `hapiproject/hapi:v7.6.0`.
- Use Fly.io to host the HAPI container (free tier available).
- Use Supabase (free tier) to host a PostgreSQL database for non-FHIR app data.

Steps — Fly.io (HAPI)
1. Install `flyctl` and log in: `flyctl auth login`.
2. From this repo folder run:

```bash
cd src/infra
flyctl launch --name hapi-fhir-app --image hapiproject/hapi:v7.6.0 --port 8080
```

3. Set secrets (replace values from Supabase below):

```bash
flyctl secrets set NONFHIR_DB_HOST=db.lrigppqtqfztybxegils.supabase.co NONFHIR_DB_PORT=5432 NONFHIR_DB_NAME=postgres NONFHIR_DB_USER=postgres NONFHIR_DB_PASSWORD=<CS6440healt>
```

4. Deploy: `flyctl deploy --config fly.toml`

Steps — Supabase (Postgres for non-FHIR data)
1. Create a Supabase project at https://app.supabase.com (free tier).
2. In Project Settings → Database, note the connection string (host, db, user, password, port).
3. Use those values when setting Fly secrets above.

Configure HAPI to persist FHIR resources into Postgres

- HAPI (the JPA server) can store FHIR resources in a Postgres database using standard Spring Boot datasource properties.
- For Fly/Supabase set these secrets (replace values):

```bash
flyctl secrets set \
	SPRING_DATASOURCE_URL=jdbc:postgresql://<host>:5432/<database> \
	SPRING_DATASOURCE_USERNAME=<user> \
	SPRING_DATASOURCE_PASSWORD=<password> \
	SPRING_DATASOURCE_DRIVER_CLASS_NAME=org.postgresql.Driver \
	SPRING_JPA_HIBERNATE_DDL_AUTO=update \
	SPRING_JPA_DATABASE_PLATFORM=org.hibernate.dialect.PostgreSQLDialect
```

- Locally with `docker-compose` the HAPI service in this repo is already configured to use the `postgres` service (see `docker-compose.yaml`).
- On first run HAPI will create the schema (because `spring.jpa.hibernate.ddl-auto=update`). For production you may want a controlled migration strategy instead.


Notes & next steps
- The compose file `docker-compose.yaml` includes a local Postgres service for testing; use it with `docker-compose up`.
- If you want HAPI to use an external Postgres for FHIR persistence, additional HAPI datasource env and JDBC settings are required — I can add that if you want.
