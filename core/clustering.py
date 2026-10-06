"""独立于 Qt 的聚类计算：K-means、凝聚层次聚类、DBSCAN 与质量评价。

聚类在标准化后（可选）的选定数值特征空间执行；
绘图所用 PCA 投影仅用于可视化，不会改变聚类标签或评价指标。
DBSCAN 噪声标签 -1 从质量评价中剔除，并明确报告被剔除数量。
"""
from dataclasses import dataclass
from time import perf_counter
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage as scipy_linkage
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    calinski_harabasz_score, davies_bouldin_score, silhouette_score,
)
from sklearn.preprocessing import StandardScaler
from core.statistics import numeric_data

ALGORITHMS = {
    "kmeans": "K-means",
    "hierarchical": "层次聚类",
    "dbscan": "DBSCAN",
}


@dataclass(frozen=True)
class ClusterResult:
    algorithm: str
    label: str
    columns: tuple[str, ...]
    n_samples: int
    standardized: bool
    parameters: dict
    labels: pd.DataFrame
    counts: pd.DataFrame
    cluster_profile: pd.DataFrame
    centers: pd.DataFrame | None
    coords: pd.DataFrame
    projection_ratios: tuple[float, ...]
    metrics: dict
    score_note: str
    n_clusters: int
    n_noise: int
    linkage_matrix: np.ndarray | None
    elapsed_seconds: float

    @property
    def comparability_key(self):
        return (self.columns, self.n_samples, self.standardized)


@dataclass(frozen=True)
class KSearchResult:
    columns: tuple[str, ...]
    n_samples: int
    standardized: bool
    seed: int
    max_iter: int
    scores: pd.DataFrame
    suggested_k: int | None
    elapsed_seconds: float


def prepare_matrix(frame, columns=None, *, standardize=True):
    data = numeric_data(frame, columns)
    if columns is not None and len(data.columns) != len(columns):
        raise ValueError("参与聚类的变量必须全部是数值变量。")
    if len(data) < 4:
        raise ValueError("聚类分析至少需要 4 行样本。")
    if len(data.columns) < 2:
        raise ValueError("聚类分析至少需要 2 个数值变量。")
    try:
        raw = data.to_numpy(dtype=np.float64, copy=True)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("数值变量包含无法转换的数据。") from exc
    if not np.isfinite(raw).all():
        raise ValueError("数据中存在缺失值或无穷值，请先进行数据清洗。")
    if np.any(np.std(raw, axis=0) == 0):
        raise ValueError("数据中存在常数变量，请取消选择或删除该变量。")
    scaler = StandardScaler() if standardize else None
    values = scaler.fit_transform(raw) if scaler else raw.copy()
    if not np.isfinite(values).all():
        raise ValueError("数据数值范围过大，无法稳定计算。")
    return data.copy(deep=True), values, scaler


def _validate_options(method, n, k, linkage, metric, max_iter, seed, eps, min_samples):
    if method not in ALGORITHMS:
        raise ValueError("聚类算法必须为 kmeans、hierarchical 或 dbscan。")
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise ValueError("随机种子必须为非负 32 位整数。")
    if method != "dbscan":
        if type(k) is not int or not 2 <= k < n:
            raise ValueError(f"聚类数 K 必须是 2 到 {n-1} 之间的整数。")
    if method == "kmeans":
        if type(max_iter) is not int or not 10 <= max_iter <= 3000:
            raise ValueError("K-means 迭代次数应在 10–3000 之间。")
    if method == "hierarchical":
        if n > 4000:
            raise ValueError("层次聚类最多支持 4000 行样本，以避免高内存占用。")
        if linkage not in ("ward", "complete", "average", "single"):
            raise ValueError("无效的层次聚类 linkage 方法。")
        if metric not in ("euclidean", "manhattan"):
            raise ValueError("距离度量只能为 euclidean 或 manhattan。")
        if linkage == "ward" and metric != "euclidean":
            raise ValueError("Ward 层次聚类只支持欧氏距离。")
    if method == "dbscan":
        if n > 10000:
            raise ValueError("DBSCAN 最多支持 10000 行样本，以避免高内存占用。")
        if metric not in ("euclidean", "manhattan"):
            raise ValueError("距离度量只能为 euclidean 或 manhattan。")
        if not isinstance(eps, (int, float, np.floating)) or not (
            np.isfinite(eps) and eps > 0
        ):
            raise ValueError("DBSCAN eps 必须是大于 0 的有限数值。")
        if type(min_samples) is not int or not 2 <= min_samples <= n:
            raise ValueError("DBSCAN min_samples 必须为 2 到样本数之间的整数。")


