# 快速启动指南

## 1. 安装依赖

```bash
cd vial-configurator
pip install -r requirements.txt
```

## 2. 运行程序

```bash
python main.py
```

## 3. 使用流程

### Step 1：布局 & 矩阵分配

1. 点击「📂 导入 KLE JSON」或「📋 粘贴 KLE JSON」
2. 选择「整体键盘」或「分体键盘」
3. 点击「⚡ 自动分配矩阵」
4. 检查底部矩阵总览表，确认所有按键已分配
5. 点击「下一步 ▶」

### Step 2：Keymap 编辑

1. 顶部选择层（Layer 0/1/2...）
2. 点击键帽选中
3. 在底部键码面板点击键码赋值
4. 重复 2-3 完成所有层的键值设置
5. 点击「下一步 ▶」

### Step 3：配置 & 导出

1. 左侧配置面板：
   - **基本信息**：填写键盘名称、VID/PID
   - **主控 & 引脚**：选择主控，分配行列引脚
   - **分体通信**：（分体键盘）配置串口引脚
   - **功能模块**：勾选需要的功能（RGB/编码器/OLED）
   - **Vial 配置**：生成 UID，设置层数
2. 右侧点击「📦 导出固件文件夹」
3. 选择输出目录
4. 完成！

## 4. 编译固件

将导出的文件夹复制到 `vial-qmk/keyboards/` 目录下，然后：

```bash
# 整体键盘
qmk compile -kb your_keyboard -km vial

# 分体键盘
qmk compile -kb your_keyboard -km vial_left
qmk compile -kb your_keyboard -km vial_right
```

## 5. 打包为 EXE（可选）

```bash
# Windows
build.bat

# 输出：dist/VialConfigurator.exe
```

---

## 常见问题

**Q: 导入 KLE JSON 后没有显示？**
A: 检查 JSON 格式是否正确，确保是从 keyboard-layout-editor.com 导出的原始 JSON。

**Q: 自动分配矩阵后坐标不对？**
A: 可以手动点击键帽，在右侧属性面板修改 row/col。

**Q: 分体键盘如何设置？**
A: Step 1 选择「分体键盘」，Step 3 配置「分体通信」标签页。

**Q: 如何添加自定义键码？**
A: Step 2 底部键码面板，在「自定义」输入框输入键码（如 `LT(1,KC_SPC)`），点击「应用」。

**Q: 导出后如何验证文件？**
A: 检查导出目录下是否有 `keyboard.json`、`keymap.c`、`vial.json` 等文件。

---

## 技术支持

- GitHub Issues: [提交问题](https://github.com/your-repo/issues)
- QMK 文档: https://docs.qmk.fm/
- Vial 文档: https://get.vial.today/docs/
