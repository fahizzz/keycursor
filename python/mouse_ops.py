import subprocess
import time
import threading


class MouseOperations:
    def __init__(self):
        self.running = True
        
        # Mouse button states
        self.left_button_down = False
        self.right_button_down = False
        
        # Movement tracking
        self.pressed_keys = set()
        self.move_start_time = None
        self.movement_duration = 0.0
        
        # Scroll states
        self.scroll_up_held = False
        self.scroll_down_held = False
        
        # Settings
        self.base_speed = 10
        self.acceleration_enabled = True
        self.precision_mode = False
        
        # Start threads
        self.move_thread = threading.Thread(target=self.continuous_movement, daemon=True)
        self.move_thread.start()
        
        self.scroll_thread = threading.Thread(target=self.continuous_scroll, daemon=True)
        self.scroll_thread.start()
    
    def move_mouse(self, x, y):
        if x != 0 or y != 0:
            subprocess.run(['ydotool', 'mousemove', '--', str(x), str(y)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def mouse_button_down(self, button='left'):
        button_code = '0x41' if button == 'right' else '0x40'
        subprocess.run(['ydotool', 'click', button_code],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def mouse_button_up(self, button='left'):
        button_code = '0x81' if button == 'right' else '0x80'
        subprocess.run(['ydotool', 'click', button_code],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def scroll(self, direction):
        amount = str(direction)
        subprocess.run(['ydotool', 'mousemove', '--wheel', '--', '0', amount],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def middle_click(self):
        subprocess.run(['ydotool', 'click', '0xC2'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def continuous_scroll(self):
        while self.running:
            if self.scroll_up_held:
                self.scroll(1)
                time.sleep(0.05)
            elif self.scroll_down_held:
                self.scroll(-1)
                time.sleep(0.05)
            else:
                time.sleep(0.05)
    
    def continuous_movement(self):
        while self.running:
            if self.pressed_keys:
                x, y = 0, 0
                
                from evdev import ecodes
                movement_keys = {ecodes.KEY_W, ecodes.KEY_S, ecodes.KEY_A, ecodes.KEY_D}
                is_moving = bool(movement_keys & self.pressed_keys)
                
                if is_moving:
                    current_time = time.time()
                    if self.move_start_time is None:
                        self.move_start_time = current_time
                        self.movement_duration = 0.0
                    else:
                        self.movement_duration = current_time - self.move_start_time
                    
                    if self.precision_mode:
                        accel_multiplier = min(1.0 + (self.movement_duration * 1.0), 3.0)
                        current_speed = int(2 * accel_multiplier)
                    elif self.acceleration_enabled:
                        accel_multiplier = min(1.0 + (self.movement_duration * 1.0), 3.0)
                        current_speed = int(self.base_speed * accel_multiplier)
                    else:
                        current_speed = self.base_speed
                    
                    if ecodes.KEY_W in self.pressed_keys:
                        y -= current_speed
                    if ecodes.KEY_S in self.pressed_keys:
                        y += current_speed
                    if ecodes.KEY_A in self.pressed_keys:
                        x -= current_speed
                    if ecodes.KEY_D in self.pressed_keys:
                        x += current_speed
                    
                    if x != 0 and y != 0:
                        x = int(x * 0.707)
                        y = int(y * 0.707)
                    
                    if x != 0 or y != 0:
                        self.move_mouse(x, y)
                else:
                    self.move_start_time = None
                    self.movement_duration = 0.0
            else:
                self.move_start_time = None
                self.movement_duration = 0.0
            
            time.sleep(0.016)
    
    def cleanup(self):
        self.running = False
        if self.left_button_down:
            self.mouse_button_up('left')
        if self.right_button_down:
            self.mouse_button_up('right')