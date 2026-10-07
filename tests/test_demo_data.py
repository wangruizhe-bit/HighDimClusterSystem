"""内置示例数据必须能支持软件的典型演示流程。"""
from pathlib import Path

import pandas as pd

from core.pca import fit_pca
from core.clustering import fit_clustering, search_k


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo_high_dimensional.csv"


def test_demo_dataset_structure_and_quality():
    frame = pd.read_csv(DEMO)
    assert frame.shape == (90, 11)
    assert frame["Sample_ID"].is_unique
    assert frame["Group"].value_counts().to_dict() == {"A": 30, "B": 30, "C": 30}
    assert frame["Batch"].nunique() == 3
    numeric = frame.select_dtypes(include="number")
    assert list(numeric.columns) == [f"Feature_{i}" for i in range(1, 9)]
    assert numeric.shape == (90, 8)
    assert int(frame.isna().sum().sum()) == 0


def test_demo_dataset_supports_pca_clustering_and_k_selection():
    frame = pd.read_csv(DEMO)
    pca = fit_pca(frame, selection="manual", component_count=3)
    assert pca.score_table.shape == (90, 4)
    assert pca.chosen_components == 3
    assert pca.retained_variance > 0.70

    cluster = fit_clustering(
        frame, method="kmeans", n_clusters=3, random_state=42, standardize=True
    )
    assert cluster.n_clusters == 3
    assert cluster.n_noise == 0
    assert cluster.metrics["silhouette"] is not None
    assert cluster.metrics["silhouette"] > 0.45

    sweep = search_k(frame, k_min=2, k_max=6, random_state=42)
    assert sweep.suggested_k == 3
