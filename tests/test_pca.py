"""PCA 数学结果、模式、异常与稳定性检查。"""
import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA as SklearnPCA
from sklearn.preprocessing import StandardScaler
from core.pca import fit_pca


@pytest.fixture
def dataset():
    rng = np.random.default_rng(180)
    x = rng.normal(size=(60, 4))
    x[:, 1] = 1.5 * x[:, 0] + 0.2 * x[:, 1]
    x[:, 3] = 2 * x[:, 2] + 0.3 * x[:, 3]
    return pd.DataFrame(x, columns=list("ABCD")).assign(label="test")


def test_eigen_and_scores_match_sklearn(dataset):
    result = fit_pca(dataset, standardize=True, selection="manual", component_count=3)
    expected = SklearnPCA(n_components=4, svd_solver="full")
    scores = expected.fit_transform(StandardScaler().fit_transform(dataset[list("ABCD")]))
    assert result.chosen_components == 3
    assert result.total_components == 4
    np.testing.assert_allclose(result.eigen_table["特征值"].to_numpy(),
                               expected.explained_variance_)
    np.testing.assert_allclose(result.eigen_table["方差贡献率(%)"].to_numpy() / 100,
                               expected.explained_variance_ratio_)
    np.testing.assert_allclose(result.score_table[["PC1", "PC2", "PC3"]].to_numpy(),
                               scores[:, :3])
    assert result.score_table.shape == (60, 4)


def test_manual_auto_threshold(dataset):
    one = fit_pca(dataset, selection="manual", component_count=1)
    assert list(one.score_table.columns) == ["样本序号", "PC1"]
    threshold = fit_pca(dataset, selection="threshold", variance_threshold=.9)
    assert threshold.retained_variance >= .9
    if threshold.chosen_components > 1:
        assert threshold.eigen_table["累计贡献率(%)"].iat[threshold.chosen_components-2] < 90
    auto = fit_pca(dataset, selection="auto", variance_threshold=.99)
    assert auto.retained_variance >= .85
    assert auto.chosen_components <= threshold.chosen_components


def test_correlation_loadings(dataset):
    output = fit_pca(dataset, standardize=False, selection="manual", component_count=2)
    for component in ("PC1", "PC2"):
        for name in "ABCD":
            corr = np.corrcoef(dataset[name], output.score_table[component])[0, 1]
            actual = output.loading_table.set_index("变量").loc[name, component]
            assert actual == pytest.approx(corr, abs=1e-12)


def test_input_immutable(dataset):
    snapshot = dataset.copy(deep=True)
    fit_pca(dataset, columns=["A", "B"], selection="manual", component_count=2)
    pd.testing.assert_frame_equal(dataset, snapshot)


@pytest.mark.parametrize("frame", [
    pd.DataFrame({"A": [1, 2]}),
    pd.DataFrame({"A": [1, 2, 3], "B": [2, np.nan, 4]}),
    pd.DataFrame({"A": [1, 2, 3], "B": [3, np.inf, 4]}),
    pd.DataFrame({"A": [1, 2, 3], "B": [1, 1, 1]}),
])
def test_invalid_frames(frame):
    with pytest.raises(ValueError):
        fit_pca(frame)


def test_invalid_parameters(dataset):
    for k in [0, 5, 1.5, True]:
        with pytest.raises(ValueError):
            fit_pca(dataset, selection="manual", component_count=k)
    for threshold in [0, -.1, 1.1, np.inf]:
        with pytest.raises(ValueError):
            fit_pca(dataset, selection="threshold", variance_threshold=threshold)
    with pytest.raises(ValueError):
        fit_pca(dataset, columns=["A", "label"])
    with pytest.raises(ValueError):
        fit_pca(dataset, selection="invalid")


def test_wide_data():
    rng = np.random.default_rng(11)
    result = fit_pca(pd.DataFrame(rng.normal(size=(5, 10))),
                     selection="manual", component_count=3)
    assert result.total_components == 5
    assert len(result.eigen_table) == 5
    assert result.score_table.shape == (5, 4)
