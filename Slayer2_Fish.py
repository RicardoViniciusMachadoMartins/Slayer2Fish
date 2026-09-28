import os
import json
import time
import mss
import numpy as np
import cv2
import pydirectinput
import keyboard
import tkinter as tk
import sys

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0.0


class FramelessBoxSelector:
    def __init__(self, title, initial_bbox, screen_w, screen_h, border_color="#00ff00"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        bg_trans = "#000001"
        self.root.config(bg=bg_trans)
        self.root.wm_attributes("-transparentcolor", bg_trans)

        self.screen_w = screen_w
        self.screen_h = screen_h
        self.result = None

        left = int(initial_bbox.get("left", screen_w * 0.7348958333333333))
        top = int(initial_bbox.get("top", screen_h * 0.2814814814814815))
        width = max(30, int(initial_bbox.get("width", screen_w * 0.034375)))
        height = max(50, int(initial_bbox.get("height", screen_h * 0.3861111111111111)))

        self.root.geometry(f"{width}x{height}+{left}+{top}")

        self.main_frame = tk.Frame(self.root, bg=bg_trans, highlightbackground=border_color, highlightthickness=2)
        self.main_frame.pack(fill="both", expand=True)

        self.label = tk.Label(
            self.main_frame, text=title, bg=bg_trans, fg=border_color,
            font=("Segoe UI", 8, "bold"), justify="center"
        )
        self.label.pack(expand=True, fill="both")

        self.btn = tk.Button(
            self.main_frame, text="[ SAVE ]", bg=bg_trans, fg=border_color,
            activebackground=bg_trans, activeforeground=border_color,
            relief="flat", font=("Segoe UI", 8, "bold"), command=self.save_and_close,
            bd=0, highlightthickness=0
        )
        self.btn.pack(side="bottom", fill="x", padx=2, pady=2)

        self.grip = tk.Label(
            self.main_frame, text="◢", bg=bg_trans, fg=border_color,
            cursor="size_nw_se", font=("Segoe UI", 10, "bold")
        )
        self.grip.place(relx=1.0, rely=1.0, x=-2, y=-2, anchor="se")

        self.main_frame.bind("<Button-1>", self._start_move)
        self.main_frame.bind("<B1-Motion>", self._do_move)
        self.label.bind("<Button-1>", self._start_move)
        self.label.bind("<B1-Motion>", self._do_move)

        self.grip.bind("<Button-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._do_resize)

        self.root.bind("<Return>", lambda event: "break")

    def _start_move(self, event):
        self._x = event.x
        self._y = event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

    def _start_resize(self, event):
        self._rx = event.x_root
        self._ry = event.y_root
        self._start_w = self.root.winfo_width()
        self._start_h = self.root.winfo_height()

    def _do_resize(self, event):
        nw = max(30, self._start_w + (event.x_root - self._rx))
        nh = max(50, self._start_h + (event.y_root - self._ry))
        self.root.geometry(f"{nw}x{nh}")

    def save_and_close(self):
        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        self.result = {
            "x": max(0, x) / self.screen_w,
            "y": max(0, y) / self.screen_h,
            "w": max(10, w) / self.screen_w,
            "h": max(10, h) / self.screen_h
        }
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.result


class FishingMacro:
    def __init__(self, config_filename="config.json"):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) \
            else os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(base_dir, config_filename)

        self.default_config = {
            "hotkeys": {"hotkey_1": "F1", "hotkey_2": "F2"},
            "scan_area": {
                "x": 0.7348958333333333,
                "y": 0.2814814814814815,
                "w": 0.030208333333333334,
                "h": 0.3685185185185185
            },
            "task_fps": 30.0,
            "timings": {
                "cast_settle_sec": 0.08,
                "cast_after_sec": 0.3,
                "wait_minigame_start_sec": 15.0,
                "after_collect_sec": 0.5,
                "after_minigame_sec": 0.3
            },
            "advanced": {
                "inertia_prediction_factor": 1.2,
                "white_gone_frames": 20.0,
                "wait_before_t_sec": 5.0
            }
        }

        self.load_config()
        self.running = False
        self.state = "IDLE"
        self.sct = mss.mss()

        self.prev_white_y = None
        self.last_frame_time = None

        monitor = self.sct.monitors[1]
        self.screen_width = monitor["width"]
        self.screen_height = monitor["height"]

    def load_config(self):
        if not os.path.exists(self.config_path) or os.path.getsize(self.config_path) == 0:
            self.cfg = self.default_config
            self.save_config()
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.cfg = json.load(f)
        except Exception:
            self.cfg = self.default_config
            self.save_config()

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, indent=2)

    def release_all_inputs(self):
        pydirectinput.mouseUp()
        pydirectinput.keyUp('t')

    def toggle_macro(self):
        self.running = not self.running
        if not self.running:
            self.release_all_inputs()
            self.state = "IDLE"
            print("\n[MACRO] >>> PAUSADO <<<")
        else:
            self.state = "CASTING"
            print("\n[MACRO] >>> INICIADO <<<")

    def select_scan_area(self):
        was_running = self.running
        self.running = False
        self.release_all_inputs()

        bbox = self.get_scan_bbox()
        selector = FramelessBoxSelector("Área do Minijogo (F2)", bbox, self.screen_width, self.screen_height,
                                         border_color="#00ff00")
        new_area = selector.run()

        if new_area:
            self.cfg["scan_area"] = new_area
            self.save_config()
            print("[F2] Área salva com sucesso!")

        self.running = was_running

    def get_scan_bbox(self):
        sa = self.cfg["scan_area"]
        w = max(10, int(sa["w"] * self.screen_width))
        h = max(10, int(sa["h"] * self.screen_height))
        left = int(sa["x"] * self.screen_width)
        top = int(sa["y"] * self.screen_height)
        return {"top": top, "left": left, "width": w, "height": h}

    def process_minigame_frame(self, frame):
        bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        mask_green = cv2.inRange(hsv, np.array([35, 25, 40]), np.array([100, 255, 255]))
        green_pixels = np.column_stack(np.where(mask_green > 0))
        
        val_channel = hsv[:, :, 2]
        white_v_thresh = max(160, min(240, np.percentile(val_channel, 92)))
        mask_white = cv2.inRange(hsv, np.array([0, 0, int(white_v_thresh)]), np.array([180, 60, 255])
        )
        contours, _ = cv2.findContours(mask_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        curr_white_y = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 5 < area < 400:
                x, y, w, h = cv2.boundingRect(cnt)
                curr_white_y = y + (h / 2.0)
                break

        if curr_white_y is None:
            self.prev_white_y = None
            return False, False

        green_y = np.mean(green_pixels[:, 0]) if len(green_pixels) > 0 else frame.shape[0] / 2.0

        now = time.time()
        velocity_y = 0.0
        if self.prev_white_y is not None and self.last_frame_time is not None:
            dt = now - self.last_frame_time
            if dt > 0:
                velocity_y = (curr_white_y - self.prev_white_y) / dt

        self.prev_white_y = curr_white_y
        self.last_frame_time = now

        prediction_factor = self.cfg.get("advanced", {}).get("inertia_prediction_factor", 1.2)
        predicted_white_y = curr_white_y + (velocity_y * (prediction_factor * 0.08))
        diff = predicted_white_y - green_y

        if diff > 1.5:
            should_hold = True
        elif diff < -1.5:
            should_hold = False
        else:
            should_hold = (int(now * 100) % 2 == 0)

        return True, should_hold

    def interruptible_sleep(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            if keyboard.is_pressed("esc") or not self.running:
                return False
            time.sleep(0.01)
        return True

    def run(self):
        hk_start = self.cfg["hotkeys"].get("hotkey_1", "F1")
        hk_select = self.cfg["hotkeys"].get("hotkey_2", "F2")

        print("\n==========================================")
        print("          AUTOFISH MACRO PYTHON             ")
        print("============================================")
        print(f"[{hk_start}]  - Iniciar / Pausar")
        print(f"[{hk_select}]  - Ajustar Área da Barra do Minijogo")
        print("[ESC] - Sair\n")

        keyboard.add_hotkey(hk_start, self.toggle_macro)
        keyboard.add_hotkey(hk_select, self.select_scan_area)

        target_fps = self.cfg.get("task_fps", 30.0)
        frame_delay = 1.0 / target_fps

        white_gone_counter = 0
        minigame_detected_once = False
        minigame_start_time = 0
        loop_counter = 0

        while True:
            if keyboard.is_pressed("esc"):
                self.release_all_inputs()
                print("\n[EMERGÊNCIA] Programa encerrado.")
                break

            if not self.running:
                time.sleep(0.05)
                continue

            start_time = time.time()
            timings = self.cfg.get("timings", {})
            loop_counter += 1
            if loop_counter > 1000:
                self.sct.close()
                self.sct = mss.mss()
                loop_counter = 0

            if self.state == "CASTING":
                print("[STATUS] Arremessando linha...")
                pydirectinput.mouseDown()

                if not self.interruptible_sleep(timings.get("cast_settle_sec", 0.08)):
                    continue
                pydirectinput.mouseUp()

                if not self.interruptible_sleep(timings.get("cast_after_sec", 0.3)):
                    continue

                self.state = "MINIGAME"
                minigame_start_time = time.time()
                minigame_detected_once = False
                white_gone_counter = 0
                self.prev_white_y = None
                print("[STATUS] Aguardando minijogo...")

            elif self.state == "MINIGAME":
                if not self.running:
                    self.release_all_inputs()
                    continue

                bbox = self.get_scan_bbox()
                frame = np.array(self.sct.grab(bbox))

                active, should_hold = self.process_minigame_frame(frame)

                if active:
                    if not minigame_detected_once:
                        print("[STATUS] Minijogo ativo! Acompanhando...")
                    minigame_detected_once = True
                    white_gone_counter = 0

                    if should_hold:
                        pydirectinput.mouseDown()
                    else:
                        pydirectinput.mouseUp()
                else:
                    pydirectinput.mouseUp()
                    if minigame_detected_once:
                        white_gone_counter += 1

                max_miss = self.cfg.get("advanced", {}).get("white_gone_frames", 20.0)
                wait_limit = timings.get("wait_minigame_start_sec", 15.0)
                time_elapsed = time.time() - minigame_start_time

                if (minigame_detected_once and white_gone_counter >= max_miss) or \
                   (not minigame_detected_once and time_elapsed > wait_limit):
                    pydirectinput.mouseUp()
                    print("[STATUS] Minijogo finalizado. Preparando para aguardar...")
                    self.state = "COLLECTING"

            elif self.state == "COLLECTING":
                wait_time = self.cfg.get("advanced", {}).get("wait_before_t_sec", 5.0)
                print(f"[STATUS] Aguardando {wait_time} segundos após minijogo...")
                if not self.interruptible_sleep(wait_time):
                    continue

                print("[STATUS] Segurando 'T' por 3 segundos...")
                t_start = time.time()
                pydirectinput.keyDown('t')
                while time.time() - t_start < 3.0:
                    if not self.running or keyboard.is_pressed("esc"):
                        break
                    time.sleep(0.01)
                self.release_all_inputs()

                if not self.interruptible_sleep(timings.get("after_collect_sec", 0.5)):
                    continue

                print("[STATUS] Ciclo concluído. Reiniciando arremesso...")
                self.state = "CASTING"

            elapsed = time.time() - start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


if __name__ == "__main__":
    macro = FishingMacro("config.json")
    macro.run()