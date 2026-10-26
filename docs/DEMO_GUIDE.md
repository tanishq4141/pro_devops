# StockPilot — Run, Screenshot & Video Guide

A step-by-step script for taking every screenshot the rubric (`GRADING.md`) asks for and recording the demo video.
Do the parts in order; each part lists the exact screenshot file names to save in `docs/screenshots/`
so they slot straight into the PPT.

**Tools:** Docker Desktop, kubectl, helm, kind, terraform, AWS CLI, gh — all already installed on this Mac.

**Screenshots on macOS:** `Cmd + Shift + 4` then `Space` then click a window → saves a PNG of just that window to the Desktop.
**Screen recording:** `Cmd + Shift + 5` → *Record Entire Screen* (or *Record Selected Portion*) → *Options* → choose
*Microphone* if you want to narrate → *Record*. Stop from the menu-bar ⏹ icon. Saves a `.mov` to the Desktop.

Tip: before recording, make the terminal font big (`Cmd +` a few times) and close unrelated tabs/notifications.

---

## Part 0 — One-time prep (2 min)

```bash
cd ~/code/pro_devops
open -a Docker                 # wait until the whale icon says "Docker Desktop is running"
docker info >/dev/null && echo "docker OK"
```

---

## Part 1 — Application with Docker Compose (M1, M4)

```bash
docker compose up --build
```

Wait until you see `Uvicorn running on http://0.0.0.0:8000`.

| # | What to capture | Save as |
|---|---|---|
| 1 | The terminal running `docker compose up --build` (all 3 services started) | `20-docker-compose-up-build.png` |
| 2 | New terminal: `docker compose ps` (3 services, healthy) | `21-docker-compose-ps.png` |
| 3 | `docker compose exec backend id` and `docker compose exec frontend id` → `uid=10001` / `uid=101` (non-root) | `21b-nonroot.png` |
| 4 | Browser <http://localhost:3000> — dashboard with KPIs | `23-compose-localhost-3000-app.png` |
| 5 | Click **Add product**, fill it in, save | `02-app-create-product.png` |
| 6 | Click **Adjust stock** on a product (restock / sale) | `03-app-adjust-stock.png` |
| 7 | Filter by **Low stock** | `04-app-low-stock-filter.png` |
| 8 | <http://localhost:8000/docs> — Swagger list of endpoints | `06-api-swagger-docs.png` |
| 9 | <http://localhost:8000/metrics> | `22-backend-metrics-endpoint.png` |

Database proof (M1 — Alembic table):

```bash
docker compose exec postgres psql -U stockpilot -d stockpilot -c '\dt' -c 'select * from alembic_version;'
```

→ save as `11-postgres-alembic-tables.png`.

Stop with `Ctrl + C`, then `docker compose down`.

---

## Part 2 — Tests (M2)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
deactivate; cd ..
```

→ screenshot showing **17 passed** → `10-pytest-all-passing.png`.

---

## Part 3 — Git & GitHub (M3)

Open <https://github.com/tanishq4141/pro_devops/commits/main> → screenshot showing ≥ 10 commits → `13-git-commits.png`.
Make sure the repo is **public** (Settings → General → Danger Zone → Change visibility) or the instructor has access.

---

## Part 4 — CI/CD + Trivy + GHCR (M5, M6)

1. Open <https://github.com/tanishq4141/pro_devops/actions> → click the latest **StockPilot CI/CD** run.
2. Screenshot the run graph with all jobs green → `14-actions-green-pipeline.png`. Copy the run URL for the submission form.
3. Click the job **Build, Trivy scan, push to GHCR** → expand **Trivy gate - backend** and **Trivy gate - frontend**
   → screenshot → `15-trivy-gate.png`.
4. Open <https://github.com/tanishq4141?tab=packages> → click **stockpilot-backend** → screenshot showing the
   tag = commit SHA → `16-ghcr-sha-tags.png`. Do the same for **stockpilot-frontend**.
5. **Make both packages public** (package → *Package settings* → *Change visibility* → Public) — Kubernetes on EKS
   needs this to pull them.
6. After the CI run is green, the **Kubernetes proof (kind)** workflow starts automatically. When it finishes, open it
   and download the `proof-compose` and `proof-kubernetes` artifacts — they contain ready-made screenshots for
   M4, M8 and M9 (pods, svc, helm list, HPA, Prometheus targets, Grafana). Use them as backup.

Trivy write-up (paste into the PPT / form): see `docs/SUBMISSION.md` → *Trivy write-up*.

---

## Part 5 — Kubernetes + Helm + Monitoring on your laptop with kind (M8, M9)

This is free and is what you can show live. (Part 6 repeats it on AWS EKS for full marks.)

```bash
# 1. cluster (port 80 on your Mac → ingress)
kind create cluster --name stockpilot --config scripts/proof/kind-config.yaml

