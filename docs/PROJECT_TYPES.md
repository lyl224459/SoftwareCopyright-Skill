# 支持的项目类型与语言

## 项目类型自动检测

本 skill 在分析项目时会自动判定项目类型 (`project_type`)，后续所有文本生成会根据类型调整措辞：

| project_type | 判定条件 | 生成措辞风格 |
|---|---|---|
| `web_frontend` | 前端框架 + 页面/组件目录 | 浏览器/页面/路由 |
| `web_backend` | 后端框架 + 接口/模型目录 | 接口/服务/数据 |
| `web_fullstack` | 同时有前端和后端 | 前后端混合 |
| `cli` | CLI 框架 + 命令入口 | 终端/命令/参数 |
| `desktop` | 桌面框架（Electron/Qt/WPF 等） | 窗口/面板/菜单 |
| `mobile` | 移动框架（Flutter/RN/MAUI） | 屏幕/触控/导航 |
| `library` | 无可运行入口的库/SDK | 模块/接口/API |
| `embedded` | 嵌入式工具链 | 硬件/设备/接口 |
| `unknown` | 无法判定 | 回退 Web 风格 |

## 支持的编程语言（30+）

| 语言 | 扩展名 | 框架覆盖 |
|---|---|---|
| TypeScript/JavaScript | .ts .tsx .js .jsx .mjs .cjs | Vue, React, Next.js, Nuxt, Svelte, Astro, Angular, Vite, Express, Koa, Fastify, NestJS, Hapi, AdonisJS, Electron |
| Python | .py | FastAPI, Flask, Django, Sanic, Tornado, Pyramid, Litestar, Bottle, Falcon, PyQt, PySide, wxPython, Click, Typer, TensorFlow, PyTorch, scikit-learn |
| Java | .java | Spring Boot, Micronaut, Quarkus, Vert.x |
| Kotlin | .kt | Spring Boot, Micronaut, Quarkus |
| Go | .go | Gin, Echo, Fiber, Chi, Cobra |
| Rust | .rs | Actix Web, Axum, Rocket, Warp, Tide, Clap |
| C# | .cs | ASP.NET Core, Entity Framework Core, WPF, WinForms, MAUI, Xamarin |
| PHP | .php | Laravel, Symfony, Slim, CakePHP |
| Ruby | .rb | Rails, Sinatra, Hanami |
| Elixir | .ex .exs | Phoenix |
| Dart | .dart | Flutter |
| Swift | .swift | — |
| C/C++ | .c .cpp .h .hpp | Qt, wxWidgets, GTK, GTKmm |
| Scala | .scala | — |
| Groovy | .groovy | — |
| Clojure | .clj .cljs | — |
| F# | .fs .fsx | — |
| Visual Basic | .vb | — |
| Lua | .lua | — |
| Zig | .zig | — |
| Nim | .nim | — |
| Julia | .jl | — |
| Haskell | .hs .lhs | — |
| Perl | .pl .pm | — |
| R | .r .rmd | — |
| SQL | .sql | — |
| Shell | .sh .bash .ps1 | — |

## 包管理器检测（11 种）

| 生态系统 | 检测文件 |
|---|---|
| Node.js / npm | package.json |
| Python | pyproject.toml |
| Rust | Cargo.toml |
| Go | go.mod |
| Java (Maven) | pom.xml |
| Java (Gradle) | build.gradle / build.gradle.kts |
| Dart / Flutter | pubspec.yaml |
| Ruby | Gemfile |
| Elixir | mix.exs |
| .NET | *.csproj / *.fsproj / *.vbproj |
| PHP | composer.json |

## 覆盖范围

- **前端**: 覆盖所有主流 Web 前端框架
- **后端**: 覆盖 Python、Go、Rust、Node.js、Java、PHP、Ruby、Elixir、.NET 主流框架
- **桌面**: 覆盖 Electron、Tauri、Qt、PyQt、WPF、WinForms
- **移动**: 覆盖 Flutter、React Native、MAUI、Xamarin
- **CLI**: 覆盖 Click、Typer、Cobra、Clap、Commander、Yargs
- **游戏**: 覆盖 Unity、Godot
- **ML/AI**: 覆盖 TensorFlow、PyTorch、scikit-learn

对于不在检测列表中的语言或框架，skill 会回退到通用处理逻辑，仍可正常生成代码材料——只是类型检测和措辞可能不够精确。欢迎提交 PR 扩展覆盖。
