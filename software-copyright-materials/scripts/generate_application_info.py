#!/usr/bin/env python3
"""Generate the Markdown draft for application form information."""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Any

from common import ensure_dir, read_json, read_text


MIN_MAIN_FUNCTION_CHARS = 500
MAX_MAIN_FUNCTION_CHARS = 1300


FIELD_ORDER = [
    "软件全称",
    "软件简称",
    "版本号",
    "软件分类",
    "开发完成日期",
    "开发方式",
    "软件说明",
    "发表状态",
    "首次发表日期",
    "著作权人",
    "权利范围",
    "权利取得方式",
    "开发的硬件环境",
    "运行的硬件环境",
    "开发该软件的操作系统",
    "软件开发环境 / 开发工具",
    "该软件的运行平台 / 操作系统",
    "软件运行支撑环境 / 支持软件",
    "编程语言",
    "源程序量",
    "开发目的",
    "面向领域 / 行业",
    "软件的主要功能",
    "软件的技术特点（标签）",
    "软件的技术特点（描述）",
    "页数",
]

SOFTWARE_TECHNICAL_TAGS = [
    "APP",
    "游戏软件",
    "教育软件",
    "金融软件",
    "医疗软件",
    "地理信息软件",
    "云计算软件",
    "信息安全软件",
    "大数据软件",
    "人工智能软件",
    "VR软件",
    "5G软件",
    "小程序",
    "物联网软件",
    "智慧城市软件",
]


def effective_len(value: str) -> int:
    return len(str(value or "").replace(" ", "").replace("\n", ""))


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("`", "").replace("#", "").strip()
    return text


def trim_effective(value: str, max_chars: int = MAX_MAIN_FUNCTION_CHARS) -> str:
    if effective_len(value) <= max_chars:
        return value
    result: list[str] = []
    count = 0
    for char in value:
        if char not in (" ", "\n"):
            count += 1
        if count > max_chars:
            break
        result.append(char)
    return "".join(result).rstrip("，。；、 ") + "。"


def business_feature_pairs(business: dict[str, Any] | None) -> list[tuple[str, str]]:
    if not business:
        return []
    features = business.get("business_features") or []
    details = business.get("business_feature_details") or {}
    if not isinstance(features, list):
        return []
    if not isinstance(details, dict):
        details = {}
    pairs: list[tuple[str, str]] = []
    for feature in features:
        name = clean_text(feature)
        if not name:
            continue
        detail = clean_text(details.get(name))
        pairs.append((name, detail))
    return pairs


def summarize_business_features(software_name: str, business: dict[str, Any] | None) -> str:
    pairs = business_feature_pairs(business)
    if not business or not pairs:
        return ""

    industry = clean_text(business.get("industry"))
    target_users = business.get("target_users") or []
    if isinstance(target_users, list):
        target_text = "、".join(clean_text(item) for item in target_users if clean_text(item))
    else:
        target_text = clean_text(target_users)
    core_value = clean_text(business.get("core_value"))
    product_positioning = clean_text(business.get("product_positioning"))
    operation_flow = business.get("operation_flow") or []
    if isinstance(operation_flow, list):
        flow_steps = [clean_text(item).rstrip("。") for item in operation_flow if clean_text(item)]
        flow_text = "，再".join(flow_steps)
    else:
        flow_text = clean_text(operation_flow)

    feature_names = "、".join(name for name, _ in pairs[:8])
    parts: list[str] = []
    if product_positioning:
        parts.append(product_positioning.rstrip("。") + "。")
    else:
        scope = f"面向{industry}" if industry else "面向实际业务场景"
        users = f"，服务于{target_text}" if target_text else ""
        parts.append(f"{software_name}是一套{scope}{users}的应用软件。")
    parts.append(f"软件主要提供{feature_names}等功能。")
    if core_value:
        parts.append(core_value.rstrip("。") + "。")

    for name, detail in pairs[:8]:
        if detail:
            detail = detail.rstrip("。")
            if detail.startswith(("用户", "系统")):
                parts.append(f"在{name}功能中，{detail}。")
            else:
                parts.append(f"{name}功能主要{detail}。")
        else:
            parts.append(f"{name}功能支持用户完成相关业务操作，并在处理完成后返回对应结果。")

    if flow_text:
        parts.append(f"用户通常先{flow_text}，系统在关键步骤提供状态反馈和结果展示。")

    result = "".join(parts)
    while effective_len(result) < MIN_MAIN_FUNCTION_CHARS:
        result += (
            f"围绕{feature_names}等核心功能，软件将用户输入、过程处理、结果查看和资料管理组织在连续的操作流程中，"
            "用户可以根据页面提示逐步完成业务处理，系统保存必要的数据记录并提供清晰的反馈信息，"
            "便于用户后续继续查看、复核和调整相关内容。"
        )
    return trim_effective(result)


