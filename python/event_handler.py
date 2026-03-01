from evdev import ecodes


class EventHandler:
    def __init__(self, mouse_ops, indicator=None, keyboard_manager=None):
        self.mouse_ops = mouse_ops
        self.indicator = indicator
        self.keyboard_manager = keyboard_manager
        self.ui = None

        self.mouse_mode = False
        self.passthrough_mode = False  # When True, all keys pass through untouched
        self.modifiers_held = set()

        self.speed_levels = {
            ecodes.KEY_1: 2,
            ecodes.KEY_2: 10,
            ecodes.KEY_3: 10,
            ecodes.KEY_4: 10,
            ecodes.KEY_5: 15,
            ecodes.KEY_6: 20,
            ecodes.KEY_7: 25,
            ecodes.KEY_8: 30,
            ecodes.KEY_9: 40,
            ecodes.KEY_0: 50,
        }

        self.allowed_keys = {
            ecodes.KEY_W, ecodes.KEY_A, ecodes.KEY_S, ecodes.KEY_D,
            ecodes.KEY_Q,
            ecodes.KEY_TAB, ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
            ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL,
            ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT,
            ecodes.KEY_ENTER, ecodes.KEY_BACKSPACE, ecodes.KEY_BACKSLASH,
            ecodes.KEY_0, ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3, ecodes.KEY_4,
            ecodes.KEY_5, ecodes.KEY_6, ecodes.KEY_7, ecodes.KEY_8, ecodes.KEY_9,
            ecodes.KEY_PAGEUP, ecodes.KEY_PAGEDOWN,
            ecodes.KEY_CAPSLOCK
        }

        self.modifier_keys = {
            ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
            ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL,
            ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT
        }

    # ------------------------------------------------------------------ #
    #  Mode helpers                                                        #
    # ------------------------------------------------------------------ #

    def exit_mouse_mode(self):
        if self.mouse_ops.left_button_down:
            self.mouse_ops.mouse_button_up('left')
            self.mouse_ops.left_button_down = False
        if self.mouse_ops.right_button_down:
            self.mouse_ops.mouse_button_up('right')
            self.mouse_ops.right_button_down = False

        self.mouse_ops.scroll_up_held = False
        self.mouse_ops.scroll_down_held = False
        self.mouse_ops.precision_mode = False

        self.mouse_mode = False
        self.mouse_ops.pressed_keys.clear()
        self.modifiers_held.clear()

        if self.indicator:
            self.indicator.hide()

        if self.keyboard_manager:
            self.keyboard_manager.ensure_capslock_off()

        print("Mouse mode: OFF")

    def enter_passthrough(self):
        """Fully disable mouse layer — all keys pass through untouched."""
        if self.mouse_mode:
            self.exit_mouse_mode()
        self.passthrough_mode = True
        self.modifiers_held.clear()
        print("Passthrough mode: ON (Ctrl+CapsLock to disable)")

    def exit_passthrough(self):
        self.passthrough_mode = False
        print("Passthrough mode: OFF")

    # ------------------------------------------------------------------ #
    #  Main event handler                                                  #
    # ------------------------------------------------------------------ #

    def handle_event(self, event):
        if event.type != ecodes.EV_KEY:
            return True

        keycode = event.code
        value = event.value  # 0=up, 1=down, 2=repeat

        # ---- Track modifiers always, even in passthrough ----
        if keycode in self.modifier_keys:
            if value == 1:
                self.modifiers_held.add(keycode)
            elif value == 0:
                self.modifiers_held.discard(keycode)
            # Always pass modifiers through
            return True

        ctrl_held = bool(self.modifiers_held & {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL})

        # ---- Ctrl + CapsLock: toggle passthrough mode ----
        if keycode == ecodes.KEY_CAPSLOCK and ctrl_held and value == 1:
            if self.passthrough_mode:
                self.exit_passthrough()
            else:
                self.enter_passthrough()
            return False

        # ---- Passthrough mode ----
        if self.passthrough_mode:
            # CapsLock alone: blink red bar as reminder, but block the key
            if keycode == ecodes.KEY_CAPSLOCK:
                if value == 1 and self.indicator:
                    self.indicator.blink_red(times=6, interval=0.08)
                return False  # Never pass CapsLock through in passthrough mode
            return True  # Everything else passes through

        # ---- Normal / mouse mode handling ----

        # CapsLock alone toggles mouse mode
        if keycode == ecodes.KEY_CAPSLOCK and value == 1:
            # Release all held keys to prevent stuck keys
            if self.ui:
                for key in range(ecodes.KEY_MAX):
                    try:
                        self.ui.write(ecodes.EV_KEY, key, 0)
                    except Exception:
                        pass
                try:
                    self.ui.syn()
                except Exception:
                    pass

            if self.mouse_mode:
                self.exit_mouse_mode()
            else:
                self.mouse_mode = True
                self.mouse_ops.pressed_keys.clear()
                if self.keyboard_manager:
                    self.keyboard_manager.ensure_capslock_off()
                if self.indicator:
                    self.indicator.show()
                print(f"Mouse mode: ON (speed: {self.mouse_ops.base_speed})")

            return False

        if not self.mouse_mode:
            return True

        # ---- Mouse mode ----

        # Exit on modifier combos (except with Enter/Backspace)
        if self.modifiers_held and keycode not in [ecodes.KEY_ENTER, ecodes.KEY_BACKSPACE]:
            if value == 1:
                print(f"Combo detected (modifier + key) - exiting mouse mode")
                self.exit_mouse_mode()
                if self.ui:
                    try:
                        self.ui.write_event(event)
                        self.ui.syn()
                    except:
                        pass
                return False

        # Exit on non-mouse keys
        if keycode not in self.allowed_keys and value == 1:
            print(f"Non-mouse key pressed - exiting mouse mode")
            self.exit_mouse_mode()
            if self.ui:
                try:
                    self.ui.write_event(event)
                    self.ui.syn()
                except:
                    pass
            return False

        # Speed change
        if keycode in self.speed_levels and value == 1:
            if self.mouse_ops.precision_mode:
                self.mouse_ops.precision_mode = False
                if self.indicator:
                    self.indicator.set_precision_mode(False)
            self.mouse_ops.base_speed = self.speed_levels[keycode]
            print(f"Speed: {self.mouse_ops.base_speed}")
            return False

        # Precision mode
        if keycode == ecodes.KEY_Q and value == 1:
            self.mouse_ops.precision_mode = not self.mouse_ops.precision_mode
            if self.indicator:
                self.indicator.set_precision_mode(self.mouse_ops.precision_mode)
            if self.mouse_ops.precision_mode:
                print(f"Precision mode: ON (speed 2 with acceleration)")
            else:
                print(f"Precision mode: OFF (speed {self.mouse_ops.base_speed})")
            self.mouse_ops.move_start_time = None
            return False

        # Acceleration toggle
        if keycode == ecodes.KEY_TAB and value == 1:
            self.mouse_ops.acceleration_enabled = not self.mouse_ops.acceleration_enabled
            if self.indicator:
                self.indicator.set_acceleration(self.mouse_ops.acceleration_enabled)
            status = "ON" if self.mouse_ops.acceleration_enabled else "OFF"
            print(f"Acceleration: {status}")
            self.mouse_ops.move_start_time = None
            return False

        # Movement keys
        if keycode in [ecodes.KEY_W, ecodes.KEY_A, ecodes.KEY_S, ecodes.KEY_D]:
            if value == 1:
                self.mouse_ops.pressed_keys.add(keycode)
            elif value == 0:
                self.mouse_ops.pressed_keys.discard(keycode)
            return False

        # Left click
        if keycode == ecodes.KEY_ENTER:
            if value == 2:
                return False
            if value == 1:
                if not self.mouse_ops.left_button_down:
                    self.mouse_ops.mouse_button_down('left')
                    self.mouse_ops.left_button_down = True
            elif value == 0:
                if self.mouse_ops.left_button_down:
                    self.mouse_ops.mouse_button_up('left')
                    self.mouse_ops.left_button_down = False
            return False

        # Right click
        if keycode == ecodes.KEY_BACKSPACE:
            if value == 2:
                return False
            if value == 1:
                if not self.mouse_ops.right_button_down:
                    self.mouse_ops.mouse_button_down('right')
                    self.mouse_ops.right_button_down = True
            elif value == 0:
                if self.mouse_ops.right_button_down:
                    self.mouse_ops.mouse_button_up('right')
                    self.mouse_ops.right_button_down = False
            return False

        # Scroll
        if keycode == ecodes.KEY_PAGEUP:
            if value == 1:
                self.mouse_ops.scroll_up_held = True
            elif value == 0:
                self.mouse_ops.scroll_up_held = False
            return False

        if keycode == ecodes.KEY_PAGEDOWN:
            if value == 1:
                self.mouse_ops.scroll_down_held = True
            elif value == 0:
                self.mouse_ops.scroll_down_held = False
            return False

        # Middle click
        if keycode == ecodes.KEY_BACKSLASH:
            if value == 1:
                self.mouse_ops.middle_click()
            return False

        return False