#!/usr/bin/env python3
"""Analyze a project and produce facts used by the copyright material workflow."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Any

from common import COPYRIGHT_CODE_EXTS, FRONTEND_EXTS, count_text_lines, is_known_config_file, iter_project_files, normalize_title, read_json, read_text, rel, write_json


DEPENDENCY_FRAMEWORKS = {
    # Web frontend
    "vue": "Vue",
    "@vue/runtime-core": "Vue",
    "react": "React",
    "next": "Next.js",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "astro": "Astro",
    "@angular/core": "Angular",
    "vite": "Vite",
    "uni-app": "UniApp",
    "@dcloudio/uni-app": "UniApp",
    # Desktop
    "electron": "Electron",
    "@tauri-apps/api": "Tauri",
    "pyqt6": "PyQt",
    "pyqt5": "PyQt",
    "pyside6": "PySide",
    "pyside2": "PySide",
    "wxpython": "wxPython",
    "customtkinter": "CustomTkinter",
    # Web backend — Python
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "sanic": "Sanic",
    "tornado": "Tornado",
    "pyramid": "Pyramid",
    "litestar": "Litestar",
    "bottle": "Bottle",
    "falcon": "Falcon",
    # Web backend — Go
    "gin-gonic/gin": "Gin",
    "github.com/gin-gonic/gin": "Gin",
    "echo": "Echo",
    "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber",
    "fiber": "Fiber",
    "github.com/go-chi/chi": "Chi",
    "chi": "Chi",
    # Web backend — Rust
    "actix-web": "Actix Web",
    "axum": "Axum",
    "rocket": "Rocket",
    "warp": "Warp",
    "tide": "Tide",
    # Web backend — JS/TS
    "express": "Express",
    "koa": "Koa",
    "fastify": "Fastify",
    "@nestjs/core": "NestJS",
    "nestjs": "NestJS",
    "@hapi/hapi": "Hapi",
    "hapi": "Hapi",
    "@adonisjs/core": "AdonisJS",
    # Web backend — Java/Kotlin
    "spring-boot-starter-web": "Spring Boot",
    "spring-boot": "Spring Boot",
    "io.micronaut": "Micronaut",
    "micronaut": "Micronaut",
    "io.quarkus": "Quarkus",
    "quarkus": "Quarkus",
    "io.vertx": "Vert.x",
    "vertx": "Vert.x",
    # Web backend — PHP
    "laravel/framework": "Laravel",
    "laravel": "Laravel",
    "symfony/http-kernel": "Symfony",
    "symfony/framework-bundle": "Symfony",
    "slim/slim": "Slim",
    "cakephp/cakephp": "CakePHP",
    # Web backend — Ruby
    "rails": "Rails",
    "railties": "Rails",
    "sinatra": "Sinatra",
    "hanami": "Hanami",
    # Web backend — .NET
    "microsoft.aspnetcore": "ASP.NET Core",
    "aspnetcore": "ASP.NET Core",
    "microsoft.entityframeworkcore": "Entity Framework Core",
    # Web backend — Elixir
    "phoenix": "Phoenix",
    "phx": "Phoenix",
    # Desktop (additional)
    "pyqt": "PyQt",
    "pyside": "PySide",
    "tkinter": "Tkinter",
    # .NET desktop
    "wpf": "WPF",
    "winforms": "WinForms",
    "microsoft.net.sdk.windowsdesktop": "Windows Desktop",
    # C++ GUI
    "qt": "Qt",
    "qt6": "Qt",
    "qt5": "Qt",
    "wxwidgets": "wxWidgets",
    "gtk": "GTK",
    "gtkmm": "GTKmm",
    # Mobile
    "flutter": "Flutter",
    "react-native": "React Native",
    ".net maui": "MAUI",
    "microsoft.maui": "MAUI",
    "xamarin": "Xamarin",
    # Game engines
    "unity": "Unity",
    "com.unity": "Unity",
    "godot": "Godot",
    # CLI
    "click": "Click",
    "typer": "Typer",
    "cobra": "Cobra",
    "clap": "Clap",
    "commander": "Commander",
    "yargs": "Yargs",
    "argparse": "Argparse",
    # Data / ML (for library-type classification)
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "scikit_learn": "scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
}

ENTRY_NAMES = {
    # JS/TS/Web
    "main.ts",
    "main.js",
    "main.tsx",
    "main.jsx",
    "index.tsx",
    "index.jsx",
    "app.vue",
    "App.vue",
    "app.tsx",
    # Python
    "main.py",
    "app.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    # Go
    "main.go",
    # Java
    "Main.java",
    "Application.java",
    "App.java",
    # C#
    "Program.cs",
    # Rust
    "main.rs",
    # Dart/Flutter
    "main.dart",
    # C/C++
    "main.c",
    "main.cpp",
    # PHP
    "index.php",
    # Ruby
    "main.rb",
    # Kotlin
    "Main.kt",
    # Swift
    "main.swift",
    "App.swift",
}


def _parse_toml_lite(text: str) -> dict[str, Any]:
    """Minimal TOML parser for top-level [project] and [tool.*] tables."""
    result: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        header = re.match(r"^\[([^\]]+)\]", stripped)
        if header:
            section = header.group(1).strip().strip('"').strip("'")
            if section == "project" or section.startswith("tool."):
                current = {}
                result[section] = current
            else:
                current = None
            continue
        if current is not None:
            kv = re.match(r'^([a-zA-Z_-]+)\s*=\s*(.+)$', stripped)
            if kv:
                key = kv.group(1).strip()
                value_str = kv.group(2).strip().split("#")[0].strip()
                # Handle inline arrays: ["item1", "item2"]
                if value_str.startswith("[") and value_str.endswith("]"):
                    items = re.findall(r'"([^"]*)"', value_str)
                    if any("." not in item and not item.startswith(">") for item in items):
                        # Simple string list (e.g. dependencies)
                        current[key] = {item: "" for item in items}
                    else:
                        current[key] = value_str
                else:
                    value_str = value_str.strip('\'"')
                    current[key] = value_str
    return result


def _parse_go_mod(text: str) -> dict[str, Any]:
    """Extract module name and Go version from go.mod."""
    result: dict[str, Any] = {"name": "", "version": ""}
    for line in text.splitlines():
        stripped = line.strip()
        module_match = re.match(r"^module\s+(\S+)", stripped)
        if module_match:
            result["name"] = module_match.group(1).split("/")[-1]
        go_match = re.match(r"^go\s+(\S+)", stripped)
        if go_match:
            result["version"] = go_match.group(1)
    return result


def _parse_pom_xml(text: str) -> dict[str, Any]:
    """Extract artifactId and version from pom.xml."""
    result: dict[str, Any] = {"name": "", "version": ""}
    artifact_match = re.search(r"<artifactId>([^<]+)</artifactId>", text)
    if artifact_match:
        result["name"] = artifact_match.group(1)
    version_match = re.search(r"<version>([^<]+)</version>", text)
    if version_match:
        result["version"] = version_match.group(1)
    return result


def _parse_gradle(text: str) -> dict[str, Any]:
    """Extract project name from build.gradle."""
    result: dict[str, Any] = {"name": "", "version": ""}
    name_match = re.search(r"""rootProject\.name\s*=\s*['"]([^'"]+)['"]""", text)
    if name_match:
        result["name"] = name_match.group(1)
    version_match = re.search(r"""version\s*=\s*['"]([^'"]+)['"]""", text)
    if version_match:
        result["version"] = version_match.group(1)
    return result


def _parse_pubspec_yaml(text: str) -> dict[str, Any]:
    """Extract name and version from pubspec.yaml."""
    result: dict[str, Any] = {"name": "", "version": ""}
    for line in text.splitlines():
        name_match = re.match(r"^name:\s*(.+)", line)
        if name_match:
            result["name"] = name_match.group(1).strip().strip("'\"")
        version_match = re.match(r"^version:\s*(.+)", line)
        if version_match:
            result["version"] = version_match.group(1).strip().strip("'\"")
    return result


def load_package(project: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load project metadata from various package manager files."""
    # npm / Node.js
    npm_candidates = [
        project / "package.json",
        project / "frontend/package.json",
        project / "client/package.json",
        project / "web/package.json",
        project / "app/package.json",
    ]
    for package_path in npm_candidates:
        if not package_path.exists():
            continue
        try:
            data = read_json(package_path)
            data["_package_type"] = "npm"
            return data, package_path
        except Exception:
            continue

    # Python / pyproject.toml
    pyproject = project / "pyproject.toml"
    if pyproject.exists():
        try:
            toml_data = _parse_toml_lite(read_text(pyproject))
            project_section = toml_data.get("project") or {}
            poetry_section = toml_data.get("tool.poetry") or {}
            deps = {}
            if isinstance(project_section, dict):
                deps_raw = project_section.get("dependencies")
                if isinstance(deps_raw, dict):
                    deps.update(deps_raw)
                elif isinstance(deps_raw, list):
                    for dep in deps_raw:
                        deps[str(dep).split("[")[0].strip()] = ""
            if isinstance(poetry_section, dict):
                poetry_deps = poetry_section.get("dependencies") or {}
                if isinstance(poetry_deps, dict):
                    deps.update({k: str(v) for k, v in poetry_deps.items() if k != "python"})
            data = {
                "name": str(project_section.get("name") or poetry_section.get("name") or project.name),
                "version": str(project_section.get("version") or poetry_section.get("version") or "V1.0"),
                "dependencies": deps,
                "_package_type": "python",
            }
            return data, pyproject
        except Exception:
            pass

    # Rust / Cargo.toml
    cargo = project / "Cargo.toml"
    if cargo.exists():
        try:
            toml_data = _parse_toml_lite(read_text(cargo))
            pkg = toml_data.get("package") or {}
            deps_section = toml_data.get("dependencies") or {}
            deps = {}
            if isinstance(deps_section, dict):
                deps = {k: str(v) for k, v in deps_section.items()}
            data = {
                "name": str(pkg.get("name") or project.name),
                "version": str(pkg.get("version") or "V1.0"),
                "dependencies": deps,
                "_package_type": "rust",
            }
            return data, cargo
        except Exception:
            pass

    # Go / go.mod
    gomod = project / "go.mod"
    if gomod.exists():
        try:
            go_data = _parse_go_mod(read_text(gomod))
            data = {
                "name": go_data.get("name") or project.name,
                "version": go_data.get("version") or "V1.0",
                "dependencies": {},
                "_package_type": "go",
            }
            return data, gomod
        except Exception:
            pass

    # Java / pom.xml
    pom = project / "pom.xml"
    if pom.exists():
        try:
            pom_data = _parse_pom_xml(read_text(pom))
            data = {
                "name": pom_data.get("name") or project.name,
                "version": pom_data.get("version") or "V1.0",
                "dependencies": {},
                "_package_type": "java-maven",
            }
            return data, pom
        except Exception:
            pass

    # Java / build.gradle
    gradle = project / "build.gradle"
    if not gradle.exists():
        gradle = project / "build.gradle.kts"
    if gradle.exists():
        try:
            gradle_data = _parse_gradle(read_text(gradle))
            data = {
                "name": gradle_data.get("name") or project.name,
                "version": gradle_data.get("version") or "V1.0",
                "dependencies": {},
                "_package_type": "java-gradle",
            }
            return data, gradle
        except Exception:
            pass

    # Dart/Flutter / pubspec.yaml
    pubspec = project / "pubspec.yaml"
    if pubspec.exists():
        try:
            pub_data = _parse_pubspec_yaml(read_text(pubspec))
            data = {
                "name": pub_data.get("name") or project.name,
                "version": pub_data.get("version") or "V1.0",
                "dependencies": {},
                "_package_type": "dart",
            }
            return data, pubspec
        except Exception:
            pass

    # Ruby / Gemfile
    gemfile = project / "Gemfile"
    if gemfile.exists():
        try:
            text = read_text(gemfile, limit=20_000)
            deps = {}
            name = project.name
            for line in text.splitlines():
                gem_match = re.match(r"""^\s*gem\s+['"]([^'"]+)['"]""", line)
                if gem_match:
                    gem_name = gem_match.group(1)
                    if gem_name != "rubocop" and not gem_name.startswith("rubocop"):
                        deps[gem_name] = ""
            data = {
                "name": name,
                "version": "V1.0",
                "dependencies": deps,
                "_package_type": "ruby",
            }
            return data, gemfile
        except Exception:
            pass

    # Elixir / mix.exs
    mixfile = project / "mix.exs"
    if mixfile.exists():
        try:
            text = read_text(mixfile, limit=20_000)
            deps = {}
            name = project.name
            version = "V1.0"
            name_match = re.search(r"""app:\s*:(\w+)""", text)
            if name_match:
                name = name_match.group(1)
            version_match = re.search(r"""version:\s*"([^"]+)""", text)
            if version_match:
                version = version_match.group(1)
            for dep_match in re.finditer(r"""{:(\w+),""", text):
                dep_name = dep_match.group(1)
                if dep_name not in ("in_umbrella", "only", "optional"):
                    deps[dep_name] = ""
            data = {
                "name": name,
                "version": version,
                "dependencies": deps,
                "_package_type": "elixir",
            }
            return data, mixfile
        except Exception:
            pass

    # .NET / .csproj or .sln
    csproj_files = list(project.glob("*.csproj")) + list(project.glob("*.fsproj")) + list(project.glob("*.vbproj"))
    if csproj_files:
        try:
            text = read_text(csproj_files[0], limit=20_000)
            deps = {}
            name = csproj_files[0].stem
            for pkg_ref in re.finditer(r"""<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)""", text):
                deps[pkg_ref.group(1)] = pkg_ref.group(2)
            # Try to get assembly name
            assembly_match = re.search(r"""<AssemblyName>([^<]+)</AssemblyName>""", text)
            if assembly_match:
                name = assembly_match.group(1)
            data = {
                "name": name,
                "version": "V1.0",
                "dependencies": deps,
                "_package_type": "dotnet",
            }
            return data, csproj_files[0]
        except Exception:
            pass

    # PHP / composer.json
    composer_json = project / "composer.json"
    if composer_json.exists():
        try:
            cdata = read_json(composer_json)
            deps = {}
            for key in ("require", "require-dev"):
                section = cdata.get(key) or {}
                if isinstance(section, dict):
                    deps.update(section)
            data = {
                "name": str(cdata.get("name") or project.name),
                "version": str(cdata.get("version") or "V1.0"),
                "dependencies": deps,
                "_package_type": "php",
            }
            return data, composer_json
        except Exception:
            pass

    return None, None