# Project-type-aware opening templates for summarize_features fallback
_FEATURE_OPENING = {
    "web_frontend": "{name}围绕{modules}等页面组织业务操作。用户通过浏览器访问系统，在页面中完成信息查看、数据录入和结果确认。",
    "web_backend": "{name}是一套后端服务软件，通过接口对外提供{modules}等数据服务和业务处理能力。客户端或前端系统通过调用接口完成数据交互和业务流程。",
    "web_fullstack": "{name}采用前后端分离架构，前端围绕{modules}等页面组织操作，后端通过接口提供数据服务和业务处理能力。",
    "cli": "{name}是一套命令行工具软件。用户在终端中输入命令和参数，完成{modules}等操作。系统处理完成后返回结果或状态信息。",
    "desktop": "{name}是一套桌面应用软件。用户通过窗口界面中的菜单、按钮和输入区域，完成{modules}等操作。",
    "mobile": "{name}是一套移动应用软件。用户在手机或平板屏幕上通过触控操作完成{modules}等功能。",
    "library": "{name}是一套软件开发库，为开发者提供{modules}等编程接口和工具函数，用于在应用系统中集成相关能力。",
    "embedded": "{name}是一套嵌入式软件，运行于目标硬件设备上，实现{modules}等核心功能。",
}

_FEATURE_CLOSING = {
    "web_frontend": "各功能模块通过统一的操作入口串联，用户可在不同页面间切换处理相关业务。",
    "web_backend": "各接口模块通过统一的请求路径和数据结构串联，调用方可按接口规范获取数据服务和业务处理结果。",
    "web_fullstack": "前后端模块通过接口协议串联，用户操作和系统服务在统一的业务流程中协同运行。",
    "cli": "各命令和子命令按功能分组组织，用户可通过帮助信息查看参数说明和用法示例。",
    "desktop": "各功能窗口和面板通过菜单栏、工具栏和快捷键组织，用户可在不同界面区域间切换操作。",
    "mobile": "各功能模块通过底部导航或侧栏菜单组织，用户可在不同屏幕间切换操作。",
    "library": "各模块按命名空间和包结构组织，开发者可通过导入对应模块调用所需功能。",
    "embedded": "各功能模块按硬件接口和控制逻辑组织，设备上电后按预设流程运行。",
}


def summarize_features(analysis: dict[str, Any], software_name: str, business: dict[str, Any] | None = None) -> str:
    """Generate a substantive main-function description for the application form.

    When business context JSON provides main_functions it will be used upstream; this
    function is a fallback that assembles the best available evidence into a multi-
    paragraph description targeting the 500-1300 character window required by the
    Chinese copyright office.
    """
    business_summary = summarize_business_features(software_name, business)
    if business_summary:
        return business_summary

    project_type = str(analysis.get("project_type") or "unknown")
    features = analysis.get("feature_candidates") or []
    readme = (analysis.get("readme_excerpt") or "").strip()
    routes = analysis.get("routes") or []
    categorized = (analysis.get("source") or {}).get("categorized_files") or {}
    page_files = categorized.get("page") or []
    entry_files = categorized.get("entry") or []
    api_files = categorized.get("api") or []

    readable_features = []
    for feature in features:
        name = humanize_feature(str(feature))
        if re.search(r"[A-Za-z]", name):
            continue
        if name and name not in readable_features:
            readable_features.append(name)

    parts: list[str] = []

    # Opening: use project-type-aware template
    feature_list = "、".join(readable_features[:8]) if readable_features else ""
    route_display = [r.strip("/") for r in routes[:8] if r != "/" and not r.startswith("/:") and len(r) < 40]
    route_names = [r.split("/")[-1].replace("-", " ").replace("_", " ") for r in route_display]
    module_names = "、".join(dict.fromkeys(route_names)[:6]) if route_display else (feature_list or "数据处理、业务管理和系统交互")

    opening_template = _FEATURE_OPENING.get(project_type, _FEATURE_OPENING["web_frontend"])
    parts.append(opening_template.format(name=software_name, modules=module_names))

    # Module descriptions from actual files
    detail_parts: list[str] = []
    is_web = project_type in ("web_frontend", "web_fullstack", "unknown")
    is_backend = project_type in ("web_backend", "web_fullstack")

    if is_web and page_files:
        for p in page_files[:6]:
            page_name = Path(p).stem.replace("-", " ").replace("_", " ")
            if page_name.lower() in {"index", "page", "layout", "loading", "error", "not-found"}:
                continue
            detail_parts.append(f"{page_name}页面用于对应业务的查看和处理，用户可在该页面完成相关操作并查看结果。")
    if is_backend and api_files:
        for p in api_files[:6]:
            api_name = Path(p).stem.replace("-", " ").replace("_", " ")
            detail_parts.append(f"{api_name}接口提供对应的数据服务和业务处理能力，调用方可按接口规范获取处理结果。")
    if not detail_parts and entry_files:
        for p in entry_files[:3]:
            entry_name = Path(p).stem.replace("-", " ").replace("_", " ")
            detail_parts.append(f"用户从{entry_name}入口进入系统后，可按引导完成业务操作。")
    if not detail_parts and route_display:
        for r in route_display[:5]:
            label = r.replace("-", " ").replace("_", " ").strip("/")
            detail_parts.append(f"用户通过{label}进行对应业务处理，提交后系统保存数据并反馈结果。")
    if not detail_parts:
        detail_parts = ["用户可在系统中完成数据录入、查询、修改和结果查看等基本操作。"]

    while detail_parts and effective_len("".join(parts) + "".join(detail_parts)) > MAX_MAIN_FUNCTION_CHARS:
        detail_parts.pop()

    parts.extend(detail_parts)

    # Closing
    closing_template = _FEATURE_CLOSING.get(project_type, _FEATURE_CLOSING["web_frontend"])
    if readme:
        first_sentence = readme.split("。")[0][:100].strip()
        if first_sentence and len(first_sentence) > 10:
            parts.append(f"系统围绕{first_sentence}。{closing_template}")
        else:
            parts.append(closing_template)
    else:
        parts.append(closing_template)

    result = "".join(parts)

    while effective_len(result) < MIN_MAIN_FUNCTION_CHARS:
        result += (
            "系统保存用户操作记录和业务数据，用户后续可继续查看、修改或导出相关内容。"
            "操作过程中，系统会根据输入规则给出提示，帮助用户正确完成各项操作。"
        )

    return trim_effective(result)


