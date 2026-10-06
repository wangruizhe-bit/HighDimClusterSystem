import pandas as pd
import pytest
from core.data_manager import DataManager

def test_csv_load_copy_and_restore(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b,group\n1,4,x\n2,5,y\n", encoding="utf-8")
    manager = DataManager()
    manager.load_file(str(path))
    assert manager.summary()["rows"] == 2
    assert manager.get_numeric_columns() == ["a", "b"]
    changed = manager.get_data()
    changed.loc[0, "a"] = 999
    assert manager.get_data().loc[0, "a"] == 1
    manager.set_data(changed)
    assert manager.get_data().loc[0, "a"] == 999
    manager.restore_original()
    assert manager.get_data().loc[0, "a"] == 1

def test_import_failure_keeps_existing_dataset(tmp_path):
    valid = tmp_path / "ok.csv"
    valid.write_text("a,b\n1,2\n", encoding="utf-8")
    manager = DataManager()
    manager.load_file(str(valid))
    with pytest.raises(ValueError):
        manager.load_file(str(tmp_path / "missing.csv"))
    assert manager.summary()["rows"] == 1

def test_excel_import(tmp_path):
    path = tmp_path / "table.xlsx"
    pd.DataFrame({"a": [1, 2], "b": [2, 3]}).to_excel(path, index=False)
    manager = DataManager()
    manager.load_file(str(path))
    assert manager.summary()["numeric"] == 2
