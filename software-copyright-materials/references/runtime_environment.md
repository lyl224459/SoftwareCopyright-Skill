# 运行环境和命令约定

本 skill 面向 Codex 优先，脚本应能在 Windows PowerShell、macOS/Linux shell、WSL 中运行。

## Python 命令

主流程命令统一写作 `<python>`：

- Windows PowerShell：优先使用 `python`。如果 `python` 是 Microsoft Store 别名，改用真实 Python 路径或 `py -3`。
- macOS/Linux/WSL：通常使用 `python3`。
- Python 版本要求：3.10+。
- 基础 DOCX 生成可使用内置 OOXML 兜底；安装 `python-docx` 后格式效果更好。

安装可选依赖时给用户可直接复制的平台命令。

Windows PowerShell：

```powershell
python -m pip install python-docx
```

如果 `python` 打开 Microsoft Store，可改用：

```powershell
py -3 -m pip install python-docx
```

macOS/Linux/WSL：

```bash
python3 -m pip install python-docx
```

## UTF-8 输出

中文输出乱码时，先为当前 shell 设置 UTF-8：

PowerShell：

```powershell
$env:PYTHONUTF8='1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

POSIX shell：

```bash
export PYTHONUTF8=1
export LANG=en_US.UTF-8
```

## DOCX 完整环境

完整 DOCX 环境依赖 `.NET SDK 8.0+` 和本 skill 内置的 `vendor/docx-toolkit`。

首次安装：

PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File <skill-dir>/vendor/docx-toolkit/scripts/setup.ps1 -Minimal
```

macOS/Linux/WSL：

```bash
bash <skill-dir>/vendor/docx-toolkit/scripts/setup.sh --minimal
```

不要对 `vendor/docx-toolkit/scripts/dotnet` 目录或 `.slnx` 文件执行隐式 restore/build。检查和构建目标必须是：

```text
<skill-dir>/vendor/docx-toolkit/scripts/dotnet/DocxToolkit.Cli/DocxToolkit.Cli.csproj
```

## 环境检查行为

`scripts/check_environment.py` 会原生检查：

- Python 模块 `docx` 是否可用。
- `pandoc` 是否可用。
- `dotnet --version` 是否为 8.0+。
- DOCX CLI csproj 是否存在。
- `dotnet restore` 与 `dotnet build` 是否能成功。

如果完整 DOCX 环境未就绪，脚本会输出 `STOP_FOR_USER`，让用户选择安装完整环境或使用基础 DOCX 兜底继续。用户选择后必须记录 `environment` 门禁。