def detect_frameworks(package: dict[str, Any] | None, files: list[Path], project: Path) -> list[str]:
    found: set[str] = set()
    deps: dict[str, Any] = {}
    pkg_type = ""
    if package:
        pkg_type = str(package.get("_package_type") or "")
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(package.get(key) or {})
        for dep in deps:
            if dep in DEPENDENCY_FRAMEWORKS:
                found.add(DEPENDENCY_FRAMEWORKS[dep])
            # Also check lowercase keys (some ecosystems use different casing)
            dep_lower = dep.lower().replace("-", "").replace("_", "")
            for key, label in DEPENDENCY_FRAMEWORKS.items():
                if dep_lower == key.lower().replace("-", "").replace("_", ""):
                    found.add(label)

    # File-extension-based detection
    suffixes = {p.suffix.lower() for p in files}
    if ".vue" in suffixes:
        found.add("Vue")
    if ".tsx" in suffixes or ".jsx" in suffixes:
        if "Vue" not in found:
            found.add("React")
    if ".py" in suffixes and not found:
        found.add("Python")
    if ".go" in suffixes:
        found.add("Go")
    if ".rs" in suffixes:
        found.add("Rust")
    if ".dart" in suffixes:
        found.add("Dart")
    if ".java" in suffixes or ".kt" in suffixes:
        found.add("Java" if ".java" in suffixes else "Kotlin")

    # Config-file-based detection
    if (project / "vite.config.ts").exists() or (project / "vite.config.js").exists():
        found.add("Vite")
    if (project / "next.config.js").exists() or (project / "next.config.ts").exists() or any(p.name in {"next.config.js", "next.config.ts"} for p in files):
        found.add("Next.js")
    if (project / "Dockerfile").exists():
        found.add("Docker")

    # Go module detection from go.mod
    gomod = project / "go.mod"
    if gomod.exists():
        try:
            for line in read_text(gomod, limit=20_000).splitlines():
                match = re.match(r"^\s*(\S+)\s+v", line.strip())
                if match:
                    dep_name = match.group(1)
                    if dep_name in DEPENDENCY_FRAMEWORKS:
                        found.add(DEPENDENCY_FRAMEWORKS[dep_name])
        except Exception:
            pass

    # Ruby Gemfile detection
    gemfile = project / "Gemfile"
    if gemfile.exists():
        found.add("Ruby")
        try:
            for line in read_text(gemfile, limit=20_000).splitlines():
                gem_match = re.match(r"""^\s*gem\s+['"]([^'"]+)['"]""", line)
                if gem_match:
                    dep_name = gem_match.group(1)
                    if dep_name in DEPENDENCY_FRAMEWORKS:
                        found.add(DEPENDENCY_FRAMEWORKS[dep_name])
        except Exception:
            pass

    # Elixir mix.exs detection
    mixfile = project / "mix.exs"
    if mixfile.exists():
        found.add("Elixir")

    # .NET .csproj detection
    csproj_files = list(project.glob("*.csproj")) + list(project.glob("*.fsproj"))
    if csproj_files:
        found.add(".NET")

    # PHP composer.json detection
    composer_json = project / "composer.json"
    if composer_json.exists():
        try:
            cdata = read_json(composer_json)
            for key in ("require", "require-dev"):
                section = cdata.get(key) or {}
                if isinstance(section, dict):
                    for dep in section:
                        if dep in DEPENDENCY_FRAMEWORKS:
                            found.add(DEPENDENCY_FRAMEWORKS[dep])
        except Exception:
            pass

    return sorted(found)


