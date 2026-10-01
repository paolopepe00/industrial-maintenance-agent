#!/usr/bin/env bash
# Uso (dalla root del repo): bash k8s/deploy.sh
set -euo pipefail
CLUSTER=imaint

# 0) vector_db serve nella build dell'agent (Dockerfile.agent lo copia)
[ -d vector_db ] || { echo "vector_db/ mancante: esegui prima 'python -m src.rag.ingest'"; exit 1; }

# 1) cluster
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --config k8s/kind-config.yaml

# 2) immagini -> caricate direttamente nei nodi kind (niente registry)
docker build -f docker/Dockerfile.cmms  -t imaint-cmms:local  .
docker build -f docker/Dockerfile.agent -t imaint-agent:local .
kind load docker-image imaint-cmms:local imaint-agent:local --name "$CLUSTER"

# 3) namespace + config + secret LangSmith dal .env (mai committato)
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-config.yaml
[ -f .env ] && kubectl -n imaint create secret generic langsmith-secret \
  --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -

# 4) workload
kubectl apply -f k8s/10-postgres.yaml
kubectl -n imaint rollout status statefulset/postgres --timeout=120s
kubectl apply -f k8s/20-cmms.yaml -f k8s/25-seed-job.yaml
kubectl -n imaint wait --for=condition=complete job/cmms-seed --timeout=180s
kubectl apply -f k8s/30-agent.yaml
kubectl -n imaint rollout status deployment/agent --timeout=180s

echo "OK -> agent: http://127.0.0.1:8110/docs | cmms: http://127.0.0.1:8111/docs"