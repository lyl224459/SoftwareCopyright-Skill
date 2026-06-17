# 开发指南

## 项目结构

```
SoftwareCopyright-Skill/
├── .claude-plugin/plugin.json     # Claude Code 插件配置
├── .github/workflows/             # GitHub Actions
├── skills/                        # Claude Code skill 入口（指向 software-copyright-materials）
├── software-copyright-materials/  # 实际 skill 目录
│   ├── SKILL.md                   # Skill 定义和工作流文档
│   ├── agents/                    # Codex agent 配置
│   ├── references/                # 参考规则和模板
│   ├── scripts/                   # Python 脚本
│   │   ├── common.py              # 共享常量和工具函数
│   │   ├── analyze_project.py     # 项目分析 + 类型检测
│   │   ├── check_environment.py   # 环境检查
│   │   ├── confirm_stage.py       # 门禁确认
│   │   ├── propose_code_selection.py  # 代码候选清单
│   │   ├── extract_code_material.py   # 代码抽取
│   │   ├── generate_business_context.py  # 业务理解生成
│   │   ├── generate_application_info.py  # 申请表信息生成
│   │   ├── generate_manual_draft.py      # 操作手册生成
│   │   ├── build_docx_from_md.py         # DOCX 构建
│   │   └── capture_screenshots.py        # 截图工具
│   └── vendor/                    # 内置 DOCX 工具包
├── docs/                          # 用户文档
│   ├── screenshots/               # 演示截图
│   ├── INSTALL.md                 # 安装指南
│   ├── USAGE.md                   # 使用指南
│   ├── SUBMISSION.md              # 官网填报提交
│   └── PROJECT_TYPES.md           # 支持的项目类型
├── 生成demo/                      # 生成材料 demo
├── CONTRIBUTING.md                # 贡献指南
├── LICENSE                        # MIT License
└── README.md                      # 项目主页
```

## 运行要求

- Python 3.10+
- python-docx (`pip install python-docx`)
- (可选) .NET SDK 8.0+ 用于 DOCX OpenXML 校验

## 脚本开发

所有脚本为独立 Python 模块，通过命令行参数调用。`common.py` 提供共享工具：

```python
from common import read_json, write_json, iter_project_files, ensure_dir
```

### 语法检查

```bash
python -m py_compile software-copyright-materials/scripts/*.py
```

### 添加新语言/框架支持

1. **文件扩展名**: 在 `common.py` 的 `CODE_EXTS` / `BACKEND_EXTS` 中添加
2. **框架检测**: 在 `analyze_project.py` 的 `DEPENDENCY_FRAMEWORKS` 中添加
3. **包管理器**: 在 `analyze_project.py` 的 `load_package()` 中添加解析逻辑
4. **语言推断**: 在 `analyze_project.py` 的 `infer_language()` 中添加映射
5. **运行命令**: 在 `analyze_project.py` 的 `infer_run_commands()` 中添加

### 添加新项目类型

1. 在 `analyze_project.py` 的 `detect_project_type()` 中添加判定逻辑
2. 在 `generate_application_info.py` 的 `_FEATURE_OPENING` / `_FEATURE_CLOSING` / `_TECH_DEFAULTS` 中添加文本模板
3. 在 `generate_manual_draft.py` 的 `_project_term()` 和相关函数中添加措辞变体
4. 在 `extract_code_material.py` 的 `category_weight()` 中添加代码优先级方案

## 测试

运行 Python 后端项目类型检测测试：

```bash
# 创建测试项目
mkdir -p /tmp/test-backend && cat > /tmp/test-backend/pyproject.toml << 'EOF'
[project]
name = "test-api"
version = "1.0.0"
dependencies = ["fastapi"]
EOF

# 运行分析
python software-copyright-materials/scripts/analyze_project.py \
  --project /tmp/test-backend \
  --out /tmp/test-analysis.json

# 验证 project_type
python -c "import json; d=json.load(open('/tmp/test-analysis.json')); print(d['project_type'])"
# 期望输出: web_backend
```

## Skill 文档规范

SKILL.md 是 skill 的定义文件，遵循 Codex/Claude Code 的 skill 格式规范。修改 SKILL.md 后：
- Claude Code: 执行 `/reload-plugins` 重新加载
- Codex: 重启会话
