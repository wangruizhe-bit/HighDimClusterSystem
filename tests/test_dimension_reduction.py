"""三类降维算法的数值、合法性、可重复性与方法指标测试。"""
import numpy as np
import pandas as pd
import pytest
from scipy.spatial.distance import pdist
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler

from core.dimension_reduction import fit_reduction


@pytest.fixture
def dataset():
    rng = np.random.default_rng(2026)
    matrix = rng.normal(size=(45, 5))
    matrix[:, 2] += matrix[:, 0]
    matrix[:, 4] = 2 * matrix[:, 1] + matrix[:, 4] * .2
    return pd.DataFrame(matrix, columns=list("ABCDE")).assign(kind="trial")


def test_factor_matches_sklearn_and_has_interpretable_loadings(dataset):
    result = fit_reduction(dataset, method="factor", n_components=2, rotation="varimax")
    matrix = StandardScaler().fit_transform(dataset[list("ABCDE")])
    model = FactorAnalysis(n_components=2, rotation="varimax", random_state=42)
    expected = model.fit_transform(matrix)
    np.testing.assert_allclose(result.coordinates[["维度1", "维度2"]].to_numpy(),
                               expected, rtol=1e-7, atol=1e-7)
    np.testing.assert_allclose(result.factor_loadings[["因子1", "因子2"]].to_numpy(),
                               model.components_.T)
    np.testing.assert_allclose(result.uniqueness["独特方差"].to_numpy(),
                               model.noise_variance_)
    assert np.isfinite(result.metrics["log_likelihood"])
    assert result.sample_count == 45


def test_mds_stress_and_reproducibility(dataset):
    r1 = fit_reduction(dataset, method="mds", n_components=3, mds_distance="manhattan",
                       mds_max_iter=90, mds_n_init=1)
    r2 = fit_reduction(dataset, method="mds", n_components=3, mds_distance="manhattan",
                       mds_max_iter=90, mds_n_init=1)
    assert r1.coordinates.shape == (45, 4)
    assert r1.metrics["raw_stress"] >= 0
    assert 0 <= r1.metrics["stress_ratio"] < 2
    np.testing.assert_allclose(r1.coordinates, r2.coordinates)
    assert r1.neighborhood_k == 5
    assert 0 <= r1.metrics["trustworthiness"] <= 1


def test_tsne_is_real_and_reproducible(dataset):
    a = fit_reduction(dataset, method="tsne", n_components=2,
                      tsne_perplexity=8, tsne_max_iter=350, random_state=13)
    b = fit_reduction(dataset, method="tsne", n_components=2,
                      tsne_perplexity=8, tsne_max_iter=350, random_state=13)
    assert a.metrics["kl_divergence"] >= 0
    assert a.coordinates.shape == (45, 3)
    np.testing.assert_allclose(a.coordinates, b.coordinates, rtol=1e-6, atol=1e-6)


def test_three_dimensional_tsne_and_rotation_option(dataset):
    tsne = fit_reduction(dataset, method="tsne", n_components=3,
                         tsne_perplexity=10, tsne_max_iter=300)
    assert tsne.coordinates.shape == (45, 4)
    factor = fit_reduction(dataset, method="factor", n_components=3,
                           rotation="quartimax", standardize=False)
    assert factor.factor_loadings.shape == (5, 4)
    assert factor.standardized is False


def test_selected_columns_dont_mutate_frame(dataset):
    original = dataset.copy(deep=True)
    result = fit_reduction(dataset, method="factor", columns=["A", "B", "C"],
                           n_components=2, rotation="none")
    assert result.columns == ("A", "B", "C")
    pd.testing.assert_frame_equal(dataset, original)


@pytest.mark.parametrize("frame", [
    pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]}),
    pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, np.nan, 2, 4]}),
    pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, np.inf, 2, 4]}),
    pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 1, 1, 1]}),
])
def test_invalid_dataset(frame):
    with pytest.raises(ValueError):
        fit_reduction(frame, method="mds")


def test_invalid_parameters(dataset):
    variants = [
        {"method": "unknown"},
        {"method": "factor", "n_components": 4, "columns": ["A", "B", "C"]},
        {"method": "factor", "rotation": "oblimin"},
        {"method": "mds", "mds_distance": "cosine"},
        {"method": "mds", "mds_max_iter": 0},
        {"method": "mds", "mds_n_init": 0},
        {"method": "tsne", "tsne_perplexity": 45},
        {"method": "tsne", "tsne_perplexity": 0},
        {"method": "tsne", "tsne_max_iter": 200},
        {"method": "tsne", "tsne_learning_rate": -1},
        {"method": "factor", "n_components": 4},
        {"method": "factor", "random_state": -3},
    ]
    for params in variants:
        method = params.pop("method")
        if method == "factor" and params.get("n_components") == 4 and "columns" not in params:
            params["n_components"] = 4.3
        with pytest.raises(ValueError):
            fit_reduction(dataset, method=method, **params)


def test_mds_distance_consistency(dataset):
    result = fit_reduction(dataset, method="mds", n_components=2,
                           mds_distance="euclidean", mds_n_init=1, mds_max_iter=90)
    std = StandardScaler().fit_transform(dataset[list("ABCDE")])
    original = pdist(std, metric="euclidean")
    embedded = pdist(result.coordinates[["维度1", "维度2"]])
    measured = np.sqrt(np.sum((original - embedded) ** 2) / np.sum(original ** 2))
    assert result.metrics["stress_ratio"] == pytest.approx(measured, rel=1e-8)


def test_tsne_tiny_perplexity_rejected(dataset):
    with pytest.raises(ValueError):
        fit_reduction(dataset, method="tsne", tsne_perplexity=np.nan)
    with pytest.raises(ValueError):
        fit_reduction(dataset, method="tsne", columns=["A", "kind"])
