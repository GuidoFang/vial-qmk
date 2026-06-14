# Vial 固件配置器 v2.0

**可视化三位一体编辑器** — 位置坐标 + 电气矩阵 + 键值 统一管理

参考 Keyboard Layout Editor、Keyboard Firmware Builder、Vial 三大网站设计，实现小白友好的固件配置工具。

---

## 核心特性

✅ **KLE 布局导入** — 支持 Keyboard Layout Editor 导出的 JSON
✅ **可视化矩阵分配** — 点击键帽分配 row/col，支持自动推断
✅ **Keymap 可视化编辑** — 点击键帽 → 选键码赋值，支持多层切换
✅ **完整配置面板** — 主控/引脚/分体/RGB/编码器/OLED/Vial 一站式配置
✅ **一键导出固件** — 自动生成 keyboard.json / keymap.c / vial.json / config.h / rules.mk
✅ **分体键盘支持** — 自动生成 vial_left / vial_right 双份固件

---

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 三步向导流程

#### **Step 1：布局 & 矩阵分配**
- 点击「导入 KLE JSON」或「粘贴 KLE JSON」导入布局
- 选择「整体键盘」或「分体键盘」
- 点击「自动分配矩阵」自动推断 row/col
- 或手动点击键帽，在右侧属性面板编辑矩阵坐标
- 底部矩阵总览表实时显示所有按键的坐标和矩阵位置

#### **Step 2：Keymap 编辑**
- 顶部切换层（Layer 0/1/2...）
- 点击键帽选中
- 在底部键码选择面板点击键码，自动赋值到选中键
- 支持搜索键码、自定义键码输入
- 键帽实时显示当前层的键值

#### **Step 3：配置 & 导出**
- **基本信息**：键盘名称、厂商、VID/PID
- **主控 & 引脚**：选择主控（RP2040/ATmega32U4/STM32），分配行列引脚
- **分体通信**：选择串口驱动、TX/RX 引脚、主从设置
- **功能模块**：RGB 灯带、编码器、OLED、多媒体键、NKRO 等
- **Vial 配置**：自动生成 UID、设置层数、防抖、解锁组合键
- 点击右侧「导出固件文件夹」按钮，选择输出目录

---

## 导出产物

导出后生成完整的 QMK/Vial 固件文件夹：

```
keyboards/
└── your_keyboard/
    ├── keyboard.json          ← 矩阵、主控、布局定义
    ├── config.h               ← RP2040 双击复位等顶层配置
    ├── rules.mk               ← 功能模块开关
    └── keymaps/
        ├── vial_left/         ← 分体左侧固件（整体键盘则为 vial/）
        │   ├── config.h       ← MASTER_LEFT + UID + 串口引脚
        │   ├── keymap.c       ← 各层键值
        │   ├── vial.json      ← Vial UI 布局文件
        │   └── rules.mk       ← VIA_ENABLE + VIAL_ENABLE
        └── vial_right/        ← 分体右侧固件（仅 MASTER_RIGHT 不同）
            ├── config.h
            ├── keymap.c
            ├── vial.json
            └── rules.mk
```

---

## 编译固件

### 方法 1：使用 QMK MSYS（Windows）

1. 将导出的文件夹复制到 `vial-qmk/keyboards/` 目录下
2. 打开 QMK MSYS
3. 执行编译命令：

```bash
# 整体键盘
qmk compile -kb your_keyboard -km vial

# 分体键盘（需分别编译左右）
qmk compile -kb your_keyboard -km vial_left
qmk compile -kb your_keyboard -km vial_right
```

### 方法 2：使用 Docker

```bash
docker run --rm -v $(pwd):/qmk_firmware ghcr.io/qmk/qmk_cli \
  qmk compile -kb your_keyboard -km vial
```

---

## 打包为 EXE

```bash
# Windows
build.bat

# 或手动执行
pyinstaller --onefile --windowed --name "VialConfigurator" main.py
```

输出：`dist/VialConfigurator.exe`

---

## 技术架构

### 核心模块

| 模块 | 说明 |
|------|------|
| `key_model.py` | 按键数据模型（位置+矩阵+键值三合一） |
| `kle_parser.py` | KLE JSON 解析器 |
| `mcu_db.py` | 主控数据库（RP2040/ATmega32U4/STM32） |
| `firmware_generator.py` | 固件文件生成器 |

### UI 组件

| 组件 | 说明 |
|------|------|
| `keyboard_canvas.py` | 键盘画布渲染器（QGraphicsScene） |
| `editor_layout.py` | 布局 & 矩阵编辑器 |
| `editor_keymap.py` | Keymap 可视化编辑器 |
| `config_panel.py` | 配置面板（主控/分体/模块/Vial） |
| `main_window.py` | 主窗口（3步向导） |

---

## 参考设计

- [Keyboard Layout Editor](http://www.keyboard-layout-editor.com/) — 布局可视化
- [Keyboard Firmware Builder](https://kbfirmware.com/) — 矩阵分配
- [Vial](https://get.vial.today/) — Keymap 编辑器

---

## 开发者

基于 DM56 分体键盘固件结构设计，支持 QMK/Vial 全功能配置。

**License:** MIT
