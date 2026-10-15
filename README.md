# StockPilot — Inventory Management · DevOps Capstone (Session 21)

StockPilot is a small inventory management system for a warehouse or shop. It keeps track of every product
(SKU, category, supplier, unit price, quantity on hand, reorder level) and **audits every stock change**
(restock, sale, return, damage, correction). The dashboard highlights low-stock and out-of-stock items
and the total inventory value, so you know what to reorder before you run out.

The application is the vehicle; the capstone is the delivery pipeline that takes it from a laptop to a
monitored, autoscaling Kubernetes cluster on AWS.

```text
Developer ──git push──▶ GitHub ──▶ GitHub Actions
                                   ├─ pytest (17 tests) + Alembic check on PostgreSQL
                                   ├─ Vite frontend build
                                   ├─ Helm lint + Terraform validate
                                   ├─ docker build (tag = commit SHA)
                                   ├─ Trivy scan  (fails on fixable HIGH/CRITICAL)
                                   ├─ push → GHCR
                                   └─ helm upgrade --install → EKS
Terraform ──▶ AWS VPC (2 public + 2 private subnets, NAT) + EKS (managed node group)
                                   │
            ┌──────────── Ingress (ingress-nginx) ───────────┐
            │  /      → frontend (React + Nginx, 2 pods)     │
            │  /api   → backend  (FastAPI, 2–6 pods, HPA)    │
            └──────────────────── PostgreSQL (StatefulSet + PVC)
Prometheus ◀── ServiceMonitor ◀── /metrics      Grafana ◀── "StockPilot API" dashboard
```

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, responsive CSS, served by unprivileged Nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, prometheus-fastapi-instrumentator |
| Database | PostgreSQL 16 (`products`, `stock_movements`) |
| Tests | Pytest — 17 tests, isolated SQLite DB per test |
| Containers | Docker (non-root), multi-stage frontend build, Docker Compose |
| CI/CD | GitHub Actions → Trivy → GHCR (SHA tags) → Helm deploy |
| Infra | Terraform: VPC + EKS + EBS CSI driver |
| Platform | Kubernetes, Helm, ingress-nginx, HPA + metrics-server |
| Observability | kube-prometheus-stack (Prometheus + Grafana) |

---

## Repository layout

```text
.
├── backend/                  FastAPI app, Alembic migrations, pytest suite, Dockerfile
│   ├── app/                  main.py (routes) · models.py · schemas.py · db.py · config.py
│   ├── alembic/versions/     0001_create_inventory · 0002_seed_demo_products
│   └── tests/                conftest.py · test_platform.py · test_products.py · test_stock.py
├── frontend/                 React app (src/components/*), multi-stage Dockerfile, nginx template
├── docker-compose.yml        postgres + backend + frontend
├── helm/stockpilot/          Helm chart (Deployments, Services, StatefulSet, Ingress, HPA, ServiceMonitor)
├── k8s/                      namespace + EKS gp3 StorageClass
├── terraform/                AWS VPC + EKS (see terraform/README.md)
├── monitoring/               kube-prometheus-stack values + Grafana dashboard ConfigMap
├── troubleshooting/          deliberately broken manifests + fix
├── scripts/                  load-test.sh, proof/ (screenshot tooling used by CI)
├── docs/screenshots/         evidence for grading
└── .github/workflows/        ci-cd.yml (pipeline) · k8s-proof.yml (kind cluster evidence)
```

---

## API

Swagger UI: `http://localhost:8000/docs`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness — process is up |
| GET | `/ready` | readiness — database reachable |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/products?q=&category=&status=` | list / search / filter (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`) |
| GET | `/api/products/stats` | totals, units, inventory value, low/out-of-stock counts |
| GET | `/api/products/{id}` | one product |
| POST | `/api/products` | create (SKU unique, opening stock recorded as a movement) |
| PUT | `/api/products/{id}` | update details / price / reorder level |
| DELETE | `/api/products/{id}` | delete product and its history |
| POST | `/api/products/{id}/adjust` | stock in/out with a reason — cannot go below zero |
| GET | `/api/products/{id}/movements` | audit trail for one product |
| GET | `/api/movements?limit=` | latest movements (dashboard feed) |

Stock status is derived: `quantity == 0 → OUT_OF_STOCK`, `quantity ≤ reorder_level → LOW_STOCK`, otherwise `IN_STOCK`.

---

## Part A — Run locally

### Docker Compose (one command)

```bash
docker compose up --build
# UI       http://localhost:3000
# API      http://localhost:8000/docs
# Metrics  http://localhost:8000/metrics
docker compose down        # stop
docker compose down -v     # stop + delete the database volume
```

The backend container runs `alembic upgrade head` before starting, so the tables and 7 demo products exist on first boot.

### Without Docker