def evaluate_labels(x, labels, *, seed=42):
    """对 DBSCAN 的非噪声样本单独评分；无效分割不产生虚假指标。"""
    labels = np.asarray(labels, dtype=int)
    valid = labels != -1
    data = x[valid]
    y = labels[valid]
    count = len(np.unique(y))
    scores = {"silhouette": None, "calinski_harabasz": None,
              "davies_bouldin": None}
    if count < 2 or count >= len(y):
        return scores, "无法计算：至少需要两个非噪声簇，且每簇组合不能全是单个样本。"
    # silhouette 是 O(n²) 距离计算；对过大的样本采取可复现抽样。
    size = min(len(y), 1200)
    if size == len(y):
        scores["silhouette"] = float(silhouette_score(data, y))
    else:
        rng = np.random.default_rng(seed)
        # 首先在各个有效簇内抽取至少一条，防止随机样本遗漏小簇。
        indices = [int(rng.choice(np.flatnonzero(y == cls))) for cls in np.unique(y)]
        remainder = np.setdiff1d(np.arange(len(y)), indices)
        indices.extend(rng.choice(remainder, size=size - len(indices), replace=False).tolist())
        sampled = np.asarray(indices, dtype=int)
        if 2 <= len(np.unique(y[sampled])) < len(sampled):
            scores["silhouette"] = float(silhouette_score(data[sampled], y[sampled]))
    scores["calinski_harabasz"] = float(calinski_harabasz_score(data, y))
    scores["davies_bouldin"] = float(davies_bouldin_score(data, y))
    note = ("质量指标仅基于非噪声样本；噪声未计入评分。" if (~valid).any()
            else "质量指标基于参与聚类的全部样本。")
    if len(y) > 1200:
        note += " 轮廓系数使用最多 1200 个样本的固定随机种子抽样。"
    return scores, note