# 2. images built locally and loaded into kind
docker build -t stockpilot-backend:demo ./backend
docker build -t stockpilot-frontend:demo ./frontend
kind load docker-image stockpilot-backend:demo stockpilot-frontend:demo --name stockpilot

# 3. platform add-ons
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/kind/deploy.yaml
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system \
  --set 'args={--kubelet-insecure-tls}' --wait
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml --wait --timeout 10m
kubectl apply -f monitoring/grafana-dashboard-configmap.yaml
kubectl wait -n ingress-nginx --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=180s

# 4. the app
kubectl apply -f k8s/namespace.yaml
helm upgrade --install stockpilot ./helm/stockpilot -n stockpilot \
  -f helm/stockpilot/values-dev.yaml \
  --set backend.image=stockpilot-backend --set backend.tag=demo --set backend.pullPolicy=Never \
  --set frontend.image=stockpilot-frontend --set frontend.tag=demo --set frontend.pullPolicy=Never \
  --wait --timeout 10m

# 5. hostname for the Ingress (asks for your Mac password)
echo "127.0.0.1 stockpilot.local" | sudo tee -a /etc/hosts
```

| # | Command / page | Save as |
|---|---|---|
| 1 | `kubectl get pods -n stockpilot -o wide` (all **Running**, 2+ backend, 2+ frontend) | `30-kubectl-get-pods.png` |
| 2 | `kubectl get svc,ingress -n stockpilot` | `31-kubectl-get-svc-ingress.png` |
| 3 | `helm list -n stockpilot` | `32-helm-list.png` |
| 4 | Browser <http://stockpilot.local> (app through the Ingress) | `33-ingress-stockpilot.local-app.png` |
| 5 | `kubectl get hpa -n stockpilot` before load | `34a-hpa-before.png` |

**HPA demo** — terminal A: `kubectl get hpa -n stockpilot -w` · terminal B: `./scripts/load-test.sh`
→ after ~1–2 min replicas go from 2 → more → `34-hpa-scale-out.png`.

**Prometheus** (new terminal, leave running):

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

<http://localhost:9090/targets> → find `stockpilot` → **UP** → `40-prometheus-targets.png`.
Graph tab → query `sum(rate(http_requests_total[1m])) by (handler)` → `41-prometheus-query.png`.

**Grafana** (another terminal):

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
```

<http://localhost:3001> → login `admin` / `stockpilot-admin` → Dashboards → **StockPilot API**
(click around the app at stockpilot.local first so the panels have data) → `42-grafana-dashboard.png`.

`/metrics` from inside the cluster:

```bash
kubectl port-forward -n stockpilot svc/stockpilot-backend 8000:8000 &
curl -s localhost:8000/metrics | head -30
```

→ `22b-k8s-metrics-curl.png`.

**Troubleshooting labs (bonus):**

```bash
kubectl apply -f troubleshooting/broken-image.yaml   && kubectl get pods -n stockpilot   # ImagePullBackOff
kubectl apply -f troubleshooting/broken-service.yaml && kubectl get endpoints -n stockpilot  # <none>
kubectl apply -f troubleshooting/fixed-service.yaml  && kubectl get endpoints -n stockpilot  # now has IPs
kubectl delete -f troubleshooting/ --ignore-not-found
```

→ `50-troubleshoot-imagepullbackoff.png`, `51-troubleshoot-service-no-endpoints.png`.

Clean up when done: `kind delete cluster --name stockpilot`.

---

## Part 6 — Terraform on AWS + EKS (M7, and M8 on real cloud)

**Cost warning:** EKS + NAT gateway costs roughly US$0.20–0.30 per hour. Do this in one sitting and **always finish
with `terraform destroy`**.

```bash
aws configure                         # your own access key, region ap-south-1 (never commit keys)
aws sts get-caller-identity           # confirms you are logged in

cd terraform
cp terraform.tfvars.example terraform.tfvars    # edit if you want another region/name
terraform init
terraform validate
terraform plan -out tfplan            # 📸 17-terraform-plan.png  (scroll to "Plan: N to add")
terraform apply tfplan                # ~15–20 min  📸 18-terraform-apply.png
$(terraform output -raw configure_kubectl)
kubectl get nodes                     # 📸 19-eks-nodes.png
cd ..
```

