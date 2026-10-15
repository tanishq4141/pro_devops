# Submission checklist — StockPilot (Inventory Management)

Legend: ✅ evidence already in `docs/screenshots/` · 🤖 produced automatically by GitHub Actions
(download the `proof-compose`, `proof-kubernetes` and `trivy-reports` artifacts from the run) · 🧑 you capture it

| Module | Requirement | Evidence |
|---|---|---|
| M1 | App running in browser | ✅ `01-app-dashboard.png`, `02-app-create-product.png`, `03-app-adjust-stock.png`, `04-app-low-stock-filter.png`, `05-app-mobile-responsive.png` |
| M1 | ≥4 REST endpoints, `/health` | ✅ `06-api-swagger-docs.png`, `07-api-swagger-try-stats.png`, `08-api-health-ready-metrics.png` |
| M1 | PostgreSQL table via Alembic | ✅ `11-postgres-alembic-tables.png` |
| M2 | `pytest -v` all passing (17 tests, SQLite test DB, `pytest.ini` + `conftest.py`) | ✅ `10-pytest-all-passing.png` |
| M1/M5 | Frontend production build | ✅ `12-frontend-build.png` |
| M3 | Public repo + ≥10 meaningful commits | 🧑 screenshot of `https://github.com/<you>/inventory-devops-capstone/commits/main` (14+ commits) |
| M4 | `docker compose up --build`, localhost:3000, non-root images | 🤖 `20-docker-compose-up-build.png`, `21-docker-compose-ps-nonroot.png`, `23-compose-localhost-3000-app.png` |
| M5 | Green pipeline | 🧑 Actions run URL + screenshot of the run graph |
| M5 | GHCR images with SHA tags | 🧑 screenshot of `https://github.com/<you>?tab=packages` → stockpilot-backend |
| M6 | Trivy in pipeline, fail on HIGH/CRITICAL | 🧑 screenshot of the "Trivy gate" step log · 🤖 `trivy-reports` artifact |
| M7 | `terraform plan`, AWS console VPC + EKS, `terraform destroy` | 🧑 run on your machine (see `terraform/README.md`) |
| M8 | `kubectl get pods`, `get svc`, `helm list`, app via Ingress | 🤖 `30-kubectl-get-pods.png`, `31-kubectl-get-svc-ingress.png`, `32-helm-list.png`, `33-ingress-stockpilot.local-app.png` (kind) — repeat on EKS for full marks |
| M8 | HPA | 🤖 `34-hpa-scale-out.png` |
| M9 | `/metrics`, Prometheus targets UP, Grafana panel | 🤖 `22-backend-metrics-endpoint.png`, `40-prometheus-scrape-status.png`, `prometheus-targets.png`, `prometheus-query.png`, `grafana-dashboard.png` |
| Extra | Troubleshooting labs | 🤖 `50-troubleshoot-imagepullbackoff.png`, `51-troubleshoot-service-no-endpoints.png` |
| M10 | README | ✅ `README.md` |

## Trivy write-up (M6) — fill in after the first pipeline run

> Trivy scanned both container images built in CI — `stockpilot-backend` (Debian-based `python:3.12-slim` plus the
> pip packages in `requirements.txt`) and `stockpilot-frontend` (Alpine-based `nginx-unprivileged` serving the static
> React build). It checks OS packages and language dependencies against public CVE databases. The pipeline gate only
> fails on **HIGH/CRITICAL vulnerabilities that already have a fix** (`ignore-unfixed: true`), because those are the
> ones we can act on by upgrading. Result: _<clean / N findings — e.g. "CVE-XXXX-YYYY in libssl, fixed in version Z,
> resolved by rebuilding on the latest base image">_.

## Live demo script (M10)

1. Change something visible, e.g. the heading in `frontend/src/App.jsx`.
2. `git commit -am "feat(ui): rename dashboard heading" && git push`.
3. Show Actions: tests → build → Trivy → push → deploy.
4. Show `kubectl get pods -n stockpilot -w` rolling to the new SHA tag and the new heading in the browser.
