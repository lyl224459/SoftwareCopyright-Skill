#!/usr/bin/env python3
"""Check runtime capabilities at the beginning of the workflow."""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from common import ensure_dir, write_json


def command_version(command: list[str]) -> tuple[bool, str]:
    if not shutil.which(command[0]):
        return False, "not found"
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=20)
        output = (completed.stdout or completed.stderr).strip().splitlines()
        return completed.returncode == 0, output[0] if output else "available"
    except Exception as exc:
        return False, str(exc)


def setup_command(skill_dir: Path) -> str:
    scripts_dir = skill_dir / "vendor" / "docx-toolkit" / "scripts"
    if os.name == "nt":
        return f'powershell -ExecutionPolicy Bypass -File "{scripts_dir / "setup.ps1"}" -Minimal'
    return f'bash "{scripts_dir / "setup.sh"}" --minimal'


def dotnet_major(version: str) -> int | None:
    match = re.match(r"^\s*(\d+)\.", version or "")
    return int(match.group(1)) if match else None


def run_dotnet_step(command: list[str], timeout: int = 120) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except Exception as exc:
        return False, str(exc)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output


def run_docx_env(skill_dir: Path) -> tuple[bool, str, dict[str, Any]]:
    dotnet_ok, dotnet_version = command_version(["dotnet", "--version"])
    cli_project = (
        skill_dir
        / "vendor"
        / "docx-toolkit"
        / "scripts"
        / "dotnet"
        / "DocxToolkit.Cli"
        / "DocxToolkit.Cli.csproj"
    )
    probe: dict[str, Any] = {
        "dotnet": dotnet_ok,
        "dotnet_version": dotnet_version,
        "cli_project": str(cli_project),
        "cli_project_exists": cli_project.is_file(),
        "restore": False,
        "build": False,
        "setup_command": setup_command(skill_dir),
    }
    lines = ["=== DOCX Environment Check ==="]

    major = dotnet_major(dotnet_version) if dotnet_ok else None
    if not dotnet_ok or major is None:
        lines.append("[FAIL] dotnet not found")
        lines.append(f"Install or initialize with: {probe['setup_command']}")
        return False, "\n".join(lines), probe
    if major < 8:
        lines.append(f"[FAIL] dotnet {dotnet_version} found, requires >= 8.0")
        lines.append(f"Upgrade or initialize with: {probe['setup_command']}")
        return False, "\n".join(lines), probe
    lines.append(f"[OK] dotnet {dotnet_version} (>= 8.0)")

    if not cli_project.is_file():
        lines.append(f"[FAIL] CLI project not found: {cli_project}")
        return False, "\n".join(lines), probe
    lines.append(f"[OK] CLI project: {cli_project}")

    restore_ok, restore_output = run_dotnet_step(
        ["dotnet", "restore", str(cli_project), "--verbosity", "quiet"],
        timeout=180,
    )
    probe["restore"] = restore_ok
    if not restore_ok:
        lines.append("[FAIL] dotnet restore failed")
        if restore_output:
            lines.extend(restore_output.splitlines()[:12])
        return False, "\n".join(lines), probe
    lines.append("[OK] dotnet restore succeeded")

    build_ok, build_output = run_dotnet_step(
        ["dotnet", "build", str(cli_project), "--verbosity", "quiet", "--no-restore"],
        timeout=180,
    )
    probe["build"] = build_ok
    if not build_ok:
        lines.append("[FAIL] dotnet build failed")
        if build_output:
            lines.extend(build_output.splitlines()[:12])
        return False, "\n".join(lines), probe
    lines.append("[OK] dotnet build succeeded")
    return True, "\n".join(lines), probe


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def check_environment(skill_dir: Path) -> dict[str, Any]:
    python_docx = module_available("docx")
    pandoc_ok, pandoc_version = command_version(["pandoc", "--version"])
    dotnet_ok, dotnet_version = command_version(["dotnet", "--version"])
    docx_ready, docx_output, docx_probe = run_docx_env(skill_dir)
    setup_hint = docx_probe["setup_command"]
    python_hint = (
        "Windows PowerShell: use `python` or `py -3`; POSIX shells: use `python3`. "
        "Set PYTHONUTF8=1 if Chinese output is garbled."
    )

    final_docx_mode = "docx-openxml" if docx_ready else ("python-docx" if python_docx else "basic-ooxml")
    requires_user_input = not docx_ready
    next_action = (
        f"请选择：1) 安装完整 DOCX 环境（{setup_hint}）；2) 使用基础 DOCX 兜底继续。回复选择后再进入项目分析。"
        if requires_user_input
        else "完整 DOCX 环境可用，可以进入项目分析。"
    )
    return {
        "output_directory": "当前目录/软件著作权申请资料",
        "capabilities": {
            "markdown_drafts": True,
            "application_txt": True,
            "basic_docx": python_docx or True,
            "python_docx": python_docx,
            "pandoc_preview": pandoc_ok,
            "docx_openxml_full": docx_ready,
            "dotnet_sdk": dotnet_ok,
        },
        "versions": {
            "pandoc": pandoc_version,
            "dotnet": dotnet_version,
        },
        "final_docx_mode": final_docx_mode,
        "recommendation": (
            "完整 DOCX OpenXML 环境已就绪，建议使用完整 Word 生成和校验流程。"
            if docx_ready
            else f"完整 DOCX OpenXML 环境未就绪。可以继续使用兜底 DOCX 生成；如需更规范的 Word 结构和校验，请运行：{setup_hint}"
        ),
        "install_prompt": (
            "是否安装完整 DOCX 环境？安装后文档生成和校验更规范；不安装也可以继续生成 Markdown、TXT 和基础 DOCX。"
            if not docx_ready
            else "无需安装，完整环境可用。"
        ),
        "python_hint": python_hint,
        "setup_command": setup_hint,
        "requires_user_input": requires_user_input,
        "confirmation_stage": "environment" if requires_user_input else None,
        "next_action": next_action,
        "docx_env_output": docx_output,
        "docx_probe": docx_probe,
    }


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    caps = data["capabilities"]
    lines = [
        "# 软著申请资料生成环境检查",
        "",
        f"- 输出目录：`{data['output_directory']}`",
        f"- 最终 Word 模式：`{data['final_docx_mode']}`",
        "",
        "## 能力状态",
        "",
        f"- Markdown 草稿：{'可用' if caps['markdown_drafts'] else '不可用'}",
        f"- 申请表 TXT：{'可用' if caps['application_txt'] else '不可用'}",
        f"- 基础 DOCX 生成：{'可用' if caps['basic_docx'] else '不可用'}",
        f"- python-docx：{'可用' if caps['python_docx'] else '不可用'}",
        f"- pandoc 预览：{'可用' if caps['pandoc_preview'] else '不可用'}（{data['versions']['pandoc']}）",
        f"- .NET SDK：{'可用' if caps['dotnet_sdk'] else '不可用'}（{data['versions']['dotnet']}）",
        f"- DOCX OpenXML 完整环境：{'可用' if caps['docx_openxml_full'] else '不可用'}",
        "",
        "## 建议",
        "",
        data["recommendation"],
        "",
        "## Python 与编码",
        "",
        data["python_hint"],
        "",
        "## 用户选择",
        "",
        data["install_prompt"],
        "",
        "如果完整 DOCX 环境不可用，必须先等待用户选择，并记录 `environment` 门禁后再继续。",
        "",
        "```text" if data.get("requires_user_input") else "",
        "STOP_FOR_USER" if data.get("requires_user_input") else "",
        f"NEXT_ACTION: {data['next_action']}" if data.get("requires_user_input") else "",
        "```" if data.get("requires_user_input") else "",
        "",
        "## DOCX 环境输出摘要",
        "",
        "```text",
        "\n".join(data["docx_env_output"].splitlines()[:40]),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="软件著作权申请资料")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    out_dir = ensure_dir(Path(args.out_dir))
    data = check_environment(skill_dir)
    write_json(out_dir / "环境检查.json", data)
    write_markdown(out_dir / "环境检查.md", data)
    print(f"OK environment check: {out_dir}")
    print(f"Final DOCX mode: {data['final_docx_mode']}")
    print(data["recommendation"])
    if data.get("requires_user_input"):
        print("STOP_FOR_USER")
        print(f"NEXT_ACTION: {data['next_action']}")


if __name__ == "__main__":
    main()
