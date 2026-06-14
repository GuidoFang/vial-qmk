#include QMK_KEYBOARD_H

#define _QWERTY 0
#define _LOWER 1
#define _RAISE 2

#define RAISE MO(_RAISE)
#define LOWER MO(_LOWER)

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_QWERTY] = LAYOUT(
        KC_GRV  , KC_1   , KC_2  , KC_3  , KC_4  , KC_5  , KC_4  ,                                 KC_5  , KC_6  , KC_7   , KC_8   , KC_9  , KC_0  , KC_LBRC  ,
        KC_TAB  , KC_Q   , KC_W  , KC_E  , KC_R  , KC_T  , KC_R  ,                                 KC_T  , KC_Y  , KC_U   , KC_I   , KC_O  , KC_P  , KC_QUOT  ,
        KC_LSFT , KC_A   , KC_S  , KC_D  , KC_F  , KC_G  , KC_F  ,                                 KC_G  , KC_H  , KC_J   , KC_K   , KC_L  ,KC_SCLN, KC_LSFT  ,
        KC_LCTL , KC_Z   , KC_X  , KC_C  , KC_V  , KC_B  ,                                                 KC_N  ,  KC_N  , KC_M   , KC_COMM,KC_DOT, KC_SLSH  ,
        KC_LCTL , KC_Z   , KC_LBRC,KC_RBRC,                                                                                 KC_PLUS, KC_EQL,KC_SLSH, KC_LCTL  ,
                                                    RAISE ,KC_SPC ,                                          KC_ENT,  LOWER ,
                                                    KC_TAB,KC_HOME,                                          KC_END,  KC_DEL,
                                                    KC_BSPC,KC_GRV,                                          KC_LGUI, KC_LALT
    ),

    [_LOWER] = LAYOUT(
        KC_GRV  , KC_1   , KC_2  , KC_3  , KC_4  , KC_5  , KC_4  ,                                 KC_5  , KC_6  , KC_7   , KC_8   , KC_9  , KC_0  , KC_LBRC  ,
        KC_TAB  , KC_Q   , KC_W  , KC_E  , KC_R  , KC_T  , KC_R  ,                                 KC_T  , KC_Y  , KC_U   , KC_I   , KC_O  , KC_P  , KC_QUOT  ,
        KC_LSFT , KC_A   , KC_S  , KC_D  , KC_F  , KC_G  , KC_F  ,                                 KC_G  , KC_H  , KC_J   , KC_K   , KC_L  ,KC_SCLN, KC_LSFT  ,
        KC_LCTL , KC_Z   , KC_X  , KC_C  , KC_V  , KC_B  ,                                                 KC_N  ,  KC_N  , KC_M   , KC_COMM,KC_DOT, KC_SLSH  ,
        KC_LCTL , KC_Z   , KC_LBRC,KC_RBRC,                                                                                 KC_PLUS, KC_EQL,KC_SLSH, KC_LCTL  ,
                                                    RAISE ,KC_SPC ,                                          KC_ENT,  LOWER ,
                                                    KC_TAB,KC_HOME,                                          KC_END,  KC_DEL,
                                                    KC_BSPC,KC_GRV,                                          KC_LGUI, KC_LALT
    ),

    [_RAISE] = LAYOUT(
        KC_GRV  , KC_1   , KC_2  , KC_3  , KC_4  , KC_5  , KC_4  ,                                 KC_5  , KC_6  , KC_7   , KC_8   , KC_9  , KC_0  , KC_LBRC  ,
        KC_TAB  , KC_Q   , KC_W  , KC_E  , KC_R  , KC_T  , KC_R  ,                                 KC_T  , KC_Y  , KC_U   , KC_I   , KC_O  , KC_P  , KC_QUOT  ,
        KC_LSFT , KC_A   , KC_S  , KC_D  , KC_F  , KC_G  , KC_F  ,                                 KC_G  , KC_H  , KC_J   , KC_K   , KC_L  ,KC_SCLN, KC_LSFT  ,
        KC_LCTL , KC_Z   , KC_X  , KC_C  , KC_V  , KC_B  ,                                                 KC_N  ,  KC_N  , KC_M   , KC_COMM,KC_DOT, KC_SLSH  ,
        KC_LCTL , KC_Z   , KC_LBRC,KC_RBRC,                                                                                 KC_PLUS, KC_EQL,KC_SLSH, KC_LCTL  ,
                                                    RAISE ,KC_SPC ,                                          KC_ENT,  LOWER ,
                                                    KC_TAB,KC_HOME,                                          KC_END,  KC_DEL,
                                                    KC_BSPC,KC_GRV,                                          KC_LGUI, KC_LALT
    )
};