def classify(path: Path, project: Path) -> str:
    r = rel(path, project).lower()
    name = path.name.lower()
    suffix = path.suffix.lower()

    # Entry files
    if path.name in ENTRY_NAMES or r in {"src/app/page.tsx", "src/app/layout.tsx", "app/page.tsx", "app/layout.tsx"} or r.endswith("/src/app/page.tsx") or r.endswith("/src/app/layout.tsx"):
        return "entry"
    if name == "main.go" or name.endswith("_test.go"):
        if name.endswith("_test.go"):
            return "source"
        return "entry"
    # Cmd directory pattern (Go, Rust)
    if "/cmd/" in r and name == "main.go":
        return "entry"
    if "/src/main.rs" in r or "/src/lib.rs" in r:
        return "entry"

    # Stylesheets
    if suffix in {".css", ".scss", ".sass", ".less"}:
        return "style"

    # Web routes
    if any(part in r for part in ("/router/", "/routes/", "router.", "routes.")):
        return "route"
    if suffix in {".py", ".go", ".rs", ".java"}:
        if any(part in r for part in ("/routers/", "/routing/", "/urls/")):
            return "route"

    # Pages / views
    if any(part in r for part in ("/pages/", "/views/", "/app/", "/screens/", "/templates/")):
        if suffix in {".css", ".scss"}:
            return "style"
        return "page"

    # Components
    if "/components/" in r or "/widgets/" in r:
        return "component"

    # API / controllers / services
    if any(part in r for part in ("/api/", "/apis/", "/services/", "request.", "/request/",
                                   "/controllers/", "/handlers/", "/views.py", "/endpoints/",
                                   "/routes/", "/routers/", "/middleware/", "/interceptors/")):
        return "api"

    # Models / schemas / entities
    if any(part in r for part in ("/models/", "/schemas/", "/entities/", "/repositories/",
                                   "/dao/", "/dtos/", "/domain/", "/migrations/", "/mapping/")):
        return "model"

    # State management (web)
    if any(part in r for part in ("/store/", "/stores/", "/pinia/", "/redux/", "/zustand/")):
        return "state"

    # Utilities / libraries
    if any(part in r for part in ("/utils/", "/lib/", "/libs/", "/hooks/", "/composables/",
                                   "/helpers/", "/common/", "/shared/", "/internal/", "/pkg/",
                                   "/core/", "/config/", "/settings/", "/constants/")):
        return "utility"

    return "source"