```bash
# backend (needs a PostgreSQL you can reach)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://stockpilot:stockpilot@localhost:5432/stockpilot'
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# frontend (second terminal) - Vite proxies /api to :8000
cd frontend && npm ci && npm run dev      # http://localhost:5173
```

## Part B — Tests

```bash
cd backend && pytest -v
```

`tests/conftest.py` points `DATABASE_URL` at a temporary SQLite file **before** the app is imported and recreates the
tables for every test, so tests never touch a real database. CI additionally runs the Alembic migrations up/down/up
against a real PostgreSQL service container.

## Part C — Docker

* `backend/Dockerfile` — `python:3.12-slim`, dependencies cached in their own layer, runs as UID **10001**.
* `frontend/Dockerfile` — **multi-stage**: `node:22-alpine` builds `dist/`, `nginxinc/nginx-unprivileged` serves it as UID **101** on port 8080.
  The `/api` upstream is injected at start-up through `BACKEND_URL` (`http://backend:8000` in Compose, the backend Service in Kubernetes).

## Part D — CI/CD (`.github/workflows/ci-cd.yml`)

Runs on every push / PR to `main`:

1. **backend-test** – `pytest -v` + Alembic migrations on a PostgreSQL service. A failing test stops the pipeline.
2. **frontend-build** – `npm ci && npm run build`.
3. **iac-validate** – `helm lint` (dev + prod values) and `terraform fmt/init/validate`.
4. **build-scan-push** (push to `main` only) – builds both images tagged with `${{ github.sha }}`, proves they run as non-root,
   scans them with **Trivy** (full report saved as an artifact; gate fails on fixable HIGH/CRITICAL), then pushes to
   `ghcr.io/<owner>/stockpilot-backend:<sha>` and `ghcr.io/<owner>/stockpilot-frontend:<sha>`.
5. **deploy-eks** – `helm upgrade --install` with the same SHA tags. Enabled by repository variable `DEPLOY_TO_EKS=true`.

`.github/workflows/k8s-proof.yml` runs after a green pipeline: it creates a **kind** cluster on the runner, installs
ingress-nginx, metrics-server and kube-prometheus-stack, deploys the Helm chart, drives load to trigger the HPA, runs
the troubleshooting labs and uploads every screenshot as the `proof-kubernetes` / `proof-compose` artifacts.

> **Security note:** `aquasecurity/trivy-action` is pinned to the commit SHA of v0.35.0 and Trivy to v0.69.3. In March 2026
> most trivy-action tags were force-pushed to malicious commits (CVE-2026-33634); pinning actions by SHA is the only
> reliable protection against a moved tag.

## Part E — Terraform (AWS)

See [`terraform/README.md`](terraform/README.md). Summary:

```bash
cd terraform
terraform init && terraform validate
terraform plan -out tfplan
terraform apply tfplan
$(terraform output -raw configure_kubectl)
...
terraform destroy
```

No credentials live in this repo: Terraform uses your AWS CLI profile; CI uses GitHub encrypted secrets.

## Part F — Kubernetes, Helm, Ingress, HPA, Monitoring

### On EKS (after `terraform apply`)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storageclass-gp3-eks.yaml

# platform add-ons
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
kubectl apply -f monitoring/grafana-dashboard-configmap.yaml

# the application (images from GHCR - make both packages public first)
helm upgrade --install stockpilot ./helm/stockpilot -n stockpilot \
  -f helm/stockpilot/values-prod.yaml \
  --set backend.image=ghcr.io/<you>/stockpilot-backend --set backend.tag=<commit-sha> \
  --set frontend.image=ghcr.io/<you>/stockpilot-frontend --set frontend.tag=<commit-sha>

kubectl get pods,svc,ingress,hpa -n stockpilot
helm list -n stockpilot
kubectl get svc -n ingress-nginx ingress-nginx-controller   # open the EXTERNAL-IP / hostname in a browser
```

Grafana: `kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80` → http://localhost:3000
(admin / `stockpilot-admin`) → dashboard **StockPilot API**.
Prometheus: `kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090` → Status → Targets.

HPA demo: `./scripts/load-test.sh` then `kubectl get hpa -n stockpilot -w`.

### Troubleshooting labs

| Lab | Apply | Symptom | Root cause |
|---|---|---|---|
| Broken image | `troubleshooting/broken-image.yaml` | `ErrImagePull` / `ImagePullBackOff` | tag does not exist |
| Broken Service | `troubleshooting/broken-service.yaml` | `kubectl get endpoints` → `<none>` | selector typo matches no pod labels; fix with `fixed-service.yaml` |

---

## Evidence

All screenshots are in [`docs/screenshots/`](docs/screenshots) — see [`docs/SUBMISSION.md`](docs/SUBMISSION.md)
for the rubric-by-rubric checklist.
