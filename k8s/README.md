# Kubernetes (kind) – industrial-maintenance-agent

```bash
bash k8s/deploy.sh
curl -s localhost:8110/chat -H 'content-type: application/json' \
  -d '{"message":"Stato della pompa P-102?","thread_id":"t1"}'
```

## Note
- **Ollama** resta su 127.0.0.1 dell'host (server condiviso). I pod lo raggiungono via proxy
  socat sul gateway della rete `kind`; imposta l'IP in `01-config.yaml` (`OLLAMA_HOST`).
  Non usare hostname custom: Ollama risponde 403.
- **Segreti**: `postgres-secret` in `01-config.yaml` e' solo dev. La chiave LangSmith arriva dal
  `.env` tramite `deploy.sh`, non e' nei manifest.
- **Agent a 1 replica**: `MemorySaver` e' in memoria, quindi stato/approvazioni (human-in-the-loop)
  non sono condivisi tra pod. Per scalare serve un checkpointer Postgres (`langgraph-checkpoint-postgres`).
- **vector_db/** viene copiato nell'immagine: rifai `ingest` + build se cambi i manuali.
- Pulizia: `kind delete cluster --name imaint`