def humanize_feature(name: str) -> str:
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    value = value.replace("-", " ").replace("_", " ").strip()
    key = value.lower().replace(" ", "")
    mapping = {
        # Auth
        "login": "软件登录",
        "register": "用户注册",
        "auth": "用户认证",
        "signin": "登录",
        "signup": "注册",
        # Navigation
        "home": "首页",
        "dashboard": "数据看板",
        "index": "首页",
        # Project management
        "project": "项目管理",
        "projects": "项目管理",
        "projectsettings": "项目设置",
        "projectssettings": "项目设置",
        # Settings
        "settings": "系统设置",
        "configuration": "配置管理",
        "config": "配置管理",
        "preferences": "偏好设置",
        # Assets / resources
        "asset": "资源管理",
        "assets": "资源管理",
        "assethub": "资源中心",
        "media": "媒体管理",
        "files": "文件管理",
        "upload": "文件上传",
        "download": "文件下载",
        # Billing / payments
        "billing": "费用管理",
        "payments": "支付管理",
        "invoice": "发票管理",
        # Chat / messaging
        "agentstatusbar": "智能体状态展示",
        "messagebubble": "消息展示",
        "chatpanel": "对话面板",
        "chatinput": "对话输入",
        "assetpanel": "资源面板",
        "messages": "消息管理",
        "notifications": "通知管理",
        # User management
        "users": "用户管理",
        "profile": "个人资料",
        "account": "账号管理",
        "roles": "角色管理",
        "permissions": "权限管理",
        # Data
        "search": "搜索",
        "filter": "筛选",
        "export": "数据导出",
        "import": "数据导入",
        "reports": "报表",
        "analytics": "数据分析",
        "logs": "日志查看",
        "history": "历史记录",
        # API / backend
        "api": "接口服务",
        "apikeys": "密钥管理",
        "webhooks": "回调通知",
        "health": "健康检查",
        "status": "状态监控",
        # Monitoring
        "metrics": "指标监控",
        "monitoring": "系统监控",
        "alerts": "告警管理",
        # Content
        "blog": "文章管理",
        "posts": "内容管理",
        "comments": "评论管理",
        "pages": "页面管理",
        "content": "内容管理",
        "cms": "内容管理",
        # E-commerce
        "products": "商品管理",
        "orders": "订单管理",
        "cart": "购物车",
        "checkout": "结算",
        "inventory": "库存管理",
        "catalog": "商品目录",
        # Common CRUD
        "create": "新建",
        "edit": "编辑",
        "delete": "删除",
        "list": "列表查看",
        "detail": "详情查看",
        "view": "查看",
        # Generic
        "admin": "后台管理",
        "management": "管理",
    }
    return mapping.get(key, value.title() if re.search(r"[A-Za-z]", value) else value)


