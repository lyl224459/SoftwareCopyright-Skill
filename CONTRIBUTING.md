# 贡献指南

欢迎提交 Issue 和 Pull Request。

## 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交改动 (`git commit -m 'feat: xxx'`)
4. 推送到你的仓库 (`git push origin feature/xxx`)
5. 提交 Pull Request

## 开发环境

```bash
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.git
cd SoftwareCopyright-Skill
python3 -m pip install python-docx
```

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` 修复
- `docs:` 文档
- `refactor:` 重构
- `chore:` 维护

## 添加新语言/框架

参见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) 中的详细说明。

## 代码检查

```bash
python -m py_compile software-copyright-materials/scripts/*.py
```

## 许可证

贡献即表示同意在 [MIT License](LICENSE) 下授权你的代码。
