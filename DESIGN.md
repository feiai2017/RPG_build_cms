# 五行棋盘 UI 设计规范（Streamlit）
参考图：assets/board_ref.png

## 目标
- 美观、大方、规整、对称
- 五行区域槽位数量严格一致（对称同构）
- 槽位类型非常明显（形状 + 描边 + 图标 + 尺寸层级）
- 可扩展：参数改一改，槽位数量可增（BD 空间大）
- 有图例（legend）和筛选/高亮交互

## 布局骨架（必须严格对称）
- 圆盘分 5 扇区：木/火/土/金/水（顺时针）
- 同心环 rings：默认 4 圈（可配置扩展到 6）
- 每元素每圈 slots_per_ring = 6（可配置）
- 相邻元素边界桥接：bridges_per_boundary_per_ring = 2（可配置）
- 中心：太极核 + 核心槽位 core_slots = 5（可配置 3~7）

## 节点类型（必须一眼可分辨）
使用「形状 + 描边 + 内部小图标/符号」进行区分：
- SMALL 普通节点：圆形 ●
- MEDIUM 中型节点：圆角方形 ◼︎(rounded)
- KEYSTONE 关键节点：六边形 ⬡（更大，更亮）
- SOCKET 插槽节点：菱形 ◆（中空/内点）
- BRIDGE 桥接节点：小六边形 ⬡（连线更亮）
- CONVERT 转化节点：六边形 ⬡ + 双箭头标记 ⇄

## 视觉风格（参考图一致）
- 深色背景，外圈 teal 光晕边框
- 五行区域使用半透明扇区底色（木绿/火红/土黄/金灰白/水蓝）
- 节点本体颜色按所属元素，节点描边更亮（霓虹感）
- 连线：
  - 域内连线：弱一些
  - 桥接连线：更亮、更粗

## 交互（Streamlit 最低要求）
- 底部图例（legend）：点击某类节点 => 高亮该类、其他变暗
- 选择元素高亮：选择木/火/土/金/水 => 该元素节点高亮
- 显示开关：Show bridges / Show labels / Show ring guides
- Hover：显示 node_id、type、element、ring、index、tags

## 数据结构（必须程序化生成，禁止手工摆点）
- 通过 generate_board(params) 生成 nodes + edges
- nodes 字段：id, element, ring, idx, type, pos(x,y), tags, unlock_realm(optional)
- edges 字段：from, to, kind(intra/bridge)

## 验收标准（必须满足）
- 每个元素的节点数量相等（严格断言）
- 节点类型在图上非常容易区分（肉眼一眼）
- 总节点数显著大于旧版（默认至少 120+）
- UI 中存在图例与筛选交互