def build_fields(
    analysis: dict[str, Any],
    manifest: dict[str, Any],
    software_name: str,
    version: str,
    answers: dict[str, str],
    business: dict[str, Any] | None = None,
) -> dict[str, str]:
    frameworks = analysis.get("frameworks") or []
    project_type = str(analysis.get("project_type") or "unknown")
    language = analysis.get("language") or "待用户确认"
    project = Path(analysis.get("project_root") or ".")
    hardware_hint = current_hardware_environment()
    dev_os_hint = current_operating_system()
    version_hint = version_confirmation_hint(analysis, version)
    software_name_hint = f"待用户确认（建议：{software_name}；请确认最终软件全称）"

    # Project-type-aware default framework text
    if frameworks:
        framework_text = "、".join(frameworks)
    elif project_type in ("web_frontend", "web_fullstack", "unknown"):
        framework_text = "前端工程化框架"
    elif project_type == "web_backend":
        framework_text = "后端服务框架"
    elif project_type == "cli":
        framework_text = "命令行工具框架"
    elif project_type == "desktop":
        framework_text = "桌面应用框架"
    elif project_type == "mobile":
        framework_text = "移动应用框架"
    else:
        framework_text = "软件开发框架"

    # Project-type-aware default technical characteristics
    _TECH_DEFAULTS = {
        "web_frontend": f"系统采用{framework_text}构建前端界面，结合模块化组件、路由组织和状态管理实现业务功能",
        "web_backend": f"系统采用{framework_text}构建后端服务，结合接口设计、数据处理和持久化存储实现业务功能",
        "web_fullstack": f"系统采用{framework_text}构建前后端，结合组件化界面、接口封装和数据处理实现业务功能",
        "cli": f"系统采用{framework_text}构建命令行工具，结合参数解析、命令分发和结果输出实现业务功能",
        "desktop": f"系统采用{framework_text}构建桌面应用，结合窗口管理、事件处理和本地数据管理实现业务功能",
        "mobile": f"系统采用{framework_text}构建移动应用，结合界面组件、触控交互和本地存储实现业务功能",
        "library": f"系统采用{framework_text}构建开发库，结合模块化接口、数据结构和工具函数提供编程能力",
        "embedded": f"系统采用{framework_text}构建嵌入式软件，结合硬件驱动、控制逻辑和状态管理实现设备功能",
    }
    default_tech = _TECH_DEFAULTS.get(project_type, _TECH_DEFAULTS["web_frontend"])

    # 软件的技术特点：拆分为标签和描述两个字段
    software_tech_option = ""
    if business:
        software_tech_option = str(business.get("software_technical_option") or "").strip()
    # 如果业务理解提供的标签不在预设列表中，保留原值供用户确认
    tech_tags = software_tech_option if software_tech_option else "待用户确认（如无符合项可不选）"
    tech_description = ""
    if business:
        tech_description = str(business.get("technical_characteristics") or "").strip()

    defaults = {
        "软件全称": software_name_hint,
        "软件简称": "",
        "版本号": version_hint,
        "软件分类": (business.get("software_category") or "应用软件") if business else "应用软件",
        "开发完成日期": "待用户确认（YYYY-MM-DD）",
        "开发方式": (business.get("development_situation") or "单独开发") if business else "单独开发",
        "软件说明": "原创",
        "发表状态": "待用户确认（已发表/未发表）",
        "首次发表日期": "待用户确认（YYYY-MM-DD，未发表则留空）",
        "著作权人": "待用户确认",
        "权利范围": (business.get("rights_scope") or "全部权利") if business else "全部权利",
        "权利取得方式": (business.get("rights_acquisition") or "原始取得") if business else "原始取得",
        "开发的硬件环境": hardware_hint,
        "运行的硬件环境": hardware_hint,
        "开发该软件的操作系统": dev_os_hint,
        "软件开发环境 / 开发工具": f"开发环境: {dev_os_hint}/开发工具: {infer_ide_name(project)}",
        "该软件的运行平台 / 操作系统": infer_runtime_os(analysis),
        "软件运行支撑环境 / 支持软件": infer_runtime_support(analysis, project),
        "编程语言": language,
        "源程序量": str(manifest.get("source_line_count") or manifest.get("selected_source_line_count") or "待用户确认"),
        "开发目的": (business.get("application_purpose") or f"待用户确认（≤50字符，需说明开发目的，不能只写软件名称）") if business else "待用户确认（≤50字符，需说明开发目的，不能只写软件名称）",
        "面向领域 / 行业": (business.get("industry") or "待用户确认") if business else "待用户确认",
        "软件的主要功能": (business.get("main_functions") or summarize_features(analysis, software_name, business)) if business else summarize_features(analysis, software_name, business),
        "软件的技术特点（标签）": tech_tags,
        "软件的技术特点（描述）": tech_description or default_tech,
        "页数": str(manifest.get("total_pages") or "待用户确认"),
    }
    defaults.update({k: v for k, v in answers.items() if v})

    # 未发表时首次发表日期应为空，不触发待确认门禁
    publish_status = defaults.get("发表状态", "")
    if "未发表" in publish_status and "已发表" not in publish_status:
        if "待用户确认" in defaults.get("首次发表日期", "") or not defaults.get("首次发表日期", "").strip():
            defaults["首次发表日期"] = ""

    # 软件的主要功能：确保业务理解提供的内容也满足最低字数
    main_func = defaults.get("软件的主要功能", "")
    if main_func and "待用户确认" not in main_func and effective_len(main_func) < MIN_MAIN_FUNCTION_CHARS:
        defaults["软件的主要功能"] = summarize_features(analysis, software_name, business)

    return defaults


