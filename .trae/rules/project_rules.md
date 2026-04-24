# 骑行路书项目规则

## 项目概述
- 路书生成工具，用于摩托车/汽车、自行车、步行路线规划
- 使用高德地图Web Service API
- 输出HTML格式路书，包含静态地图和路线详情

## 代码修改规则
- **不要随便修改用户已确认OK的代码**
- 每次修改前确认是否在用户要求范围内
- 不明确时先询问，不要臆测

## UI布局规范

### 页面结构
- 左右两栏布局（6:4比例）
- 左侧：表单输入区
- 右侧：上方结果预览，下方历史记录

### 途经点组件
- 使用 `.waypoint-tag` 标签式显示，紧凑排列
- 容器设置 `min-height: 50px` 预留空间
- 标签可自动换行，不影响页面整体高度

### 历史记录
- 查看按钮使用较小尺寸：`padding: 6px 12px; font-size: 13px;`
- 按钮样式：`flex: none; width: auto;` 避免撑满宽度

### 添加按钮
- 边框使用蓝色 `--accent-color`
- 文字颜色蓝色，与滚动条区分
- 增加 `margin-top` 间距

## 样式约定
- CSS变量定义在 `:root` 和 `[data-theme="dark"]`
- 颜色变量：`--bg-primary`, `--bg-secondary`, `--accent-color`, `--border-color` 等
- 使用 `flex: 1` 的按钮需单独覆盖 `flex: none` 恢复自然宽度
