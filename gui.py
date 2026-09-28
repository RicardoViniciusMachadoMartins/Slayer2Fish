import os
import json
import time
import threading
import tkinter as tk
import customtkinter as ctk

from Slayer2_Fish import FishingMacro, FramelessBoxSelector

ctk.CTk._windows_set_titlebar_color = lambda self, color_mode: None

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AutoFishGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoFish Bot - Configurações")
        self.geometry("520x620")
        self.resizable(False, False)

        self.bind("<Escape>", self.emergency_exit)
        self.macro = FishingMacro("config.json")

        self.tabview = ctk.CTkTabview(self, width=490, height=580)
        self.tabview.pack(padx=15, pady=10, fill="both", expand=True)

        self.tab_main = self.tabview.add("Principal")
        self.tab_adv = self.tabview.add("Avançado (Config)")

        self.build_main_tab()
        self.build_advanced_tab()

        self.update_status_loop()

    def emergency_exit(self, event=None):
        print("\n[EMERGÊNCIA] Encerrando aplicação via ESC...")
        if hasattr(self, 'macro') and self.macro:
            try:
                self.macro.release_all_inputs()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)

    def build_main_tab(self):
        self.lbl_title = ctk.CTkLabel(
            self.tab_main, 
            text="AUTOFISH MACRO", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_title.pack(pady=(15, 5))

        self.lbl_status = ctk.CTkLabel(
            self.tab_main, 
            text="STATUS: DESATIVADO", 
            text_color="#FF4B4B", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_status.pack(pady=(0, 20))

        self.btn_toggle = ctk.CTkButton(
            self.tab_main, 
            text="INICIAR MACRO (F1)", 
            fg_color="#28a745", 
            hover_color="#218838",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.toggle_macro_gui
        )
        self.btn_toggle.pack(fill="x", padx=30, pady=10)

        self.btn_select_area = ctk.CTkButton(
            self.tab_main, 
            text="DEFINIR ÁREA DO MINIJOGO (F2)", 
            fg_color="#17a2b8", 
            hover_color="#138496",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.select_area_gui
        )
        self.btn_select_area.pack(fill="x", padx=30, pady=10)

        info_frame = ctk.CTkFrame(self.tab_main)
        info_frame.pack(fill="x", padx=30, pady=20)

        lbl_info = ctk.CTkLabel(
            info_frame, 
            text="Atalhos Globais:\n"
                 "• [F1] : Liga / Pausa a automação\n"
                 "• [F2] : Redimensiona a caixa de leitura do minijogo\n"
                 "• [ESC] : FECHAR DE EMERGÊNCIA\n",
            justify="left",
            font=ctk.CTkFont(size=12)
        )
        lbl_info.pack(padx=15, pady=15)

    def build_advanced_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_adv, width=450, height=450)
        scroll_frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.entries = {}


        def add_field(parent, label_text, key_path, default_val):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", pady=4, padx=5)
            
            lbl = ctk.CTkLabel(frame, text=label_text, anchor="w", font=ctk.CTkFont(size=11))
            lbl.pack(side="left", padx=5)

            entry = ctk.CTkEntry(frame, width=120)
            entry.insert(0, str(default_val))
            entry.pack(side="right", padx=5)

            self.entries[key_path] = entry

        ctk.CTkLabel(scroll_frame, text="Teclas de Atalho", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 5))
        add_field(scroll_frame, "Atalho Iniciar/Pausar:", "hotkeys.hotkey_1", self.macro.cfg["hotkeys"].get("hotkey_1", "F1"))
        add_field(scroll_frame, "Atalho Selecionar Área:", "hotkeys.hotkey_2", self.macro.cfg["hotkeys"].get("hotkey_2", "F2"))


        ctk.CTkLabel(scroll_frame, text="Desempenho", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(15, 5))
        add_field(scroll_frame, "FPS Alvo:", "task_fps", self.macro.cfg.get("task_fps", 60.0))

        timings = self.macro.cfg.get("timings", {})
        ctk.CTkLabel(scroll_frame, text="Tempos de Espera (Segundos)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(15, 5))
        add_field(scroll_frame, "Tempo para Arremessar (Settle):", "timings.cast_settle_sec", timings.get("cast_settle_sec", 0.08))
        add_field(scroll_frame, "Pausa Após Arremesso:", "timings.cast_after_sec", timings.get("cast_after_sec", 0.3))
        add_field(scroll_frame, "Tempo Máx Aguardando Minijogo:", "timings.wait_minigame_start_sec", timings.get("wait_minigame_start_sec", 15.0))
        add_field(scroll_frame, "Pausa Pós Minijogo:", "timings.after_minigame_sec", timings.get("after_minigame_sec", 0.3))
        add_field(scroll_frame, "Pausa Pós Coleta:", "timings.after_collect_sec", timings.get("after_collect_sec", 0.5))

        adv = self.macro.cfg.get("advanced", {})
        ctk.CTkLabel(scroll_frame, text="Parâmetros de Precisão", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(15, 5))
        add_field(scroll_frame, "Fator Predição de Inércia:", "advanced.inertia_prediction_factor", adv.get("inertia_prediction_factor", 1.2))
        add_field(scroll_frame, "Limite Quadros Sem Branco:", "advanced.white_gone_frames", adv.get("white_gone_frames", 20.0))
        add_field(scroll_frame, "Espera Pós-Minijogo (Segura T):", "advanced.wait_before_t_sec", self.macro.cfg.get("advanced", {}).get("wait_before_t_sec", 5.0))

        btn_save = ctk.CTkButton(
            self.tab_adv, 
            text="SALVAR CONFIGURAÇÕES", 
            fg_color="#28a745", 
            hover_color="#218838",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.save_advanced_config
        )
        btn_save.pack(fill="x", padx=10, pady=10)

    def toggle_macro_gui(self):
        self.macro.toggle_macro()
        self.update_gui_status()

    def select_area_gui(self):
        threading.Thread(target=self.macro.select_scan_area, daemon=True).start()

    def update_gui_status(self):
        if self.macro.running:
            self.lbl_status.configure(text="STATUS: EM EXECUÇÃO", text_color="#28a745")
            self.btn_toggle.configure(text="PAUSAR MACRO (F1)", fg_color="#dc3545", hover_color="#c82333")
        else:
            self.lbl_status.configure(text="STATUS: DESATIVADO", text_color="#FF4B4B")
            self.btn_toggle.configure(text="INICIAR MACRO (F1)", fg_color="#28a745", hover_color="#218838")

    def update_status_loop(self):
        self.update_gui_status()
        self.after(200, self.update_status_loop)

    def save_advanced_config(self):
        try:
            for key_path, entry in self.entries.items():
                val_str = entry.get().strip()
                keys = key_path.split(".")

                try:
                    val = float(val_str) if "." in val_str else int(val_str)
                except ValueError:
                    val = val_str

                if len(keys) == 1:
                    self.macro.cfg[keys[0]] = val
                elif len(keys) == 2:
                    if keys[0] not in self.macro.cfg:
                        self.macro.cfg[keys[0]] = {}
                    self.macro.cfg[keys[0]][keys[1]] = val

            self.macro.save_config()
            tk.messagebox.showinfo("Sucesso", "Configurações salvas com sucesso no config.json!")

        except Exception as e:
            tk.messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")


if __name__ == "__main__":
    app = AutoFishGUI()
    
    macro_thread = threading.Thread(target=app.macro.run, daemon=True)
    macro_thread.start()

    app.mainloop()