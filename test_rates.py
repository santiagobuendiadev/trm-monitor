"""Offline tests for rates_service: python3 -m unittest test_rates"""
import unittest

import rates_service as rs

ECB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
  <gesmes:subject>Reference rates</gesmes:subject>
  <Cube>
    <Cube time="2026-11-26">
      <Cube currency="USD" rate="1.0800"/>
      <Cube currency="JPY" rate="160.00"/>
      <Cube currency="BRL" rate="6.4800"/>
      <Cube currency="MXN" rate="21.6000"/>
    </Cube>
  </Cube>
</gesmes:Envelope>"""

BCRP_JSON = """{"config":{"title":"Tipo de cambio","series":[{"name":"TC Interbancario (S/ por US$) - Venta","dec":"3"}]},
"periods":[{"name":"25.Nov.26","values":["3.750"]},{"name":"26.Nov.26","values":["3.760"]},{"name":"27.Nov.26","values":["n.d."]}]}"""

BCRA_JSON = """{"status":200,"results":{"fecha":"2026-11-26","detalle":[
{"codigoMoneda":"EUR","descripcion":"EURO","tipoPase":1.08,"tipoCotizacion":1296.0},
{"codigoMoneda":"USD","descripcion":"DOLAR E.E.U.U.","tipoPase":0.0,"tipoCotizacion":1200.0}]}}"""

TRM = {"value": 4000.0, "valid_from": "2026-11-27T00:00:00-05:00",
       "valid_until": "2026-11-27T00:00:00-05:00", "success": True}


class ParserTests(unittest.TestCase):
    def test_ecb(self):
        r = rs.parse_ecb(ECB_XML)
        self.assertAlmostEqual(r["EUR"][0], 1 / 1.08)
        self.assertAlmostEqual(r["MXN"][0], 20.0)
        self.assertAlmostEqual(r["BRL"][0], 6.0)
        self.assertEqual(r["EUR"][1], "2026-11-26")

    def test_bcrp_skips_missing_values(self):
        self.assertEqual(rs.parse_bcrp(BCRP_JSON), {"PEN": (3.76, "2026-11-26")})

    def test_bcrp_september(self):
        self.assertEqual(rs._parse_bcrp_date("01.Set.26"), "2026-09-01")

    def test_bcra(self):
        self.assertEqual(rs.parse_bcra(BCRA_JSON), {"ARS": (1200.0, "2026-11-26")})


class BuildTests(unittest.TestCase):
    def sources(self, fail_bcra=False):
        def bcra():
            if fail_bcra:
                raise RuntimeError("timeout")
            return rs.parse_bcra(BCRA_JSON)
        return (
            ("BCE", rs.ECB_CURRENCIES, lambda: rs.parse_ecb(ECB_XML)),
            ("BCRP", ("PEN",), lambda: rs.parse_bcrp(BCRP_JSON)),
            ("BCRA", ("ARS",), bcra),
        )

    def test_cross_rates(self):
        out = rs.build_rates(TRM, sources=self.sources())
        r = out["rates"]
        self.assertEqual(r["USD"]["value"], 4000.0)
        self.assertEqual(r["EUR"]["value"], 4320.0)   # 4000 * 1.08
        self.assertEqual(r["MXN"]["value"], 200.0)    # 4000 / 20
        self.assertEqual(r["BRL"]["value"], 666.67)   # 4000 / 6
        self.assertEqual(r["PEN"]["value"], 1063.83)  # 4000 / 3.76
        self.assertEqual(r["ARS"]["value"], 3.33)     # 4000 / 1200
        self.assertEqual(out["errors"], {})
        self.assertEqual(out["base"], "COP")

    def test_failed_source_keeps_previous_value(self):
        previous = {"rates": {"ARS": {"value": 3.5, "source": "BCRA", "source_date": "2026-11-25"}}}
        out = rs.build_rates(TRM, previous, sources=self.sources(fail_bcra=True))
        self.assertEqual(out["rates"]["ARS"]["value"], 3.5)
        self.assertTrue(out["rates"]["ARS"]["stale"])
        self.assertIn("ARS", out["errors"])
        self.assertEqual(out["rates"]["EUR"]["value"], 4320.0)

    def test_failed_source_without_previous_is_omitted(self):
        out = rs.build_rates(TRM, sources=self.sources(fail_bcra=True))
        self.assertNotIn("ARS", out["rates"])
        self.assertIn("ARS", out["errors"])


class UnitFileTests(unittest.TestCase):
    def test_one_file_per_currency_with_trm_keys(self):
        trm = dict(TRM, id="1922301")
        doc = rs.build_rates(trm, sources=BuildTests().sources())
        files = rs.build_unit_files(doc, trm)
        self.assertEqual(sorted(files), ["ARS", "BRL", "EUR", "MXN", "PEN", "USD"])
        for key in ("value", "unit", "valid_from", "valid_until", "success", "id"):
            self.assertIn(key, files["EUR"])
        self.assertEqual(files["EUR"]["value"], 4320.0)
        self.assertEqual(files["EUR"]["unit"], "COP")
        self.assertEqual(files["USD"]["id"], "1922301")
        self.assertTrue(files["EUR"]["success"])

    def test_stale_currency_is_not_success(self):
        previous = {"rates": {"ARS": {"value": 3.5, "source": "BCRA", "source_date": "2026-11-25"}}}
        doc = rs.build_rates(TRM, previous, sources=BuildTests().sources(fail_bcra=True))
        ars = rs.build_unit_files(doc, TRM)["ARS"]
        self.assertFalse(ars["success"])
        self.assertTrue(ars["stale"])
        self.assertIn("timeout", ars["error"])


if __name__ == "__main__":
    unittest.main()
