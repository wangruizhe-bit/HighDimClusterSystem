"""因子分析、度量 MDS 与 t-SNE 的数值计算层。

所有输入都采用用户直接测量的数值变量。不将辅助指标视作新数据维度。
方法间只对同一数据、变量、预处理和输出维度的局部邻域保持度作有限比较。
"""
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from sklearn.decomposition import FactorAnalysis
from sklearn.manifold import MDS, TSNE, trustworthiness
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

from core.statistics import numeric_data


METHOD_LABELS = {
    "factor": "因子分析",
    "mds": "MDS 多维尺度分析",
    "tsne": "t-SNE",
}


@dataclass(frozen=True)
class ReductionResult:
    """运行结果快照（坐标独立于输入工作表）。"""

    method: str
    method_label: str
    columns: tuple[str, ...]
    sample_count: int
    dimensions: int
    standardized: bool
    parameters: dict
    coordinates: pd.DataFrame
    factor_loadings: pd.DataFrame | None
    uniqueness: pd.DataFrame | None
    metrics: dict[str, float | None]
    neighborhood_k: int | None
    elapsed_seconds: float

    @property
    def comparability_key(self) -> tuple:
        """对比条件：相同数据版本应由应用层进行校验。"""
        return (self.columns, self.sample_count, self.standardized, self.dimensions)


