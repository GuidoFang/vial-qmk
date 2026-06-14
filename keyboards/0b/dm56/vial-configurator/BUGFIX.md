# Bug 修复：引脚分配后仍提示未分配

## 问题描述

用户点击「⚡ 自动分配引脚」后，页面显示了对应的引脚，但导出固件时仍然提示"引脚未分配"。

---

## 根本原因

### 1. 配置未保存
**问题**：用户在 Step 3 页面修改引脚配置后，直接点击「导出固件文件夹」按钮，没有触发 `validate()` 方法，导致配置没有保存到 `self.cfg`。

**原因**：
- Step 2 → Step 3 时会调用 `config_panel.validate()`
- 但 Step 3 是最后一步，没有"下一步"按钮
- 用户在 Step 3 修改配置后，直接点击导出按钮
- 导出按钮没有调用 `validate()`，配置未保存

### 2. 检查逻辑不够精确
**问题**：原检查逻辑只判断 `if not self.cfg.row_pins`，无法检测引脚数量不足的情况。

---

## 修复方案

### 修复 1：导出前强制保存配置
**文件**：`src/ui/main_window.py`

```python
def _do_export(self):
    # 强制保存当前配置
    if hasattr(self, 'config_panel'):
        self.config_panel.validate()

    # ... 后续检查逻辑
```

**效果**：确保导出前配置已保存。

---

### 修复 2：优化引脚保存逻辑
**文件**：`src/ui/config_panel.py`

**修改前**：
```python
self.cfg.row_pins = [c.currentText() for c in self.row_combos
                     if not c.currentText().startswith("—")]
```

**修改后**：
```python
self.cfg.row_pins = []
for cmb in self.row_combos:
    pin = cmb.currentText()
    if not pin.startswith("—"):
        self.cfg.row_pins.append(pin)
```

**效果**：逻辑更清晰，便于调试。

---

### 修复 3：改进导出检查逻辑
**文件**：`src/ui/main_window.py`

**修改前**：
```python
if not self.cfg.row_pins or not self.cfg.col_pins:
    QMessageBox.warning(self, "引脚未分配", "...")
```

**修改后**：
```python
rows, cols = self.kb.matrix_size()
if self.cfg.is_split:
    rows = rows // 2

if len(self.cfg.row_pins) < rows or len(self.cfg.col_pins) < cols:
    QMessageBox.warning(
        self, "引脚未完全分配",
        f"矩阵需要：{rows} 行 + {cols} 列\n"
        f"当前已分配：{len(self.cfg.row_pins)} 行 + {len(self.cfg.col_pins)} 列\n\n"
        "请在左侧「主控 & 引脚」标签页完成引脚分配，\n"
        "或点击「⚡ 自动分配引脚」按钮。"
    )
```

**效果**：
- 精确检查引脚数量是否足够
- 提供详细的错误信息
- 提示用户使用自动分配功能

---

## 测试验证

### 测试步骤

1. **正常流程**：
   - Step 1：导入 KLE，自动分配矩阵（6行×6列）
   - Step 2：编辑 Keymap
   - Step 3：选择 RP2040，点击「⚡ 自动分配引脚」
   - 点击「📦 导出固件文件夹」
   - ✅ 应该成功导出

2. **修改后导出**：
   - 完成上述步骤后
   - 在 Step 3 手动修改某个引脚
   - 直接点击「📦 导出固件文件夹」
   - ✅ 应该成功导出（配置已自动保存）

3. **引脚不足**：
   - Step 1：导入 10行×10列的大矩阵
   - Step 3：选择 ATmega32U4（只有 18 个可用引脚）
   - 点击「⚡ 自动分配引脚」
   - ✅ 应该提示"引脚不足"

4. **部分未分配**：
   - Step 3：手动分配 5 行引脚，但矩阵需要 6 行
   - 点击「📦 导出固件文件夹」
   - ✅ 应该提示"引脚未完全分配：矩阵需要 6 行，当前已分配 5 行"

---

## 相关文件

- `src/ui/main_window.py` — 导出逻辑
- `src/ui/config_panel.py` — 配置保存逻辑

---

## 修复状态

✅ **已修复** — 2024-03-07

---

## 额外改进建议

### 1. 实时验证
在引脚选择器的 `currentIndexChanged` 信号中实时更新配置：

```python
def _rebuild_pin_selectors(self, pins: list):
    # ...
    for i in range(rows):
        cmb = QComboBox()
        # 添加实时保存
        cmb.currentIndexChanged.connect(
            lambda idx, i=i: self._on_row_pin_changed(i, idx)
        )
```

### 2. 视觉反馈
未分配的引脚用红色高亮显示：

```python
if cmb.currentText().startswith("—"):
    cmb.setStyleSheet("border: 1px solid red;")
```

### 3. 自动保存提示
在 Step 3 页面添加提示：

```
💡 提示：配置会在导出时自动保存，无需手动操作。
```

---

**问题已解决！** 🎉