def version_numbers(value: str) -> tuple[int, ...]:
    raw = str(value or "").strip()
    raw = raw.lstrip("vV")
    parts = re.findall(r"\d+", raw)
    return tuple(int(part) for part in parts[:3])


def version_less_than_1(value: str) -> bool:
    numbers = version_numbers(value)
    return bool(numbers) and numbers[0] < 1


def normalize_version_label(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return raw if raw.upper().startswith("V") else f"V{raw}"


def project_version_candidate(analysis: dict[str, Any]) -> str:
    value = str((analysis.get("package") or {}).get("version") or "").strip()
    if value and value.upper() != "V1.0":
        return normalize_version_label(value)
    return ""


def version_confirmation_hint(analysis: dict[str, Any], requested_version: str) -> str:
    project_version = project_version_candidate(analysis)
    requested = normalize_version_label(requested_version or "V1.0")
    if project_version and version_less_than_1(project_version):
        return (
            f"待用户确认（项目版本号为 {project_version}，软著首次提交通常建议从 V1.0 开始；"
            f"请确认填写 V1.0 还是 {project_version}）"
        )
    if not project_version and version_less_than_1(requested):
        return (
            f"待用户确认（当前建议版本号为 {requested}，软著首次提交通常建议从 V1.0 开始；"
            f"请确认填写 V1.0 还是 {requested}）"
        )
    if project_version and project_version != requested:
        return f"待用户确认（项目版本号为 {project_version}，当前建议为 {requested}；请确认最终申报版本号）"
    return f"待用户确认（建议：{requested}；请确认最终版本号）"


def format_gb(size: int | None) -> str:
    if not size:
        return ""
    return f"{size / (1024 ** 3):.0f}GB"


def total_memory_bytes() -> int | None:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None


def current_hardware_environment() -> str:
    parts: list[str] = []
    cpu_count = os.cpu_count()
    machine = platform.machine()
    processor = platform.processor()
    if processor and processor != machine and processor.lower() != "arm":
        parts.append(f"CPU {processor}")
    if cpu_count:
        parts.append(f"CPU {cpu_count}核")
    if machine:
        parts.append(f"架构 {machine}")
    memory = format_gb(total_memory_bytes())
    if memory:
        parts.append(f"内存 {memory}")
    try:
        disk = shutil.disk_usage(Path.home())
        disk_total = format_gb(disk.total)
        if disk_total:
            parts.append(f"硬盘 {disk_total}")
    except OSError:
        pass
    if parts:
        return "、".join(parts)
    return "待用户确认"


def current_operating_system() -> str:
    system = platform.system()
    if system == "Darwin":
        version = platform.mac_ver()[0]
        label = f"macOS {version}" if version else f"macOS（Darwin {platform.release()}）"
    elif system == "Windows":
        label = f"Windows {platform.release()}"
    elif system == "Linux":
        label = f"Linux {platform.release()}"
    else:
        label = f"{system} {platform.release()}".strip() or "待用户确认"
    return label


def infer_ide_name(project: Path) -> str:
    if (project / ".idea").exists():
        # Detect JetBrains IDE type from project files
        if (project / "pubspec.yaml").exists():
            return "Android Studio 或 IntelliJ IDEA"
        if any(project.glob("*.py")):
            return "PyCharm 或 IntelliJ IDEA"
        if any(project.glob("*.go")):
            return "GoLand 或 IntelliJ IDEA"
        if any(project.glob("*.rs")):
            return "RustRover 或 IntelliJ IDEA"
        return "WebStorm 或 IntelliJ IDEA"
    if (project / ".vscode").exists() or list(project.glob("*.code-workspace")):
        return "Visual Studio Code"
    if (project / ".vs").exists() or list(project.glob("*.sln")) or list(project.glob("*.csproj")):
        return "Visual Studio"
    if list(project.glob("*.xcworkspace")) or list(project.glob("*.xcodeproj")):
        return "Xcode"
    if (project / ".project").exists() or (project / ".classpath").exists() or (project / ".settings").exists():
        return "Eclipse"
    if (project / "CMakeLists.txt").exists():
        return "VS Code 或 Qt Creator 或 CLion"
    return "待用户确认"


def infer_runtime_os(analysis: dict[str, Any]) -> str:
    project_type = str(analysis.get("project_type") or "unknown")
    frameworks = set(analysis.get("frameworks") or [])
    deps = set((analysis.get("package") or {}).get("dependency_names") or [])

    if project_type == "mobile":
        return "iOS 16及以上 / Android 13及以上"
    if project_type == "desktop":
        if "Electron" in frameworks or "Tauri" in frameworks:
            return "Windows 10/11、macOS 13及以上版本、Linux 桌面环境"
        return "Windows 10/11、macOS 13及以上版本、Linux 桌面环境"
    if project_type == "web_backend":
        return "Linux 服务器 / Windows Server / 容器环境（Docker）"
    if project_type == "cli":
        return "Windows 10/11、macOS 13及以上版本、Linux 终端环境"
    if project_type == "embedded":
        return "目标嵌入式硬件平台"
    if project_type == "library":
        return "与集成该库的应用系统运行环境一致"
    # web_frontend, web_fullstack, unknown
    return "Windows 10/11 或 macOS 13及以上版本，支持现代浏览器访问"


def project_file(project: Path, relative: str) -> Path | None:
    if not relative:
        return None
    path = project / relative
    return path if path.exists() else None


def load_project_package(project: Path, analysis: dict[str, Any]) -> dict[str, Any]:
    package_path = project_file(project, (analysis.get("package") or {}).get("path") or "")
    if package_path:
        try:
            return read_json(package_path)
        except Exception:
            return {}
    return {}


def read_readme(project: Path) -> str:
    for name in ("README.md", "README.zh.md", "readme.md", "Readme.md"):
        path = project / name
        if path.exists():
            try:
                return read_text(path, limit=12000)
            except Exception:
                return ""
    return ""


def extract_requirement_bullets(text: str) -> list[str]:
    wanted = ("python", "node", "docker", "compose", "postgres", "redis", "chrome", "edge", "safari")
    # Patterns that indicate a feature description rather than a runtime requirement.
    _feature_start = re.compile(r"^(?:[一-鿿]|L\d|P\d|[A-Z]\d\s)")
    bullets: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*[-*]\s+(.+)", line)
        if not match:
            continue
        item = match.group(1).strip()
        if any(key in item.lower() for key in wanted) and item not in bullets:
            if len(item) > 80:
                continue
            if _feature_start.match(item) and "（" in item:
                continue
            bullets.append(item)
    return bullets[:8]


def detect_package_manager(project: Path, package_path: str) -> str:
    base = (project / package_path).parent if package_path else project
    checks = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "Yarn"),
        ("bun.lock", "Bun"),
        ("bun.lockb", "Bun"),
        ("package-lock.json", "npm"),
    ]
    for filename, manager in checks:
        if (base / filename).exists() or (project / filename).exists():
            return manager
    return "npm"


