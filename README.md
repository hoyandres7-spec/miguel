# value-alert-bot

Bot en Python que estima probabilidades con un modelo Elo simple y compara contra probabilidades implícitas de cuotas públicas (The Odds API). Cuando el edge supera un umbral configurable, envía una alerta por Telegram y/o imprime en consola.

> **Aviso importante**: Esto **no** es asesoría financiera ni promesa de ganancias. El bot **solo estima probabilidades** y avisa cuando existe diferencia con la probabilidad implícita. El usuario decide y **asume el riesgo**. Apuesta responsablemente.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Para dependencias de desarrollo:

```bash
pip install -e .[dev]
```

## Configuración

1. Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

2. Configura al menos `ODDS_API_KEY`.

### Variables de entorno

- **ODDS_API_KEY** (obligatoria)
- SPORT_KEY (default: `soccer_epl`)
- REGIONS (default: `eu`)
- MARKETS (default: `h2h`)
- ODDS_FORMAT (default: `decimal`)
- TELEGRAM_BOT_TOKEN (opcional)
- TELEGRAM_CHAT_ID (opcional)
- EDGE_THRESHOLD (default: `0.03`)
- MIN_ODDS (default: `1.50`)
- MAX_ALERTS_PER_RUN (default: `15`)
- DEDUPE_TTL_HOURS (default: `24`)
- DEDUPE_DB_PATH (default: `./data/dedupe.sqlite`)
- LOG_LEVEL (default: `INFO`)
- TIMEZONE (default: `UTC`)

### Parámetros de modelo Elo

- DEFAULT_ELO (default: `1500`)
- HOME_ADV (default: `60`)
- BASE_DRAW (default: `0.26`)
- DRAW_DECAY (default: `600`)

## Uso

Ejecutar una vez:

```bash
python -m value_alert_bot.cli run
```

Modo dry-run (no envía a Telegram):

```bash
python -m value_alert_bot.cli run --dry-run
```

Exportar señales a JSON:

```bash
python -m value_alert_bot.cli export --out signals.json
```

### Programar con cron

Ver ejemplo en `scripts/cron_example.txt`.

### Ejemplo de salida

```
[ALERTA] Arsenal vs Chelsea | 2025-01-01T12:30:00Z | 1X2 | LOCAL
Cuota: 2.10 (book: bet365)
P_modelo: 0.51 | P_imp: 0.46 | edge: 5.0%
No es garantía; apuesta responsable.
```

## Limitaciones

- Solo usa APIs oficiales (The Odds API). No hay scraping.
- El modelo Elo es **simple** y **no** representa la realidad completa.
- La precisión depende de la calidad de datos y parámetros.

## Juego responsable

- Establece límites de gasto y tiempo.
- Evita perseguir pérdidas.
- Si el juego deja de ser entretenimiento, busca ayuda profesional.

## Desarrollo y pruebas

```bash
pytest
```

## Estructura

```
value-alert-bot/
  src/value_alert_bot/
    cli.py
    config.py
    odds_api.py
    models/
    notifier/
    scoring.py
    dedupe.py
    utils.py
  tests/
  scripts/
```
