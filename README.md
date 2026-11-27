# TRM Monitor 🇨🇴

Official TRM (Tasa Representativa del Mercado) monitor for Colombia. 

This project fetches the daily TRM directly from the **Superintendencia Financiera de Colombia** using an automated GitHub Action.

## 🚀 API Endpoint (JSON)

You can consume the latest TRM data directly from this URL:

```text
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/trm.json
```

### Response Example

```json
{
  "value": 3675.81,
  "unit": "COP",
  "valid_from": "2026-04-02T00:00:00-05:00",
  "valid_until": "2026-04-06T00:00:00-05:00",
  "success": true,
  "id": "1922301"
}
```

## 🌎 Other currencies (rates.json)

EUR, MXN, BRL, PEN and ARS in Colombian pesos:

```text
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates.json
```

Only the US dollar has an official TRM in Colombia. The other values are **reference rates**: the TRM crossed with each currency's official rate against the dollar (`value = TRM / per_usd`), the same method Banco de la República uses.

| Currency | Source | Rate used |
|---|---|---|
| USD | Superfinanciera | Official TRM |
| EUR, MXN, BRL | European Central Bank | Daily euro reference rates |
| PEN | Banco Central de Reserva del Perú | Interbank rate, sell (PD04638PD) |
| ARS | Banco Central de la República Argentina | Official quote (Estadísticas Cambiarias API) |

```json
{
  "base": "COP",
  "updated_at": "2026-11-27T20:00:00-05:00",
  "trm": { "value": 3675.81, "valid_from": "...", "valid_until": "..." },
  "rates": {
    "USD": { "value": 3675.81, "per_usd": 1.0, "source": "Superfinanciera (TRM oficial)", "source_date": "2026-11-27", "type": "oficial" },
    "EUR": { "value": 3969.87, "per_usd": 0.925926, "source": "BCE (Banco Central Europeo)", "source_date": "2026-11-26", "type": "referencia" }
  },
  "errors": {}
}
```

If a source fails, the other currencies are still updated; the failing one keeps its previous value with `"stale": true` and the reason appears in `errors`. `trm.json` keeps its original format.

## 🛠️ How it works
- **No Dependencies:** The script uses only Python's standard library.
- **Official Source:** Data is fetched via SOAP from the Superfinanciera's official endpoint.
- **Automated:** Updates every day at 8:00 PM COT via GitHub Actions.

## 💻 Local Execution
If you want to run it manually:
```bash
python3 main.py
```
To update the local JSON files:
```bash
python3 main.py trm.json rates.json
```
Offline tests:
```bash
python3 -m unittest test_rates
```
