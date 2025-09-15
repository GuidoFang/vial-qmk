#pragma once

#ifdef RGBLIGHT_ENABLE
// RGB 灯带配置
#define RGB_DI_PIN GP2              // 数据引脚（GP2 为示例；左右手 MCU 均使用相同定义，但硬件上连接各自的 GP2）
#define RGBLED_NUM 20               // 总 LED 数（左手 10 + 右手 10）
#define RGBLED_SPLIT { 10, 10 }     // 分体 LED 分配：左手 10 颗，右手 10 颗
#define RGBLIGHT_LIMIT_VAL 120      // 最大亮度（0-255；降低以节省功耗，避免过热）
#define RGBLIGHT_HUE_STEP 8         // 色调调整步长
#define RGBLIGHT_SAT_STEP 8         // 饱和度调整步长
#define RGBLIGHT_VAL_STEP 8         // 亮度调整步长

// 启用常见灯效（可选，根据需求选择；这些在 Vial GUI 中可用）
#define RGBLIGHT_EFFECT_BREATHING
#define RGBLIGHT_EFFECT_RAINBOW_MOOD
#define RGBLIGHT_EFFECT_RAINBOW_SWIRL
#define RGBLIGHT_EFFECT_SNAKE
#define RGBLIGHT_EFFECT_KNIGHT
#define RGBLIGHT_EFFECT_CHRISTMAS
#define RGBLIGHT_EFFECT_STATIC_GRADIENT
#define RGBLIGHT_EFFECT_RGB_TEST
#define RGBLIGHT_EFFECT_ALTERNATING
#define RGBLIGHT_EFFECT_TWINKLE
#endif
