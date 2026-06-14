#include QMK_KEYBOARD_H

#define _QWERTY 0
#define _LOWER 1
#define _RAISE 2

#define RAISE MO(_RAISE)
#define LOWER MO(_LOWER)

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_QWERTY] = LAYOUT(
        KC_Q  , KC_W  , KC_E  , KC_R  , KC_T  ,                         KC_Y  , KC_U  , KC_I  , KC_O  , KC_P  ,
        KC_A  , KC_S  , KC_D  , KC_F  , KC_G  ,                         KC_H  , KC_J  , KC_K  , KC_L  ,KC_SCLN,
        KC_Z  , KC_X  , KC_C  , KC_V  , KC_B  ,                         KC_N  , KC_M  ,KC_COMM,KC_DOT ,KC_SLSH,
                 KC_LBRC,KC_RBRC,                                                       KC_PLUS, KC_EQL,
                                  RAISE,KC_SPC,                          KC_ENT, LOWER,
                                 KC_TAB,KC_HOME,                         KC_END,  KC_DEL,
                                 KC_BSPC, KC_GRV,                        KC_LGUI, KC_LALT
    ),

    [_LOWER] = LAYOUT(
        KC_1  , KC_2  , KC_3  , KC_4  , KC_5  ,                         KC_6  , KC_7  , KC_8  , KC_9  , KC_0  ,
        KC_HOME,KC_PGUP,KC_PGDN,KC_END ,KC_LPRN,                        KC_RPRN, KC_P4 , KC_P5 , KC_P6 ,KC_MINS,
        _______,_______,_______,_______,_______,                        _______, KC_P1 , KC_P2 , KC_P3 ,KC_EQL ,
                 _______,KC_PSCR,                                                       _______, KC_P0,
                                        _______,_______,            _______,_______,
                                      _______,_______,            _______,_______,
                                     _______,_______,            _______,_______

    ),

    [_RAISE] = LAYOUT(
        KC_F1 , KC_F2 , KC_F3 , KC_F4 , KC_F5 ,                        KC_F6  , KC_F7 , KC_F8 , KC_F9 ,KC_F10 ,
        KC_LEFT,KC_UP  ,KC_DOWN,KC_RGHT,KC_LPRN,                        KC_RPRN,KC_MPRV,KC_MPLY,KC_MNXT,_______,
        _______,_______,_______,_______,_______,                        _______,_______,_______,_______,_______,
                _______,_______,                                                        KC_EQL ,_______,
                                          _______,_______,            _______,_______,
                                          _______,_______,            _______,_______,
                                          _______,_______,            _______,_______
    )
};

// ===== WS2812B 5-LED 灯带控制 =====
// 每手 5 颗灯珠 (LED 索引 0-4)，仅主控端计算，从端通过 RGBLIGHT_SPLIT 自动同步
//
// 优先级: 锁定状态 > 非默认图层 > 打字速度 > 放行给 Vial 灯效
//
static uint8_t  active_layer     = 0;
static bool     caps_lock_active = false;
static bool     num_lock_active  = false;
static uint8_t  current_wpm      = 0;

// --- 图层颜色 (HSV) ---
static const HSV layer_colors[5] = {
    [0] = {0,   0,   255},   // QWERTY: 纯白
    [1] = {128, 255, 255},   // LOWER:  青色
    [2] = {28,  255, 255},   // RAISE:  橙色
    [3] = {85,  255, 255},   // Layer 3: 翠绿
    [4] = {191, 255, 255},   // Layer 4: 紫罗兰
};

// --- WPM → 颜色映射 ---
static HSV wpm_color(uint8_t wpm) {
    if (wpm < 20) return (HSV){85,  255, 255};  // 慢速: 绿
    if (wpm < 40) return (HSV){43,  255, 255};  // 中速: 黄
    if (wpm < 60) return (HSV){21,  255, 255};  // 快速: 橙
    return               (HSV){0,   255, 255};   // 极速: 红
}

// --- WPM 计算 (基于最近 16 次按键的时间戳) ---
static uint32_t key_ts[16] = {0};
static uint8_t  key_ts_i    = 0;