def fit_clustering(frame, *, method="kmeans", columns=None, standardize=True,
                   n_clusters=3, linkage="ward", metric="euclidean",
                   max_iter=300, random_state=42, eps=.5, min_samples=5):
    """执行真实聚类并返回标签、中心/树、类别统计、质量指标与绘图坐标。"""
    source, x, scaler = prepare_matrix(frame, columns, standardize=standardize)
    n = len(source)
    _validate_options(method, n, n_clusters, linkage, metric, max_iter,
                      random_state, eps, min_samples)
    started = perf_counter()
    if method in ("kmeans", "hierarchical") and len(np.unique(x, axis=0)) < n_clusters:
        raise ValueError("不同特征组合数少于目标聚类数 K，无法形成要求的类别。")
    parameters = {"standardize": bool(standardize)}
    hierarchy_tree = None
    centers = None
    inertia = None
    if method == "kmeans":
        model = KMeans(n_clusters=n_clusters, n_init=10, max_iter=max_iter,
                       random_state=random_state)
        labels = model.fit_predict(x)
        originals = scaler.inverse_transform(model.cluster_centers_) if scaler else model.cluster_centers_
        centers = pd.DataFrame(originals, columns=source.columns)
        centers.insert(0, "簇标签", np.arange(n_clusters))
        inertia = float(model.inertia_)
        parameters.update({"k": n_clusters, "max_iter": max_iter, "seed": random_state,
                           "n_init": 10})
    elif method == "hierarchical":
        model = AgglomerativeClustering(n_clusters=n_clusters, metric=metric,
                                        linkage=linkage, compute_distances=True)
        labels = model.fit_predict(x)
        children = model.children_
        sizes = np.zeros(n - 1, dtype=float)
        for i, pair in enumerate(children):
            for child in pair:
                sizes[i] += 1 if child < n else sizes[child - n]
        hierarchy_tree = np.column_stack([children, model.distances_, sizes])
        parameters.update({"k": n_clusters, "linkage": linkage, "metric": metric})
    else:
        model = DBSCAN(eps=float(eps), min_samples=min_samples, metric=metric, n_jobs=1)
        labels = model.fit_predict(x)
        parameters.update({"eps": float(eps), "min_samples": min_samples, "metric": metric})
    labels = np.asarray(labels, dtype=int)
    valid_labels = sorted(int(i) for i in np.unique(labels) if i != -1)
    noise = int(np.count_nonzero(labels == -1))
    counts = pd.DataFrame([
        {"簇标签": i, "类别": "噪声" if i == -1 else f"第{i+1}类",
         "样本数": int(np.sum(labels == i))}
        for i in sorted(np.unique(labels))
    ])
    samples = pd.DataFrame({"样本序号": np.arange(1, n+1), "簇标签": labels,
                            "类别": ["噪声" if i == -1 else f"第{i+1}类" for i in labels]})
    profiles = []
    for cluster_id in valid_labels:
        mask = labels == cluster_id
        row = {"簇标签": cluster_id, "样本数": int(mask.sum())}
        row.update({str(name): float(val) for name, val in source.loc[mask].mean().items()})
        profiles.append(row)
    profile_frame = pd.DataFrame(profiles, columns=["簇标签", "样本数", *list(source.columns)])
    scores, note = evaluate_labels(x, labels, seed=random_state)
    scores["inertia"] = inertia
    scores["noise_ratio"] = noise / n
    if method == "dbscan":
        note += " DBSCAN 允许只有一个簇或只有噪声，相关指标此时显示空值。"
    projection_dim = min(3, x.shape[1], len(x))
    pca = PCA(n_components=projection_dim, svd_solver="full")
    projection = pca.fit_transform(x)
    coordinates = pd.DataFrame(projection, columns=[f"PC{i+1}" for i in range(projection_dim)])
    coordinates.insert(0, "簇标签", labels)
    coordinates.insert(0, "样本序号", np.arange(1, n+1))
    return ClusterResult(
        algorithm=method, label=ALGORITHMS[method],
        columns=tuple(str(c) for c in source.columns),
        n_samples=n, standardized=bool(standardize), parameters=parameters,
        labels=samples, counts=counts, cluster_profile=profile_frame, centers=centers,
        coords=coordinates, projection_ratios=tuple(float(v) for v in pca.explained_variance_ratio_),
        metrics=scores, score_note=note, n_clusters=len(valid_labels),
        n_noise=noise, linkage_matrix=hierarchy_tree,
        elapsed_seconds=round(perf_counter() - started, 4),
    )


def search_k(frame, *, columns=None, standardize=True, k_min=2, k_max=10,
             max_iter=300, random_state=42):
    """真实 K-means 惯性与轮廓系数曲线；后者最大值只作为辅助建议。"""
    source, x, _ = prepare_matrix(frame, columns, standardize=standardize)
    n = len(source)
    if type(k_min) is not int or type(k_max) is not int or not (
        2 <= k_min <= k_max < n and k_max - k_min <= 28
    ):
        raise ValueError(f"K 的范围应为 2 到 {n-1}，且单次最多扫描 29 个 K 值。")
    _validate_options("kmeans", n, k_min, "ward", "euclidean",
                      max_iter, random_state, .5, 5)
    distinct = len(np.unique(x, axis=0))
    if k_max > distinct:
        raise ValueError("最大 K 不能超过数据中不同的样本特征组合数。")
    start = perf_counter()
    rows = []
    for k in range(k_min, k_max + 1):
        model = KMeans(n_clusters=k, max_iter=max_iter, n_init=10,
                       random_state=random_state)
        tags = model.fit_predict(x)
        score, _ = evaluate_labels(x, tags, seed=random_state)
        rows.append({"K": k, "惯性(SSE)": float(model.inertia_),
                     "轮廓系数": score["silhouette"]})
    table = pd.DataFrame(rows)
    eligible = table.dropna(subset=["轮廓系数"])
    suggested = int(eligible.loc[eligible["轮廓系数"].idxmax(), "K"]) if not eligible.empty else None
    return KSearchResult(tuple(str(c) for c in source.columns), n, bool(standardize),
                         random_state, max_iter, table, suggested,
                         round(perf_counter() - start, 4))
