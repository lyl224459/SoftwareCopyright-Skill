# 安装指南

## 环境要求

### 必需
- **Python 3.10+** 和 **python-docx**
- **支持 Skill/Plugin 的代码助手**（Codex 或 Claude Code）
- 可读取的项目源码（在代码助手中打开你的项目目录）

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

### 可选
- **.NET SDK 8.0+**：完整 DOCX OpenXML 校验（无 .NET SDK 也可使用基础 DOCX 生成）
- **Codex 浏览器工具 / Chrome DevTools MCP**：自动截取网页截图
- **Codex Computer Use**：桌面应用截图

## 安装方式

### 获取仓库

```bash
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.git
cd SoftwareCopyright-Skill
```

不会用 Git 的用户在 GitHub 页面点击 `Code` → `Download ZIP`，解压后进入仓库目录。

### Codex

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\software-copyright-materials" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux/WSL：

```bash
mkdir -p ~/.codex/skills
cp -R software-copyright-materials ~/.codex/skills/
```

也可复制到项目的 `.codex/skills/`：

Windows PowerShell：

```powershell
$PROJECT_DIR = "<你的项目目录>"
New-Item -ItemType Directory -Force "$PROJECT_DIR\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\software-copyright-materials" "$PROJECT_DIR\.codex\skills\"
```

macOS/Linux/WSL：

```bash
PROJECT_DIR="<你的项目目录>"
mkdir -p "$PROJECT_DIR/.codex/skills"
cp -R software-copyright-materials "$PROJECT_DIR/.codex/skills/"
```

### Claude Code

作为插件目录加载：

```bash
claude --plugin-dir /path/to/SoftwareCopyright-Skill
```

在本仓库目录中可直接执行：

```bash
claude --plugin-dir .
```

手动调用时使用插件命名空间：

```text
/software-copyright-materials:software-copyright-materials
```

在目标项目目录启动时指定本仓库：

```bash
cd "<你的项目目录>"
claude --plugin-dir "<SoftwareCopyright-Skill 仓库路径>"
```

修改后重启会话或执行 `/reload-plugins` 重新加载。

## 环境检查

每次开始生成资料时，skill 会自动运行环境检查，在当前目录生成：

```text
软件著作权申请资料/环境检查.md
软件著作权申请资料/环境检查.json
```

环境检查会告知：
- Markdown 草稿、TXT、基础 DOCX 是否可用
- 完整 DOCX OpenXML 环境是否可用
- .NET SDK 是否缺失
- 材料生成路径

如果完整 DOCX 环境缺失，会停下来让你选择安装完整环境或使用基础 DOCX 兜底。

完整 DOCX 环境可按平台初始化：

PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File software-copyright-materials/vendor/docx-toolkit/scripts/setup.ps1 -Minimal
```

macOS/Linux/WSL：

```bash
bash software-copyright-materials/vendor/docx-toolkit/scripts/setup.sh --minimal
```
