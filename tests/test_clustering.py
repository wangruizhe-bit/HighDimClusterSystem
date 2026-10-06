"""第四阶段：聚类数学正确性、噪声语义、K 扫描与错误条件。"""
import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from core.clustering import fit_clustering, search_k, evaluate_labels


@pytest.fixture
def data():
    x, _ = make_blobs(n_samples=90, n_features=4, centers=3,
                      cluster_std=.4, random_state=10)
    return pd.DataFrame(x, columns=["a", "b", "c", "d"]).assign(tag="training")


def test_kmeans_is_real_and_matches_sklearn(data):
    original = data.copy(deep=True)
    result = fit_clustering(data, method="kmeans", n_clusters=3, random_state=24)
    x = StandardScaler().fit_transform(data[list("abcd")])
    expected = KMeans(n_clusters=3, n_init=10, max_iter=300, random_state=24).fit(x)
    np.testing.assert_array_equal(result.labels["簇标签"].to_numpy(), expected.labels_)
    assert result.metrics["inertia"] == pytest.approx(expected.inertia_)
    assert result.metrics["silhouette"] == pytest.approx(silhouette_score(x, expected.labels_))
    assert result.metrics["calinski_harabasz"] > 0
    assert result.metrics["davies_bouldin"] >= 0
    assert result.centers.shape == (3, 5)
    assert sum(result.counts["样本数"]) == 90
    assert result.coords.shape == (90, 5)
    assert result.n_clusters == 3
    pd.testing.assert_frame_equal(data, original)


def test_hierarchical_dendrogram_and_ward_distance(data):
    result = fit_clustering(data, method="hierarchical", n_clusters=3,
                            linkage="ward", metric="euclidean")
    assert result.linkage_matrix.shape == (89, 4)
    assert sorted(result.counts["样本数"].tolist()) == [30, 30, 30]
    assert result.n_clusters == 3
    assert np.all(result.linkage_matrix[:, 2] >= 0)
    manhattan = fit_clustering(data, method="hierarchical", n_clusters=3,
                               linkage="complete", metric="manhattan")
    assert manhattan.n_clusters == 3
    assert manhattan.linkage_matrix is not None


def test_dbscan_noise_excluded_from_scores():
    rng = np.random.default_rng(9)
    x = np.vstack([
        rng.normal(loc=(-3, 0), scale=.15, size=(30, 2)),
        rng.normal(loc=(3, 0), scale=.15, size=(30, 2)),
        [[0, 9], [0, -9]]
    ])
    frame = pd.DataFrame(x, columns=["x", "y"])
    result = fit_clustering(frame, method="dbscan", eps=.4, min_samples=4,
                            standardize=False)
    assert result.n_clusters == 2
    assert result.n_noise == 2
    assert -1 in result.labels["簇标签"].to_numpy()
    assert "噪声" in result.counts["类别"].tolist()
    assert result.metrics["silhouette"] == pytest.approx(
        silhouette_score(x[:-2], result.labels["簇标签"].to_numpy()[:-2])
    )
    assert result.metrics["noise_ratio"] == pytest.approx(2/62)
    assert "非噪声样本" in result.score_note


def test_dbscan_one_cluster_and_all_noise_undefined_metrics():
    rng = np.random.default_rng(12)
    cluster = pd.DataFrame(rng.normal(size=(30, 2)), columns=["x", "y"])
    one = fit_clustering(cluster, method="dbscan", eps=100, min_samples=4)
    assert one.n_clusters == 1
    for metric in ("silhouette", "calinski_harabasz", "davies_bouldin"):
        assert one.metrics[metric] is None
    no_cluster = fit_clustering(cluster, method="dbscan", eps=.00001, min_samples=5)
    assert no_cluster.n_clusters == 0
    assert no_cluster.n_noise == 30
    assert no_cluster.metrics["silhouette"] is None
    assert no_cluster.cluster_profile.empty


def test_k_search_inertia_and_repeatable_best(data):
    first = search_k(data, k_min=2, k_max=5, random_state=8)
    other = search_k(data, k_min=2, k_max=5, random_state=8)
    assert first.scores["K"].tolist() == [2, 3, 4, 5]
    assert np.all(np.diff(first.scores["惯性(SSE)"].to_numpy()) <= 1e-7)
    pd.testing.assert_frame_equal(first.scores, other.scores)
    assert first.suggested_k == 3
    assert first.n_samples == 90
    assert first.standardized


def test_noise_label_not_counted_as_real_class():
    x = np.array([[0,0],[0,1],[4,4],[4,5],[8,8],[8,9]], dtype=float)
    tags = np.array([0, 0, 1, 1, -1, -1])
    scores, note = evaluate_labels(x, tags)
    assert scores["silhouette"] is not None
    assert "噪声" in note


@pytest.mark.parametrize("bad", [
    {"method": "unavailable"},
    {"method": "kmeans", "n_clusters": 1},
    {"method": "kmeans", "n_clusters": 90},
    {"method": "kmeans", "max_iter": 0},
    {"method": "hierarchical", "linkage": "ward", "metric": "manhattan"},
    {"method": "hierarchical", "metric": "cosine"},
    {"method": "dbscan", "eps": -1},
    {"method": "dbscan", "min_samples": 100},
    {"method": "dbscan", "eps": np.nan},
    {"method": "kmeans", "random_state": -1},
])
def test_bad_algorithms_and_params(data, bad):
    with pytest.raises(ValueError):
        fit_clustering(data, **bad)


@pytest.mark.parametrize("bad", [
    pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}),
    pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, np.nan, 3, 5]}),
    pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, np.inf, 3, 5]}),
    pd.DataFrame({"x": [1, 2, 3, 4], "y": [4, 4, 4, 4]}),
])
def test_bad_data(bad):
    with pytest.raises(ValueError):
        fit_clustering(bad)


def test_k_search_invalid_boundaries(data):
    for lo, hi in [(0, 4), (2, 90), (7, 5), (2, 40)]:
        with pytest.raises(ValueError):
            search_k(data, k_min=lo, k_max=hi)
    with pytest.raises(ValueError):
        search_k(data, columns=["a", "tag"])


def test_two_features_3d_unavailable(data):
    result = fit_clustering(data, columns=["a", "b"], method="kmeans", n_clusters=3)
    assert "PC3" not in result.coords
    assert result.coords.shape == (90, 4)
