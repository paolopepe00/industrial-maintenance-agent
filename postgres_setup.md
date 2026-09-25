# PostgreSQL — Setup locale (utente, senza sudo)

Setup pensato per un host condiviso dove non si vuole toccare configurazioni di sistema: PostgreSQL gira come processo del proprio utente, con una data directory e una porta dedicate, isolato da tutto il resto.

## Installazione

```bash
conda install -c conda-forge postgresql -y
```
Installa i binari PostgreSQL (`initdb`, `pg_ctl`, `psql`, `createdb`, ecc.) dentro l'ambiente conda attivo (`imaint-agent`). Nessun pacchetto di sistema, nessun servizio systemd, nessun sudo.

## Inizializzazione del data directory

```bash
mkdir -p ~/pgdata/imaint-agent
initdb -D ~/pgdata/imaint-agent -U paolopepe
```
- `mkdir -p ~/pgdata/imaint-agent` — crea la cartella dove PostgreSQL scriverà tutti i suoi file (tabelle, indici, WAL). È il tuo "cluster" personale, separato da eventuali altre istanze sul server.
- `initdb -D <dir> -U <utente>` — inizializza un nuovo cluster PostgreSQL in quella cartella, creando il superuser `paolopepe`. Va eseguito **una sola volta**; rifarlo su una directory già inizializzata la sovrascrive.

## Avvio del server

```bash
pg_ctl -D ~/pgdata/imaint-agent -l ~/pgdata/imaint-agent/logfile -o "-p 5433" start
```
- `pg_ctl ... start` — avvia il processo `postgres` in background, puntando al tuo data directory.
- `-l <file>` — reindirizza i log del server su file invece che sul terminale.
- `-o "-p 5433"` — passa l'opzione `-p 5433` al processo postgres: lo fa ascoltare sulla porta 5433 invece della 5432 di default, per evitare conflitti con eventuali altre istanze PostgreSQL già in uso da altri sul server condiviso.

## Creazione del database

```bash
createdb -p 5433 -U paolopepe imaint_agent
```
Crea il database `imaint_agent` all'interno del cluster avviato sopra. `-p 5433` deve corrispondere alla porta scelta all'avvio; `-U paolopepe` specifica l'utente proprietario.

## Verifica connessione

```bash
psql -p 5433 -U paolopepe -d imaint_agent -c "SELECT version();"
```
Apre una connessione al database `imaint_agent` sulla porta 5433 ed esegue una query SQL diretta (`-c`) senza entrare nella shell interattiva. Se stampa la versione di PostgreSQL, il setup è corretto.

Per entrare invece nella shell interattiva (utile per esplorare tabelle manualmente più avanti):
```bash
psql -p 5433 -U paolopepe -d imaint_agent
```

## Arresto del server

```bash
pg_ctl -D ~/pgdata/imaint-agent stop
```
Ferma il processo postgres in modo pulito. Buona pratica su un host condiviso: fermarlo quando non serve, per non tenere occupate risorse (RAM, connessioni) inutilmente.

## Riavvio in una sessione futura

Il data directory è persistente su disco — non va reinizializzato. Basta:
```bash
pg_ctl -D ~/pgdata/imaint-agent -l ~/pgdata/imaint-agent/logfile -o "-p 5433" start
```

## Connection string per l'app (FastAPI/SQLAlchemy)

```
postgresql://paolopepe@localhost:5433/imaint_agent
```
Da usare più avanti nel backend CMMS per collegarsi al DB (nessuna password impostata in questo setup locale — solo per sviluppo, non adatto a produzione).