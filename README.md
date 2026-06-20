# Software Copyright Materials Skill

从真实项目生成中国软件著作权申请资料（Word/TXT）的 AI Skill / 插件。Codex 优先，兼容本地代码助手工作流。

> **本项目完全免费。请不要相信任何使用本项目包装出来的付费服务。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![CI](https://github.com/lyl224459/SoftwareCopyright-Skill/actions/workflows/ci.yml/badge.svg)](https://github.com/lyl224459/SoftwareCopyright-Skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/lyl224459/SoftwareCopyright-Skill?include_prereleases)](https://github.com/lyl224459/SoftwareCopyright-Skill/releases)
[![Wiki](https://img.shields.io/badge/Wiki-在线文档-brightgreen)](https://github.com/lyl224459/SoftwareCopyright-Skill/wiki)

---

## 它能做什么

把你写好的项目交给支持本 skill 的代码助手，它会：

- 自动分析项目类型、编程语言和框架
- 引导你确认软件名称、版本号、著作权人等关键字段
- 从**真实源码**中按要求抽取前 30 页 / 后 30 页代码材料
- 生成面向审核员的操作手册（非空泛模板）
- 一键输出 Word (DOCX) 和 TXT 格式的正式资料
- 全程在本地生成，代码和文档都不离开你的电脑

支持 **30+ 种编程语言**和 **90+ 个主流框架**，覆盖 Web 前后端、桌面应用、移动端、CLI 工具、嵌入式等 **9 种项目类型**。

## 快速开始

Windows PowerShell：

```powershell
python -m pip install python-docx
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\SoftwareCopyright-Skill\software-copyright-materials" "$env:USERPROFILE\.codex\skills\"
```

如果 `python` 打开 Microsoft Store，可改用 `py -3 -m pip install python-docx`。

macOS/Linux/WSL：

```bash
python3 -m pip install python-docx
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.git
mkdir -p ~/.codex/skills
cp -R ./SoftwareCopyright-Skill/software-copyright-materials ~/.codex/skills/
```

在代码助手中打开你的项目，说：

```text
使用 software-copyright-materials 生成当前项目的软件著作权申请资料
```

材料生成到 `软件著作权申请资料/正式资料/`，确认后可导出 PDF 上传官网。

### 使用 Release 包（无需 clone 仓库）

每次 [Release](https://github.com/lyl224459/SoftwareCopyright-Skill/releases) 自动打包为 `tar.gz` 和 `zip`：

```bash
# 下载 v1.3 Release 包
wget https://github.com/lyl224459/SoftwareCopyright-Skill/releases/download/v1.3/software-copyright-materials-v1.3.tar.gz
tar xzf software-copyright-materials-v1.3.tar.gz

# Codex: 复制 skill 到 Codex skills 目录
mkdir -p ~/.codex/skills
cp -R ./software-copyright-materials-v1.3/software-copyright-materials ~/.codex/skills/

# Claude Code: 直接加载
claude --plugin-dir ./software-copyright-materials-v1.3
```

Release 包含 `software-copyright-materials/`、`skills/`、`docs/`、`plugin.json` 和 `README`，解压即用。

## v1.3 与 v1.2 的区别

v1.3 是面向 Codex 使用体验和 Windows 可靠性的兼容增强版本：

- Skill 主入口改为 Codex 兼容 frontmatter，主 `SKILL.md` 更短，细节规则拆到 references，减少上下文占用。
- 环境检查不再依赖 bash，改为 Python 原生检查 Python、pandoc、.NET SDK 和 DOCX CLI；中文输出默认做 UTF-8 处理。
- Windows PowerShell 和 macOS/Linux/WSL 安装命令分开展示，README 与安装指南都提供可直接复制的命令块。
- 缺少 `python-docx` 和 `pandoc` 时，操作手册的纯 OOXML 兜底 DOCX 现在支持简单 Markdown 表格。
- 截图方式保留原有取值，并新增 Codex 友好的 `browser-tool` 别名。
- 代码材料选择规则收敛为按完整文件复制，`代码文件选择.json` 以 `selected` 和 `model_reason` 为有效字段。

## 文档

| 文档 | 说明 |
|---|---|
| [安装指南](docs/INSTALL.md) | 详细安装步骤、环境配置 |
| [使用指南](docs/USAGE.md) | 完整工作流、输出文件说明 |
| [官网填报](docs/SUBMISSION.md) | 版权中心申请流程、文件用法 |
| [支持的项目类型](docs/PROJECT_TYPES.md) | 30+ 语言、90+ 框架覆盖 |
| [开发指南](docs/DEVELOPMENT.md) | 项目架构、扩展开发 |
| [贡献指南](CONTRIBUTING.md) | 如何参与贡献 |

## 演示

| 生成流程 | 生成流程 |
|---------|---------|
| ![demo-1](docs/screenshots/demo-1.png) | ![demo-2](docs/screenshots/demo-2.png) |
| ![demo-3](docs/screenshots/demo-3.png) | ![demo-4](docs/screenshots/demo-4.png) |
| ![demo-5](docs/screenshots/demo-5.png) | ![demo-6](docs/screenshots/demo-6.png) |

完整生成示例见 [`生成demo/`](生成demo/)。

## 目录结构

```
├── docs/                            # 文档
├── software-copyright-materials/    # Skill 核心
│   ├── SKILL.md                     # Skill 定义
│   ├── scripts/                     # Python 脚本
│   ├── references/                  # 参考规则和模板
│   └── vendor/                      # DOCX 工具包
├── 生成demo/                        # 生成示例
├── .github/workflows/               # CI/CD
└── README.md
```

## 许可证

[MIT License](LICENSE) — 自由使用、修改、分发。使用者需自行核对生成材料是否符合实际项目和官网要求。

---

<p align="left"><sub>友情链接：<a href="https://linux.do/">Linux Do 社区</a> · <a href="https://www.v2ex.com/">V2EX</a></sub></p>
