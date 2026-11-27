"""
Reference rates in Colombian pesos (COP) for other currencies.

Colombia only has an official TRM for the US dollar (Superfinanciera).
For other currencies this module does what Banco de la Republica does for
its reference rates: it crosses the TRM with each currency's official rate
against the dollar.

    rate in COP = TRM / (units of the currency per 1 USD)

Sources (all free, no API key, standard library only):
  - EUR, MXN, BRL: European Central Bank daily reference rates (XML).
  - PEN: Banco Central de Reserva del Peru, interbank rate (JSON API).
  - ARS: Banco Central de la Republica Argentina, official quote (JSON API).

Each source is fetched on its own: if one fails, the others are still
published and the failing currencies keep their previous value, marked
as stale.
"""
import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

USER_AGENT = "trm-monitor (+https://github.com/santiagobuendiadev/trm-monitor)"

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_CURRENCIES = ("EUR", "MXN", "BRL")

# PD04638PD = Tipo de cambio interbancario, venta (S/ por US$).
BCRP_SERIES = "PD04638PD"
BCRP_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{series}/json/{start}/{end}"

BCRA_URL = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"

COLOMBIA_TZ = timezone(timedelta(hours=-5))

SPANISH_MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


def _http_get(url, verify=True, timeout=30):
    context = None if verify else ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=context, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read().decode("utf-8")


# ---------------------------------------------------------------- parsers
# Each parser returns {currency: (units_per_usd, source_date "YYYY-MM-DD")}.

def parse_ecb(xml_text):
    """ECB rates are units of each currency per 1 EUR."""
    root = ET.fromstring(xml_text)
    day = None
    per_eur = {}
    for node in root.iter():
        if node.tag.endswith("Cube"):
            if node.get("time"):
                day = node.get("time")
            if node.get("currency") and node.get("rate"):
                per_eur[node.get("currency")] = float(node.get("rate"))
    if "USD" not in per_eur or not day:
        raise ValueError("ECB response has no USD rate or date")

    usd_per_eur = per_eur["USD"]
    result = {"EUR": (1 / usd_per_eur, day)}
    for code in ECB_CURRENCIES:
        if code != "EUR":
            if code not in per_eur:
                raise ValueError(f"ECB response has no {code} rate")
            result[code] = (per_eur[code] / usd_per_eur, day)
    return result


def _parse_bcrp_date(name):
    # Period names look like "26.Nov.26".
    try:
        day, month, year = name.split(".")
        return datetime(2000 + int(year), SPANISH_MONTHS[month.lower()[:3]], int(day)).strftime("%Y-%m-%d")
    except (ValueError, KeyError):
        return name


def parse_bcrp(json_text):
    data = json.loads(json_text)
    for period in reversed(data.get("periods", [])):
        values = period.get("values") or []
        try:
            value = float(values[0])
        except (IndexError, TypeError, ValueError):
            continue  # "n.d." on holidays
        return {"PEN": (value, _parse_bcrp_date(period.get("name", "")))}
    raise ValueError("BCRP response has no numeric value")


def parse_bcra(json_text):
    data = json.loads(json_text)
    results = data.get("results") or {}
    for item in results.get("detalle", []):
        if item.get("codigoMoneda") == "USD" and item.get("tipoCotizacion"):
            return {"ARS": (float(item["tipoCotizacion"]), results.get("fecha"))}
    raise ValueError("BCRA response has no USD quote")


# ---------------------------------------------------------------- fetchers

def fetch_ecb():
    return parse_ecb(_http_get(ECB_URL))


def fetch_bcrp(today=None):
    today = today or datetime.now()
    url = BCRP_URL.format(
        series=BCRP_SERIES,
        start=(today - timedelta(days=10)).strftime("%Y-%m-%d"),
        end=today.strftime("%Y-%m-%d"),
    )
    return parse_bcrp(_http_get(url))


def fetch_bcra():
    # The BCRA server has had an incomplete certificate chain, which makes
    # verification fail on clean runners, so it is not verified (same as
    # the Superfinanciera call in trm_service.py).
    return parse_bcra(_http_get(BCRA_URL, verify=False))


SOURCES = (
    ("BCE (Banco Central Europeo)", ECB_CURRENCIES, fetch_ecb),
    ("BCRP (Banco Central de Reserva del Peru)", ("PEN",), fetch_bcrp),
    ("BCRA (Banco Central de la Republica Argentina)", ("ARS",), fetch_bcra),
)


# ---------------------------------------------------------------- builder

def build_rates(trm, previous=None, sources=SOURCES, now=None):
    """
    trm: the successful result of TRMService.get_current_trm().
    previous: the last published rates.json (dict), used to keep the
              previous value of a currency whose source failed.
    """
    now = now or datetime.now(COLOMBIA_TZ)
    previous_rates = (previous or {}).get("rates", {})
    trm_value = trm["value"]

    rates = {
        "USD": {
            "value": round(trm_value, 2),
            "per_usd": 1.0,
            "source": "Superfinanciera (TRM oficial)",
            "source_date": (trm.get("valid_from") or "")[:10],
            "type": "oficial",
        }
    }
    errors = {}

    for source_name, currencies, fetch in sources:
        try:
            fetched = fetch()
            for code in currencies:
                per_usd, source_date = fetched[code]
                rates[code] = {
                    "value": round(trm_value / per_usd, 2),
                    "per_usd": round(per_usd, 6),
                    "source": source_name,
                    "source_date": source_date,
                    "type": "referencia",
                }
        except Exception as e:  # one source failing must not stop the rest
            for code in currencies:
                errors[code] = f"{source_name}: {e}"
                if code in previous_rates:
                    stale = dict(previous_rates[code])
                    stale["stale"] = True
                    rates[code] = stale

    return {
        "base": "COP",
        "updated_at": now.isoformat(timespec="seconds"),
        "trm": {
            "value": trm_value,
            "valid_from": trm.get("valid_from"),
            "valid_until": trm.get("valid_until"),
        },
        "rates": rates,
        "errors": errors,
    }
