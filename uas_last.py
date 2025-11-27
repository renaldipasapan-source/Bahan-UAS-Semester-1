# game_tebak_gambar_final.py
import pygame
import sys
import time
import json
import os

pygame.init()

# ---------- Config ----------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Tebak Gambar - Final")

FPS = 60

# Colors (keinginan: jangan ubah background global)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
BLUE = (80, 160, 255)
DARK_BLUE = (30, 40, 70)   # keep original-ish dark bg
GREEN = (100, 220, 140)
RED = (255, 100, 110)
YELLOW = (255, 230, 120)
PURPLE = (200, 120, 255)
ORANGE = (255, 160, 60)
BG_COLOR = (41, 56, 90)    # not changing user's background preference
CARD_COLOR = (30, 40, 60)
HEADER_BAR = (120, 170, 255)  # light blue for table header

# Fonts
title_font = pygame.font.SysFont('arial', 46, bold=True)
header_font = pygame.font.SysFont('arial', 30, bold=True)
button_font = pygame.font.SysFont('arial', 26, bold=True)
option_font = pygame.font.SysFont('arial', 22, bold=True)
small_font = pygame.font.SysFont('arial', 16)

# ---------- Game Data ----------
GAME_DATA = [
    {"image_path": "images/gambar1.jpg", "correct_answer": "Apel", "options": ["Apel","Jeruk","Pisang","Mangga"], "Clue":"Buah merah yang renyah"},
    {"image_path": "images/gambar2.jpg", "correct_answer": "Mobil", "options": ["Sepeda","Mobil","Motor","Bus"], "Clue":"Kendaraan bermotor roda empat"},
    {"image_path": "images/gambar3.jpg", "correct_answer": "Rumah", "options": ["Gedung","Rumah","Sekolah","Kantor"], "Clue":"Tempat tinggal keluarga"},
    {"image_path": "images/gambar4.jpg", "correct_answer": "Buku", "options": ["Buku","Pensil","Penghapus","Penggaris"], "Clue":"Kumpulan kertas berisi tulisan"},
    {"image_path": "images/gambar5.jpg", "correct_answer": "Matahari", "options": ["Bulan","Bintang","Matahari","Awan"], "Clue":"Bintang di pusat tata surya kita"}
]

