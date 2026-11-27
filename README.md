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

### Lookup by currency

Each currency also has its own file, with the same keys as `trm.json` (`value`, `unit`, `valid_from`, `valid_until`, `success`, `id`), so a system can pick a unit and read it the same way it reads the TRM:

```text
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/USD.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/EUR.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/MXN.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/BRL.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/PEN.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/ARS.json
```

```json
{
  "value": 3969.87,
  "unit": "COP",
  "currency": "EUR",
  "valid_from": "2026-11-27T00:00:00-05:00",
  "valid_until": "2026-11-28T00:00:00-05:00",
  "success": true,
  "id": null,
  "per_usd": 0.925926,
  "source": "BCE (Banco Central Europeo)",
  "source_date": "2026-11-26",
  "type": "referencia",
  "updated_at": "2026-11-27T20:00:00-05:00"
}
```

`valid_from` and `valid_until` are those of the TRM used for the cross. `id` is the Superfinanciera id and is only set for USD. If a currency could not be updated, its file keeps the previous value with `"success": false`, `"stale": true` and an `error`.

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
