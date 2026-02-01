# Node Types

## skill
- 技能/效果触发源。
- 需要输入端口（触发/气）。

## mechanic
- 规则改变、放大、门控、转换等。
- 常见模板：SOURCE / CONVERTER / AMPLIFIER / FILTER / GATE / STORAGE。

## stat
- 属性/资源/阈值/上限。
- 作为被动贡献与通气节点。

## unknown
- 迁移不完整标记，需人工修复。

## Template Catalog
- 见 `web/node_templates.json`。
- 每个模板包含 param_schema 与 ports 约束。
