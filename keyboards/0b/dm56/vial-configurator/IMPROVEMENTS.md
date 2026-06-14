# 改进进度

## ✅ 已完成

### 1. KLE 标签自动赋值 Layer0
- 更新了 `kle_parser.py`
- 添加了 `LABEL_TO_KEYCODE` 映射表
- 添加了 `_infer_keycode()` 方法
- 支持字母、数字、符号、功能键、F键、导航键自动识别
- 支持 "MO(1)", "Layer 1" 等层切换标签识别

---

## 🔄 待完成

### 2. 键码分类参考 Vial 页面布局
**文件**: `src/ui/editor_keymap.py`

需要更新 `KEYCODE_GROUPS` 字典，参考 Vial 的分类：
- Basic（基础）
- Media（媒体）
- Macro（宏）
- Layers（层）
- Special（特殊）
- Quantum（QMK 特殊）
- Lighting（灯光）
- Numpad（数字键盘）
- International（国际化）

### 3. 主控引脚自动分配
**文件**: `src/ui/config_panel.py` 的 `_rebuild_pin_selectors()` 方法

需要添加：
```python
def _auto_assign_pins(self):
    """选择主控后自动按顺序分配引脚"""
    mcu = MCU_DATABASE.get(self.cfg.mcu_key)
    pins = mcu.usable_pins() if mcu else []

    rows, cols = self.kb.matrix_size()
    if self.cfg.is_split:
        rows = rows // 2

    # 自动分配：前 N 个引脚给行，后 M 个引脚给列
    self.cfg.row_pins = [p.name for p in pins[:rows]]
    self.cfg.col_pins = [p.name for p in pins[rows:rows+cols]]
```

### 4. 32U4/RP2040 分体通信优化
**文件**: `src/core/mcu_db.py`

需要更新 `SPLIT_SERIAL_PRESETS`：
```python
SPLIT_SERIAL_PRESETS = {
    "atmega32u4": [
        {
            "desc": "单线通信（VCC+GND+1引脚）",
            "driver": "bitbang",
            "tx": "PD0",  # 同一引脚
            "rx": "PD0",
            "note": "TRRS 4芯线：VCC/GND/Data/NC"
        },
    ],
    "RP2040": [
        {
            "desc": "双线全双工（VCC+GND+2引脚）",
            "driver": "vendor",
            "tx": "GP0",
            "rx": "GP1",
            "note": "TRRS 4芯线：VCC/GND/TX/RX"
        },
    ],
}
```

### 5. UI 风格参照 Vial 客户端
**文件**: `src/ui/main_window.py` 和所有 UI 文件

需要调整：
- 配色方案：Vial 使用深色主题 + 蓝紫色强调色
- 字体：更紧凑的布局
- 按钮样式：扁平化设计
- 键帽渲染：更接近 Vial 的圆角矩形 + 渐变阴影

---

## 📝 下一步操作建议

由于改进点较多，建议分批完成：

**批次 1（核心功能）**:
- ✅ KLE 标签自动赋值（已完成）
- 键码分类参考 Vial
- 主控引脚自动分配

**批次 2（用户体验）**:
- 32U4/RP2040 分体通信优化
- UI 风格调整

请告诉我继续哪一批次？
