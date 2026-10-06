# 高维数据降维与聚类分析系统 V1.0

High-dimensional Data Dimensionality Reduction and Clustering Analysis System

> 当前进度：**五阶段全部完成。Windows/Linux 各 83 项自动化测试通过，Windows 独立 EXE 打包、启动自检与真实界面截图全部成功。** 项目可在本地独立运行，不依赖在线服务。

## 已完成的 Windows 安装包与截图

[Windows V1.0 最终成功打包记录](https://github.com/wangruizhe-bit/HighDimClusterSystem/actions/runs/37431338463)

打开工作流页面下方的 **Artifacts**，下载：

- **HighDimClusterSystem-V1.0-Windows**：完整可运行 Windows 程序目录。解压 ZIP，保留整个文件夹并启动 HighDimClusterSystem.exe。该版本通过了打包后独立启动自检。
- **HighDimClusterSystem-V1.0-Screenshots**：基于实际 Windows Qt 程序生成的界面截图，可作为说明书素材。

GitHub Actions 附件保留 30 天；到期后可以重新运行 Windows 构建工作流。当前程序没有商业代码签名，请从已登录的 Private 仓库验证来源后运行。

[查看 Windows 和 Linux 各 83 项成功测试](https://github.com/wangruizhe-bit/HighDimClusterSystem/actions/runs/37431338512)

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

## 第三阶段实现内容

- **因子分析（Factor Analysis）**：数值变量选择、二维/三维潜因子得分；varimax、quartimax 或不旋转；展示因子载荷（模型 components）与每变量独特方差；报告每样本平均对数似然。
- **度量 MDS（Multidimensional Scaling）**：可选欧氏/曼哈顿原始样本距离、最大迭代次数、初始化次数与随机种子；对预先计算的距离矩阵执行度量 MDS；报告原始 Stress 与标准化距离残差比例（sqrt(残差平方和 / 原始距离平方和)）。
- **t-SNE**：二维/三维输出、perplexity、自动/手动学习率、最大迭代次数及随机种子；显示算法自身 KL 散度。perplexity 必须严格小于样本数。
- 三种算法都支持 Z-score 标准化、变量选择、二维或三维样本坐标与真实散点图。
- 后台工作线程执行运算，避免耗时计算长时间阻塞 Qt 界面。关闭窗口时若仍在计算，将阻止关闭并提示。
- 数据导入、预处理、原始数据恢复后，会清除旧结果，异步返回时会检查数据版本，拒绝保存过期结果。
- 最多保留当前数据版本最近 12 份降维记录，可按同数据版本、同变量顺序、同标准化方案和同输出维度进行**并排图形对比**。
- 提供共用辅助指标 trustworthiness（局部邻域保持度，使用同样欧氏邻域及近邻数，最多 1500 样本计算）。注意：该指标不能单独代表整体效果，也不能比较不同数据条件；因子分析对数似然、MDS 距离残差、t-SNE KL 散度**不能直接彼此比较或排序**。
- 数学输入检查覆盖缺失/无穷值、常数列、样本过少、因子数过大、perplexity 无效、距离度量与超范围迭代数等，不会制造虚假结果。
- 内存保护：MDS 目前最多支持 3000 行，t-SNE 最多支持 10000 行，超限时需用户抽样。Matplotlib 优先选择系统安装的中文字体，避免图表标题显示缺字。

## 第四阶段实现内容

- **K-means 聚类**：用户控制簇数 K、迭代次数、随机种子与标准化，提供真实的类别标签、簇大小、K-means 聚类中心（显示原始量纲）、类别变量均值、SSE 惯性。
- **凝聚层次聚类**：Ward、complete、average、single 连接方式，欧氏或曼哈顿距离（Ward 只支持欧氏），提供连接距离树状图及类别结果。超过 160 行不绘制拥挤树图，但依然完成聚类计算。
- **DBSCAN**：eps、min_samples、距离度量，-1 噪声单独标识；有效簇只统计非噪声标签。
- **聚类评价**：Silhouette、Calinski–Harabasz、Davies–Bouldin 三项指标；不能评价的单簇/全噪声等情形明确显示“不适用”。DBSCAN 的质量指标**仅针对非噪声样本**，需要结合噪声比例判断。
- **K 值辅助选择**：可选 K 范围、随机种子、迭代次数，真实绘制惯性 SSE 肘部法曲线与轮廓系数曲线；最高轮廓系数的 K 为辅助推荐，肘部位置仍需人为解读。
- **可视化**：聚类类别在二维/三维 PCA 投影上着色；投影只用于展示，不参与聚类计算及其评价。层次树状图显示合并层次。
- **方法对比**：保存当前数据版本最多 12 次分析，展示同条件指标对比。同条件要求同一数据版本、同变量顺序、同标准化方式；不同算法仍需谨慎解释。
- **长耗时计算**：聚类与 K 搜索在后台线程执行；数据集改变后自动使旧结果失效，防止过期结果进入界面。
- **资源保护**：层次聚类上限 4000 行、DBSCAN 上限 10000 行、K 值扫描最多 29 个不同的 K，轮廓系数对大数据使用最多 1200 行可重复抽样。
- 已为聚类核心计算及 Qt 页面添加自动化测试，Windows 与 Linux 各 **68 项全部通过**。

## 第五阶段：结果管理、文件导出、交付

- **结果中心**：整合当前数据、特征统计、PCA、因子分析、MDS、t-SNE、K-means、层次聚类、DBSCAN 及 K 值扫描所产生的真实数据表和参数摘要，可选表预览。
- **CSV**：单独导出选中真实结果表（UTF-8 BOM），保留完整数据行数。
- **Excel**：把已实际计算的各项目结果及参数分开保存到多个工作表，工作表名称安全截断与去重，保留数值类型。
- **HTML**：生成本地离线查看的中文分析报告，展示真实表格摘要和算法说明；大量数据只做预览，完整数据请导出为表格文件。
- **PNG / SVG**：保存当前真实图表和模型可视化，不生成未执行的算法结果。高分辨率 PNG 适合说明书插图。
- **安全可靠性**：保护敏感的电子表格文本，避免将其写成公式；先在临时目录完整保存，再替换正式导出文件；数据变更时清理过期分析快照，点击“清空结果”不会删除当前数据。
- **Windows 交付**：另有 GitHub Actions 工作流自动使用 PyInstaller 打包桌面程序、运行可执行文件启动自检，生成真实 Qt 界面截图附件。通过的运行任务下可直接下载对应 ZIP，不需要安装 Codex。
- **用户说明**：见 [中文用户操作说明](docs/用户操作说明.md)，涵盖 8 个功能页面、软件启动、分析建议与常见问题。
- **自动化测试**：增加实际文件读回、Excel 公式安全、图片格式、GUI 导出和保留原数据、失败导出保护等用例。Windows 与 Linux 各 **83 项自动化测试已经全部通过**。

### 交付注意事项

八个功能页面均已有真实可用功能，结果中心已实现导出。软件截图必须来自实际运行界面，提交软著材料前仍需要审核申请表、著作权归属、完整源代码与说明书。

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
  dimension_page.py       第三阶段降维 GUI、后台执行与方法对比
  clustering_page.py      聚类分析与图形显示
  evaluation_page.py      聚类评价和 K 值辅助选择
  results_page.py         结果管理、表格/报告/图表导出 GUI
core/
  data_manager.py         数据状态管理与恢复
  io.py                   CSV 与 Excel 读取
  preprocessing.py        真实预处理计算
  statistics.py           描述统计、相关性与协方差
  pca.py                  PCA 谱分解、载荷与得分
  dimension_reduction.py  因子分析、度量 MDS、t-SNE 核心算法
  clustering.py           K-means、层次聚类、DBSCAN 与 K 搜索
  reporting.py            真实结果表与 CSV/Excel/HTML/图像导出
data/sample_data.csv      示例测试数据
tests/                    单元测试、文件导出与无头 Qt 联调测试
tools/capture_screenshots.py 实际界面截图生成工具
docs/用户操作说明.md       完整中文操作说明
.github/workflows/tests.yml Windows/Linux 自动化测试
.github/workflows/build-windows.yml Windows EXE 打包与截图
requirements.txt          Python 依赖
```

## 自动化测试

```powershell
python -m compileall -q main.py app core tests
python -m pytest -q
```

测试包括数据读取和恢复、缺失值处理、标准化、描述统计、PCA 数值对照、因子载荷、MDS 距离残差、t-SNE 随机种子复现、8 页切换、后台线程运行、分析记录与方法对比。GitHub Actions 在 Linux 和 Windows 上各完成 **83 项检查**；这属于自动化及无头 GUI 冒烟测试，并非 Windows 桌面人工交互和视觉验收的替代品。

## 后续五阶段路线

1. 基础框架、数据管理、基础统计（已完成）
2. 特征统计完善、PCA 核心计算及二维/三维展示（已实现）
3. 因子分析、MDS、t-SNE 与降维对比（已完成、双平台自动化测试通过）
4. K-means、层次聚类、DBSCAN、聚类评价与参数辅助选择（已完成）
5. 统一结果管理、CSV/Excel/HTML/图像导出、中文说明、Windows 打包（已完成，双平台测试与 EXE 启动通过）

## 说明

申请软件著作权前应完成全部开发阶段，检查软件的独立性、代码归属、操作说明、真实运行截图和提交材料的一致性；软著登记仍需要源代码、说明书、界面截图、申请主体与权属材料的一致性，且最终登记结果由审核机构决定。