AWS Console (region **ap-south-1 / Mumbai**):
VPC → *Your VPCs* + *Subnets* (2 public + 2 private) → `19a-aws-vpc.png`; EKS → *Clusters* → `stockpilot-eks` → *Compute* tab
(node group) → `19b-aws-eks.png`.

Then deploy exactly as in README **Part F** (ingress-nginx, metrics-server, kube-prometheus-stack, then the chart with
your GHCR images and the commit SHA from Part 4) and repeat the Part 5 screenshots with an `-eks` suffix. The app URL is
the `EXTERNAL-IP` of `kubectl get svc -n ingress-nginx ingress-nginx-controller`.

Optional auto-deploy from CI: in GitHub → Settings → Secrets and variables → Actions add secrets `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY` and variable `DEPLOY_TO_EKS=true`. Every push to `main` then runs **Deploy to EKS with Helm**.

**Tear down (mandatory):**

```bash
helm uninstall stockpilot -n stockpilot
helm uninstall ingress-nginx -n ingress-nginx     # removes the AWS load balancer first
cd terraform && terraform destroy                 # 📸 19c-terraform-destroy.png ("Destroy complete!")
```

---

## Part 7 — The demo video (M10, 5–8 minutes)

Record with `Cmd + Shift + 5`. Suggested script — prepare everything (cluster running, browser tabs open) **before**
pressing record:

| Time | Show | Say |
|---|---|---|
| 0:00 | README on GitHub | "StockPilot is an inventory system; this project is its DevOps pipeline." |
| 0:30 | Repo folders in VS Code | One line per folder: backend, frontend, docker, helm, terraform, monitoring, workflows. |
| 1:00 | Browser localhost:3000 / stockpilot.local | Add a product, adjust stock, filter low stock. |
| 2:00 | Terminal `pytest -v` | "17 tests on an isolated SQLite DB." |
| 2:30 | `kubectl get pods,svc,ingress,hpa -n stockpilot` + `helm list -n stockpilot` | Replicas, ClusterIP services, ingress routing `/` and `/api`. |
| 3:15 | **Live change:** edit the heading in `frontend/src/App.jsx`, then `git commit -am "feat(ui): rename dashboard heading" && git push` | "Every push to main triggers the pipeline." |
| 3:45 | GitHub Actions run | tests → frontend build → helm/terraform checks → build → Trivy → push to GHCR (→ deploy). |
| 5:00 | GHCR package page | Tag equals the commit SHA. |
| 5:30 | HPA load test (`kubectl get hpa -w`) | Pods scale out under load. |
| 6:15 | Prometheus targets UP, Grafana dashboard | Requests, latency, error-rate panels. |
| 7:00 | Browser refresh | New heading visible (on kind: rebuild with `docker build`, `kind load`, `helm upgrade --set frontend.tag=<new>`; on EKS the pipeline does it). |

Export: QuickTime → *File → Export As → 1080p* to keep the file small. If the file is too big for the submission
form, upload to Google Drive / YouTube (unlisted) and paste the link.

---

## Part 8 — Building the PPT

Suggested slides (one screenshot per slide, a one-line caption on each):

1. Title — StockPilot · DevOps Capstone · your name
2. Architecture diagram (copy the ASCII diagram from README, or redraw it)
3. M1 App — dashboard, create product, adjust stock, Swagger
4. M1 DB — Alembic tables
5. M2 Tests — pytest 17 passed
6. M3 Git — commit history
7. M4 Docker — compose up, compose ps, non-root ids, localhost:3000
8. M5 CI/CD — green Actions run graph
9. M6 Trivy — gate output + 3-sentence write-up
10. M5 GHCR — packages with SHA tags
11. M7 Terraform — plan, AWS VPC, AWS EKS, destroy
12. M8 Kubernetes — pods, svc/ingress, helm list, app via ingress, HPA
13. M9 Observability — /metrics, Prometheus targets UP, Grafana dashboard
14. Troubleshooting labs
15. Demo video link + GitHub repo link
16. Learnings / challenges (e.g. "Trivy gate failed on CVEs inside pip's vendored libraries — fixed by removing pip from the runtime image")