def has_support_term(items: list[str], term: str) -> bool:
    return any(term.lower() in item.lower() for item in items)


def infer_runtime_support(analysis: dict[str, Any], project: Path) -> str:
    """Infer runtime support environment (≤50 chars plain text)."""
    package_info = load_project_package(project, analysis)
    package_path = (analysis.get("package") or {}).get("path") or ""
    deps = set((analysis.get("package") or {}).get("dependency_names") or [])
    frameworks = set(analysis.get("frameworks") or [])
    project_type = str(analysis.get("project_type") or "unknown")
    pkg_type = str((analysis.get("package") or {}).get("type") or "")

    support: list[str] = []
    readme_requirements = extract_requirement_bullets(read_readme(project))
    is_web = project_type in ("web_frontend", "web_fullstack", "unknown")

    # Node.js ecosystem
    if pkg_type == "npm" or deps or frameworks & {"Vue", "React", "Vite", "Next.js", "Nuxt", "Svelte", "Astro", "Angular"}:
        if not has_support_term(support, "node"):
            node_engine = str((package_info.get("engines") or {}).get("node") or "").strip()
            support.append(f"Node.js {node_engine}".strip() if node_engine else "Node.js")
        support.append(detect_package_manager(project, package_path))

    # Only add browser for web projects
    if is_web:
        support.append("现代浏览器")

    # Python ecosystem
    if pkg_type == "python" or (project / "pyproject.toml").exists() or any(project.glob("*/pyproject.toml")):
        if not has_support_term(support, "python"):
            support.append("Python")
    if (project / "requirements.txt").exists() or list(project.glob("*/requirements*.txt")):
        if not has_support_term(support, "python"):
            support.append("Python")

    # Go ecosystem
    if pkg_type == "go" or (project / "go.mod").exists():
        if not has_support_term(support, "go"):
            support.append("Go")

    # Rust ecosystem
    if pkg_type == "rust" or (project / "Cargo.toml").exists():
        if not has_support_term(support, "rust"):
            support.append("Rust")

    # Java ecosystem
    if pkg_type and pkg_type.startswith("java"):
        if not has_support_term(support, "java"):
            support.append("JVM")

    # Dart/Flutter
    if pkg_type == "dart" or (project / "pubspec.yaml").exists():
        if not has_support_term(support, "dart"):
            support.append("Dart/Flutter")
    # Ruby
    if pkg_type == "ruby" or (project / "Gemfile").exists():
        if not has_support_term(support, "ruby"):
            support.append("Ruby")
    # Elixir
    if pkg_type == "elixir" or (project / "mix.exs").exists():
        if not has_support_term(support, "elixir"):
            support.append("Elixir/Erlang")
    # .NET
    if pkg_type == "dotnet" or list(project.glob("*.csproj")) or list(project.glob("*.sln")):
        if not has_support_term(support, "dotnet"):
            support.append(".NET Runtime")
    # PHP
    if pkg_type == "php" or (project / "composer.json").exists():
        if not has_support_term(support, "php"):
            support.append("PHP")
    # C/C++
    if any((project / name).exists() for name in ("CMakeLists.txt", "Makefile", "configure")):
        if not has_support_term(support, "c"):
            support.append("C/C++ Runtime")
    if (project / "docker-compose.yml").exists() or (project / "docker-compose.yaml").exists() or list(project.glob("docker-compose*.yml")):
        if not has_support_term(support, "docker"):
            support.append("Docker")

    compose_text = ""
    for compose in list(project.glob("docker-compose*.yml")) + list(project.glob("docker-compose*.yaml")):
        try:
            compose_text += "\n" + read_text(compose, limit=20000).lower()
        except Exception:
            continue
    if "postgres" in compose_text:
        support.append("PostgreSQL")
    if "redis" in compose_text:
        support.append("Redis")

    # Readme requirements
    for req in readme_requirements:
        if not has_support_term(support, req.split()[0].lower()):
            support.append(req)

    # Deduplicate
    unique: list[str] = []
    for item in support:
        clean = str(item).strip().rstrip("；;")
        if clean and clean not in unique:
            unique.append(clean)

    if not unique:
        return "待用户确认"

    result = "、".join(unique)
    if len(result) > 50:
        trimmed: list[str] = []
        for item in unique:
            candidate = "、".join(trimmed + [item])
            if len(candidate) <= 50:
                trimmed.append(item)
            else:
                break
        result = "、".join(trimmed) if trimmed else unique[0][:50]
    return result


