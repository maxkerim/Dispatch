# Dispatch

## Local development

Start the API and PostgreSQL together with Docker Compose:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. To run it directly on the host
instead, start only PostgreSQL with `docker compose up -d db`, then run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `DATABASE_URL` to use different PostgreSQL credentials or a remote database.

Run the API and database tests with:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Run the local monitoring stack with:

```bash
docker compose up --build
```

Prometheus is available at `http://localhost:9090` and Grafana at
`http://localhost:3000` (`admin` / `admin`, local development only). Grafana
loads the Dispatch API dashboard automatically. The API metrics endpoint is
`/metrics`.

`/health` checks that the API process is running. `/ready` also checks the
PostgreSQL connection.

## Kubernetes

Create a Secret containing the connection URL before installing the Helm chart:

```bash
kubectl create secret generic dispatch-db \
	--from-literal=DATABASE_URL='postgresql+psycopg://user:password@postgres:5432/dispatch'
```

Set `database.existingSecret` and `database.secretKey` in `values.yaml` to use a
different Secret or key.

GitHub Actions runs linting and tests on pushes to `main` and pull requests. It
also builds the image, validates the Helm chart, deploys the API and PostgreSQL
to a temporary `kind` cluster, and checks `/ready`. After a successful
deployment on `main`, it publishes the image to GHCR with `sha-<commit>` and
`latest` tags.