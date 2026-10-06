"""结果中心的可复现导出逻辑（纯 Python，不依赖 Qt）。

CSV: 当前选择的单张真实结果表；XLSX: 现有全部真实结果表；
HTML: 仅含真实统计值和截断的表格预览（本地离线查看）。
对用户输入的单元格文本进行电子表格公式注入转义。
"""
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
import re

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResultItem:
    key: str
    title: str
    category: str
    frame: pd.DataFrame
    description: str = ""


def _numbers_as_frame(metrics, *, title="指标"):
    return pd.DataFrame(
        [{title: str(k), "数值": "不适用" if v is None else v}
         for k, v in metrics.items()]
    )


def build_catalog(
    data,
    *,
    data_name="当前数据",
    pca=None,
    reductions=(),
    clusters=(),
    k_search=None,
    feature_result=None,
):
    """收集已有结果快照；没有计算过的分析项目不会伪造表格。"""
    items = []
    if data is not None:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("当前数据集必须是 DataFrame。")
        if not data.empty:
            items.append(ResultItem("working_data", f"当前工作数据 · {data_name}", "数据集",
                                    data.copy(deep=True), "导出的为处理后的当前工作数据。"))
            basics = {
                "数据集名称": data_name,
                "样本数": len(data),
                "变量数": len(data.columns),
                "缺失单元格": int(data.isna().sum().sum()),
                "重复样本": int(data.duplicated().sum()),
            }
            items.append(ResultItem("data_summary", "数据概览", "数据集",
                                    _numbers_as_frame(basics, title="项目")))
    if feature_result is not None:
        title, frame = feature_result
        if frame is not None and not frame.empty:
            items.append(ResultItem("feature_statistics", f"特征统计 · {title}",
                                    "特征统计", frame.copy(deep=True)))

    if pca is not None:
        items.append(ResultItem("pca_parameters", "PCA · 运行参数", "PCA",
                                _numbers_as_frame({
                                    "样本数": pca.sample_count, "数值变量": ", ".join(pca.columns),
                                    "是否标准化": "是" if pca.standardized else "否",
                                    "选择策略": pca.selection, "主成分数量": pca.chosen_components,
                                    "累计方差贡献率(%)": round(pca.retained_variance * 100, 6),
                                }, title="参数")))
        for ident, name, frame in [
            ("variance", "特征值与方差贡献率", pca.eigen_table),
            ("loadings", "相关载荷", pca.loading_table),
            ("coefficients", "主成分系数", pca.coefficient_table),
            ("scores", "主成分得分", pca.score_table),
        ]:
            items.append(ResultItem(f"pca_{ident}", f"PCA · {name}", "PCA", frame.copy(deep=True),
                                    f"选用 {pca.chosen_components} 个主成分；"
                                    f"累计方差贡献率 {pca.retained_variance * 100:.2f}%。"))
    for index, result in enumerate(reductions, 1):
        prefix = f"reduce_{index}"
        text = f"第 {index} 次降维 · {result.method_label} · {result.dimensions}维"
        items.append(ResultItem(prefix + "_parameters", text + " 参数", "降维",
                                _numbers_as_frame({
                                    "方法": result.method_label, "样本数": result.sample_count,
                                    "变量": ", ".join(result.columns), "目标维数": result.dimensions,
                                    "是否标准化": "是" if result.standardized else "否",
                                    **result.parameters,
                                }, title="参数")))
        items.append(ResultItem(prefix + "_coordinates", text + " 坐标", "降维",
                                result.coordinates.copy(deep=True)))
        if result.factor_loadings is not None:
            items.append(ResultItem(prefix + "_loadings", text + " 载荷", "降维",
                                    result.factor_loadings.copy(deep=True)))
        if result.uniqueness is not None:
            items.append(ResultItem(prefix + "_uniqueness", text + " 独特方差", "降维",
                                    result.uniqueness.copy(deep=True)))
        items.append(ResultItem(prefix + "_metrics", text + " 指标", "降维",
                                _numbers_as_frame(result.metrics)))
    for index, result in enumerate(clusters, 1):
        prefix = f"cluster_{index}"
        text = f"第 {index} 次聚类 · {result.label}"
        items.append(ResultItem(prefix + "_parameters", text + " 参数", "聚类",
                                _numbers_as_frame({
                                    "算法": result.label, "样本数": result.n_samples,
                                    "变量": ", ".join(result.columns),
                                    "有效簇数": result.n_clusters, "噪声数": result.n_noise,
                                    **result.parameters,
                                }, title="参数"), result.score_note))
        for part, name, frame in [
            ("labels", "样本标签", result.labels),
            ("counts", "簇大小", result.counts),
            ("profile", "簇特征均值", result.cluster_profile),
            ("centers", "K-means 簇中心", result.centers),
        ]:
            if frame is not None:
                items.append(ResultItem(prefix + "_" + part, text + " · " + name,
                                        "聚类", frame.copy(deep=True), result.score_note))
        items.append(ResultItem(prefix + "_metrics", text + " · 质量指标", "聚类",
                                _numbers_as_frame(result.metrics), result.score_note))
    if k_search is not None:
        items.append(ResultItem("k_search_parameters", "K 值扫描 · 参数", "K 值辅助选择",
                                _numbers_as_frame({
                                    "样本数": k_search.n_samples,
                                    "变量": ", ".join(k_search.columns),
                                    "是否标准化": "是" if k_search.standardized else "否",
                                    "随机种子": k_search.seed,
                                    "迭代上限": k_search.max_iter,
                                    "建议 K": k_search.suggested_k,
                                }, title="参数")))
        items.append(ResultItem("k_search", "K 值扫描 · SSE 与轮廓系数", "K 值辅助选择",
                                k_search.scores.copy(deep=True),
                                f"最大轮廓系数对应 K={k_search.suggested_k}，仅作为辅助推荐。"))
    return items


FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def _escape_formula(value):
    """只修饰文本字段，不将负数变成文本。"""
    if isinstance(value, str) and value and (
        value.startswith(FORMULA_PREFIXES) or
        (value.lstrip(" \t").startswith(FORMULA_PREFIXES)
         and value.lstrip(" \t") != value)
    ):
        return "'" + value
    return value


def _safe_frame(frame):
    output = frame.copy(deep=True)
    for column in output.columns:
        if output[column].dtype == object or pd.api.types.is_string_dtype(output[column]):
            output[column] = output[column].map(_escape_formula)
    output.columns = [_escape_formula(str(c)) for c in output.columns]
    return output


def _validate_suffix(path, suffix):
    destination = Path(path)
    if destination.suffix.lower() != suffix:
        raise ValueError(f"文件扩展名必须为 {suffix}。")
    if not destination.parent.is_dir():
        raise ValueError("目标文件夹不存在，请重新选择。")
    return destination


def _safe_export(destination, save):
    """先写到同一磁盘的暂存位置，成功后再替换正式文件。"""
    with TemporaryDirectory(dir=destination.parent) as folder:
        temporary = Path(folder) / destination.name
        save(temporary)
        temporary.replace(destination)
    return destination


def export_csv(item, path):
    """输出所选结果表全部行，使用 utf-8-sig 方便 Windows Excel 打开。"""
    if not isinstance(item, ResultItem):
        raise ValueError("请先选择一张可导出的结果表。")
    destination = _validate_suffix(path, ".csv")
    return _safe_export(destination, lambda file: _safe_frame(item.frame).to_csv(
        file, index=False, encoding="utf-8-sig"))


def _sheet_name(text, taken):
    """Excel 名称不能超过 31 字符，且需避免特殊字符及重复。"""
    cleaned = re.sub(r"[\[\]:*?/\\]", "_", text).strip("' ") or "分析结果"
    short = cleaned[:31]
    candidate = short
    num = 2
    while candidate.lower() in taken:
        suffix = f"_{num}"
        candidate = short[:31 - len(suffix)] + suffix
        num += 1
    taken.add(candidate.lower())
    return candidate


def export_excel(items, path):
    """保存全部真实分析结果。先写临时工作簿，成功后替换目标文件。"""
    if not items:
        raise ValueError("尚无可导出的真实数据和分析结果。")
    destination = _validate_suffix(path, ".xlsx")
    for item in items:
        if not isinstance(item, ResultItem):
            raise ValueError("结果列表包含未知对象。")
        if len(item.frame) >= 1_048_576 or len(item.frame.columns) > 16_384:
            raise ValueError(f"{item.title} 超出 Excel 单表大小限制，请改用 CSV。")

    def write(temporary):
        used = set()
        with pd.ExcelWriter(temporary, engine="openpyxl") as writer:
            for item in items:
                name = _sheet_name(item.title, used)
                _safe_frame(item.frame).to_excel(writer, sheet_name=name, index=False)
                sheet = writer.sheets[name]
                sheet.freeze_panes = "A2"
                sheet.auto_filter.ref = sheet.dimensions
                for cells in sheet.iter_cols(max_row=1):
                    cells[0].font = cells[0].font.copy(bold=True)

    return _safe_export(destination, write)