def write_application_md(path: Path, fields: dict[str, str], analysis: dict[str, Any], manifest: dict[str, Any], business: dict[str, Any] | None = None) -> None:
    # 兜底：未发表时首次发表日期不应输出"待用户确认"，直接留空
    publish_status = fields.get("发表状态", "")
    if "未发表" in publish_status and "已发表" not in publish_status:
        if "待用户确认" in (fields.get("首次发表日期") or "") or not (fields.get("首次发表日期") or "").strip():
            fields["首次发表日期"] = ""

    lines = ["# 申请表信息", ""]
    for field in FIELD_ORDER:
        lines.append(f"➤{field}：{fields.get(field, '待用户确认')}")
    pending = [field for field in FIELD_ORDER if "待用户确认" in (fields.get(field) or "")]

    # Build warnings for common issues
    warnings: list[str] = []
    soft_name = fields.get("软件全称", "")
    clean_name = str(soft_name).strip()
    raw_name = clean_name
    if "待用户确认" in clean_name and "建议：" in clean_name:
        try:
            raw_name = clean_name.split("建议：")[1].rstrip("）").split("；")[0].strip()
        except (IndexError, ValueError):
            raw_name = clean_name
    for suffix in ["软件", "平台"]:
        if raw_name.endswith(suffix):
            warnings.append(f"软件全称以「{suffix}」结尾，存在被驳回风险。建议考虑去掉「{suffix}」后缀或改用其他命名方式。")

    main_func = fields.get("软件的主要功能", "")
    if main_func and "待用户确认" not in main_func:
        func_len = len(str(main_func).replace(" ", "").replace("\n", ""))
        if func_len < MIN_MAIN_FUNCTION_CHARS:
            warnings.append(f"软件的主要功能仅有 {func_len} 字符，应不少于 {MIN_MAIN_FUNCTION_CHARS} 字符。请扩写功能说明。")
        elif func_len > MAX_MAIN_FUNCTION_CHARS:
            warnings.append(f"软件的主要功能共 {func_len} 字符，超过建议上限 {MAX_MAIN_FUNCTION_CHARS} 字符。请精简。")

    # Check character limits for fields with ≤50 or ≤100 constraints
    char_limit_fields = {
        "开发的硬件环境": 50,
        "运行的硬件环境": 50,
        "开发该软件的操作系统": 50,
        "软件开发环境 / 开发工具": 50,
        "该软件的运行平台 / 操作系统": 50,
        "软件运行支撑环境 / 支持软件": 50,
        "开发目的": 50,
        "面向领域 / 行业": 50,
        "软件的技术特点（描述）": 100,
    }
    for field_name, limit in char_limit_fields.items():
        value = fields.get(field_name, "")
        if value and "待用户确认" not in value and len(value) > limit:
            warnings.append(f"{field_name}共 {len(value)} 字符，超过限制 {limit} 字符。请精简。")

    lines.extend(
        [
            "",
            "## 字段填写口径",
            "",
            "- 软件全称：必须由用户确认；最终正式资料文件名、代码页眉和操作手册中的软件名称均以本字段为准。",
            "- 软件简称：可选；如有常用简称则填写。",
            "- 版本号：必须由用户确认；如果项目版本小于 V1.0，软著首次提交通常建议使用 V1.0，也可按实际项目版本填写，最终以本字段为准。",
            "- 软件分类：应用软件/嵌入式软件/中间件/系统软件/其他。",
            "- 开发完成日期、首次发表日期：必须使用 YYYY-MM-DD 格式。",
            "- 开发方式：单独开发/合作开发/委托开发/下达任务开发。",
            "- 软件说明：原创 / 修改（含翻译软件、合成软件）。",
            "- 发表状态：已发表或未发表；已发表需附首次发表日期，未发表则首次发表日期留空。",
            "- 软件开发环境 / 开发工具：≤50字符，格式 `开发环境: <OS>/开发工具: <IDE名称>`。",
            "- 开发该软件的操作系统：≤50字符，填写实际开发电脑的操作系统版本。",
            "- 该软件的运行平台 / 操作系统：≤50字符，填写软件运行所在的操作系统或浏览器环境。",
            "- 软件运行支撑环境 / 支持软件：≤50字符，直接列出运行依赖（如 Node.js、npm、浏览器），不加格式前缀。",
            "- 开发的硬件环境和运行的硬件环境：≤50字符，可使用检测到的电脑配置作为建议值。",
            "- 源程序量：纯数字（不含'行'字），指全部源程序的总行数。",
            "- 开发目的：≤50字符，用一句话说明目的，不能只写软件名称。",
            "- 面向领域 / 行业：≤50字符。",
            "- 软件的主要功能：500~1300字符。",
            "- 软件的技术特点（标签）：多选标签（APP/游戏软件/教育软件/金融软件/医疗软件/地理信息软件/云计算软件/信息安全软件/大数据软件/人工智能软件/VR软件/5G软件/小程序/物联网软件/智慧城市软件），如无符合项可不选。",
            "- 软件的技术特点（描述）：≤100字符，简述技术架构和关键技术。",
            "",
            "## 项目分析摘要",
            "",
            f"- 项目目录：{analysis.get('project_root', '')}",
            f"- 框架：{'、'.join(analysis.get('frameworks') or []) or '未识别'}",
            f"- 源码文件数：{analysis.get('source', {}).get('total_file_count', analysis.get('source', {}).get('file_count', 0))}",
            f"- 源程序量（含空行）：{analysis.get('source', {}).get('total_line_count', analysis.get('source', {}).get('line_count', 0))}",
            f"- 代码材料页数：{manifest.get('total_pages', 0)}",
            f"- 代码输出模式：{manifest.get('mode', '')}",
            f"- 业务理解：{'已读取 草稿/业务理解.json' if business else '未提供，使用项目分析兜底'}",
            "",
            "## 待确认字段",
            "",
        ]
    )
    if warnings:
        lines.append("## 字段提醒")
        lines.append("")
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")
    if pending:
        lines.extend(f"- {field}" for field in pending)
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "```text",
            "STOP_FOR_USER",
            "NEXT_ACTION: 请补全并确认申请表字段；确认后运行 confirm_stage.py --stage application-fields。",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def require_confirmed_business(business: dict[str, Any] | None) -> None:
    if business is None:
        raise SystemExit(
            "STOP_FOR_USER\n"
            "NEXT_ACTION: 申请表信息必须基于已确认的业务理解生成。请先生成并确认 草稿/业务理解.md。"
        )
    if business.get("confirmation_required") and not business.get("user_confirmed"):
        raise SystemExit(
            "STOP_FOR_USER\n"
            "NEXT_ACTION: 业务理解尚未确认。请先确认 草稿/业务理解.md，"
            "再运行 `<python> <skill-dir>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage business --note \"<用户确认内容>\"`。"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--code-manifest", required=True)
    parser.add_argument("--software-name", required=True)
    parser.add_argument("--version", default="V1.0")
    parser.add_argument("--answers", help="Optional JSON object with confirmed field values")
    parser.add_argument("--business-context", help="Business context JSON generated before material drafting")
    parser.add_argument("--out-dir", default="软件著作权申请资料/草稿")
    args = parser.parse_args()

    analysis = read_json(Path(args.analysis))
    manifest = read_json(Path(args.code_manifest))
    answers = read_json(Path(args.answers)) if args.answers else {}
    business = read_json(Path(args.business_context)) if args.business_context else None
    require_confirmed_business(business)
    out_dir = ensure_dir(Path(args.out_dir))

    fields = build_fields(analysis, manifest, args.software_name, args.version, answers, business)
    out_path = out_dir / "申请表信息.md"
    write_application_md(out_path, fields, analysis, manifest, business)
    print(f"OK application draft: {out_path}")
    print("STOP_FOR_USER")
    print("NEXT_ACTION: 请补全并确认申请表字段；确认后运行 confirm_stage.py --stage application-fields。")


if __name__ == "__main__":
    main()