# ---------- Utilities ----------
def load_image(path, size):
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        surf = pygame.Surface(size)
        surf.fill(PURPLE)
        txt = small_font.render("No Image", True, WHITE)
        surf.blit(txt, txt.get_rect(center=(size[0]//2, size[1]//2)))
        return surf

def lerp(a, b, t):
    return a + (b - a) * t

def draw_rounded_rect(surface, rect, color, radius=12):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# ---------- UI Components ----------
class Button:
    def __init__(self, x, y, w, h, text, base_color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.text = text
        self.hovered = False
        self.pressed = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.color = base_color

    def update(self, dt, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.target_scale = 0.98 if self.pressed else (1.04 if self.hovered else 1.0)
        self.scale = lerp(self.scale, self.target_scale, min(1, dt * 10))
        # color lerp
        t = (self.scale - 1.0) / 0.04 if self.target_scale > 1 else 0
        self.color = (
            int(lerp(self.base_color[0], self.hover_color[0], max(0, t))),
            int(lerp(self.base_color[1], self.hover_color[1], max(0, t))),
            int(lerp(self.base_color[2], self.hover_color[2], max(0, t)))
        )

    def draw(self, surface):
        w = int(self.rect.w * self.scale)
        h = int(self.rect.h * self.scale)
        r = pygame.Rect(0,0,w,h)
        r.center = self.rect.center
        # subtle shadow
        shadow = pygame.Surface((w+6,h+6), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,70), shadow.get_rect(), border_radius=14)
        surface.blit(shadow, (r.x-3, r.y+3))
        draw_rounded_rect(surface, r, self.color, radius=12)
        pygame.draw.rect(surface, BLACK, r, 2, border_radius=12)
        txt = button_font.render(self.text, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=r.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.pressed = True
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(pygame.mouse.get_pos()):
                self.pressed = False
                return True
            self.pressed = False
        return False

class OptionButton(Button):
    def __init__(self, x, y, w, h, text, index):
        super().__init__(x, y, w, h, text, BLUE, (60,120,220))
        self.index = index
        self.is_correct = False
        self.is_wrong = False

    def draw(self, surface):
        if self.is_correct:
            bg = GREEN
        elif self.is_wrong:
            bg = RED
        else:
            bg = self.color
        w = int(self.rect.w * self.scale)
        h = int(self.rect.h * self.scale)
        r = pygame.Rect(0,0,w,h); r.center = self.rect.center
        shadow = pygame.Surface((w+6,h+6), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,60), shadow.get_rect(), border_radius=10)
        surface.blit(shadow, (r.x-3, r.y+3))
        draw_rounded_rect(surface, r, bg, radius=10)
        pygame.draw.rect(surface, BLACK, r, 2, border_radius=10)
        font = pygame.font.SysFont('arial', max(18, int(20 * self.scale)), bold=True)
        txt = font.render(self.text, True, WHITE)
        surface.blit(txt, txt.get_rect(center=r.center))

# ---------- Main Game ----------
class Game:
    def __init__(self):
        self.state = "input_name"  # input_name, home, gameplay, results, leaderboard
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.mouse_pos = (0,0)

        # gameplay
        self.current_q = 0
        self.score = 0
        self.correct_count = 0
        self.time_left = 30
        self.timer_start = 0
        self.game_active = False

        # player input
        self.player_name = ""
        self.input_active = True
        self.input_rect = pygame.Rect(SCREEN_WIDTH//2 - 260, 200, 520, 72)
        # caret position index within player_name
        self.caret_index = 0
        self.caret_visible = True
        self.caret_timer = 0

        # leaderboard
        self.leaderboard = self.load_leaderboard()
        self.recent_entry = None

        # UI
        self.setup_ui()
        self.images = [load_image(d["image_path"], (420,300)) for d in GAME_DATA]

    def setup_ui(self):
        cx = SCREEN_WIDTH//2
        self.btn_continue = Button(cx-150, 300, 300, 62, "Lanjut", GREEN, (80,230,150))
        self.btn_home_start = Button(cx-150, 360, 300, 62, "Mulai Game", GREEN, (80,230,150))
        self.btn_leader = Button(cx-150, 430, 300, 62, "Lihat Leaderboard", BLUE, (120,200,255))
        self.btn_quit = Button(cx-150, 500, 300, 62, "Keluar Game", RED, (240,80,90))

        self.btn_skip = Button(SCREEN_WIDTH-120, SCREEN_HEIGHT-75, 92, 44, "Skip", ORANGE, (255,180,100))
        self.btn_play_again = Button(cx-150, 340, 300, 62, "Main Lagi", GREEN, (80,230,150))
        self.btn_back = Button(cx-150, 420, 300, 62, "Kembali", BLUE, (120,200,255))

        self.option_buttons = []

    def load_leaderboard(self):
        try:
            if os.path.exists("leaderboard.json"):
                with open("leaderboard.json","r") as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_leaderboard(self):
        entry = {
            "name": self.player_name or f"Player_{time.strftime('%Y%m%d')}",
            "score": self.score,
            "correct": self.correct_count,
            "date": time.strftime("%d/%m/%Y %H:%M")
        }
        self.leaderboard.append(entry)
        self.leaderboard.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.leaderboard = self.leaderboard[:10]
        try:
            with open("leaderboard.json","w") as f:
                json.dump(self.leaderboard, f, indent=2)
        except:
            pass
        self.recent_entry = entry

    def start_game(self):
        self.state = "gameplay"
        self.current_q = 0
        self.score = 0
        self.correct_count = 0
        self.game_active = True
        self.load_question()

    def load_question(self):
        if self.current_q >= len(GAME_DATA):
            self.end_game()
            return
        self.time_left = 30
        self.timer_start = time.time()
        self.create_option_buttons()

    def create_option_buttons(self):
        self.option_buttons = []
        option_w, option_h = 380, 56
        spacing = 16
        left_x = SCREEN_WIDTH//2 - option_w - spacing//2
        right_x = SCREEN_WIDTH//2 + spacing//2
        start_y = 480
        for i, opt in enumerate(GAME_DATA[self.current_q]["options"]):
            x = left_x if i%2==0 else right_x
            y = start_y + (i//2) * (option_h + spacing)
            btn = OptionButton(x, y, option_w, option_h, opt, i)
            self.option_buttons.append(btn)

    def check_answer(self, selected_text):
        if not self.game_active:
            return
        correct = GAME_DATA[self.current_q]["correct_answer"]
        for b in self.option_buttons:
            if b.text == correct:
                b.is_correct = True
            elif b.text == selected_text:
                b.is_wrong = True
            b.hovered = False

        if selected_text == correct:
            self.correct_count += 1
            self.score += 10 + max(0, self.time_left)//2

        self.game_active = False
        pygame.time.set_timer(pygame.USEREVENT, 900)

    def skip_question(self):
        if not self.game_active:
            return
        self.game_active = False
        pygame.time.set_timer(pygame.USEREVENT, 300)

    def next_question(self):
        pygame.time.set_timer(pygame.USEREVENT, 0)
        self.current_q += 1
        if self.current_q >= len(GAME_DATA):
            self.end_game()
        else:
            self.game_active = True
            self.load_question()

    def end_game(self):
        self.game_active = False
        self.save_leaderboard()
        self.state = "results"

    # ---------- Input helpers ----------
    def set_caret_from_mouse(self, mouse_x):
        # compute caret index based on click x inside input box
        padding = 15
        rel_x = mouse_x - (self.input_rect.x + padding)
        if rel_x <= 0:
            self.caret_index = 0
            return
        text = self.player_name
        # iterate char widths to find nearest index
        accum = 0
        for i in range(len(text)):
            ch = text[i]
            w = header_font.size(ch)[0]
            if accum + w/2 >= rel_x:
                self.caret_index = i
                return
            accum += w
        self.caret_index = len(text)

    # ---------- Update & Draw ----------
    def update(self):
        self.dt = self.clock.tick(FPS) / 1000.0
        self.mouse_pos = pygame.mouse.get_pos()

        # update buttons
        buttons = [
            self.btn_continue, self.btn_home_start, self.btn_leader, self.btn_quit,
            self.btn_skip, self.btn_play_again, self.btn_back
        ]
        for b in buttons:
            b.update(self.dt, self.mouse_pos)
        for opt in self.option_buttons:
            opt.update(self.dt, self.mouse_pos)

        # caret blink
        if pygame.time.get_ticks() - self.caret_timer > 500:
            self.caret_visible = not self.caret_visible
            self.caret_timer = pygame.time.get_ticks()

        # gameplay timer
        if self.game_active and self.state == "gameplay":
            elapsed = time.time() - self.timer_start
            self.time_left = max(0, 30 - int(elapsed))
            if self.time_left <= 0:
                self.skip_question()

    def draw_input_name(self):
        SCREEN.fill(BG_COLOR)
        # card
        card = pygame.Rect(SCREEN_WIDTH//2 - 340, 80, 680, 500)
        draw_rounded_rect(SCREEN, card, CARD_COLOR, radius=18)
        pygame.draw.rect(SCREEN, (60,80,110), card, 3, border_radius=18)

        # title
        title_s = title_font.render("Masukkan Nama Pemain", True, WHITE)
        SCREEN.blit(title_s, title_s.get_rect(center=(SCREEN_WIDTH//2, 140)))

        # input box
        box = self.input_rect
        draw_rounded_rect(SCREEN, box, WHITE, radius=12)
        pygame.draw.rect(SCREEN, (180,180,200), box, 3, border_radius=12)

        # render text inside box
        txt = self.player_name if self.player_name != "" else "Ketik nama..."
        color = BLACK if self.player_name != "" else (140,140,160)
        text_surf = header_font.render(txt, True, color)
        SCREEN.blit(text_surf, (box.x + 15, box.y + (box.h - text_surf.get_height())//2))

        # caret
        if self.input_active:
            # compute caret x
            padding = 15
            left_x = box.x + padding
            # width of text up to caret_index
            pre_text = self.player_name[:self.caret_index]
            pre_width = header_font.size(pre_text)[0] if pre_text else 0
            caret_x = left_x + pre_width
            caret_y = box.y + 10
            if self.caret_visible:
                pygame.draw.rect(SCREEN, BLACK, (caret_x, caret_y, 3, box.h - 20))

        # buttons (big background shapes for look)
        # place buttons and draw through Button.draw to keep animation
        self.btn_continue.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 300, 300, 62)
        self.btn_leader.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 372, 300, 62)
        self.btn_quit.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 444, 300, 62)

        self.btn_continue.draw(SCREEN)
        self.btn_leader.draw(SCREEN)
        self.btn_quit.draw(SCREEN)

    def draw_home(self):
        SCREEN.fill(BG_COLOR)
        t = title_font.render("GAME TEBAK GAMBAR", True, WHITE)
        SCREEN.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 120)))
        sub = header_font.render("Uji pengetahuan — gaya modern & fun", True, (200,200,220))
        SCREEN.blit(sub, sub.get_rect(center=(SCREEN_WIDTH//2, 160)))

        # home card
        card = pygame.Rect(SCREEN_WIDTH//2 - 260, 200, 520, 300)
        draw_rounded_rect(SCREEN, card, CARD_COLOR, radius=16)
        info = small_font.render("Tekan Mulai untuk memasukkan nama dan mulai bermain", True, (190,190,210))
        SCREEN.blit(info, info.get_rect(center=(SCREEN_WIDTH//2, 240)))

        # buttons
        self.btn_home_start.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 260, 300, 62)
        self.btn_leader.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 336, 300, 62)
        self.btn_quit.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 412, 300, 62)
        self.btn_home_start.draw(SCREEN)
        self.btn_leader.draw(SCREEN)
        self.btn_quit.draw(SCREEN)

    def draw_game(self):
        SCREEN.fill(BG_COLOR)
        # header
        header = pygame.Rect(0,0,SCREEN_WIDTH,84)
        draw_rounded_rect(SCREEN, header, CARD_COLOR, radius=0)
        title_str = f"{self.player_name}  •  Skor: {self.score}"
        t = header_font.render(title_str, True, WHITE)
        SCREEN.blit(t, (20, 20))
        timer_s = header_font.render(f"Waktu: {self.time_left}s", True, (255,200,80) if self.time_left > 10 else RED)
        SCREEN.blit(timer_s, (SCREEN_WIDTH - 220, 20))

        # image
        img = self.images[self.current_q]
        SCREEN.blit(img, img.get_rect(center=(SCREEN_WIDTH//2, 270)))

        # clue & UI
        clue = option_font.render(f"Clue: {GAME_DATA[self.current_q]['Clue']}", True, YELLOW)
        SCREEN.blit(clue, clue.get_rect(center=(SCREEN_WIDTH//2, 442)))

        # option buttons
        for b in self.option_buttons:
            b.draw(SCREEN)

        # skip
        self.btn_skip.rect = pygame.Rect(SCREEN_WIDTH-120, SCREEN_HEIGHT-75, 92, 44)
        self.btn_skip.draw(SCREEN)

    def draw_results(self):
        SCREEN.fill(BG_COLOR)
        t = title_font.render("Hasil Permainan", True, WHITE)
        SCREEN.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 120)))
        score_txt = header_font.render(f"Skor Akhir: {self.score}", True, YELLOW)
        SCREEN.blit(score_txt, score_txt.get_rect(center=(SCREEN_WIDTH//2, 200)))
        correct_txt = header_font.render(f"Jawaban Benar: {self.correct_count}/{len(GAME_DATA)}", True, GREEN)
        SCREEN.blit(correct_txt, correct_txt.get_rect(center=(SCREEN_WIDTH//2, 260)))

        self.btn_play_again.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 320, 300, 62)
        self.btn_back.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 398, 300, 62)
        self.btn_play_again.draw(SCREEN)
        self.btn_back.draw(SCREEN)

    def draw_leaderboard(self):
        SCREEN.fill(BG_COLOR)
        title = title_font.render("LEADERBOARD", True, YELLOW)
        SCREEN.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 60)))

        # --- TABLE OUTER SIZE ---
        table_x = 80
        table_w = SCREEN_WIDTH - 2 * table_x
        header_h = 64
        header_rect = pygame.Rect(table_x, 110, table_w, header_h)

        # header background
        draw_rounded_rect(SCREEN, header_rect, HEADER_BAR, radius=18)
        pygame.draw.rect(SCREEN, (200,220,255), header_rect, 2, border_radius=18)

        # --- HEADER COLUMNS SPACING (fixed, aesthetic) ---
        # little shift to create left margin for "Peringkat"
        shift_left = 18

        cols = [0.10, 0.40, 0.15, 0.10, 0.25]   # new, cleaner proportions

        headers = ["Peringkat", "Nama", "Skor", "Benar", "Tanggal"]

        x = table_x
        for i, htext in enumerate(headers):
            w = int(table_w * cols[i])

            # header centered text
            txt = header_font.render(htext, True, (10,10,10))

            # add shift only for first column
            cx = x + w//2 + (shift_left if i == 0 else 0)

            SCREEN.blit(txt, txt.get_rect(center=(cx, 110 + header_h//2)))
            x += w

        # --- ROWS ---
        row_h = 56
        start_y = 110 + header_h + 16

        for idx, entry in enumerate(self.leaderboard):
            y = start_y + idx * (row_h + 12)
            row_rect = pygame.Rect(table_x, y, table_w, row_h)

            shade = (36,46,66) if idx % 2 == 0 else (30,40,60)
            draw_rounded_rect(SCREEN, row_rect, shade, radius=12)

            # highlight current session entry
            if self.recent_entry and \
            entry["name"] == self.recent_entry["name"] and \
            entry["score"] == self.recent_entry["score"]:
                pygame.draw.rect(SCREEN, (255,240,200), row_rect, 3, border_radius=12)

            # render row cells
            x = table_x
            for i, key in enumerate(["rank", "name", "score", "correct", "date"]):
                w = int(table_w * cols[i])

                # center X position per column
                cx = x + w//2 + (shift_left if i == 0 else 0)
                cy = y + row_h//2

                if key == "rank":
                    text_s = option_font.render(str(idx+1), True, WHITE)
                elif key == "name":
                    text_s = option_font.render(entry.get("name", "-"), True, WHITE)
                elif key == "score":
                    text_s = option_font.render(f"{entry.get('score',0)} pts", True, WHITE)
                elif key == "correct":
                    text_s = option_font.render(str(entry.get("correct",0)), True, WHITE)
                elif key == "date":
                    text_s = option_font.render(entry.get("date", "-"), True, WHITE)

                SCREEN.blit(text_s, text_s.get_rect(center=(cx, cy)))
                x += w

        # --- BACK BUTTON ---
        self.btn_back.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 90, 300, 56)
        self.btn_back.draw(SCREEN)



    # ---------- Event Loop ----------
    def handle_input_events(self, event):
        # keyboard & mouse input for name field
        if self.state == "input_name":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # if clicked inside box, activate and set caret by click pos
                if self.input_rect.collidepoint(event.pos):
                    self.input_active = True
                    # place caret at clicked position
                    self.set_caret_from_click(event.pos[0])
                else:
                    self.input_active = False
            if event.type == pygame.KEYDOWN and self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    if self.caret_index > 0:
                        # delete char before caret
                        self.player_name = self.player_name[:self.caret_index-1] + self.player_name[self.caret_index:]
                        self.caret_index -= 1
                elif event.key == pygame.K_DELETE:
                    if self.caret_index < len(self.player_name):
                        self.player_name = self.player_name[:self.caret_index] + self.player_name[self.caret_index+1:]
                elif event.key == pygame.K_RETURN:
                    if self.player_name.strip() != "":
                        self.start_game()
                elif event.key == pygame.K_LEFT:
                    if self.caret_index > 0:
                        self.caret_index -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.caret_index < len(self.player_name):
                        self.caret_index += 1
                elif event.key == pygame.K_HOME:
                    self.caret_index = 0
                elif event.key == pygame.K_END:
                    self.caret_index = len(self.player_name)
                else:
                    # text input (ignore control keys)
                    if event.unicode and len(self.player_name) < 24:
                        # insert at caret
                        ch = event.unicode
                        self.player_name = self.player_name[:self.caret_index] + ch + self.player_name[self.caret_index:]
                        self.caret_index += 1

    def set_caret_from_click(self, mouse_x):
        # calculate caret index by measuring character widths
        padding = 15
        rel_x = mouse_x - (self.input_rect.x + padding)
        if rel_x <= 0:
            self.caret_index = 0
            return
        accum = 0
        for i, ch in enumerate(self.player_name):
            w = header_font.size(ch)[0]
            if rel_x < accum + w/2:
                self.caret_index = i
                return
            accum += w
        self.caret_index = len(self.player_name)

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # first handle name-field keyboard/mouse
            self.handle_input_events(event)

            # handle button events & states
            # input_name screen buttons
            if self.state == "input_name":
                if self.btn_continue.handle_event(event):
                    if self.player_name.strip() != "":
                        # ensure caret at end so next time behaves
                        self.caret_index = len(self.player_name)
                        self.start_game()
                if self.btn_leader.handle_event(event):
                    self.state = "leaderboard"
                if self.btn_quit.handle_event(event):
                    return False

            elif self.state == "home":
                if self.btn_home_start.handle_event(event):
                    self.state = "input_name"
                if self.btn_leader.handle_event(event):
                    self.state = "leaderboard"
                if self.btn_quit.handle_event(event):
                    return False

            elif self.state == "gameplay":
                if self.btn_skip.handle_event(event):
                    self.skip_question()
                if self.game_active:
                    for b in self.option_buttons:
                        if b.handle_event(event):
                            # click detected -> check answer
                            self.check_answer(b.text)

            elif self.state == "results":
                if self.btn_play_again.handle_event(event):
                    # clear name so user re-enters if desired
                    self.player_name = ""
                    self.caret_index = 0
                    self.state = "input_name"
                if self.btn_back.handle_event(event):
                    self.state = "home"

            elif self.state == "leaderboard":
                if self.btn_back.handle_event(event):
                    self.state = "home"

            # timer next question
            if event.type == pygame.USEREVENT:
                self.next_question()

        return True

    def run(self):
        running = True
        # init caret timer
        self.caret_timer = pygame.time.get_ticks()
        while running:
            running = self.event_loop()
            self.update()

            # draw
            if self.state == "input_name":
                self.draw_input_name()
            elif self.state == "home":
                self.draw_home()
            elif self.state == "gameplay":
                self.draw_game()
            elif self.state == "results":
                self.draw_results()
            elif self.state == "leaderboard":
                self.draw_leaderboard()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    if not os.path.exists("images"):
        os.makedirs("images")
    Game().run()