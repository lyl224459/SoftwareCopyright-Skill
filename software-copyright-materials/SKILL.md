---
name: software-copyright-materials
description: >
  Generate guided Chinese software copyright application materials from a real
  project. Use this skill when the user asks for 软件著作权, 软著申请资料,
  软著代码材料, 操作手册, 申请表信息, or wants Word/TXT materials for
  software copyright registration. The workflow analyzes the imported project,
  extracts real source code, creates Markdown drafts for user confirmation, then
  uses bundled DOCX tooling to produce final Word documents and TXT.
metadata:
  short-description: 生成软著申请资料 Word/TXT
---

# 软著申请资料生成

生成可审阅、可追溯的中国软件著作权申请资料。面向用户生成材料时，固定写入当前工作目录下的 `软件著作权申请资料/`，不要写到临时目录。只有测试本 skill 时才允许显式指定临时输出目录。

## 先读哪些参考

按需读取这些 reference，不要把所有细节塞回主流程：

- 运行环境、Python 命令、DOCX 工具安装：`references/runtime_environment.md`
- 软著鉴别材料页数和代码页规则：`references/copyright_material_rules.md`
- 业务理解模型稿要求：`references/business_understanding_rules.md`
- 申请表字段和填写口径：`references/application_fields.md`
- 代码候选和抽取规则：`references/code_selection_rules.md`
- 操作手册章节、语言和截图要求：`references/manual_structure.md`
- 签章页和合作开发协议说明：`references/signature_page_template.md`、`references/cooperation_agreement_guide.md`

## 核心约束

- 先生成 Markdown 草稿，用户确认后再生成正式 Word/TXT。
- 正式 Word/TXT 只能写入 `软件著作权申请资料/正式资料/`。
- 正式 Word/TXT 使用默认黑色字体；Markdown 链接写入 Word 时转成普通文本。
- 正式资料的软件名称、版本号以 `草稿/申请表信息.md` 中已确认字段为准。
- 代码材料必须来自真实项目源码，禁止 AI 编造代码。
- 写申请表和操作手册前，必须先生成并确认 `草稿/业务理解.md/json`。
- 行业判断、功能抽取、代码选择、操作手册结构必须由模型阅读项目后决定，脚本只收集证据、校验字段和生成文件。
- Word 生成能力必须使用本 skill 内置的 `vendor/docx-toolkit`，不得引用外部 DOCX 目录。

## 命令约定

示例命令使用 `<python>` 和 `<skill-dir>` 占位：

- Windows PowerShell 通常使用 `python`；如果 `python` 是 Microsoft Store 别名，则使用真实 Python 解释器路径或 `py -3`。
- macOS/Linux/WSL 通常使用 `python3`。
- 中文输出乱码时，PowerShell 先设置 `$env:PYTHONUTF8='1'`；POSIX shell 先设置 `export PYTHONUTF8=1`。
- `<skill-dir>` 是本 skill 目录，例如 `software-copyright-materials` 的绝对路径。

## 强制人工门禁

凡是涉及用户选择、确认或补充信息的阶段，必须停止当前执行，不得继续调用下一步脚本。即使处于自动审核、自动继续或无人值守模式，也必须把 `STOP_FOR_USER` 和 `NEXT_ACTION` 原样告知用户，并等待用户输入后再继续。

记录用户确认：

```bash
<python> <skill-dir>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage <阶段名> --note "<用户确认内容>"
```

必须停住的门禁：

- `environment`：完整 DOCX 环境缺失时，让用户选择安装完整环境或使用基础 DOCX 兜底继续。
- `project`：存在多个项目候选目录时，让用户指定项目目录。
- `business`：`草稿/业务理解.md` 生成后，让用户确认行业、目标用户、核心功能和申请口径。
- `application-fields`：`草稿/申请表信息.md` 生成后，让用户补全并确认硬件、系统环境、著作权人、日期等字段。
- `code-selection`：`草稿/代码文件选择.json` 生成后，让用户确认或修改抽取文件。
- `screenshot-method`：操作手册截图前，让用户在可用浏览器工具、Computer Use、用户自行截图、跳过截图中选择。
- `markdown`：全部 Markdown 草稿完成后，让用户确认可以进入 Word/TXT 生成。

## 工作流

### 1. 检查环境

先读取 `references/runtime_environment.md`，再运行：

```bash
<python> <skill-dir>/scripts/check_environment.py --out-dir 软件著作权申请资料
```

输出：

- `软件著作权申请资料/环境检查.md`
- `软件著作权申请资料/环境检查.json`

如果脚本输出 `STOP_FOR_USER`，先让用户选择安装完整 DOCX 环境或使用基础 DOCX 兜底。用户回复后记录 `environment` 门禁，再进入项目分析。

### 2. 定位项目

用户通常会把项目放在当前文件夹下。先扫描当前目录，避开本 skill、自身输出目录、`node_modules`、构建产物和隐藏目录，找到最可能的项目根目录。多个候选目录必须停止询问；只有一个明显候选项目时可以直接使用。

### 3. 分析项目

```bash
<python> <skill-dir>/scripts/analyze_project.py \
  --project <项目目录> \
  --out 软件著作权申请资料/analysis/project.json
```

分析内容包括项目配置、README、依赖、入口文件、路由、页面、组件、接口、状态管理、源码数量、源程序行数、软件名称候选和运行命令候选。

### 4. 形成业务理解

先读取 `references/business_understanding_rules.md`。脚本先收集证据，不决定最终业务口径：

```bash
<python> <skill-dir>/scripts/generate_business_context.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --software-name "<软件全称>" \
  --out-dir 软件著作权申请资料/草稿
```

