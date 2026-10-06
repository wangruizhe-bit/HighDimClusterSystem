import numpy as np
import pandas as pd
import pytest
from core.preprocessing import (
    drop_missing, fill_missing, remove_duplicates, scale_numeric
)

def test_delete_missing():
    original = pd.DataFrame({"x": [1, None, 3], "group": ["a","b","c"]})
    assert len(drop_missing(original)) == 2
    assert len(original) == 3

def test_fill_mean_and_median():
    original = pd.DataFrame({"x": [1., 2., 100., np.nan], "label": ["a","b","c","d"]})
    mean = fill_missing(original, "mean")
    median = fill_missing(original, "median")
    assert mean.loc[3, "x"] == pytest.approx(103/3)
    assert median.loc[3, "x"] == 2.
    assert pd.isna(original.loc[3, "x"])

def test_all_missing_numeric_rejected():
    with pytest.raises(ValueError):
        fill_missing(pd.DataFrame({"x":[np.nan,np.nan]}))

def test_duplicates():
    original = pd.DataFrame({"x":[1,1,2], "label":["a","a","b"]})
    assert len(remove_duplicates(original)) == 2

def test_scalers_preserve_category():
    original = pd.DataFrame({"x":[0.,10.,20.], "label":["a","b","c"]})
    z = scale_numeric(original, "zscore")
    mm = scale_numeric(original, "minmax")
    assert z["x"].mean() == pytest.approx(0)
    assert z["x"].std(ddof=0) == pytest.approx(1)
    assert mm["x"].tolist() == pytest.approx([0, .5, 1])
    assert mm["label"].tolist() == original["label"].tolist()

def test_scaling_rejects_missing():
    with pytest.raises(ValueError):
        scale_numeric(pd.DataFrame({"x":[1.,np.nan]}))
