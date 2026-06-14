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

void keyboard_post_init_user(void) {
    debug_enable=true;
    debug_matrix=true;
    debug_keyboard=true;
    debug_mouse=true;
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
