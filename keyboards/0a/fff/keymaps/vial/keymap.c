/*
Copyright 2019 @foostan
Copyright 2020 Drashna Jaelre <@drashna>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include QMK_KEYBOARD_H

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
      KC_Q,    KC_W,               KC_Y,    KC_U,
      KC_A,    KC_S,                   KC_H,    KC_J
  ),

    [1] = LAYOUT(
       KC_1,    KC_2,                     KC_6,    KC_7,
      XXXXXXX, XXXXXXX,                    KC_LEFT, KC_DOWN
  ),

    [2] = LAYOUT(
       KC_TAB, KC_EXLM,                      KC_CIRC, KC_AMPR,
      KC_LCTL, XXXXXXX,                     KC_MINS,  KC_EQL

  ),

    [3] = LAYOUT(
      QK_BOOT, XXXXXXX,                     XXXXXXX, XXXXXXX,
      RGB_TOG, RGB_HUI,                     XXXXXXX, XXXXXXX
  )
};
