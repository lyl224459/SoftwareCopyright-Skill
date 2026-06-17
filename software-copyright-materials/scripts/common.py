#!/usr/bin/env python3
"""Shared helpers for the software copyright materials skill."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".vs",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    "target",
    "vendor",
    "bin",
    "obj",
    "out",
    "Debug",
    "Release",
    ".gradle",
    "Pods",
    ".eggs",
    "DerivedData",
    "软件著作权申请资料",
    "software-copyright-materials",
}

CODE_EXTS = {
    # Web frontend
    ".vue", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".css", ".scss", ".sass", ".less", ".html", ".svelte", ".astro",
    # Data/config
    ".json", ".md", ".yaml", ".yml", ".toml", ".xml",
    # Backend languages
    ".py", ".java", ".go", ".rs", ".cs", ".php", ".rb",
    ".kt", ".swift", ".cpp", ".c", ".h", ".hpp",
    # Database
    ".sql",
    # Scripting
    ".sh", ".bash", ".ps1",
    # JVM
    ".scala", ".groovy", ".clj", ".cljs",
    # .NET
    ".fs", ".fsx", ".vb",
    # Mobile
    ".dart",
    # Functional / systems
    ".ex", ".exs", ".hs", ".lhs",
    ".lua", ".zig", ".nim", ".jl",
    # Scripting (legacy)
    ".pl", ".pm",
    # Data science
    ".r", ".rmd",
    # Other
    ".proto", ".graphql",
}

# SOURCE_EXTS is the canonical name; CODE_EXTS kept for backward compatibility
SOURCE_EXTS = CODE_EXTS

KNOWN_CONFIG_FILES = {
    # JS/TS ecosystem
    ".babelrc",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.yaml",
    ".eslintrc.yml",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".swcrc",
    "angular.json",
    "app.json",
    "astro.config.mjs",
    "astro.config.ts",
    "babel.config.js",
    "babel.config.json",
    "eslint.config.cjs",
    "eslint.config.js",
    "eslint.config.mjs",
    "jsconfig.json",
    "lerna.json",
    "manifest.json",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "nuxt.config.js",
    "nuxt.config.ts",
    "nx.json",
    "package-lock.json",
    "package.json",
    "playwright.config.js",
    "playwright.config.ts",
    "postcss.config.cjs",
    "postcss.config.js",
    "prettier.config.cjs",
    "prettier.config.js",
    "prettier.config.mjs",
    "project.json",
    "rollup.config.js",
    "rollup.config.mjs",
    "rollup.config.ts",
    "svelte.config.js",
    "stylelintrc.json",
    "tailwind.config.js",
    "tailwind.config.ts",
    "tsconfig.app.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "tslint.json",
    "turbo.json",
    "vite.config.js",
    "vite.config.mjs",
    "vite.config.ts",
    "vitest.config.js",
    "vitest.config.ts",
    "webpack.config.js",
    "webpack.config.ts",
    "workspace.json",
    # Python ecosystem
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "requirements.txt",
    # Java/Kotlin ecosystem
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.lockfile",
    "gradlew",
    "gradlew.bat",
    # C#/.NET ecosystem
    # (csproj/fsproj/vbproj matched by extension below)
    # Go ecosystem
    "go.mod",
    "go.sum",
    # Rust ecosystem
    "Cargo.toml",
    "Cargo.lock",
    # Ruby ecosystem
    "Gemfile",
    "Gemfile.lock",
    # PHP ecosystem
    "composer.json",
    "composer.lock",
    # Dart/Flutter ecosystem
    "pubspec.yaml",
    "pubspec.lock",
    # Swift ecosystem
    "Package.swift",
    "Package.resolved",
    # C/C++ ecosystem
    "CMakeLists.txt",
    "Makefile",
    "Makefile.am",
    "configure",
    # Elixir ecosystem
    "mix.exs",
    "mix.lock",
    # iOS/CocoaPods
    "Podfile",
    "Podfile.lock",
    # General
    "docker-compose.yaml",
    "docker-compose.yml",
    "Dockerfile",
    ".dockerignore",
}

FRONTEND_EXTS = {
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".svelte",
    ".astro",
}

BACKEND_EXTS = {
    ".py", ".java", ".go", ".rs", ".cs", ".php", ".rb",
    ".kt", ".swift", ".cpp", ".c", ".h", ".hpp",
    ".scala", ".groovy", ".clj", ".cljs",
    ".fs", ".fsx", ".vb",
    ".ex", ".exs", ".hs", ".lhs",
    ".lua", ".zig", ".nim", ".jl",
    ".pl", ".pm",
    ".r", ".rmd",
}

SUPPLEMENT_CODE_EXTS = {
    ".cmake", ".bzl", ".bazel",
    ".rst", ".adoc", ".tex",
    ".jinja", ".jinja2", ".hbs", ".ejs",
    ".gradle",
}

COPYRIGHT_CODE_EXTS = FRONTEND_EXTS | BACKEND_EXTS | SUPPLEMENT_CODE_EXTS

LOCK_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "bun.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Podfile.lock",
    "mix.lock",
    "gradle.lockfile",
    "Package.resolved",
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    name = path.name
    if name.startswith(".") and name not in {".env.example"}:
        return True
    if name in LOCK_FILES:
        return True
    if name.endswith(".map") or name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    return False


def iter_project_files(project: Path, exts: set[str] | None = None) -> Iterable[Path]:
    project = project.resolve()
    for root, dirs, files in os.walk(project):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not is_excluded(root_path / d)]
        for filename in files:
            path = root_path / filename
            if is_excluded(path):
                continue
            if exts is not None and path.suffix.lower() not in exts:
                continue
            yield path


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path, limit: int | None = None) -> str:
    data = path.read_bytes()
    if limit is not None:
        data = data[:limit]
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def count_text_lines(path: Path, skip_blank: bool = True) -> int:
    try:
        text = read_text(path)
    except Exception:
        return 0
    if not text:
        return 0
    if skip_blank:
        return sum(1 for line in text.splitlines() if line.strip())
    return len(text.splitlines())


CONFIG_EXT_PATTERNS = {".csproj", ".fsproj", ".vbproj", ".sln", ".slnx"}

def is_known_config_file(path: Path) -> bool:
    """Return True for well-known config files that shouldn't count as source code."""
    if path.name in KNOWN_CONFIG_FILES:
        return True
    if path.suffix.lower() in CONFIG_EXT_PATTERNS:
        return True
    return False


def looks_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except Exception:
        return True
    return b"\x00" in chunk


def normalize_title(value: str) -> str:
    value = re.sub(r"[-_]+", " ", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value or "待命名软件"


def safe_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    return value or "软件"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
