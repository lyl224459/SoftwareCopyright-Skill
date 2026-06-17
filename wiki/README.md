# GitHub Wiki

这个目录包含 GitHub Wiki 的源文件。要发布到 GitHub Wiki：

```bash
# 克隆 wiki 仓库
git clone https://github.com/lyl224459/SoftwareCopyright-Skill.wiki.git wiki-repo

# 复制 wiki 源文件
cp wiki/*.md wiki-repo/

# 提交并推送
cd wiki-repo
git add .
git commit -m "Update wiki"
git push
```

GitHub Wiki 是独立于主仓库的 Git 仓库，使用 `.wiki.git` 后缀。
