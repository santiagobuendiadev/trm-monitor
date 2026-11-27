# TRM Monitor 🇨🇴

Official TRM (Tasa Representativa del Mercado) monitor for Colombia, plus reference rates in Colombian pesos for EUR, MXN, BRL, PEN and ARS.

A GitHub Action fetches the data every day and publishes it as static JSON files in this repository. Any system can read them over HTTPS: no API key, no server, no sign-up.

## 🚀 Endpoints

All URLs start with `https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/`.

| File | What it returns | Use it when |
|---|---|---|
| `trm.json` | The official USD TRM (original format, unchanged) | You already consume the TRM, or you only need USD |
| `rates/<UNIT>.json` | One currency in COP, same keys as `trm.json` | The user selects a currency and you need its rate |
| `rates.json` | Every currency in one document | You need several currencies at once (a table, a converter) |

Available units: `USD`, `EUR`, `MXN`, `BRL`, `PEN`, `ARS`.

```text
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/trm.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/USD.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/EUR.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/MXN.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/BRL.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/PEN.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/ARS.json
https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates.json
```

## 💱 Lookup by currency: `rates/<UNIT>.json`

Build the URL with the unit the user picked. Every file has the same keys as `trm.json` (`value`, `unit`, `valid_from`, `valid_until`, `success`, `id`), so code that already reads the TRM can read any currency without changes.

```json
{
  "value": 3978.37,
  "unit": "COP",
  "currency": "EUR",
  "valid_from": "2026-11-26T00:00:00-05:00",
  "valid_until": "2026-11-27T00:00:00-05:00",
  "success": true,
  "id": null,
  "per_usd": 0.912659,
  "source": "BCE (Banco Central Europeo)",
  "source_date": "2026-11-27",
  "type": "referencia",
  "updated_at": "2026-11-27T11:14:21-05:00"
}
```

| Field | Meaning |
|---|---|
| `value` | Pesos (COP) for 1 unit of `currency` |
| `unit` | Always `COP` (same meaning as in `trm.json`) |
| `currency` | The currency of the file: `USD`, `EUR`, ... |
| `valid_from`, `valid_until` | Validity of the TRM used to compute the value |
| `success` | `true` if the value was updated in the last run. `false` means it is the previous value (see `stale`) |
| `id` | Superfinanciera TRM id. Only set for `USD`, `null` for the rest |
| `per_usd` | Units of the currency per 1 US dollar, as published by its source |
| `source` | Where `per_usd` comes from |
| `source_date` | Date of the source's rate (`YYYY-MM-DD`) |
| `type` | `oficial` for USD (the TRM), `referencia` for the others |
| `updated_at` | When the file was generated (Colombia time) |
| `stale`, `error` | Only present when the last update failed: the value is the previous one and `error` says why |

### Examples

JavaScript:

```js
async function getRate(unit) {
  const url = `https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/${unit}.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Unit ${unit} not available`);
  return res.json();
}

const eur = await getRate("EUR");
console.log(`1 EUR = ${eur.value} COP`);
```

Python:

```python
import json, urllib.request

def get_rate(unit):
    url = f"https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/{unit}.json"
    with urllib.request.urlopen(url) as r:
        return json.load(r)

print(get_rate("MXN")["value"])
```

Command line:

```bash
curl -s https://raw.githubusercontent.com/santiagobuendiadev/trm-monitor/main/rates/BRL.json
```

A unit that is not in the list returns HTTP 404.

## 🇺🇸 Official TRM: `trm.json`

Unchanged, so the systems that already use it keep working.

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

`rates/USD.json` returns the same value with the extra fields described above.

## 🌎 All currencies: `rates.json`

```json
{
  "base": "COP",
  "updated_at": "2026-11-27T11:14:21-05:00",
  "trm": { "value": 3630.89, "valid_from": "2026-11-26T00:00:00-05:00", "valid_until": "2026-11-27T00:00:00-05:00" },
  "rates": {
    "USD": { "value": 3630.89, "per_usd": 1.0, "source": "Superfinanciera (TRM oficial)", "source_date": "2026-11-26", "type": "oficial" },
    "EUR": { "value": 3978.37, "per_usd": 0.912659, "source": "BCE (Banco Central Europeo)", "source_date": "2026-11-27", "type": "referencia" },
    "MXN": { "value": 186.08, "per_usd": 19.512093, "source": "BCE (Banco Central Europeo)", "source_date": "2026-11-27", "type": "referencia" }
  },
  "errors": {}
}
```

`rates` has one entry per currency (shortened above). `errors` lists the currencies whose source failed in the last run, with the reason; those keep their previous value with `"stale": true`.

## 📐 How the rates are calculated

Only the US dollar has an official TRM in Colombia, published by the Superintendencia Financiera. The other currencies are **reference rates**: the TRM crossed with each currency's official rate against the dollar, the same method Banco de la República uses for its rates of other currencies.

```text
value (COP per unit) = TRM / per_usd
```

| Currency | Source | Rate used |
|---|---|---|
| USD | Superintendencia Financiera de Colombia | Official TRM (SOAP web service) |
| EUR, MXN, BRL | European Central Bank | Daily euro reference rates |
| PEN | Banco Central de Reserva del Perú | Interbank exchange rate, sell (series PD04638PD) |
| ARS | Banco Central de la República Argentina | Official quote (Estadísticas Cambiarias API) |

All sources are free and need no registration or API key.

Things to keep in mind:
- The reference rates are not an official TRM. Use them for display and estimates; for accounting or legal purposes in Colombia only the USD TRM is official.
- Each source publishes on its own schedule and skips its own holidays, so `source_date` can differ from the TRM date. On a holiday a source keeps its last rate.
- Argentina has several exchange rates; this uses the BCRA official quote.

## 🛠️ How it works

- **No dependencies:** only Python's standard library.
- **Automated:** a GitHub Action runs every day at 8:00 PM COT (and on every push to `main`), runs the offline tests, fetches all sources and commits the JSON files if they changed.
- **Fault tolerant:** if the TRM cannot be fetched, the job fails and no file is overwritten. If another source fails, the rest are still published and the failing currency keeps its previous value, marked as stale.
- **Cache:** `raw.githubusercontent.com` can serve a file up to a few minutes old after an update.

| File | Purpose |
|---|---|
| `trm_service.py` | Fetches the TRM from Superfinanciera |
| `rates_service.py` | Fetches the other sources, computes the cross rates, builds `rates.json` and `rates/<UNIT>.json` |
| `main.py` | Entry point used by the workflow |
| `test_rates.py` | Offline tests with sample responses |

## 💻 Local execution

Print the TRM:
```bash
python3 main.py
```
Update all JSON files (`trm.json`, `rates.json` and `rates/`):
```bash
python3 main.py trm.json rates.json
```
Offline tests:
```bash
python3 -m unittest test_rates
```
