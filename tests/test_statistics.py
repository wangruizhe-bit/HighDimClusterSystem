import pandas as pd
import pytest
from core.statistics import describe, correlation, covariance

@pytest.fixture
def sample():
    return pd.DataFrame({"x":[1.,2.,3.], "y":[2.,4.,6.], "label":["a","b","c"]})

def test_describe(sample):
    out = describe(sample)
    assert len(out) == 2
    assert out.loc[0, "均值"] == pytest.approx(2)
    assert out.loc[0, "中位数"] == pytest.approx(2)

def test_pearson(sample):
    out = correlation(sample)
    assert out.loc["x","y"] == pytest.approx(1)

def test_covariance(sample):
    out = covariance(sample)
    assert out.loc["x","y"] == pytest.approx(2)

def test_not_enough_columns(sample):
    with pytest.raises(ValueError):
        correlation(sample, ["x"])
