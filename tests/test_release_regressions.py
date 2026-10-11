"""Release edge cases; existing tests remain unchanged."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from core.clustering import evaluate_labels, fit_clustering
from core.dimension_reduction import fit_reduction
from core.preprocessing import fill_missing, scale_numeric
from core.pca import fit_pca
from tools.verify_release import check_bundle


def test_more_clusters_than_silhouette_budget_is_not_a_crash():
    x = np.random.default_rng(2).normal(size=(2600, 2))
    labels = np.repeat(np.arange(1300), 2)
    scores, note = evaluate_labels(x, labels)
    assert scores["silhouette"] is None
    assert np.isfinite(scores["calinski_harabasz"])
    assert np.isfinite(scores["davies_bouldin"])
    assert "抽样上限" in note


def test_manhattan_clustering_uses_manhattan_silhouette():
    data = pd.DataFrame(np.random.default_rng(10).normal(size=(30, 3)))
    result = fit_clustering(data, method="hierarchical", linkage="average", metric="manhattan")
    x = StandardScaler().fit_transform(data)
    expected = silhouette_score(x, result.labels["簇标签"], metric="manhattan")
    assert result.metrics["silhouette"] == pytest.approx(expected)


def test_tsne_requires_optimization_after_early_exaggeration():
    data = pd.DataFrame(np.random.default_rng(10).normal(size=(30, 3)))
    with pytest.raises(ValueError, match="250"):
        fit_reduction(data, method="tsne", tsne_max_iter=250, tsne_perplexity=8)
    result = fit_reduction(data, method="tsne", tsne_max_iter=300, tsne_perplexity=8)
    assert 0 <= result.metrics["kl_divergence"] < 100


@pytest.mark.parametrize("operation", [fill_missing, scale_numeric])
def test_cleaning_rejects_infinite_values_without_mutating_input(operation):
    data = pd.DataFrame({"a": [1., np.inf, 3.], "b": [2., 4., 6.]})
    original = data.copy(deep=True)
    with pytest.raises(ValueError, match="无穷"):
        operation(data)
    pd.testing.assert_frame_equal(data, original)


def test_duplicate_selection_cannot_duplicate_pca_features():
    data = pd.DataFrame({"a": [1., 2., 3., 4.], "b": [4., 2., 1., 3.]})
    with pytest.raises(ValueError, match="重复"):
        fit_pca(data, columns=["a", "a", "b"])


def test_release_hash_check_detects_corruption_outside_sklearn(tmp_path):
    import shutil
    original = tmp_path / "original"
    dll = original / "_internal/sklearn/.libs/vcomp140.dll"
    dll.parent.mkdir(parents=True)
    dll.write_bytes(b"x" * 4096)
    (original / "HighDimClusterSystem.exe").write_bytes(b"original")
    downloaded = tmp_path / "downloaded"
    shutil.copytree(original, downloaded)
    (downloaded / "HighDimClusterSystem.exe").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA256"):
        check_bundle(original, downloaded)