输出：

- `草稿/业务理解证据.md`
- `草稿/业务理解证据.json`
- `草稿/业务理解模型稿模板.json`

模型必须阅读证据、README/需求文档、页面文案、路由、接口和必要源码，自行编写业务理解模型稿 JSON。不得用脚本关键字表决定行业、功能和手册结构。随后运行：

```bash
<python> <skill-dir>/scripts/generate_business_context.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --software-name "<软件全称>" \
  --out-dir 软件著作权申请资料/草稿 \
  --model-context <模型生成的业务理解JSON>
```

生成 `草稿/业务理解.md/json` 后必须停止，等待用户确认；确认后记录 `business` 门禁。

### 5. 引导用户确认申请表字段

先读取 `references/application_fields.md`。根据项目分析和业务理解给出建议值，但软件全称、版本号、著作权人、日期、硬件/系统环境等必须由用户确认。字段确认后生成申请表草稿：

```bash
<python> <skill-dir>/scripts/generate_application_info.py \
  --analysis 软件著作权申请资料/analysis/project.json \
  --code-manifest 软件著作权申请资料/草稿/代码提取清单.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

生成后必须停止，让用户补全并确认 `草稿/申请表信息.md`；确认后记录 `application-fields` 门禁。

### 6. 确认代码文件选择

先读取 `references/code_selection_rules.md` 和 `references/copyright_material_rules.md`。生成候选文件：

```bash
<python> <skill-dir>/scripts/propose_code_selection.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --out-dir 软件著作权申请资料/草稿
```

脚本只列候选，不默认选择。模型阅读业务理解、候选文件、入口文件、页面文件和必要源码后，修改 `草稿/代码文件选择.json`：

- `selected: true` 表示抽取该完整文件。
- `selected: false` 表示不抽取该文件。
- `model_reason` 说明选择或不选择原因。

代码材料按用户确认的完整文件复制，不支持只抽取文件中间行段。用户确认后记录 `code-selection` 门禁。

### 7. 生成 Markdown 草稿

抽取代码材料：

```bash
<python> <skill-dir>/scripts/extract_code_material.py \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --selection 软件著作权申请资料/草稿/代码文件选择.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

生成操作手册前读取 `references/manual_structure.md`。操作手册必须基于已确认的 `业务理解.json`，尤其是 `manual_modules`、`system_requirements`、`faq` 和 `glossary`：

```bash
<python> <skill-dir>/scripts/generate_manual_draft.py \
  --analysis 软件著作权申请资料/analysis/project.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

脚本会同步输出 `草稿/操作手册自检记录.md/json`。如果自检仍有问题，必须回到业务理解阶段补全真实页面内容、操作规则和结果反馈，不要绕过检查。

### 8. 选择并获取截图

截图前必须先让用户选择，并记录 `screenshot-method` 门禁：

```bash
<python> <skill-dir>/scripts/confirm_stage.py \
  --workdir 软件著作权申请资料 \
  --stage screenshot-method \
  --method <browser-tool|chrome-devtools|computer-use|user-supplied|skip> \
  --note "<用户选择>"
```

选择工具截图时，先用工具发现确认当前环境是否有可用浏览器或桌面控制工具。不可用时停止，让用户改选用户自行截图或跳过截图。用户自行截图时，把 PNG/JPG/JPEG/WebP 放入 `软件著作权申请资料/用户截图/`，再运行：

```bash
<python> <skill-dir>/scripts/capture_screenshots.py \
  --manual-dir 软件著作权申请资料/用户截图 \
  --out-dir 软件著作权申请资料/截图
```

用户选择跳过截图或截图失败时，操作手册仍必须保留正式 Word 中可见的截图预留文字。

### 9. 用户确认 Markdown

生成 Word 前，必须让用户确认 `软件著作权申请资料/草稿/` 下的 Markdown。重点核对软件名称、版本号、业务理解、申请表字段、代码来源、操作手册真实性、截图或截图预留位。

确认后记录 `markdown` 门禁：

```bash
<python> <skill-dir>/scripts/confirm_stage.py \
  --workdir 软件著作权申请资料 \
  --stage markdown \
  --note "<用户确认内容>"
```

### 10. 生成正式 Word/TXT

```bash
<python> <skill-dir>/scripts/build_docx_from_md.py \
  --workdir 软件著作权申请资料 \
  --software-name "<软件全称>" \
  --version "<版本号>"
```

正式生成脚本会重新读取 `草稿/申请表信息.md` 中已确认的“软件全称”和“版本号”，并以申请表字段为准生成文件名、代码 Word 页眉和操作手册 Word 页眉。

输出：

- `正式资料/申请表信息.txt`
- `正式资料/<软件全称>-代码(前30页).docx` 和 `正式资料/<软件全称>-代码(后30页).docx`，或代码不足 60 页时的 `正式资料/<软件全称>-代码(全部).docx`
- `正式资料/<软件全称>_操作手册.docx`
- `正式资料/生成报告.md`

### 11. 验证

至少检查：

- 目标 Word/TXT 存在且非空。
- 代码片段能回溯到项目源码。
- 申请表和操作手册中的行业、目标用户、主要功能、操作流程能回溯到 `业务理解.md` 和项目证据。
- 软件名称、版本号、页数规则、申请表字段、操作手册标题和截图引用一致。

可运行：

```bash
<python> -m py_compile <skill-dir>/scripts/*.py
```

如果完整 DOCX 环境不可用，用户明确选择兜底并记录 `environment` 门禁后，可以继续生成 Markdown、TXT 和基础 DOCX，并在报告中说明当前使用兜底路径。
