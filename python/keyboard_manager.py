import time
import glob
import threading
import subprocess
from evdev import InputDevice, UInput, ecodes, list_devices


class KeyboardManager:
    def __init__(self):
        self.keyboards = {}
        self.keyboards_lock = threading.Lock()
        self.ui = None
        self.running = True

        self.monitor_thread = threading.Thread(target=self.monitor_new_devices, daemon=True)
        self.monitor_thread.start()

        self.ensure_capslock_off()

    def check_capslock_led_state(self, keyboard):
        try:
            leds = keyboard.leds()
            return ecodes.LED_CAPSL in leds
        except:
            return False

    def ensure_capslock_off(self):
        print("🔍 Checking CapsLock state...")

        keyboards = self.find_all_keyboards()

        capslock_on = False
        for kbd in keyboards:
            if self.check_capslock_led_state(kbd):
                capslock_on = True
                print(f"🔴 CapsLock is ON - turning it off...")
                break

        if not capslock_on:
            print("✅ CapsLock is already OFF")
            return

        try:
            if keyboards:
                ui = UInput.from_device(keyboards[0], name='capslock-fix-virtual')
                for i in range(2):
                    ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 1)
                    ui.syn()
                    ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 0)
                    ui.syn()
                ui.close()
                subprocess.run(['xdotool', 'key', 'Caps_Lock'],
                              capture_output=True, timeout=2)
                print("✅ CapsLock turned OFF!")
        except Exception as e:
            print(f"⚠️  Could not turn off CapsLock: {e}")

    def find_all_keyboards(self):
        keyboards = []
        devices = [InputDevice(path) for path in list_devices()]

        for device in devices:
            if 'ydotool' in device.name.lower() or 'kb-mouse' in device.name.lower():
                continue

            caps = device.capabilities()
            if ecodes.EV_KEY in caps:
                keys = caps[ecodes.EV_KEY]
                if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                    keyboards.append(device)
                    print(f"Found keyboard: {device.name} ({device.path})")

        return keyboards

    def add_keyboard(self, device):
        with self.keyboards_lock:
            if device.path not in self.keyboards:
                try:
                    device.grab()
                    self.keyboards[device.path] = device
                    print(f"+ Added: {device.name}")
                except Exception as e:
                    print(f"Failed to add {device.name}: {e}")

    def remove_keyboard(self, path):
        with self.keyboards_lock:
            if path in self.keyboards:
                device = self.keyboards[path]
                try:
                    device.ungrab()
                except:
                    pass
                print(f"- Removed: {device.name}")
                del self.keyboards[path]

    def monitor_new_devices(self):
        known_paths = set()

        while self.running:
            try:
                current_devices = list_devices()
                current_paths = set(current_devices)

                new_paths = current_paths - known_paths
                for path in new_paths:
                    try:
                        device = InputDevice(path)
                        if 'ydotool' in device.name.lower() or 'kb-mouse' in device.name.lower():
                            known_paths.add(path)
                            continue
                        caps = device.capabilities()
                        if ecodes.EV_KEY in caps:
                            keys = caps[ecodes.EV_KEY]
                            if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                                self.add_keyboard(device)
                                known_paths.add(path)
                    except:
                        pass

                removed_paths = known_paths - current_paths
                for path in removed_paths:
                    self.remove_keyboard(path)
                    known_paths.discard(path)

                time.sleep(2)
            except:
                time.sleep(2)

    def get_devices(self):
        with self.keyboards_lock:
            return list(self.keyboards.values())

    def cleanup(self):
        self.running = False
        with self.keyboards_lock:
            for device in self.keyboards.values():
                try:
                    device.ungrab()
                except:
                    pass

        # Ungrab causes LED to turn on (kernel quirk).
        # Write 0 directly to sysfs to fix it.
        time.sleep(0.15)  # Let ungrab settle
        for path in glob.glob('/sys/class/leds/*capslock*/brightness'):
            try:
                with open(path, 'w') as f:
                    f.write('0')
            except Exception:
                pass  # Not all paths are writable, that's fine

        if self.ui:
            self.ui.close()