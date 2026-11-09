"""Regresiones del inventario: ceros, huecos, fechas y ventanas sin imputación."""
from datetime import datetime
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from openpyxl.utils.datetime import WINDOWS_EPOCH

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from inventario_sprint3 import (Book, NS, as_datetime, column_index, detect_header,
                               forecast_windows, header, intervals, numeric, plausible)


class InventoryTests(unittest.TestCase):
    def test_zero_is_available(self):
        self.assertEqual(numeric(0), 0)
        self.assertEqual(numeric('0'), 0)
        self.assertTrue(plausible('CO', 0))

    def test_invalid_markers_are_not_zero(self):
        for value in (None, '', 'IF', 'IC', '#N/A', float('inf'), 'NaN', True):
            self.assertIsNone(numeric(value))

    def test_negatives_and_physical_ranges(self):
        self.assertFalse(plausible('PM10', -1))
        self.assertTrue(plausible('ET', -1))
        self.assertTrue(plausible('RH', 100))
        self.assertFalse(plausible('RH', 100.1))
        self.assertTrue(plausible('WD', 360))
        self.assertFalse(plausible('WD', 361))

    def test_headers_do_not_require_day_month(self):
        self.assertEqual([header(v) for v in ['station ', 'fecha', 'PM2.5', 'PM2_5', 'mes ']],
                         ['STATION', 'DATE', 'PM2.5', 'PM2.5', 'MES'])

    def test_dates_are_unambiguous_and_leap_day_survives(self):
        self.assertEqual(as_datetime('2024-02-29 03:00:00', WINDOWS_EPOCH), datetime(2024, 2, 29, 3))
        self.assertIsNone(as_datetime('01/02/2015', WINDOWS_EPOCH))
        self.assertEqual(as_datetime(42005, WINDOWS_EPOCH), datetime(2015, 1, 1))

    def test_sparse_column_addresses(self):
        self.assertEqual(column_index('A1'), 0)
        self.assertEqual(column_index('AA21'), 26)

    def test_formula_cache_and_shared_strings(self):
        book = Book.__new__(Book)
        book.strings = ['MIR']
        self.assertEqual(book.cell(ET.fromstring(f'<c xmlns="{NS[1:-1]}" t="s"><v>0</v></c>')), 'MIR')
        self.assertEqual(book.cell(ET.fromstring(f'<c xmlns="{NS[1:-1]}"><f>1-1</f><v>0</v></c>')), 0)
        self.assertIsNone(book.cell(ET.fromstring(f'<c xmlns="{NS[1:-1]}"><f>1-1</f></c>')))

    def test_duplicate_normalized_headers_rejected(self):
        class FakeBook:
            def rows(self, sheet):
                yield 1, {0: 'STATION', 1: 'DATE', 2: 'PM2.5', 3: 'PM2_5'}, [], [], {}
        with self.assertRaises(ValueError):
            detect_header(FakeBook(), {'name': 'Data'})

    def test_intervals_never_bridge_a_gap(self):
        index = pd.date_range('2024-02-28 23:00', periods=5, freq='h')
        result = intervals([True, True, False, True, True], index)
        self.assertEqual([r[2] for r in result], [2, 2])
        self.assertEqual(result[0][1], '2024-02-29T00:00:00')

    def test_windows_respect_gaps_and_year_boundaries(self):
        values = np.zeros(8760)  # Ceros reales, no ausencias.
        values[100] = np.nan
        arrays = {2015: {'PM10': values}, 2016: {'PM10': np.zeros(8784)}}
        result = forecast_windows(arrays)
        a = next(r for r in result if r['year'] == 2015 and r['variable'] == 'PM10')
        b = next(r for r in result if r['year'] == 2016 and r['variable'] == 'PM10')
        self.assertEqual(a['pair_t_tplus1'], 8760 - 2)
        self.assertEqual(a['windows_24past_3future'], 8760 - 23 - 27)
        self.assertEqual(b['windows_24past_3future'], 8784 - 3)
        self.assertEqual(b['pair_t_tplus3'], 8784 - 3)


if __name__ == '__main__':
    unittest.main()
