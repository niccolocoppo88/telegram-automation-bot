# TASK-001: Setup Python Project

## Feature
Initializzazione progetto Python con python-telegram-bot v20+, virtual environment, dipendenze e struttura directory completa per il bot Telegram con FastAPI webhook support.

## Obiettivo
Creare la base solida su cui costruire tutto il resto — progetto Python configurato correttamente con tutte le dipendenze, struttura directory standard e readiness per sviluppo e deployment.

## Criteri di Successo
- [ ] `python -c "import telegram; print(telegram.__version__)"` funziona e stampa versione >= 20
- [ ] `uvicorn src.api:app --reload` parte senza errori
- [ ] `python -m venv venv` crea virtual environment funzionante
- [ ] Directory structure rispecchia quanto in SPEC.md:
  - `src/` con bot.py, handlers.py, models.py, database.py, api.py, __init__.py
  - `tests/` con test_handlers.py, test_models.py
  - `config.py`, `requirements.txt`, `.env.example`
  - `Dockerfile`, `docker-compose.yml`
- [ ] Tutti i file Python passano `python -m py_compile`

## Dipendenze
- [ ] Accesso a GitHub repo `niccolocoppo88/telegram-automation-bot`
- [ ] Token GitHub configurato per push
- [ ] Python 3.11+ disponibile localmente

## Output Atteso
Repo aggiornato con:
- `requirements.txt` con tutte le dipendenze pinneate
- `.env.example` con tutte le variabili ambiente documentate
- `src/` directory con file boilerplate che compilano senza errori
- `tests/` directory con test stub che passano

## Criteri QA
- Goksu verifica che `pip install -r requirements.txt` installa tutto senza conflict
- Goksu esegue `pytest tests/` e verifica che i stub passano
- Verifica che `docker build -t telegram-bot .` parte (anche se fallisce per mancanza token)

## Note
- Usare `python-telegram-bot` v20+ (async), NON v13 (sync)
- FastAPI per webhook endpoint, non Flask
- SQLite default, PostgreSQL opzionale solo se necessario per scaling

---

**Assegnato a:** Thomas
**Status:** TODO
**Creato il:** 2026-04-22
**Approvato da:** Elisa