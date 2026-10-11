# Windows 11 发布验收

本流程验证当前独立分支上的代码。Linux 无头截图、Windows Server CI，以及按画布比例放大的图片，都不能替代 Windows 11 实机验收。验收脚本在本机运行真实算法、Qt 窗口和打包 EXE；不上传数据，不更改 main，不修改任何已有测试。

## 准备

1. 使用交付的源代码 ZIP 解压到新目录；或在现有仓库建立独立分支并应用交付补丁。不要覆盖已有修改，不直接在 main 修改源代码。
2. 安装 Python 3.12（包含 `py` 启动器）。建议屏幕分辨率至少 1920×1080，设为主屏；保留 Windows 自带微软雅黑。
3. 在 Windows 设置 → 系统 → 显示中，将缩放设为 **125%**。不要使用 `QT_SCALE_FACTOR` 等环境变量模拟系统 DPI。窗口最小逻辑尺寸为 1180×760；更小的逻辑桌面不在本轮支持范围。
4. 打开 PowerShell，进入项目根目录。允许窗口正常显示，保持窗口无遮挡；截图时不最小化窗口。

## 自动化验证

```powershell
powershell -NoProfile -File .\tools\verify_windows_release.ps1 -Scale 125
```

脚本检查真实 Windows 11 的系统版本，创建/复用项目 `.venv`，安装固定版本依赖和 PyInstaller 6.16.0，运行依赖检查、全部测试、原生 PCA 绘图回归、启动与绘图压力自检。之后通过界面按钮执行数据导入、统计、PCA、因子分析、MDS、t-SNE、三种聚类、聚类评价、K 扫描和 CSV/Excel/HTML/PNG/SVG 导出，并读回表格验证内容。

使用 `data/demo_high_dimensional.csv`，90 行、8 个数值变量；该文件是仓库明确标注的人工示例数据，不冒充科学实验数据。算法和指标均实际计算。

程序将使用真正安装且具备中文字符的 Qt 字体。截图通过 Windows 屏幕抓取，包含窗口标题栏，记录系统版本、字体、实际 Qt DPI、示例数据哈希、计算参数、指标和生成文件。脚本要求实际缩放与指定比例一致。人工截图检查仍是验收必需步骤，自动化成功不等于视觉通过。

随后构建 GUI EXE，检查 sklearn 隐藏 DLL，复制整个发布目录到独立目录并比对**每个文件**的 SHA256，再启动独立目录里的 EXE，执行三次启动耗时测量、PCA 高频切换、全部绘图自检和同样的功能截图/导出验收。复制验收不冒充 GitHub 附件传输；已有 GitHub 工作流继续承担实际附件上传/下载验证。

输出位于 `release-evidence/windows11-125-时间/`：

- `source/`、`exe/`：真实截图、导出文件和 `evidence.json`。
- 各步骤 `.log`：保留原始退出状态和失败输出；有任一步失败即停止。
- `exe-startup-timing.log`：三次实际进程启动、自检并退出的耗时，包含第一次和后续启动；不是单纯窗口出现耗时。
- `local-appdata/HighDimClusterSystem/logs/`：本轮崩溃诊断日志。
- `dist/`、`transferred/`：完整发布目录；不要单独复制 EXE。
- `windows-run.json`：全部脚本成功后才生成；记录提交和视觉待审状态。

再在 Windows 设置中改为 **100%**，重复：

```powershell
powershell -NoProfile -File .\tools\verify_windows_release.ps1 -Scale 100
```

若 PowerShell 的本机策略阻止脚本，请按本机管理策略处理；本流程不修改执行策略。建议直接使用交付 ZIP，脚本通过 Git 提交文件或 `.git` 记录识别版本。

## 人工验收

逐一打开 `source/` 和 `exe/` 的 PNG，比较 100% 和 125% 的真实截图：

- 软件原生标题栏、品牌栏、八项导航中文可读，没有方框或乱码。
- 参数、按钮、表格、图表标题和轴文字完整；长数据集名称显示省略号，悬停可读完整名称。
- 窗口最小尺寸下滚动可达全部参数、图表和导出操作；没有控件覆盖。标签页不足时可用左右滚动箭头访问，不要求全部标签同时显示。
- 因子分析、MDS、t-SNE、三种聚类截图显示实际结果；层次树、PCA 图、评价和 K 扫描图可见。
- 手动双击 `transferred/HighDimClusterSystem.exe`：导入示例文件、切换全部页面、执行分析、通过真正的保存对话框选择路径并导出 Excel/PNG、关闭窗口。自动验收调用同一导出按钮处理逻辑并预设路径，不能替代人工保存对话框交互。
- 打开导出的 Excel 和 PNG，确认不是空文件、乱码或占位图。确认退出后无残留进程；记录异常关闭、启动体感和 SmartScreen 提示。

回传 `source/`、`exe/`、JSON、所有 `.log` 和诊断日志；不必传巨大的 `build/`、`dist/` 或虚拟环境。注明人工检查结论和出现问题的截图文件名。当前版本的 Windows 11、Windows DLL 和 EXE 结果将在收到实机证据后更新，不能提前标记正式发布通过。
