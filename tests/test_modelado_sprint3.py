"""Fechas exactas, causalidad, referencias, fronteras y métricas del modelado."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from pm10_modelado import (baselines, calculate_metrics, causal_features, feature_names,
                          metrics_tables, predict_at, require_grid, sample_audit, select_key)


class ModelingTests(unittest.TestCase):
    def series(self, start='2022-12-29', periods=120):
        return pd.Series(np.arange(periods, dtype=float), index=pd.date_range(start, periods=periods, freq='h'))

    def test_lags_and_past_summaries(self):
        x = causal_features(self.series()).iloc[30]
        self.assertEqual(x.pm10_lag_0, 30)
        self.assertEqual(x.pm10_lag_23, 7)
        self.assertEqual(x.pm10_mean_3h, 29)
        self.assertEqual(x.pm10_min_24h, 7)
        self.assertAlmostEqual(x.pm10_std_3h, np.std([28, 29, 30], ddof=0))
        self.assertEqual(list(x.index), feature_names())

    def test_future_mutation_cannot_change_features(self):
        a = self.series()
        b = a.copy()
        b.iloc[61:] = 1e8
        pd.testing.assert_frame_equal(causal_features(a).iloc[:61], causal_features(b).iloc[:61])

    def test_feature_parity_short_history(self):
        series = self.series()
        whole = causal_features(series).iloc[[-1]].to_numpy()
        short = causal_features(series.iloc[-24:]).iloc[[-1]].to_numpy()
        np.testing.assert_array_equal(whole, short)

    def test_predict_only_needs_past_context(self):
        class Fake:
            def predict(self, x):
                return x[:, 0] + x[:, 1] * .1
        series = self.series()
        origin = series.index[60]
        models = {h: {'estimator': Fake(), 'features': feature_names()} for h in [1, 2, 3]}
        a = predict_at(models, series.loc[:origin], origin)
        series.loc[origin + pd.Timedelta(hours=1):] = np.nan
        self.assertEqual(a, predict_at(models, series, origin))

    def test_predict_rejects_missing_past(self):
        series = self.series()
        series.iloc[50] = np.nan
        with self.assertRaises(ValueError):
            predict_at({}, series, series.index[60])

    def test_daily_reference_is_horizon_specific(self):
        x = causal_features(self.series()).iloc[[23]]
        pred = baselines(x.to_numpy(), list(x.columns))
        np.testing.assert_array_equal(pred['persistencia'], [[23, 23, 23]])
        np.testing.assert_array_equal(pred['diaria'], [[0, 1, 2]])

    def test_zero_is_not_missing(self):
        series = self.series()
        series[:] = 0
        audit = sample_audit(series)
        self.assertEqual(audit.initial_window.sum(), len(series) - 26)

    def test_gap_not_compacted(self):
        series = self.series()
        series.iloc[50] = np.nan
        audit = sample_audit(series)
        self.assertFalse(audit.loc[series.index[47]:series.index[73]].initial_window.any())
        with self.assertRaises(ValueError):
            causal_features(series.dropna())

    def test_train_border_purged_refit_recovered(self):
        audit = sample_audit(self.series())
        border = audit.loc['2022-12-31 21:00':'2022-12-31 23:00']
        self.assertEqual(border.boundary_excluded.sum(), 3)
        self.assertFalse(border.included.any())
        self.assertTrue(border.refit_included.all())
        self.assertTrue(audit.loc['2023-01-01 00:00', 'included'])

    def test_validation_border_never_enters_refit(self):
        audit = sample_audit(self.series('2023-12-29'))
        border = audit.loc['2023-12-31 21:00':'2023-12-31 23:00']
        self.assertTrue(border.boundary_excluded.all())
        self.assertFalse(border.refit_included.any())
        self.assertTrue(audit.loc['2024-01-01 00:00', 'included'])

    def test_leap_day_and_dates(self):
        series = self.series('2024-02-28', 100)
        audit = sample_audit(series)
        self.assertEqual(len(audit.loc['2024-02-29']), 24)
        self.assertTrue(audit.loc['2024-02-29'].included.all())

    def test_invalid_grid_negative_duplicate(self):
        series = self.series()
        series.iloc[0] = -1
        with self.assertRaises(ValueError):
            require_grid(series)
        duplicate = pd.concat([self.series().iloc[:1], self.series()])
        with self.assertRaises(ValueError):
            require_grid(duplicate)

    def test_metrics_match_independent_sklearn(self):
        y = np.array([1, 7, 12, 2.5])
        p = np.array([4, 1, 10, 8])
        result = calculate_metrics(y, p)
        self.assertAlmostEqual(result['mae'], mean_absolute_error(y, p))
        self.assertAlmostEqual(result['rmse'], np.sqrt(mean_squared_error(y, p)))
        self.assertAlmostEqual(result['r2'], r2_score(y, p))
        self.assertAlmostEqual(result['bias'], np.mean(p - y))

    def test_negative_r2_retained(self):
        self.assertLess(calculate_metrics([0, 1, 2], [100, 100, 100])['r2'], 0)

    def test_undefined_r2_visible(self):
        self.assertIsNone(calculate_metrics([2, 2], [2, 2])['r2'])
        self.assertEqual(calculate_metrics([], [])['r2_reason'], 'sin_muestras')
        self.assertEqual(calculate_metrics([2], [1])['r2_reason'], 'n_menor_2')

    def test_metrics_never_silently_drop_rows(self):
        with self.assertRaises(ValueError):
            calculate_metrics([1, np.nan], [1, 2])

    def test_explicit_tie_break(self):
        a = {'id': 'C1', 'max_leaf_nodes': 15, 'max_iter': 300, 'learning_rate': .1}
        b = {'id': 'C2', 'max_leaf_nodes': 31, 'max_iter': 150, 'learning_rate': .05}
        self.assertLess(select_key(a, 10), select_key(b, 10))

    def test_monthly_and_high_denominators(self):
        frame = pd.DataFrame({'partition': 'test', 'model': 'persistencia', 'horizon': 1, 'fit_period': 'sin_ajuste',
                              'target_time': ['2024-01-31T23:00:00', '2024-02-01T00:00:00', '2024-02-01T01:00:00'],
                              'observed': [0., 10., 100.], 'predicted': [1., 20., 50.]})
        glob, monthly, high = metrics_tables([frame], 90)
        self.assertEqual(monthly.n.sum(), glob.iloc[0].n)
        self.assertEqual(high[high.month.eq(0)].iloc[0].n, 1)
        self.assertEqual(monthly[monthly.month.eq(3)].iloc[0].r2_reason, 'sin_muestras')
        self.assertEqual(high[high.month.eq(0)].iloc[0].bias, -50)


if __name__ == '__main__':
    unittest.main()