def extract_route_paths(path: Path) -> list[str]:
    try:
        text = read_text(path, limit=200_000)
    except Exception:
        return []
    suffix = path.suffix.lower()
    patterns: list[str] = []

    # JS/TS route patterns
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        patterns.extend([
            r"path\s*:\s*['\"]([^'\"]+)['\"]",
            r"<Route[^>]+path=['\"]([^'\"]+)['\"]",
            r"href=['\"](/[^'\"]*)['\"]",
        ])

    # Python route patterns
    if suffix == ".py":
        patterns.extend([
            r"""@\w+\.(?:route|get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]""",
            r"""path\s*\(\s*['\"]([^'\"]+)['\"]""",
            r"""re_path\s*\(\s*[r]?['\"]([^'\"]+)['\"]""",
        ])

    # Go route patterns
    if suffix == ".go":
        patterns.extend([
            r"""\.(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(\s*['\"]([^'\"]+)['\"]""",
            r"""\.HandleFunc\s*\(\s*['\"]([^'\"]+)['\"]""",
            r"""\.Handle\s*\(\s*['\"]([^'\"]+)['\"]""",
        ])

    # Rust route patterns
    if suffix == ".rs":
        patterns.extend([
            r"""#\[(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]""",
            r"""\.route\s*\(\s*['\"]([^'\"]+)['\"]""",
        ])

    # Java annotation-based routes
    if suffix == ".java":
        patterns.extend([
            r"""@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)['\"]""",
        ])

    routes: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            if match.startswith("/") and len(match) < 120 and "*" not in match:
                routes.append(match)
    return routes