def fit_reduction(
    frame: pd.DataFrame,
    *,
    method: str,
    columns: list[str] | None = None,
    n_components: int = 2,
    standardize: bool = True,
    random_state: int = 42,
    rotation: str = "varimax",
    mds_distance: str = "euclidean",
    mds_max_iter: int = 300,
    mds_n_init: int = 2,
    tsne_perplexity: float = 30.0,
    tsne_learning_rate: float | str = "auto",
    tsne_max_iter: int = 1000,
) -> ReductionResult:
    """执行降维并报告真实指标。

    因子分析：因子载荷与独特方差、平均对数似然。
    MDS：以实际输入距离矩阵为目标的原始与标准化距离残差。
    t-SNE：KL 散度。以上专有指标没有跨算法意义，不能互相排序。
    共同对比指标仅在相同输入条件下使用 trustworthiness（欧氏局部邻域）。
    """
    if method not in METHOD_LABELS:
        raise ValueError("降维方法必须为 factor、mds 或 tsne。")
    data = numeric_data(frame, columns)
    if columns is not None and len(data.columns) != len(columns):
        raise ValueError("所选字段必须全部为数值变量。")
    n_samples, n_features = data.shape
    if n_samples < 4:
        raise ValueError("降维分析至少需要 4 个样本。")
    if n_features < 2:
        raise ValueError("降维分析至少需要 2 个数值变量。")
    if type(n_components) is not int or n_components not in (2, 3):
        raise ValueError("目标维度必须是 2 或 3。")
    if method == "factor" and n_components > min(n_features, n_samples - 1):
        raise ValueError("因子数不能超过变量数或样本数减一。")
    if type(random_state) is not int or not 0 <= random_state <= 2147483647:
        raise ValueError("随机种子应为 0 到 2147483647 的整数。")
    try:
        values = data.to_numpy(dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("变量包含无法转换成有限数值的内容。") from exc
    if not np.isfinite(values).all():
        raise ValueError("存在缺失或无穷数值，请先进行数据清洗。")
    if (np.std(values, axis=0) <= 0).any():
        raise ValueError("存在常数变量，必须先将其移除。")
    normalized = bool(standardize)
    x = StandardScaler().fit_transform(values) if normalized else values
    if not np.isfinite(x).all():
        raise ValueError("数据的数值范围过大，无法稳定计算。")

    parameters: dict = {"random_state": random_state}
    result_loadings = None
    uniqueness = None
    metrics: dict[str, float | None] = {}
    timer = perf_counter()
    if method == "factor":
        if rotation not in ("none", "varimax", "quartimax"):
            raise ValueError("旋转方法只能为 none、varimax 或 quartimax。")
        model = FactorAnalysis(
            n_components=n_components,
            rotation=None if rotation == "none" else rotation,
            random_state=random_state,
        )
        try:
            reduced = model.fit_transform(x)
            likelihood = float(model.score(x))
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            raise ValueError("因子分析无法收敛或数据不适合该模型。") from exc
        names = [f"因子{i + 1}" for i in range(n_components)]
        result_loadings = pd.DataFrame(model.components_.T, columns=names)
        result_loadings.insert(0, "变量", [str(col) for col in data.columns])
        uniqueness = pd.DataFrame({
            "变量": [str(col) for col in data.columns],
            "独特方差": np.asarray(model.noise_variance_, dtype=float),
        })
        metrics["log_likelihood"] = likelihood
        parameters["rotation"] = rotation
    elif method == "mds":
        if mds_distance not in ("euclidean", "manhattan"):
            raise ValueError("MDS 距离仅支持 euclidean 或 manhattan。")
        if type(mds_max_iter) is not int or not 30 <= mds_max_iter <= 3000:
            raise ValueError("MDS 最大迭代数必须为 30–3000。")
        if type(mds_n_init) is not int or not 1 <= mds_n_init <= 8:
            raise ValueError("MDS 初始化次数必须为 1–8。")
        original_distances = pairwise_distances(x, metric=mds_distance)
        model = MDS(
            n_components=n_components,
            metric=True,
            dissimilarity="precomputed",
            max_iter=mds_max_iter,
            n_init=mds_n_init,
            random_state=random_state,
            normalized_stress=False,
            n_jobs=1,
        )
        try:
            reduced = model.fit_transform(original_distances)
        except (ValueError, FloatingPointError) as exc:
            raise ValueError("MDS 计算失败，请检查距离矩阵和参数。") from exc
        high = original_distances[np.triu_indices(n_samples, k=1)]
        low = pdist(reduced, metric="euclidean")
        squared = float(np.sum((high - low) ** 2))
        denom = float(np.sum(high ** 2))
        metrics["raw_stress"] = squared
        metrics["stress_ratio"] = float(np.sqrt(squared / denom)) if denom > 0 else None
        parameters.update({"distance": mds_distance, "max_iter": mds_max_iter,
                           "n_init": mds_n_init})
    else:
        if not isinstance(tsne_perplexity, (int, float, np.integer, np.floating)) or (
            not np.isfinite(tsne_perplexity) or not 0 < tsne_perplexity < n_samples
        ):
            raise ValueError(f"t-SNE perplexity 必须大于 0 且小于样本数 {n_samples}。")
        if type(tsne_max_iter) is not int or not 250 <= tsne_max_iter <= 5000:
            raise ValueError("t-SNE 迭代次数必须为 250–5000。")
        if tsne_learning_rate != "auto" and (
            not isinstance(tsne_learning_rate, (int, float, np.floating)) or
            not np.isfinite(tsne_learning_rate) or tsne_learning_rate <= 0
        ):
            raise ValueError("t-SNE 学习率必须为 auto 或正数。")
        model = TSNE(
            n_components=n_components,
            perplexity=float(tsne_perplexity),
            learning_rate=tsne_learning_rate,
            max_iter=tsne_max_iter,
            init="pca" if n_features >= n_components else "random",
            random_state=random_state,
            method="barnes_hut",
        )
        try:
            reduced = model.fit_transform(x)
        except (ValueError, FloatingPointError) as exc:
            raise ValueError("t-SNE 无法完成计算，请调整 perplexity 或迭代次数。") from exc
        metrics["kl_divergence"] = float(model.kl_divergence_)
        parameters.update({"perplexity": float(tsne_perplexity),
                           "learning_rate": tsne_learning_rate,
                           "max_iter": tsne_max_iter})
    reduced = np.asarray(reduced, dtype=np.float64)
    if reduced.shape != (n_samples, n_components) or not np.isfinite(reduced).all():
        raise ValueError("计算产生非有限坐标，请调整分析参数。")

    # trustworthiness 计算开销 O(n²)，大数据集不在 GUI 主线程外额外重复计算。
    k = min(5, (n_samples - 1) // 2) if n_samples <= 1500 else None
    metrics["trustworthiness"] = (
        float(trustworthiness(x, reduced, n_neighbors=k)) if k is not None else None
    )
    coords = pd.DataFrame(
        reduced, columns=[f"维度{i + 1}" for i in range(n_components)]
    )
    coords.insert(0, "样本序号", np.arange(1, n_samples + 1))
    return ReductionResult(
        method=method,
        method_label=METHOD_LABELS[method],
        columns=tuple(str(col) for col in data.columns),
        sample_count=n_samples,
        dimensions=n_components,
        standardized=normalized,
        parameters=parameters,
        coordinates=coords,
        factor_loadings=result_loadings,
        uniqueness=uniqueness,
        metrics=metrics,
        neighborhood_k=k,
        elapsed_seconds=round(perf_counter() - timer, 4),
    )
