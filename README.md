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

## 🛠️ How it works
- **No Dependencies:** The script uses only Python's standard library.
- **Official Source:** Data is fetched via SOAP from the Superfinanciera's official endpoint.
- **Automated:** Updates every day at 8:00 PM COT via GitHub Actions.

## 💻 Local Execution
If you want to run it manually:
```bash
python3 main.py
```
To update the local JSON file:
```bash
python3 main.py trm.json
```
