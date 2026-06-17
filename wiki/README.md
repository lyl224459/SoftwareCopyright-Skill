# GitHub Wiki

这个目录包含 GitHub Wiki 的源文件。

## 自动同步

推送 `wiki/` 目录的改动到 main 分支后，[wiki-sync](../.github/workflows/wiki-sync.yml) workflow 会自动将文件同步到 GitHub Wiki 仓库。

## 手动同步

如需手动同步：

```bash
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.wiki.git wiki-repo
cp wiki/*.md wiki-repo/
cd wiki-repo && git add . && git commit -m "Update wiki" && git push
```
