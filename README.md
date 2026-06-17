# Software Copyright Materials Skill

从真实项目生成中国软件著作权申请资料（Word/TXT）的 AI Skill / 插件。支持 Codex 和 Claude Code。

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

```bash
# 1. 安装 Python 依赖
python3 -m pip install python-docx

# 2. 克隆仓库
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.git

# 3. Claude Code: 作为插件加载
claude --plugin-dir ./SoftwareCopyright-Skill
```

在代码助手中打开你的项目，说：

```text
使用 software-copyright-materials 生成当前项目的软件著作权申请资料
```

材料生成到 `软件著作权申请资料/正式资料/`，确认后可导出 PDF 上传官网。

### 使用 Release 包（无需 clone 仓库）

每次 [Release](https://github.com/lyl224459/SoftwareCopyright-Skill/releases) 自动打包为 `tar.gz` 和 `zip`：

```bash
# 下载指定版本的 Release 包（替换 v1.2 为最新版本）
wget https://github.com/lyl224459/SoftwareCopyright-Skill/releases/download/v1.2/software-copyright-materials-v1.2.tar.gz
tar xzf software-copyright-materials-v1.2.tar.gz

# Claude Code 直接加载
claude --plugin-dir ./software-copyright-materials-v1.2
```

Release 包含 `software-copyright-materials/`、`skills/`、`docs/`、`plugin.json` 和 `README`，解压即用。

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
