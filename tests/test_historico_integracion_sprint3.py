from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import normativa as N
from historico_sprint3 import POLS, daily_tables, paired, events_and_anomalies


class HistoricalTests(unittest.TestCase):
    def test_zero_daily_category_is_valid(self):
        frame = pd.DataFrame(0., index=pd.date_range('2015-01-01', periods=48, freq='h'), columns=N.POLS + ['NO', 'NOX', 'ET', 'RH', 'WS', 'WD'])
        _, daily = daily_tables(frame)
        self.assertEqual(daily.iloc[0].C_PM10, 0)
        self.assertEqual(daily.iloc[0].C_CO, 0)
        self.assertEqual(daily.iloc[0].N_PM10, 24)

    def test_missing_is_not_buena_and_gases_need18_project(self):
        frame = pd.DataFrame(np.nan, index=pd.date_range('2015-01-01', periods=48, freq='h'), columns=N.POLS + ['NO', 'NOX', 'ET', 'RH', 'WS', 'WD'])
        frame.loc[frame.index[:17], 'O3'] = .05
        _, daily = daily_tables(frame)
        self.assertTrue(pd.isna(daily.iloc[0].C_PM10))
        self.assertTrue(pd.isna(daily.iloc[0].C_O3))
        self.assertEqual(daily.iloc[0].N_O3, 17)

    def test_no_and_nox_do_not_receive_categories(self):
        frame = pd.DataFrame(0., index=pd.date_range('2015-01-01', periods=48, freq='h'), columns=N.POLS + ['NO', 'NOX', 'ET', 'RH', 'WS', 'WD'])
        _, daily = daily_tables(frame)
        self.assertTrue(daily.C_NO.isna().all())
        self.assertTrue(daily.C_NOX.isna().all())
        self.assertEqual(daily.iloc[0].I_NO, 0)

    def dataset(self, a, b):
        index = pd.date_range(f'{a}-01-01', f'{a}-12-31', freq='D').append(pd.date_range(f'{b}-01-01', f'{b}-12-31', freq='D'))
        return pd.DataFrame({'EXACT_PM10': 0., 'EXACT_NO2': .01}, index=index)

    def test_february_common_dates_and_zero_denominator(self):
        row = paired(self.dataset(2023, 2024), 2023, 2024, 'PM10', 2)
        self.assertEqual(row['expected'], 28)
        self.assertNotIn('02-29', row['dates'])
        self.assertIsNone(row['change_pct'])
        self.assertEqual(row['a'], 0)

    def test_two_leap_years_keep_feb29(self):
        row = paired(self.dataset(2016, 2020), 2016, 2020, 'PM10', 2)
        self.assertEqual(row['n'], 29)
        self.assertIn('02-29', row['dates'])

    def test_annual_requires_quarters_and_no2_exploratory(self):
        data = self.dataset(2023, 2024)
        self.assertFalse(paired(data, 2023, 2024, 'NO2', 12)['sufficient'])
        data.loc['2024-01-01':'2024-03-31', 'EXACT_PM10'] = np.nan
        row = paired(data, 2023, 2024, 'PM10', 0)
        self.assertGreaterEqual(row['n'] / row['expected'], .75)
        self.assertFalse(row['sufficient'])

    def test_episodes_stop_at_missing_day(self):
        idx = pd.date_range('2023-12-29', periods=5, freq='D')
        day = pd.DataFrame(index=idx)
        for p in POLS:
            day[f'C_{p}'] = np.nan
            day[f'I_{p}'] = np.nan
            day[f'N_{p}'] = 0
        day['C_PM10'] = [2, 2, np.nan, 3, 3]
        day['I_PM10'] = [70, 70, np.nan, 140, 140]
        day['N_PM10'] = [24, 24, 0, 24, 24]
        clean = pd.DataFrame(np.nan, index=pd.date_range('2023-12-29', periods=120, freq='h'), columns=POLS)
        episodes, _, _ = events_and_anomalies(clean, day)
        self.assertEqual([e['days'] for e in episodes], [2, 2])
        self.assertEqual(episodes[1]['start'], '2024-01-01')


if __name__ == '__main__':
    unittest.main()