static uint8_t calc_wpm(void) {
    if (!is_keyboard_master()) return current_wpm;

    uint32_t now    = timer_read32();
    uint8_t  valid  = 0;
    uint32_t oldest = now;

    for (int i = 0; i < 16; i++) {
        if (key_ts[i] == 0) continue;
        if (now - key_ts[i] < 5000) {   // 5 秒内的按键有效
            valid++;
            if (key_ts[i] < oldest) oldest = key_ts[i];
        }
    }

    if (valid < 3) return 0;              // 至少 3 次按键才算打字
    uint32_t elapsed = now - oldest;
    if (elapsed < 500) return 0;          // 间隔太短无意义
    return (uint8_t)((valid * 60000UL) / elapsed);
}

// --- 刷新灯带 (仅主控端操作) ---
static void refresh_strip(void) {
    if (!is_keyboard_master()) return;

    // 基础层 + 空闲 + 无锁 → 不覆盖，放行给 Vial 灯效
    if (!caps_lock_active && !num_lock_active && current_wpm == 0 && active_layer == 0) {
        return;
    }

    HSV c;
    if (caps_lock_active && num_lock_active) {
        c = (HSV){215, 255, 255};         // 双锁: 品红
    } else if (caps_lock_active) {
        c = (HSV){0, 255, 255};           // Caps: 红
    } else if (num_lock_active) {
        c = (HSV){170, 255, 255};         // Num: 蓝
    } else if (active_layer > 0) {
        c = layer_colors[active_layer];   // 非默认层: 图层颜色优先
    } else if (current_wpm > 0) {
        c = wpm_color(current_wpm);       // 默认层: 打字速度
    } else {
        c = layer_colors[active_layer];   // 兜底
    }

    for (int i = 0; i < 5; i++) {
        rgblight_sethsv_at(c.h, c.s, c.v, i);
    }
}

// --- QMK 钩子 ---
layer_state_t layer_state_set_user(layer_state_t state) {
    active_layer = get_highest_layer(state);
    refresh_strip();
    return state;
}

bool led_update_user(led_t led_state) {
    caps_lock_active = led_state.caps_lock;
    num_lock_active  = led_state.num_lock;
    refresh_strip();
    return true;
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (record->event.pressed && is_keyboard_master()) {
        key_ts[key_ts_i] = timer_read32();
        key_ts_i = (key_ts_i + 1) % 16;
        current_wpm = calc_wpm();
        refresh_strip();
    }
    return true;
}

void housekeeping_task_user(void) {
    // 每 500ms 重新计算 WPM，实现停止打字后的速度衰减
    static uint32_t last_check = 0;
    if (timer_elapsed32(last_check) > 500) {
        last_check = timer_read32();
        uint8_t new_wpm = calc_wpm();
        if (new_wpm != current_wpm) {
            current_wpm = new_wpm;
            refresh_strip();
        }
    }
}

void keyboard_post_init_user(void) {
    debug_enable   = true;
    debug_matrix   = true;
    debug_keyboard = true;
    debug_mouse    = true;
    refresh_strip();
};
static int prev_direction = 0;  // 0=center, 1=up, 2=down, 3=left, 4=right

static int prev_prev_direction = 0;

static int prev_prev_prev_direction = 0;

int get_direction(int x, int y) {
    if (abs(x) < 2 && abs(y) < 2) return 0;

    if (abs(y) > abs(x)) {
        return (y > 0) ? 2 : 1;
    } else {
        return (x > 0) ? 3 : 4;
    }
}

report_mouse_t pointing_device_task_combined_user(report_mouse_t left_report, report_mouse_t right_report) {
    // Left side for scrolling
    left_report.h = left_report.x * 0.1;
    left_report.v = left_report.y * 0.1;
    left_report.x = 0;
    left_report.y = 0;

    // Right side for directional keys
    int current_direction = get_direction(-right_report.x, right_report.y);

    if (prev_direction != 0 && prev_prev_prev_direction == prev_direction) {
        current_direction = prev_direction;
    } else if (current_direction != 0 && prev_prev_direction == current_direction) {
        prev_direction = current_direction;
    };

    if (current_direction != prev_direction) {

        switch (current_direction) {
            case 1: tap_code(KC_UP); break;
            case 2: tap_code(KC_DOWN); break;
            case 3: tap_code(KC_LEFT); break;
            case 4: tap_code(KC_RIGHT); break;
            case 0: break;
        }
    };

    prev_prev_prev_direction = prev_prev_direction;
    prev_prev_direction = prev_direction;
    prev_direction = get_direction(-right_report.x, right_report.y);

    right_report.x = 0;
    right_report.y = 0;
    return pointing_device_combine_reports(left_report, right_report);
}
