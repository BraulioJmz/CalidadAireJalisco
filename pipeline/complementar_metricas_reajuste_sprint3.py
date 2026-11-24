"""Complemento de métricas por etapa. Usa exclusivamente inferencia guardada."""
import importlib.metadata

import joblib
import pandas as pd
from threadpoolctl import threadpool_limits

from entrenar_sprint3 import load_data
from pm10_modelado import HORIZONS, OUT, PROTOCOL, ROOT, calculate_metrics, read_json, sha, write_json


DEST = ROOT / "web/public/datos/sprint-3/complemento_reajuste.json"


def main():
    report = read_json(OUT / "evaluacion_final.json")
    signatures = report["outputs_sha256"]
    for name, signature in signatures.items():
        if sha(OUT / name) != signature:
            raise ValueError(f"Artefacto congelado modificado: {name}")
    frozen = read_json(OUT / "config_congelada.json")
    if frozen["selected"]["id"] != report["selected"] or sha(PROTOCOL) != report["protocol_sha256"]:
        raise ValueError("Protocolo o selección inconsistentes")
    protocol = read_json(PROTOCOL)
    data, origins, features, targets = load_data(OUT)
    refit = origins.refit_included.to_numpy(dtype=bool)
    refit_origins = origins.loc[refit]
    boundary = pd.Timestamp(protocol["partitions"]["test"][0])
    if len(refit_origins) != report["refit_n"] or not (refit_origins.target_3 < boundary).all():
        raise ValueError("El complemento requiere exactamente la población de reajuste previa a 2024")
    fit_period = f'{protocol["partitions"]["train"][0][:4]}–{boundary.year - 1}'
    metrics = []
    models = [f"modelos/reajuste/pm10_h{h}.joblib" for h in HORIZONS]
    version = importlib.metadata.version("scikit-learn")
    with threadpool_limits(limits=protocol["threads"]):
        for column, (horizon, path) in enumerate(zip(HORIZONS, models)):
            model = joblib.load(OUT / path)
            estimator_params = model["estimator"].get_params()
            if (
                model["horizon"] != horizon
                or model["fit_stage"] != "reajuste"
                or model["sklearn_version"] != version
                or model["train_n"] != len(refit_origins)
                or model["protocol_sha256"] != report["protocol_sha256"]
                or model["last_target"] != refit_origins.target_3.max().isoformat()
                or model["features"] != data["features"]
                or model["parameters"] != frozen["selected"]["parameters"]
                or any(estimator_params[key] != value for key, value in model["parameters"].items())
            ):
                raise ValueError(f"Modelo o entorno de inferencia incompatible: {path}")
            prediction = model["estimator"].predict(features[refit])
            metrics.append({
                "horizon": horizon,
                **calculate_metrics(targets[refit, column], prediction),
            })
    source_names = ["config_congelada.json", "datos_congelados.json", "origenes.csv", "features.npy", "targets.npy", *models]
    write_json(DEST, {
        "schema": "mir-pm10-reajuste-en-muestra-v1",
        "partition": "refit_in_sample",
        "configuration": report["selected"],
        "fit_period": fit_period,
        "evaluation_period": fit_period,
        "method": "predict sobre refit_included de origenes.csv, en el orden de features.npy y targets.npy",
        "source_root": OUT.relative_to(ROOT).as_posix(),
        "sources_sha256": {name: signatures[name] for name in source_names},
        "generator_sha256": sha(ROOT / "pipeline/complementar_metricas_reajuste_sprint3.py"),
        "protocol_sha256": report["protocol_sha256"],
        "sklearn_version": version,
        "first_origin": refit_origins.origin.min().isoformat(),
        "last_target": refit_origins.target_3.max().isoformat(),
        "metrics": metrics,
    })
    for row in metrics:
        print(f'+{row["horizon"]} h: n={row["n"]}, MAE={row["mae"]:.6f}, RMSE={row["rmse"]:.6f}, R²={row["r2"]:.6f}')


if __name__ == "__main__":
    main()
