# 引脚冲突检测 & 不对称分体键盘支持

## 修复内容

### 1. 引脚冲突检测 ✅

**问题**：通信引脚（GP0, GP1）出现在矩阵引脚分配中，导致引脚冲突。

**解决方案**：

#### 1.1 自动分配时避开通信引脚
- 修改 `_auto_assign_pins()` 方法
- 添加 `_get_reserved_pins()` 方法获取保留引脚
- 自动分配时过滤掉通信引脚

```python
def _get_reserved_pins(self) -> set:
    """获取保留引脚（通信引脚 + 模块引脚）"""
    reserved_pins = set()
    if self.cfg.is_split:
        presets = SPLIT_SERIAL_PRESETS.get(self.cfg.mcu_key, [])
        if presets:
            preset = presets[0]
            tx = preset.get("tx", "")
            rx = preset.get("rx", "")
            if tx:
                reserved_pins.add(tx)
            if rx:
                reserved_pins.add(rx)
    return reserved_pins
```

#### 1.2 实时引脚冲突检测
- 添加 `_check_pin_conflict()` 方法
- 每个引脚选择器绑定 `currentIndexChanged` 信号
- 实时检测：
  - 通信引脚冲突（红色边框）
  - 重复分配（橙色边框）

```python
def _check_pin_conflict(self, combo: QComboBox):
    """检查引脚冲突"""
    pin = combo.currentText()
    if pin.startswith("—"):
        combo.setStyleSheet("")
        return

    # 检查通信引脚冲突
    reserved_pins = self._get_reserved_pins()
    if pin in reserved_pins:
        combo.setStyleSheet("border: 2px solid red;")
        QMessageBox.warning(...)
        return

    # 检查重复分配
    if all_assigned.count(pin) > 1:
        combo.setStyleSheet("border: 2px solid orange;")
        QMessageBox.warning(...)
        return

    combo.setStyleSheet("")
```

---

### 2. 不对称分体键盘支持 ✅

**需求**：左右手引脚配置不同的分体键盘（如 DM56）。

**解决方案**：

#### 2.1 UI 改进
- 在「分体通信」标签页添加复选框：`左右手不对称（需分别配置引脚）`
- 勾选后，「主控 & 引脚」标签页显示：
  - 左手行引脚
  - 左手列引脚
  - 右手行引脚
  - 右手列引脚

#### 2.2 数据模型扩展
在 `ProjectConfig` 中添加：
```python
self.row_pins_right: List[str] = []  # 右手行引脚
self.col_pins_right: List[str] = []  # 右手列引脚
self.is_asymmetric = False  # 是否不对称分体
```

#### 2.3 自动分配逻辑
- 对称分体：左右手共用同一套引脚配置
- 不对称分体：左右手各自分配独立引脚

```python
# 对称分体：矩阵行数减半
if self.cfg.is_split and not is_asymmetric:
    rows = rows // 2

# 不对称分体：需要双倍引脚
needed = rows + cols
if is_asymmetric:
    needed = needed * 2  # 左右手各需要一套引脚
```

#### 2.4 固件导出
- **对称分体**：生成单个固件文件夹
  ```
  keyboard_name/
    ├── keyboard.json
    ├── config.h
    ├── rules.mk
    └── keymaps/
        ├── vial_left/
        └── vial_right/
  ```

- **不对称分体**：生成两个独立固件文件夹
  ```
  keyboard_name_left/
    ├── keyboard.json (使用 row_pins + col_pins)
    ├── config.h
    ├── rules.mk
    └── keymaps/
        └── vial_left/

  keyboard_name_right/
    ├── keyboard.json (使用 row_pins_right + col_pins_right)
    ├── config.h
    ├── rules.mk
    └── keymaps/
        └── vial_right/
  ```

---

## 测试场景

### 场景 1：对称分体键盘（RP2040）
1. Step 1：导入 KLE，选择「分体键盘」
2. Step 3：选择 RP2040，点击「⚡ 自动分配引脚」
3. 检查结果：
   - 行引脚：GP2-GP6（避开 GP0, GP1）
   - 列引脚：GP7-GP20
   - 通信引脚：GP0(TX), GP1(RX)
4. 导出固件：生成单个文件夹，包含 vial_left 和 vial_right

### 场景 2：不对称分体键盘（DM56）
1. Step 1：导入 DM56 的 KLE JSON
2. Step 3：
   - 勾选「左右手不对称」
   - 选择 RP2040
   - 点击「⚡ 自动分配引脚」
3. 检查结果：
   - 左手行引脚：GP2-GP6
   - 左手列引脚：GP7-GP20
   - 右手行引脚：GP21-GP25
   - 右手列引脚：GP26-GP29, GP0-GP9（避开通信引脚）
4. 导出固件：生成两个独立文件夹
   - `dm56_left/` 使用左手引脚
   - `dm56_right/` 使用右手引脚

### 场景 3：引脚冲突检测
1. 手动选择引脚时，选择 GP0（通信引脚）
2. 应显示红色边框 + 警告弹窗
3. 选择已被其他矩阵占用的引脚
4. 应显示橙色边框 + 警告弹窗

---

## 修改文件清单

1. **src/ui/config_panel.py**
   - 添加不对称分体复选框
   - 添加 `_on_asymmetric_changed()` 方法
   - 修改 `_rebuild_pin_selectors()` 支持右手引脚
   - 修改 `_auto_assign_pins()` 支持不对称分配
   - 添加 `_get_reserved_pins()` 方法
   - 添加 `_check_pin_conflict()` 方法
   - 修改 `validate()` 保存右手引脚

2. **src/core/firmware_generator.py**
   - 扩展 `ProjectConfig` 添加右手引脚字段
   - 修改 `gen_keyboard_json()` 支持 side 参数
   - 修改 `generate_all()` 支持不对称分体导出

3. **src/ui/main_window.py**
   - 修改 `_do_export()` 检查右手引脚
   - 添加不对称分体导出提示

---

## 用户体验提升

### 改进前
- ❌ 通信引脚与矩阵引脚冲突
- ❌ 无法配置不对称分体键盘
- ❌ 引脚冲突无提示

### 改进后
- ✅ 自动避开通信引脚
- ✅ 实时检测引脚冲突（红色/橙色边框）
- ✅ 支持不对称分体键盘
- ✅ 左右手独立引脚配置
- ✅ 导出时生成独立固件文件夹

---

**修复完成！** 🎉