def _html_table(frame, *, max_rows=10, max_columns=14):
    subset = frame.iloc[:max_rows, :max_columns]
    headers = "".join(f"<th>{escape(str(column))}</th>" for column in subset.columns)
    rows = []
    for record in subset.itertuples(index=False, name=None):
        cells = "".join(f"<td>{escape(_format_html_value(cell))}</td>" for cell in record)
        rows.append(f"<tr>{cells}</tr>")
    note = ""
    if len(frame) > max_rows or len(frame.columns) > max_columns:
        note = (
            f"<p class='muted'>预览只显示前 {max_rows} 行、前 {max_columns} 列；"
            "完整数值请使用 CSV 或 Excel 导出。</p>"
        )
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>{note}"


def _format_html_value(value):
    try:
        if bool(pd.isna(value)):
            return "—"
    except (ValueError, TypeError):
        pass
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.7g}"
    return str(value)


def export_html_report(items, path, *, application="高维数据降维与聚类分析系统 V1.0"):
    """可离线打开的 HTML 结果摘要；报告不调用外部 CDN 或联网接口。"""
    if not items:
        raise ValueError("尚无数据或分析结果，不能生成报告。")
    destination = _validate_suffix(path, ".html")
    by_group = {}
    for item in items:
        by_group.setdefault(item.category, []).append(item)
    sections = []
    for group, entries in by_group.items():
        blocks = []
        for item in entries:
            desc = f"<p>{escape(item.description)}</p>" if item.description else ""
            blocks.append(
                f"<section><h3>{escape(item.title)}</h3>{desc}"
                f"<p class='muted'>实际数据：{len(item.frame)} 行 × {len(item.frame.columns)} 列</p>"
                + _html_table(item.frame) + "</section>"
            )
        sections.append(f"<h2>{escape(group)}</h2>" + "".join(blocks))
    date = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    document = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(application)} · 结果报告</title>
<style>
body{{max-width:1100px;margin:35px auto;padding:0 24px;color:#1d3148;
font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;line-height:1.6}}
h1{{color:#174777}}h2{{margin-top:35px;border-bottom:2px solid #e1eafa;padding-bottom:9px}}
section{{padding:15px 22px;margin:13px 0;border:1px solid #e0e8f2;border-radius:9px}}
table{{border-collapse:collapse;display:block;overflow-x:auto;width:100%;font-size:13px}}
th,td{{border:1px solid #d9e5ef;padding:7px 10px;white-space:nowrap}}
th{{background:#eaf2fb}}tr:nth-child(even){{background:#f7fafd}}
.muted{{color:#667c92;font-size:13px}}
</style></head><body>
<h1>{escape(application)}</h1>
<p class="muted">报告生成时间：{escape(date)}。全部内容来自本次本地分析的数据快照。</p>
<p><strong>使用说明：</strong>各类算法的评价指标含义与计算条件不同，不能只凭单项指标直接判断
跨模型优劣。DBSCAN 噪声点不会被当作独立簇参与质量评分。</p>
{''.join(sections)}
<footer><p class="muted">此报告为结果摘要预览，完整数据请使用独立的 Excel/CSV 导出功能。</p></footer>
</body></html>"""
    destination.write_text(document, encoding="utf-8")
    return destination


def export_figure(figure, path):
    """输出已有真实 Matplotlib 图像，不重新生成与当前数据无关的图。"""
    if figure is None or not getattr(figure, "axes", None):
        raise ValueError("尚无可以保存的实际图形。")
    suffix = Path(path).suffix.lower()
    if suffix not in (".png", ".svg"):
        raise ValueError("图片格式仅支持 PNG 或 SVG。")
    destination = _validate_suffix(path, suffix)
    figure.savefig(destination, format=suffix.lstrip("."), dpi=200, bbox_inches="tight")
    return destination
