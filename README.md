# 高维数据降维与聚类分析系统 V1.0

High-dimensional Data Dimensionality Reduction and Clustering Analysis System

> 当前进度：**第一、二阶段已完成，PCA 与特征统计模块已通过自动化测试**。本项目是本地 Windows 桌面软件，不依赖远程接口；未开发的因子分析、MDS、t-SNE、聚类算法及指标不会生成虚假结果。

## 环境与启动

推荐 **Windows + Python 3.12**。在仓库根目录打开 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

如果 PowerShell 不允许激活虚拟环境，可直接调用 `.venv\Scripts\python.exe -m pip install -r requirements.txt` 和 `.venv\Scripts\python.exe main.py`。

## 第一阶段已实现

- PySide6 专业中文桌面布局，左侧导航、顶部页面信息以及 **8 个功能页面**。
- CSV（UTF-8 / GB18030）和 Excel（XLSX/XLS）导入，文件格式校验与异常提示。
- 原始数据与工作数据相互独立，导入、恢复及预处理后跨页面刷新。
- 数据预览（前 500 行）、行列数量、缺失单元格数、重复行数、数值/非数值字段数量以及每列概况。
- 删除含缺失值的样本、均值或中位数填补数值变量缺失值、删除重复行、Z-score 标准化与 Min-Max 归一化。
- 描述性统计、Pearson 相关系数矩阵、协方差矩阵、真实相关性热力图。
- 复用的 Matplotlib 画布、中文参数面板、规范化错误提示。
- 后续阶段的 PCA、因子分析、MDS、t-SNE、K-means、层次聚类、DBSCAN、聚类评价和结果中心的 UI 入口及参数区域。

## 第二阶段实现内容

- 在“主成分分析（PCA）”页面选择数值变量，按需进行 Z-score 标准化。
- **自动推荐**：保留累计解释方差达到 85% 的最少主成分；**指定数量**：保留用户选定的 k；**自定义阈值**：保留达到指定累计贡献率的最少主成分。
- 真正计算特征值、各主成分解释方差比例、累计比例、变量主成分系数（特征向量）、变量与主成分的 Pearson 相关载荷及样本得分。
- 图形支持方差贡献柱状图与累计贡献曲线、二维 PC1-PC2 得分图、三维 PC1-PC2-PC3 得分图；如果保留维数不足，明确提示，不伪造坐标。
- 在“特征统计分析”增加真实变量直方图（使用所选首列）、多变量箱线图（最多首 12 列）和双变量散点图（使用所选前两列）。
- 数据导入、预处理和恢复原始数据时自动清除旧 PCA 结果，避免数据与结果不一致。
- `core/pca.py` 的计算不依赖 GUI，包含与 scikit-learn 基准结果的对照测试和 GUI 集成测试。

**数学约定**：载荷表示原变量与主成分得分的 Pearson 相关系数，主成分系数表示特征向量；两者不混用。完整特征值表基于全部 `min(样本数, 变量数)` 个可提取分量。常数列、缺失值、无穷值、无效参数会明确阻止分析。

### 尚未实现

因子分析、MDS、t-SNE、聚类、聚类评分以及完整结果管理与导出页面目前为可操作的**占位入口**，点击执行后会提示功能尚未接入。功能区域不显示模拟统计结果。

示例文件 `data/sample_data.csv` 为**人工构造的测试数据**，不代表真实科学实验数据。

## 目录

```text
main.py                   主程序入口
app/
  main_window.py          八页面与交互
  session.py              数据变化 Qt 信号
  styles.py               主题样式
  table_model.py          500 行数据预览模型
  plot_canvas.py          Matplotlib 可复用画布
  pca_page.py             PCA 真正计算与二维三维输出
core/
  data_manager.py         数据状态管理与恢复
  io.py                   CSV 与 Excel 读取
  preprocessing.py        真实预处理计算
  statistics.py           描述统计、相关性与协方差
  pca.py                  PCA 谱分解、载荷与得分
data/sample_data.csv      示例测试数据
tests/                    单元测试与无头 Qt 冒烟测试
.github/workflows/tests.yml GitHub Actions 自动化测试
requirements.txt          Python 依赖
```

## 自动化测试

```powershell
python -m compileall -q main.py app core tests
python -m pytest -q
```

测试包括文件导入和错误处理、数据隔离与恢复、缺失值处理、去重、标准化、描述统计、相关矩阵、协方差、8 页切换。仓库中已加入 GitHub Actions，推送后可在 Actions 页面查看实际执行结果。

## 后续五阶段路线

1. 基础框架、数据管理、基础统计（已完成）
2. 特征统计完善、PCA 核心计算及二维/三维展示（已实现）
3. 因子分析、MDS、t-SNE 与降维对比
4. K-means、层次聚类、DBSCAN、聚类评价与参数辅助选择
5. 统一结果管理、CSV/Excel/图像导出、鲁棒性及界面全面验收

## 说明

申请软件著作权前应完成全部开发阶段，检查软件的独立性、代码归属、操作说明、真实运行截图和提交材料的一致性；不能仅凭目前两个阶段的工程保证登记结果。
