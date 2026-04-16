import multiprocessing
import customtkinter as ctk
import psutil
import requests
import time
import threading
import os
import sys
import subprocess
import tkinter.messagebox as messagebox
import platform
import uuid
import ctypes
import json
from velox_hwid import get_unique_id
from PIL import Image, ImageTk
from velox_security import VeloxSecurity
from velox_config import get_ai_provider
from groq import Groq
from duckduckgo_search import DDGS
import sys
import os

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсам, работает и для dev, и для PyInstaller """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Функция для корректного пути к ресурсам внутри EXE ---


def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсам, работает и для dev и для PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


try:
    from proxy import Proxy
except ImportError:
    Proxy = None

# --- КОНФИГУРАЦИЯ ---
VERSION = "1.5.0"
NODE_NAME = f"{platform.node()}_{hex(uuid.getnode())[-4:].upper()}".replace(
    " ", "_")
SETTINGS_URL = "https://nexus-app-6769e-default-rtdb.europe-west1.firebasedatabase.app/settings.json"
ALL_NODES_URL = "https://nexus-app-6769e-default-rtdb.europe-west1.firebasedatabase.app/nodes.json"

cloud_session = requests.Session()
cloud_session.trust_env = False

# --- ЦВЕТОВАЯ ПАЛИТРА UI ---
BG_COLOR = "#0B0F19"
CARD_COLOR = "#151B2B"
ACCENT_COLOR = "#00E5FF"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
BTN_INACTIVE = "#1E293B"
BTN_HOVER = "#00B8D4"


def start_hidden_bot():
    """Запускает вторую копию этого же EXE, но в режиме бота"""
    if "--bot-mode" in sys.argv:
        return
    try:
        # Определяем путь к исполняемому файлу (скрипт или EXE)
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])

        args = [executable,
    script_path,
    "--bot-mode"] if not getattr(sys,
    'frozen',
    False) else [executable,
     "--bot-mode"]

        # Запуск процесса с флагом скрытого окна (CREATE_NO_WINDOW =
        # 0x08000000)
        subprocess.Popen(args,
                         creationflags=0x08000000,
                         close_fds=True)
    except Exception as e:
        print(f"Ошибка автозапуска бота: {e}")

class VeloxApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Инициализируем защиту и получаем токен
        self.sec = VeloxSecurity()
        _, self.token = self.sec.auth_node()

        # 2. Формируем ПОСТОЯННЫЙ ID (из нашего нового файла velox_hwid.py)
        self.display_id = get_unique_id() 

        self.velox_id = self.display_id
        self.safe_node_id = self.display_id
        
        # 3. Твой базовый URL для Firebase
        self.my_db_url = f"https://nexus-app-6769e-default-rtdb.europe-west1.firebasedatabase.app/nodes/{self.display_id}.json"

        # --- ОБНОВЛЕННЫЙ БЛОК ЗАГРУЗКИ С ПАМЯТЬЮ ---
        import requests
        # Инициализируем базовые значения (накопленные ранее)
        self.base_mb = 0.0
        self.base_vlx = 0.0
        self.last_mb = 0.0
        self.last_vlx = 0.0

        try:
            # Добавим таймаут, чтобы приложение не зависало при плохом интернете
            response = requests.get(self.my_db_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Загружаем накопленные данные из Firebase
                    self.base_mb = float(data.get('mb_total', 0.0))
                    self.base_vlx = float(data.get('vlx_earned', 0))
                    
                    # Устанавливаем текущие значения равными накопленным,
                    # чтобы GUI сразу показал общую сумму
                    self.last_mb = self.base_mb
                    self.last_vlx = self.base_vlx
                    print(f"Успех! Баланс узла {self.display_id}: {self.last_vlx} VLX")
                else:
                    print("Новый узел, данных в базе еще нет.")
            else:
                print(f"Статус базы: {response.status_code}")
        except Exception as e:
            print(f"Ошибка связи при загрузке: {e}")
        
        # Эти переменные будут использоваться для отображения в GUI
        self.public_ip = "Unknown" 
        # --- КОНЕЦ БЛОКА ЗАГРУЗКИ ---

        # 4. Настройка окна
        self.withdraw()
        self.after(200, self._set_custom_icon)

    def _set_custom_icon(self):
        try:
            import ctypes
            from PIL import Image, ImageTk
            
            # Регистрируем приложение в Windows (для чистой иконки в панели задач)
            myappid = 'velox.network.node.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            icon_path = resource_path("VELOX.ico") # Убедись, что имя файла совпадает!
            
            if os.path.exists(icon_path):
                # Метод А: Стандартный заголовок окна
                self.iconbitmap(icon_path)
                
                # Метод Б: Принудительная передача пикселей (для панели задач)
                img = Image.open(icon_path)
                self._icon_ref = ImageTk.PhotoImage(img) # Храним ссылку в self!
                self.wm_iconphoto(True, self._icon_ref)
                
                # Метод В: Прямой системный вызов (самый мощный)
                hicon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
                if hicon:
                    ctypes.windll.user32.SendMessageW(self.winfo_id(), 0x80, 1, hicon)
                    ctypes.windll.user32.SendMessageW(self.winfo_id(), 0x80, 0, hicon)
        except Exception as e:
            print(f"Icon error: {e}")
        finally:
            # 3. Показываем окно уже с нашей иконкой
            self.deiconify()

# ОТКЛЮЧАЕМ СТАНДАРТНУЮ ИКОНКУ CTK
        self.after(200, lambda: self.iconbitmap(resource_path("VELOX.ico")))
        
        self.last_mb = 0.0
        self.last_vlx = 0.0
        self.current_lang = "ru"
        self.mining_is_active = True  # Флаг состояния майнинга
        self.translations = self.get_default_translations()
        self.load_external_lang()

        # --- НАСТРОЙКИ ОКНА ---
        self.title("VELOX")
        window_width = 360
        window_height = 720  
        self.geometry(f"{window_width}x{window_height}") 
        self.configure(fg_color=BG_COLOR)
        ctk.set_appearance_mode("dark")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.resizable(False, False)

        # --- СУПЕР-ФИКС ИКОНКИ (ПЕРЕБИВАЕТ СИНИЙ КВАДРАТ) ---
        def set_final_icon():
            try:
                icon_path = resource_path("VELOX.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
                    img = Image.open(icon_path)
                    self.tk_icon = ImageTk.PhotoImage(img)
                    self.wm_iconphoto(True, self.tk_icon)
                    # Фикс для панели задач
                    myappid = f'velox.network.node.v1'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass

        self.after(500, set_final_icon)

        # --- ШАПКА (ИСПРАВЛЕНА ЦЕНТРОВКА И ОТСТУПЫ) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 5))
        self.header_frame.pack_propagate(False)

        # 1. Загружаем логотип для шапки
        try:
            logo_path = resource_path("VELOX_logo.png") 
            if os.path.exists(logo_path):
                raw_logo = Image.open(logo_path)
                logo_resized = raw_logo.resize((35, 35), Image.Resampling.LANCZOS)
                self.header_logo = ImageTk.PhotoImage(logo_resized)
                
                self.logo_label = ctk.CTkLabel(self.header_frame, image=self.header_logo, text="")
                self.logo_label.place(relx=0.33, rely=0.5, anchor="center")
        except Exception as e:
            print(f"Ошибка загрузки лого в шапку: {e}")

        # 2. Сам заголовок
        self.label_title = ctk.CTkLabel(self.header_frame, text="V E L O X", 
                                        font=("Segoe UI Black", 28), text_color=ACCENT_COLOR)
        self.label_title.place(relx=0.54, rely=0.5, anchor="center")

        # 3. Кнопка RU справа
        self.lang_btn = ctk.CTkButton(self.header_frame, text="RU", width=40, height=28, 
                                      fg_color=CARD_COLOR, hover_color=BTN_INACTIVE,
                                      command=self.toggle_language, font=("Segoe UI", 11, "bold"),
                                      corner_radius=8)
        self.lang_btn.place(relx=1.0, rely=0.5, anchor="e")

        # 4. Кнопка AI слева
        self.ai_btn = ctk.CTkButton(self.header_frame, text="🤖 AI", width=45, height=28, 
                                     fg_color=CARD_COLOR, hover_color="#8B5CF6",
                                     command=self.open_ai_chat, font=("Segoe UI", 11, "bold"),
                                     corner_radius=8, border_width=1, border_color="#334155")
        self.ai_btn.place(relx=0.0, rely=0.5, anchor="w")

        # 5. Статус-метка под шапкой
        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI Semibold", 13), text_color="#10B981")
        self.status_label.pack(pady=(0, 10))

        # --- БЛОК NODE ID ---
        self.id_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.id_frame.pack(pady=5, padx=20, fill="x")

        self.id_title = ctk.CTkLabel(self.id_frame, text="NODE ID / КЛЮЧ СИНХРОНИЗАЦИИ", 
                                          font=("Segoe UI", 9, "bold"), text_color=TEXT_MUTED)
        self.id_title.pack(pady=(8, 0))

        self.id_entry = ctk.CTkEntry(self.id_frame, height=30, 
                                          fg_color=BG_COLOR, border_color=BTN_INACTIVE, 
                                          corner_radius=8, justify="center", font=("Consolas", 12))
        self.id_entry.insert(0, self.velox_id)
        self.id_entry.configure(state="readonly", cursor="hand2")
        self.id_entry.pack(pady=(5, 5), padx=15, fill="x")
        self.id_entry.bind("<Button-1>", lambda e: self.copy_node_id())

        self.copy_hint = ctk.CTkLabel(self.id_frame, text="Нажмите, чтобы скопировать", 
                                     font=("Segoe UI", 8), text_color=TEXT_MUTED)
        self.copy_hint.pack(pady=(0, 8))

        # --- РЕЖИМЫ ---
        self.mode_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.mode_frame.pack(pady=5, padx=20, fill="x")

        self.mode_label = ctk.CTkLabel(self.mode_frame, text="NETWORK MODE / РЕЖИМ СЕТИ", 
                                       font=("Segoe UI", 9, "bold"), text_color=TEXT_MUTED)
        self.mode_label.pack(pady=(8, 10))

        self.btn_grid = ctk.CTkFrame(self.mode_frame, fg_color="transparent")
        self.btn_grid.pack(pady=(0, 10), padx=10, fill="x")

        self.btn_mine = ctk.CTkButton(self.btn_grid, text="", command=self.toggle_mining, 
                                      height=40, font=("Segoe UI", 12, "bold"),
                                      corner_radius=10)
        self.btn_mine.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_vpn = ctk.CTkButton(self.btn_grid, text="", command=self.set_vpn_mode, 
                                     height=40, font=("Segoe UI", 12, "bold"),
                                     corner_radius=10)
        self.btn_vpn.pack(side="left", expand=True, fill="x", padx=4)

        # --- СТАТИСТИКА ---
        self.stats_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.stats_frame.pack(pady=10, padx=20, fill="x")

        self.balance_title = ctk.CTkLabel(self.stats_frame, text="TOTAL EARNED / ЗАРАБОТАНО", 
                                          font=("Segoe UI", 9, "bold"), text_color=TEXT_MUTED)
        self.balance_title.pack(pady=(12, 0))

        self.balance_label = ctk.CTkLabel(self.stats_frame, text="0 VLX", 
                                          font=("Segoe UI Black", 32), text_color="#FDE047") 
        self.balance_label.pack(pady=(0, 5))

        self.stats_divider = ctk.CTkFrame(self.stats_frame, height=1, fg_color=BTN_INACTIVE)
        self.stats_divider.pack(fill="x", padx=40, pady=5)

        self.stats_info_label = ctk.CTkLabel(self.stats_frame, text="Data Shared: 0.00 MB", 
                                        font=("Segoe UI Medium", 14), text_color=TEXT_MAIN)
        self.stats_info_label.pack(pady=(5, 12))

        # --- КОШЕЛЕК (ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ БЛОК) ---
        # 1. Сначала создаем фрейм
        self.wallet_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.wallet_frame.pack(pady=5, padx=20, fill="x")

        # 2. Заголовок (сделали акцент на цвете, чтобы бросалось в глаза)
        self.wallet_title = ctk.CTkLabel(self.wallet_frame, text="KASPA WALLET (KRC-20 ONLY)", 
                                          font=("Segoe UI", 9, "bold"), text_color=ACCENT_COLOR)
        self.wallet_title.pack(pady=(8, 0))

        # 3. Поле ввода
        self.wallet_entry = ctk.CTkEntry(self.wallet_frame, placeholder_text="kaspa:...",
                                          height=30, fg_color=BG_COLOR, 
                                          border_color=BTN_INACTIVE, corner_radius=8, font=("Consolas", 11))
        self.wallet_entry.pack(pady=(5, 5), padx=15, fill="x")
        
        # 4. ПОДСКАЗКА ДЛЯ ВЫВОДА (самое важное!)
        self.wallet_hint = ctk.CTkLabel(self.wallet_frame, 
                                        text="Используйте KasWare Wallet или другой кошелек KRC-20", 
                                        font=("Segoe UI", 8), text_color=TEXT_MUTED)
        self.wallet_hint.pack(pady=(0, 8))
        
        # 4. БИНДЫ ДЛЯ ВСТАВКИ (БЕЗ ОШИБОК)
        # Стандартная вставка
        self.wallet_entry.bind("<Control-v>", self.handle_paste)
        self.wallet_entry.bind("<Control-V>", self.handle_paste)
        
        # Вставка правой кнопкой мыши (самый надежный вариант)
        self.wallet_entry.bind("<Button-3>", self.handle_paste) 
        
        # Резервный бинд для любой раскладки (включая русскую)
        # Если нажата любая клавиша с Ctrl, handle_paste сама проверит, 'v' это или 'м'
        self.wallet_entry.bind("<Control-KeyPress>", self.handle_paste)

        # 5. Загрузка и сохранение
        self.load_wallet()
        self.wallet_entry.bind("<KeyRelease>", lambda e: self.save_wallet())

        # --- НИЖНИЕ КНОПКИ ---
        self.btn_reset_net = ctk.CTkButton(self, text="🛠  FIX INTERNET / СБРОС СЕТИ", 
                                          fg_color="transparent", text_color=TEXT_MUTED, hover_color=CARD_COLOR,
                                          command=self.manual_fix, height=35, font=("Segoe UI Semibold", 11),
                                          corner_radius=10, border_width=1, border_color=CARD_COLOR)
        self.btn_reset_net.pack(fill="x", padx=30, pady=10)

        self.info_label = ctk.CTkLabel(self, text=f"Node: {self.velox_id}\nIP: Detecting...", 
                                      font=("Segoe UI", 9), text_color=TEXT_MUTED, justify="center")
        self.info_label.pack(side="bottom", pady=15)

        # Логика инициализации
        self.current_mode = "mine"
        self.public_ip = "Unknown"
        self.start_val = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        
        self.update_ui_text()
        self.setup_firewall()
        self.disable_proxy()

        threading.Thread(target=self.run_proxy_engine, daemon=True).start()
        threading.Thread(target=self.update_loop, daemon=True).start()
        self.after(5000, self.check_for_updates)

    def toggle_mining(self):
        """Переключатель режима майнинга"""
        t = self.translations[self.current_lang]
        if self.mining_is_active:
            self.mining_is_active = False
            self.current_mode = "paused"
            self.btn_mine.configure(text=t["mine_mode"], fg_color=BTN_INACTIVE, text_color=TEXT_MUTED)
            self.status_label.configure(text=t["status_pause"], text_color="yellow")
        else:
            self.mining_is_active = True
            self.current_mode = "mine"
            self.btn_mine.configure(text=t["pause_btn"], fg_color=ACCENT_COLOR, text_color=BG_COLOR)
            self.status_label.configure(text=t["status_mine"], text_color="#10B981")

    def handle_paste(self, event=None):
        # Если это событие клавиатуры, проверяем, что нажата именно V (англ) или М (рус)
        if event and event.type == "2": # KeyPress
            if event.keysym.lower() not in ['v', 'cyrillic_em']:
                return # Если это Ctrl+C или что-то еще — не прерываем
        
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                # Удаляем выделенное, если есть
                try:
                    self.wallet_entry.delete("sel.first", "sel.last")
                except: pass
                
                # Вставляем и сохраняем
                self.wallet_entry.insert(ctk.INSERT, clipboard_text)
                self.save_wallet()
        except: pass
        
        return "break" # Блокирует стандартную ошибку дублирования текста

    def copy_node_id(self):
        self.clipboard_clear()
        self.clipboard_append(self.velox_id) # Копируем self.velox_id
        self.update()
        old_text = self.copy_hint.cget("text")
        self.copy_hint.configure(text="✅ ID СКОПИРОВАН!", text_color=ACCENT_COLOR)
        self.after(2000, lambda: self.copy_hint.configure(text=old_text, text_color=TEXT_MUTED))

    def get_default_translations(self):
        return {
            "ru": {
                "mine_mode": "МАЙНИНГ", 
                "vpn_mode": "VPN РЕЖИМ", 
                "pause_btn": "ПАУЗА",
                "shared": "Раздано трафика: {:.2f} MB", 
                "earned": "{:d} VLX",  # ИСПРАВЛЕНО: удалена точка перед d
                "status_mine": "● СТАТУС: МАЙНИНГ АКТИВЕН", 
                "status_pause": "● СТАТУС: ПАУЗА",
                "status_searching": "● ПОИСК УЗЛОВ...",
                "conn_to": "● ПОДКЛЮЧЕНО К: {}", 
                "no_nodes": "Нет доступных узлов!",
                "fix_done": "Настройки сети сброшены. Браузеры должны заработать."
            },
            "en": {
                "mine_mode": "MINING", 
                "vpn_mode": "VPN MODE", 
                "pause_btn": "PAUSE",
                "shared": "Data Shared: {:.2f} MB", 
                "earned": "{:d} VLX",  # ИСПРАВЛЕНО: удалена точка перед d
                "status_mine": "● STATUS: MINING ACTIVE", 
                "status_pause": "● STATUS: PAUSED",
                "status_searching": "● SEARCHING...",
                "conn_to": "● CONNECTED TO: {}", 
                "no_nodes": "No nodes available!",
                "fix_done": "Network settings reset. Browsers should work now."
            }
        }

    def save_wallet(self):
        address = self.wallet_entry.get().strip()
        try:
            with open("wallet.cfg", "w", encoding="utf-8") as f:
                f.write(address)
        except: pass

    def load_wallet(self):
        if os.path.exists("wallet.cfg"):
            try:
                with open("wallet.cfg", "r", encoding="utf-8") as f:
                    addr = f.read().strip()
                    self.wallet_entry.delete(0, ctk.END)
                    self.wallet_entry.insert(0, addr)
            except: pass

    def load_external_lang(self):
        if os.path.exists("lang.json"):
            try:
                with open("lang.json", "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except: pass

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "ru" else "ru"
        self.lang_btn.configure(text=self.current_lang.upper())
        self.update_ui_text()

    def update_ui_text(self):
        t = self.translations[self.current_lang]
        self.btn_vpn.configure(text=t["vpn_mode"])
        
        if self.mining_is_active:
            self.btn_mine.configure(text=t["pause_btn"], fg_color=ACCENT_COLOR, text_color=BG_COLOR)
            self.status_label.configure(text=t["status_mine"], text_color="#10B981")
        else:
            self.btn_mine.configure(text=t["mine_mode"], fg_color=BTN_INACTIVE, text_color=TEXT_MUTED)
            self.status_label.configure(text=t["status_pause"], text_color="yellow")
            
        # ВАЖНО: передаем int(self.last_vlx), чтобы убрать .0000 при смене языка
        self.update_stats_display(self.last_mb, int(self.last_vlx))

    def update_stats_display(self, mb, vlx):
        self.last_mb = mb
        self.last_vlx = int(vlx) # Это гарантирует отсутствие дробной части
        t = self.translations[self.current_lang]
        self.stats_info_label.configure(text=t["shared"].format(mb))
        # Здесь формат {:d} из перевода теперь сработает без ошибок
        self.balance_label.configure(text=t["earned"].format(self.last_vlx))

    def setup_firewall(self):
        try:
            rule_name = "VELOX_Network_Node"
            subprocess.run(f'netsh advfirewall firewall delete rule name="{rule_name}"', shell=True, capture_output=True)
            cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport=8888 profile=any'
            subprocess.run(cmd, shell=True, capture_output=True)
        except: pass

    def set_proxy(self, ip, port):
        try:
            xpath = "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
            hKey = ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, xpath, 0, 0x20006)
            def set_reg(name, val, reg_type):
                if reg_type == 1:
                    ctypes.windll.advapi32.RegSetValueExW(hKey, name, 0, reg_type, val, len(val)*2)
                else:
                    v = ctypes.c_uint32(val)
                    ctypes.windll.advapi32.RegSetValueExW(hKey, name, 0, reg_type, ctypes.byref(v), 4)
            set_reg("ProxyServer", f"{ip}:{port}", 1)
            set_reg("ProxyEnable", 1, 4)
            set_reg("ProxyOverride", "localhost;127.0.0.1;*.firebasedatabase.app;*.googleapis.com;api.ipify.org;<local>", 1)
            ctypes.windll.advapi32.RegCloseKey(hKey)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0) 
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
            return True
        except: return False

    def disable_proxy(self):
        try:
            subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        except: pass

    def manual_fix(self):
        self.disable_proxy()
        self.set_mine_mode()
        messagebox.showinfo("VELOX Fixer", self.translations[self.current_lang]["fix_done"])

    def run_proxy_engine(self):
        if Proxy:
            try:
                proxy_args = ['--hostname', '0.0.0.0', '--port', '8888', '--backlog', '200']
                with Proxy(proxy_args) as p:
                    p.run()
            except: pass

    def set_mine_mode(self):
        self.disable_proxy()
        self.mining_is_active = True
        self.current_mode = "mine"
        self.update_ui_text()

    def set_vpn_mode(self):
        self.mining_is_active = False
        self.btn_mine.configure(fg_color=BTN_INACTIVE, text_color=TEXT_MUTED)
        self.btn_vpn.configure(fg_color="#8B5CF6", text_color=TEXT_MAIN)
        self.status_label.configure(text=self.translations[self.current_lang]["status_searching"], text_color="#F59E0B")
        threading.Thread(target=self.connect_logic, daemon=True).start()

    def connect_logic(self):
        try:
            response = cloud_session.get(ALL_NODES_URL, timeout=10).json()
            if not response:
                messagebox.showwarning("VELOX", self.translations[self.current_lang]["no_nodes"])
                self.after(0, self.set_mine_mode)
                return
            target = None
            for nid, data in response.items():
                if data.get("ip") and data.get("ip") != self.public_ip and data.get("status") == "online":
                    target = data
                    break
            if target:
                ip = target.get("ip")
                if self.set_proxy(ip, 8888):
                    self.current_mode = "vpn"
                    self.after(0, lambda: self.status_label.configure(
                        text=self.translations[self.current_lang]["conn_to"].format(ip), text_color="#8B5CF6"))
                else: raise Exception()
            else:
                self.after(0, lambda: messagebox.showwarning("VPN", self.translations[self.current_lang]["no_nodes"]))
                self.after(0, self.set_mine_mode)
        except:
            self.after(0, self.set_mine_mode)

    def update_loop(self):
        """Главный цикл обновления данных с защитой от сброса сети"""
        while True:
            try:
                if self.mining_is_active or self.current_mode == "vpn":
                    counters = psutil.net_io_counters()
                    current_total = counters.bytes_sent + counters.bytes_recv
                    
                    if not hasattr(self, 'start_val'):
                        self.start_val = current_total
                    
                    # --- ЗАЩИТА ОТ МИНУСА (Сброс VPN/Адаптера) ---
                    # Если текущий трафик меньше начального, значит интерфейс обнулился
                    if current_total < self.start_val:
                        print("⚠️ Сетевой интерфейс сброшен. Корректировка start_val...")
                        # Чтобы баланс не упал в минус, фиксируем текущий заработок в базе
                        self.base_mb = self.last_mb
                        self.base_vlx = self.last_vlx
                        # Начинаем отсчет новой сессии с текущей точки
                        self.start_val = current_total
                    
                    # 1. Считаем чистый трафик сессии в МБ
                    session_mb = (current_total - self.start_val) / (1024 * 1024)
                    
                    # 2. НАСТРОЙКА: 1 МБ за монету
                    mb_per_coin = 1 
                    
                    # 3. Считаем целые монеты за сессию
                    session_vlx_whole = int(session_mb // mb_per_coin)
                    
                    # 4. ИТОГО = База (загруженная) + Сессия
                    self.last_mb = getattr(self, 'base_mb', 0.0) + session_mb
                    self.last_vlx = int(getattr(self, 'base_vlx', 0)) + session_vlx_whole
                    
                    # Обновляем UI (целые числа)
                    self.after(0, lambda: self.update_stats_display(self.last_mb, int(self.last_vlx)))

                # 5. Отправка в Firebase (защита: не шлем 0, если в базе были монеты)
                if self.last_vlx == 0 and int(getattr(self, 'base_vlx', 0)) > 0:
                    time.sleep(1) # Ждем прогрузки базы
                else:
                    payload = {
                        "mb_total": round(self.last_mb, 2),
                        "vlx_earned": int(self.last_vlx),
                        "status": "online" if self.mining_is_active else "paused",
                        "last_ping": time.time()
                    }
                    
                    cloud_session.patch(
                        self.my_db_url, 
                        json=payload, 
                        params={"auth": self.token}, 
                        timeout=5
                    )

            except Exception as e:
                print(f"Ошибка обновления: {e}")
            
            time.sleep(10)

    def check_for_updates(self):
        try:
            r = cloud_session.get(SETTINGS_URL, timeout=5).json()
            if r and r.get("current_version") > VERSION:
                messagebox.showinfo("Update", f"Новая версия {r.get('current_version')} доступна!")
        except: pass

    # --- ИНТЕГРАЦИЯ AI ПОМОЩНИКА ---
    def open_ai_chat(self):
        if hasattr(self, 'ai_window') and self.ai_window.winfo_exists():
            self.ai_window.focus()
            return

        self.ai_window = ctk.CTkToplevel(self)
        self.ai_window.title("VELOX AI")
        self.ai_window.geometry("360x520")
        self.ai_window.configure(fg_color="#0B0F19")
        
        # Исправленная установка иконки через resource_path
        try:
            icon_p = resource_path("VELOX.ico")
            self.ai_window.after(200, lambda: self.ai_window.iconbitmap(icon_p))
        except:
            pass
            
        self.ai_window.attributes("-topmost", True)
        self.ai_window.resizable(False, False)    

        # Поле чата (теперь копируемое)
        self.chat_display = ctk.CTkTextbox(self.ai_window, width=340, height=400, 
                                           fg_color="#151B2B", text_color="#F8FAFC",
                                           font=("Segoe UI", 13), wrap="word")
        
        # НАСТРОЙКА ВИДИМОГО ВЫДЕЛЕНИЯ
        self.chat_display._textbox.configure(
            selectbackground="#00E5FF", 
            selectforeground="#0B0F19",
            inactiveselectbackground="#00E5FF" # Чтобы выделение не исчезало при клике на другое окно
        )
        self.chat_display.pack(pady=(15, 5), padx=10)

        # 1. Определяем ID
        self.node_id = "VELOX_D8EFF5C0" 

        # 2. Вставляем приветственный текст
        welcome_text = (
            "VELOX AI: Привет! Я твой универсальный ассистент.\n"
            "Я помогу с VPN, майнингом VLX, а также найду для тебя:\n"
            "• Актуальные курсы валют и криптовалют\n"
            "• Свежие новости мира и крипторынка\n"
            "• Точный прогноз погоды и ответы на любые вопросы.\n"
            "______________________________________\n"
            f"Ваш ID узла: {self.node_id}\n" 
        )
        
        self.chat_display.insert("0.0", welcome_text)
        self.chat_display.configure(state="disabled")

        # СОЗДАНИЕ КОНТЕКСТНОГО МЕНЮ (ПРАВАЯ КНОПКА МЫШИ)
        import tkinter as tk
        self.chat_menu = tk.Menu(self.chat_display._textbox, tearoff=0, bg="#1E293B", fg="white", borderwidth=0)
        self.chat_menu.add_command(label="Копировать", command=lambda: self.chat_display._textbox.event_generate("<<Copy>>"))
        self.chat_menu.add_command(label="Выделить всё", command=lambda: self.chat_display._textbox.event_generate("<<SelectAll>>"))

        def do_popup(event):
            try:
                self.chat_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.chat_menu.grab_release()

        # Привязываем правую кнопку мыши
        self.chat_display._textbox.bind("<Button-3>", do_popup)
        
        # Привязываем левую кнопку для фокуса (Ctrl+C)
        self.chat_display.bind("<Button-1>", lambda event: self.chat_display.focus_set())

        # --- ПОЛЕ ВВОДА ---
        input_frame = ctk.CTkFrame(self.ai_window, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)

        self.ai_entry = ctk.CTkEntry(input_frame, placeholder_text="Введите сообщение...", 
                                     fg_color="#1E293B", border_color="#334155", height=45)
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ai_entry.bind("<Return>", lambda e: self.send_ai_message())

        self.send_ai_btn = ctk.CTkButton(input_frame, text="▲", width=45, height=45,
                                         fg_color="#00E5FF", text_color="#0B0F19",
                                         hover_color="#00B4CC", font=("Arial", 16, "bold"),
                                         command=self.send_ai_message)
        self.send_ai_btn.pack(side="right")

    def send_ai_message(self):
        user_text = self.ai_entry.get().strip()
        if not user_text: 
            return

        self.update_chat_display(f"Вы: {user_text}")
        self.ai_entry.delete(0, 'end')

        def ai_thread():
            try:
                import requests
                import json
                import re
                from datetime import datetime
                from velox_config import get_ai_provider
                from duckduckgo_search import DDGS # Используем твой импорт

                current_date = datetime.now().strftime("%d.%m.%Y")
                node_id = self.node_id

                # --- БЕСПЛАТНЫЙ ПОИСК В ИНТЕРНЕТЕ ---
                search_results = ""
                # Проверяем, нужен ли поиск (курс, новости, погода и т.д.)
                keywords = ["курс", "цена", "новости", "погода", "крипто", "сколько стоит", "актуально"]
                if any(word in user_text.lower() for word in keywords):
                    try:
                        with DDGS() as ddgs:
                            # Ограничиваем 3 результатами для экономии
                            ddgs_gen = ddgs.text(user_text, max_results=3)
                            search_results = "\n".join([r['body'] for r in ddgs_gen])
                    except Exception as se:
                        print(f"Search error: {se}")
                        search_results = "Данные из интернета временно недоступны."

                # Формируем системную инструкцию с учетом поиска
                project_knowledge = (
                    "ТЫ — VELOX AI. Ты официальный голос VELOX (VPN + Майнинг VLX).\n"
                    f"АКТУАЛЬНЫЕ ДАННЫЕ ИЗ СЕТИ:\n{search_results}\n\n"
                    "ОТВЕЧАЙ ЧИСТЫМ ТЕКСТОМ. Никаких ссылок и кода! "
                    "Если в данных есть курс валют — используй его."
                )

                DYNAMIC_KEY = get_ai_provider()

                payload = {
                    "model": "deepseek/deepseek-chat", # Платная, но очень дешевая и умная
                    "messages": [
                        {"role": "system", "content": f"{project_knowledge}\nСегодня: {current_date}"},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.4, # Чуть снизил для большей точности цифр
                }

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {DYNAMIC_KEY}", "Content-Type": "application/json"},
                    data=json.dumps(payload),
                    timeout=45 
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']
                    
                    # Очистка хлама (ссылки, маркдаун)
                    answer = re.sub(r'\[([^\]]+)\]\(https?://[^\)]+\)', r'\1', answer)
                    answer = re.sub(r'https?://\S+', '', answer)
                    answer = re.sub(r'\[\d+\]', '', answer)
                    
                    self.after(0, lambda: self.update_chat_display(f"VELOX AI: {answer}"))
                
                elif response.status_code in [429, 402, 401]:
                    pay_msg = (
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "⚠️ ДОСТУП ОГРАНИЧЕН (ЛИМИТ ИСЧЕРПАН)\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Для общения без лимитов активируйте 'Priority Pass'.\n\n"
                        "💎 Стоимость: 100 KAS (~$1.5)\n"
                        "🔗 Кошелек KASPA (выдели и скопируй):\n"
                        "kaspa:qzfk78p6n45x8dln48c7k242vhthqf9x9jejae44t3qe93pths6z2aw7wp9dv\n\n"
                        "📝 ВАШИ ДАННЫЕ:\n"
                        f"• Ваш ID: {node_id}\n"
                        "• Поддержка: @VELOX_DEPIN\n\n"
                        "Отправь скрин чека и свой ID в Telegram."
                    )
                    self.after(0, lambda: self.update_chat_display(pay_msg))
                else:
                    self.after(0, lambda: self.update_chat_display("VELOX AI: Ошибка связи. Попробуйте позже."))

            except Exception as e:
                self.after(0, lambda: self.update_chat_display(f"VELOX AI: Ошибка сети."))

        import threading
        threading.Thread(target=ai_thread, daemon=True).start()

    def update_chat_display(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message + "\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        # Фокус для работы Ctrl+C
        self.chat_display.focus_set()

    def on_closing(self):
        """Гарантированное сохранение данных перед выходом (с учетом памяти и целых монет)"""
        try:
            # 1. Сразу отключаем прокси
            self.disable_proxy()
            
            # 2. Расчет данных текущей сессии
            counters = psutil.net_io_counters()
            current_total = counters.bytes_sent + counters.bytes_recv
            
            # Считаем трафик сессии в МБ
            session_mb = (current_total - getattr(self, 'start_val', current_total)) / (1024 * 1024)
            
            # --- ЛОГИКА ЦЕЛЫХ МОНЕТ ---
            # Используем тот же порог, что и в update_loop (1 МБ = 1 монета)
            mb_per_coin = 1  # Теперь за каждый 1 МБ будет даваться 1 монета 
            session_vlx_whole = int(session_mb // mb_per_coin) 
            
            # ИТОГО = База (целая) + Целые монеты за текущую сессию
            final_mb = getattr(self, 'base_mb', 0.0) + session_mb
            final_vlx = int(getattr(self, 'base_vlx', 0)) + session_vlx_whole 
            
            # 3. Подготавливаем финальный пакет данных (БЕЗ ЛИШНИХ НУЛЕЙ)
            final_payload = {
                "mb_total": round(final_mb, 2),
                "vlx_earned": int(final_vlx), # Сохраняем как чистое целое число
                "status": "offline",
                "last_ping": time.time(),
                "wallet": self.wallet_entry.get().strip() if hasattr(self, 'wallet_entry') else "Не указан"
            }

            # 4. Отправляем в Firebase (синхронно)
            print(f"Синхронизация перед выходом... Итого: {int(final_vlx)} VLX")
            requests.patch(
                self.my_db_url, 
                json=final_payload, 
                params={"auth": self.token}, 
                timeout=7 
            )
            print("✅ Все данные успешно сохранены в облаке.")

        except Exception as e:
            print(f"❌ Ошибка при финальном сохранении: {e}")
        
        # 5. Завершение работы
        try:
            self.destroy()
            if platform.system() == "Windows":
                os.system(f"taskkill /F /T /PID {os.getpid()}")
            else:
                os._exit(0)
        except:
            pass

if __name__ == "__main__":
    # Поддержка многопроцессорности для PyInstaller
    multiprocessing.freeze_support()
    
    # Режим скрытого бота
    if "--bot-mode" in sys.argv:
        try:
            p = psutil.Process(os.getpid())
            if platform.system() == "Windows":
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            
            bot_path = resource_path("velox_bot.py")
            if os.path.exists(bot_path):
                with open(bot_path, "r", encoding="utf-8") as f:
                    exec(f.read(), globals())
        except Exception as e:
            with open("bot_error.log", "a") as f:
                f.write(f"Error: {e}\n")
        sys.exit(0)

    # Обычный запуск приложения
    start_hidden_bot()
    app = VeloxApp()
    app.mainloop()