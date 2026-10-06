"""主成分分析：严格输入验证、谱分解、载荷及得分，计算独立于 GUI。"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .statistics import numeric_data


@dataclass(frozen=True)
class PCAResult:
    columns: tuple[str, ...]
    sample_count: int
    standardized: bool
    selection: str
    chosen_components: int
    total_components: int
    retained_variance: float
    eigen_table: pd.DataFrame
    coefficient_table: pd.DataFrame
    loading_table: pd.DataFrame
    score_table: pd.DataFrame


def fit_pca(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
    *,
    standardize: bool = True,
    selection: str = "auto",
    component_count: int | None = None,
    variance_threshold: float = 0.85,
) -> PCAResult:
    """分析 PCA：auto 推荐累计>=85%；manual 指定个数；threshold 自定义阈值。

    特征向量为主成分系数；载荷定义为变量和对应主成分得分的 Pearson 相关系数。
    """
    features = numeric_data(frame, columns)
    if columns is not None and len(features.columns) != len(columns):
        raise ValueError("参与主成分分析的变量必须全部为数值型。")
    n, p = features.shape
    if n < 3:
        raise ValueError("主成分分析至少需要 3 行样本。")
    if p < 2:
        raise ValueError("主成分分析至少需要 2 个数值变量。")
    try:
        values = features.to_numpy(dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("数值变量包含无法转换的数值。") from exc
    if not np.isfinite(values).all():
        raise ValueError("数据中存在缺失值或无穷值，请先清洗。")
    spreads = np.std(values, axis=0)
    if not np.isfinite(spreads).all() or np.any(spreads == 0):
        raise ValueError("存在常数变量（标准差为零），请取消选择或删除该变量。")
    if selection not in {"auto", "manual", "threshold"}:
        raise ValueError("请选择有效的主成分数量确定方式。")
    count = min(n, p)
    if selection == "manual":
        if isinstance(component_count, bool) or not isinstance(component_count, (int, np.integer)):
            raise ValueError("指定主成分数量必须为整数。")
        if not 1 <= int(component_count) <= count:
            raise ValueError(f"主成分数量必须在 1 到 {count} 之间。")
    if selection == "threshold":
        if not isinstance(variance_threshold, (int, float, np.floating)) or not (
            np.isfinite(variance_threshold) and 0 < variance_threshold <= 1
        ):
            raise ValueError("累计方差贡献率阈值必须大于 0% 且不超过 100%。")
    prepared = StandardScaler().fit_transform(values) if standardize else values
    model = PCA(n_components=count, svd_solver="full")
    all_scores = model.fit_transform(prepared)
    ratios = model.explained_variance_ratio_
    if not np.isfinite(ratios).all():
        raise ValueError("无法计算有效的方差贡献率。")
    cumulative = np.cumsum(ratios)
    if selection == "manual":
        k = int(component_count)
    else:
        goal = 0.85 if selection == "auto" else float(variance_threshold)
        k = min(count, int(np.searchsorted(cumulative, goal, side="left") + 1))
    pcs = [f"PC{i + 1}" for i in range(k)]
    all_pcs = [f"PC{i + 1}" for i in range(count)]
    vectors = model.components_[:k].T
    scores_sd = np.sqrt(model.explained_variance_[:k])
    feature_sd = np.std(prepared, axis=0, ddof=1)
    loadings = np.clip(vectors * scores_sd[np.newaxis, :] / feature_sd[:, np.newaxis], -1., 1.)
    eigen = pd.DataFrame({
        "主成分": all_pcs,
        "特征值": model.explained_variance_,
        "方差贡献率(%)": ratios * 100,
        "累计贡献率(%)": cumulative * 100,
    })
    coefficients = pd.DataFrame(vectors, columns=pcs)
    coefficients.insert(0, "变量", [str(c) for c in features.columns])
    loading_table = pd.DataFrame(loadings, columns=pcs)
    loading_table.insert(0, "变量", [str(c) for c in features.columns])
    score_table = pd.DataFrame(all_scores[:, :k], columns=pcs)
    score_table.insert(0, "样本序号", np.arange(1, n + 1))
    return PCAResult(
        columns=tuple(str(c) for c in features.columns),
        sample_count=n, standardized=bool(standardize),
        selection=selection, chosen_components=k, total_components=count,
        retained_variance=float(cumulative[k - 1]),
        eigen_table=eigen, coefficient_table=coefficients,
        loading_table=loading_table, score_table=score_table,
    )