def detect_project_type(
    project: Path,
    package: dict[str, Any] | None,
    frameworks: list[str],
    categorized: dict[str, list[str]],
    files: list[Path],
) -> str:
    """Classify the project into a high-level type for downstream behavior selection.

    The detection uses file structure, framework signals, and package type evidence.
    When uncertain, returns "unknown" which triggers web-centric fallback behavior.
    """
    pkg_type = str(package.get("_package_type") or "") if package else ""
    suffixes = {p.suffix.lower() for p in files}
    has_py = ".py" in suffixes
    has_go = ".go" in suffixes
    has_rs = ".rs" in suffixes
    has_java = ".java" in suffixes or ".kt" in suffixes
    has_dart = ".dart" in suffixes

    # Frontend signals
    has_frontend_pages = bool(categorized.get("page") or categorized.get("route"))
    has_frontend_entry = bool(categorized.get("entry"))
    web_frameworks = {"Vue", "React", "Next.js", "Nuxt", "Svelte", "Astro", "Angular", "Vite"}
    has_web_framework = bool(set(frameworks) & web_frameworks)
    # True frontend only if JS/TS/web files present (not Python backend with route-like dirs)
    has_js_ts_files = suffixes & {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"}

    # Backend signals
    backend_frameworks = {"FastAPI", "Flask", "Django", "Sanic", "Tornado",
                          "Pyramid", "Litestar", "Bottle", "Falcon",
                          "Gin", "Echo", "Fiber", "Chi",
                          "Actix Web", "Axum", "Rocket", "Warp", "Tide",
                          "Express", "Koa", "Fastify", "NestJS", "Hapi", "AdonisJS",
                          "Spring Boot", "Micronaut", "Quarkus", "Vert.x",
                          "Laravel", "Symfony", "Slim", "CakePHP",
                          "Rails", "Sinatra", "Hanami",
                          "ASP.NET Core", "Entity Framework Core",
                          "Phoenix"}
    has_backend_framework = bool(set(frameworks) & backend_frameworks)
    has_backend_api = bool(categorized.get("api") or categorized.get("model"))

    # Desktop signals
    desktop_frameworks = {"Electron", "Tauri", "PyQt", "PySide", "wxPython", "CustomTkinter",
                          "Tkinter", "WPF", "WinForms", "Windows Desktop",
                          "Qt", "wxWidgets", "GTK", "GTKmm"}
    has_desktop_framework = bool(set(frameworks) & desktop_frameworks)

    # Mobile signals
    mobile_frameworks = {"Flutter", "React Native", "MAUI", "Xamarin"}
    has_mobile_framework = bool(set(frameworks) & mobile_frameworks)

    # Game engine signals
    game_frameworks = {"Unity", "Godot"}
    has_game_framework = bool(set(frameworks) & game_frameworks)

    # CLI signals
    cli_frameworks = {"Click", "Typer", "Cobra", "Clap", "Commander", "Yargs", "Argparse"}
    has_cli_framework = bool(set(frameworks) & cli_frameworks)
    has_cli_files = any(
        name in {p.name.lower() for p in files}
        for name in {"setup.py", "cli.py", "commands.py", "cmd.go", "commands.go"}
    ) or (project / "setup.py").exists()

    # Embedded signals
    has_embedded = any(
        (project / name).exists()
        for name in ("platformio.ini", "CMakeLists.txt", "Makefile")
    ) or suffixes & {".ino", ".c", ".cpp", ".h", ".hpp"}

    # Library signals: no entry points, no run scripts, no server config
    has_entry = bool(categorized.get("entry"))
    has_run_scripts = bool((package or {}).get("scripts")) if package else False
    has_server_config = any(
        (project / name).exists()
        for name in ("docker-compose.yml", "docker-compose.yaml", "Dockerfile", "nginx.conf")
    )

    # Decision tree
    # True frontend: has web framework OR has JS/TS files and page/component structure
    has_frontend = has_web_framework or (has_frontend_pages and has_js_ts_files) or (has_frontend_entry and has_js_ts_files)
    # True backend: has backend framework OR has API/model files in non-JS languages
    has_backend = has_backend_framework or has_backend_api or (has_py and not has_web_framework) or (has_go and not has_web_framework) or (has_rs and not has_web_framework) or (has_java and not has_web_framework)

    if has_game_framework:
        return "desktop"  # Game engines treated as desktop applications
    if has_mobile_framework:
        return "mobile"
    if has_desktop_framework:
        return "desktop"
    if has_cli_framework or (has_cli_files and not has_frontend and not has_backend):
        return "cli"
    if has_embedded and not has_frontend and not has_backend and not has_web_framework:
        return "embedded"
    if has_frontend and has_backend:
        return "web_fullstack"
    if has_frontend:
        return "web_frontend"
    if has_backend:
        return "web_backend"
    if has_dart:
        return "mobile"
    if not has_entry and not has_run_scripts and not has_server_config and files:
        return "library"

    return "unknown"


def summarize_readme(project: Path) -> str:
    for name in ("README.md", "README.zh.md", "readme.md", "Readme.md"):
        path = project / name
        if path.exists():
            text = read_text(path, limit=4000)
            return "\n".join(line.strip() for line in text.splitlines()[:60] if line.strip())
    return ""


def analyze(project: Path) -> dict[str, Any]:
    project = project.resolve()
    package, package_path = load_package(project)
    source_files = [p for p in iter_project_files(project, COPYRIGHT_CODE_EXTS) if not is_known_config_file(p)]
    frontend_files = [p for p in source_files if p.suffix.lower() in FRONTEND_EXTS]
    class_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    source_lines = 0
    total_source_lines = 0
    categorized: dict[str, list[str]] = {
        "entry": [],
        "route": [],
        "page": [],
        "component": [],
        "api": [],
        "model": [],
        "state": [],
        "utility": [],
        "style": [],
        "source": [],
    }
    route_paths: list[str] = ["/"]

    for path in source_files:
        category = classify(path, project)
        class_counts[category] += 1
        extension_counts[path.suffix.lower()] += 1
        categorized[category].append(rel(path, project))
        source_lines += count_text_lines(path, skip_blank=False)
        # Extract routes from frontend AND backend files
        if category in {"route", "page", "entry", "api"}:
            route_paths.extend(extract_route_paths(path))

    total_source_lines = source_lines

    package_name = ""
    scripts: dict[str, str] = {}
    dependencies: dict[str, str] = {}
    if package:
        package_name = str(package.get("name") or "")
        scripts = {k: str(v) for k, v in (package.get("scripts") or {}).items()}
        for key in ("dependencies", "devDependencies"):
            dependencies.update({k: str(v) for k, v in (package.get(key) or {}).items()})
        # For non-npm packages, dependencies are already extracted in load_package
        if package.get("_package_type") and package["_package_type"] != "npm":
            pkg_deps = package.get("dependencies") or {}
            if isinstance(pkg_deps, dict):
                dependencies.update({k: str(v) for k, v in pkg_deps.items()})

    frameworks = detect_frameworks(package, source_files, project)
    project_type = detect_project_type(project, package, frameworks, categorized, source_files)
    language = infer_language(extension_counts, frameworks)
    route_paths = sorted(set(route_paths), key=lambda x: (x.count("/"), x))

    return {
        "project_root": str(project),
        "project_name": project.name,
        "project_type": project_type,
        "software_name_candidate": normalize_title(package_name or project.name),
        "package": {
            "name": package_name,
            "path": rel(package_path, project) if package_path else "",
            "version": str(package.get("version") or "V1.0") if package else "V1.0",
            "type": str(package.get("_package_type") or "") if package else "",
            "scripts": scripts,
            "dependency_names": sorted(dependencies),
        },
        "frameworks": frameworks,
        "language": language,
        "source": {
            "file_count": len(source_files),
            "line_count": source_lines,
            "total_file_count": len(source_files),
            "total_line_count": total_source_lines,
            "extension_counts": dict(sorted(extension_counts.items())),
            "category_counts": dict(sorted(class_counts.items())),
            "categorized_files": {k: v[:80] for k, v in categorized.items() if v},
        },
        "routes": route_paths[:80],
        "readme_excerpt": summarize_readme(project),
        "run_command_candidates": infer_run_commands(scripts, project, package),
        "feature_candidates": infer_features(categorized, route_paths),
    }


def infer_workdir(out: Path) -> Path:
    if out.parent.name == "analysis":
        return out.parent.parent
    return out.parent


def check_environment_gate(out: Path) -> None:
    workdir = infer_workdir(out)
    env_path = workdir / "环境检查.json"
    if not env_path.exists():
        return
    env = read_json(env_path)
    if not env.get("requires_user_input"):
        return
    confirmation_path = workdir / "环境确认.json"
    confirmed = False
    if confirmation_path.exists():
        confirmed = bool(read_json(confirmation_path).get("environment_confirmed"))
    if not confirmed:
        raise SystemExit(
            "STOP_FOR_USER\n"
            "NEXT_ACTION: 完整 DOCX 环境未确认。请先让用户选择安装完整环境或使用基础 DOCX 兜底继续，"
            "然后运行 `<python> <skill-dir>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage environment --note \"<用户选择>\"`。"
        )


def infer_language(extension_counts: Counter[str], frameworks: list[str]) -> str:
    langs: list[str] = []
    if extension_counts.get(".ts") or extension_counts.get(".tsx"):
        langs.append("TypeScript")
    if extension_counts.get(".js") or extension_counts.get(".jsx") or extension_counts.get(".mjs"):
        langs.append("JavaScript")
    language_by_ext = {
        ".py": "Python",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".cs": "C#",
        ".php": "PHP",
        ".rb": "Ruby",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".sql": "SQL",
        ".sh": "Shell",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C",
        ".hpp": "C++",
        ".dart": "Dart",
        ".scala": "Scala",
        ".groovy": "Groovy",
        ".clj": "Clojure",
        ".cljs": "ClojureScript",
        ".fs": "F#",
        ".fsx": "F#",
        ".vb": "Visual Basic",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".hs": "Haskell",
        ".lhs": "Haskell",
        ".lua": "Lua",
        ".zig": "Zig",
        ".nim": "Nim",
        ".jl": "Julia",
        ".pl": "Perl",
        ".pm": "Perl",
        ".r": "R",
        ".rmd": "R",
        ".bash": "Shell",
        ".ps1": "PowerShell",
    }
    for ext, label in language_by_ext.items():
        if extension_counts.get(ext):
            langs.append(label)
    if not langs:
        langs = [ext.lstrip(".").upper() for ext, _ in extension_counts.most_common(3) if ext]
    return "、".join(dict.fromkeys(langs)) or "待用户确认"


def infer_run_commands(scripts: dict[str, str], project: Path, package: dict[str, Any] | None = None) -> list[str]:
    """Infer run commands based on detected package type and available scripts."""
    pkg_type = str(package.get("_package_type") or "") if package else ""
    commands: list[str] = []

    # npm / Node.js
    if pkg_type == "npm":
        preferred = ["dev", "start", "serve", "preview"]
        for name in preferred:
            if name in scripts:
                commands.append(f"npm run {name}")
        return commands

    # Python
    if pkg_type == "python":
        if scripts:
            for name in scripts:
                commands.append(name)
        # Common Python run patterns
        if (project / "manage.py").exists():
            commands.append("python manage.py runserver")
        elif any((project / name).exists() for name in ("main.py", "app.py")):
            commands.append("python main.py" if (project / "main.py").exists() else "python app.py")
        else:
            commands.append("python -m <module>")
        # Check for uvicorn
        if any("uvicorn" in str(v).lower() for v in scripts.values()):
            commands.insert(0, "uvicorn <app>:app --reload")
        return commands[:5]

    # Rust
    if pkg_type == "rust":
        return ["cargo run", "cargo build --release"]
    # Go
    if pkg_type == "go":
        return ["go run .", "go run ./cmd/...", "go build -o <binary>"]
    # Java
    if pkg_type and pkg_type.startswith("java"):
        if (project / "gradlew").exists() or (project / "gradlew.bat").exists():
            return ["./gradlew bootRun", "./gradlew run", "./gradlew build"]
        if (project / "mvnw").exists() or (project / "mvnw.cmd").exists():
            return ["./mvnw spring-boot:run", "./mvnw compile exec:java"]
        return ["./gradlew bootRun", "java -jar <jar>"]
    # Dart/Flutter
    if pkg_type == "dart":
        return ["flutter run", "dart run"]
    # .NET
    if pkg_type == "dotnet":
        return ["dotnet run", "dotnet build", "dotnet publish"]
    # Ruby
    if pkg_type == "ruby":
        if (project / "config.ru").exists():
            return ["bundle exec rackup", "ruby <entry>.rb"]
        if (project / "bin/rails").exists():
            return ["bin/rails server", "bundle exec rails server"]
        return ["bundle exec ruby <entry>.rb", "ruby <entry>.rb"]
    # Elixir
    if pkg_type == "elixir":
        return ["mix phx.server", "iex -S mix", "mix run"]
    # PHP
    if pkg_type == "php":
        if (project / "artisan").exists():
            return ["php artisan serve", "php artisan"]
        return ["php -S localhost:8000", "composer install && php <entry>.php"]
    if (project / "Makefile").exists():
        commands.append("make")
        commands.append("make run")
    if (project / "docker-compose.yml").exists() or (project / "docker-compose.yaml").exists():
        commands.append("docker-compose up")
    if scripts:
        preferred = ["dev", "start", "serve", "run"]
        for name in preferred:
            if name in scripts:
                commands.append(f"npm run {name}" if pkg_type == "npm" else name)
    return commands[:5]


def infer_features(categorized: dict[str, list[str]], routes: list[str]) -> list[str]:
    stop = {
        "index",
        "main",
        "app",
        "layout",
        "page",
        "globals",
        "providers",
        "loading",
        "error",
        "not-found",
        "template",
        "default",
        "button",
        "input",
        "label",
        "avatar",
        "card",
        "textarea",
        "scroll area",
    }
    names: list[str] = []
    for route in routes:
        cleaned = route.strip("/").replace("-", " ").replace("_", " ")
        if cleaned and not cleaned.startswith(":") and cleaned.lower() not in stop:
            names.append(cleaned)
    for file in categorized.get("page", [])[:60]:
        route_name = feature_from_page_path(file)
        if route_name and route_name.lower() not in stop:
            names.append(route_name)
    for category in ("api", "component"):
        for file in categorized.get(category, [])[:30]:
            lowered = file.lower()
            if "/ui/" in lowered or "/components/ui/" in lowered:
                continue
            stem = Path(file).stem
            normalized = stem.replace("-", " ").replace("_", " ").strip()
            if normalized.lower() not in stop:
                names.append(normalized)
    unique: list[str] = []
    for name in names:
        normalized = re.sub(r"\s+", " ", name).strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique[:30]


def feature_from_page_path(file: str) -> str:
    parts = Path(file).parts
    useful: list[str] = []
    for part in parts:
        if part in {"src", "app", "pages", "views", "screens", "frontend", "client", "web"}:
            continue
        if part.startswith("(") and part.endswith(")"):
            continue
        stem = Path(part).stem
        if stem in {"page", "layout", "index", "route", "loading", "error", "globals", "providers"}:
            continue
        if stem.startswith("[") and stem.endswith("]"):
            continue
        useful.append(stem)
    return " ".join(useful[-2:]).replace("-", " ").replace("_", " ").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Project root directory")
    parser.add_argument("--out", default="软件著作权申请资料/analysis/project.json")
    args = parser.parse_args()

    project = Path(args.project)
    if not project.exists():
        raise SystemExit(f"Project not found: {project}")

    out = Path(args.out)
    check_environment_gate(out)
    result = analyze(project)
    write_json(out, result)
    print(f"OK analysis: {out}")
    print(f"Project: {result['project_name']}")
    print(f"Frameworks: {', '.join(result['frameworks']) or 'unknown'}")
    print(f"Language: {result['language']}")
    print(f"Source files: {result['source']['file_count']}")
    print(f"Source lines: {result['source']['line_count']}")
    print(f"Total source files: {result['source']['total_file_count']}")
    print(f"Total source lines: {result['source']['total_line_count']}")


if __name__ == "__main__":
    main()
