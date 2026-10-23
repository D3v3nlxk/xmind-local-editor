# Xmind Local Editor

让 AI 助手通过本地文件工具读取、扩写和修改现代 `.xmind` 导图。无需 Xmind 云服务；Python 3 标准库即可运行。

## 能力

- 读取工作表、节点、备注；按标题搜索或查看指定子树。
- 重命名节点和工作表，添加子节点或完整多层分支。
- 先预览再提交；源文件摘要校验、稳定节点 ID、批次操作编号。
- 另存副本，并生成 `.changes.json` 变更记录，原文件保持不变。

## 作为 skill 使用

将本仓库放入助手支持的技能目录，例如 `~/.codex/skills/xmind-local-editor`，然后在新会话中使用：

> 使用 xmind-local-editor 读取指定导图，在“开发计划”下补充测试和发布步骤，另存副本。

入口为 [SKILL.md](SKILL.md)，助手自行调用脚本。

## 命令行

```sh
python3 scripts/xmind.py inspect /path/map.xmind
python3 scripts/xmind.py inspect /path/map.xmind --query 开发
python3 scripts/xmind.py plan /path/map.xmind --request request.json
python3 scripts/xmind.py edit /path/map.xmind --request request.json --output /path/map-edited.xmind
```

请求格式和操作见 SKILL.md。修改前需使用 inspect 返回的 SHA-256 和节点 ID。

## 边界

目前仅支持含 `content.json` 的现代 Xmind ZIP 文档。不是 Xmind 官方项目，不控制打开的窗口或未保存内容，不提供订阅授权功能。尚不支持节点移动、删除、关系或样式修改。保留的缩略图可能过时，归档验证不代表已经通过 GUI 渲染验证。

协议研究记录见 [references/protocol.md](references/protocol.md)。仓库不包含 Xmind 程序、解包源码、模板或账户凭据。

## 测试

```sh
python3 -m unittest discover -s tests -v
```

测试使用自行构造的最小文档，覆盖预览/提交一致性、资源保留和失败批次拒绝，不替代真实应用兼容性测试。
