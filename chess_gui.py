import pygame
import chess
import random
import time
from pygame.locals import *
from stockfish import Stockfish
import json
from datetime import datetime

pygame.init()

try:
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    print("Sound system initialized successfully")
except pygame.error as e:
    print(f"Could not initialize sound system: {e}")
    pygame.mixer = None

WIDTH, HEIGHT = 800, 800
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
INFO_PANEL_WIDTH = WIDTH - BOARD_SIZE

THEMES = {
    "Classic": {
        "light": (240, 240, 200),  # Creamy light green
        "dark": (100, 160, 80)     # Rich dark green
    },
    "Blue": {
        "light": (230, 240, 255),  # Light blue
        "dark": (70, 130, 180)     # Steel blue
    },
    "Wood": {
        "light": (240, 217, 181),  # Light wood
        "dark": (180, 135, 102)    # Dark wood
    },
    "Gray": {
        "light": (240, 240, 240),  # Light gray
        "dark": (120, 120, 120)    # Dark gray
    }
}
current_theme = "Classic"

# Colors
LIGHT = (240, 240, 200)
DARK = (100, 160, 80)
HIGHLIGHT = (247, 247, 105, 150)
LAST_MOVE = (247, 247, 105, 100)
CHECK_RED = (255, 50, 50, 180)
POPUP_BG = (50, 50, 50, 220)
POPUP_TEXT = (255, 255, 255)
BUTTON_COLOR = (70, 95, 130)
BUTTON_HOVER = (100, 130, 170)
BUTTON_TEXT = (255, 255, 255)
PANEL_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)

TIMER_DURATION = 10 * 60  # 10 minutes in seconds
MOVE_TIME_LIMIT = 30      

DIFFICULTY_SETTINGS = {
    "Easy": {
        "skill_level": 5,
        "depth": 8,
        "random_factor": 0.3  
    },
    "Medium": {
        "skill_level": 10,
        "depth": 12,
        "random_factor": 0.1  
    },
    "Hard": {
        "skill_level": 15,
        "depth": 16,
        "random_factor": 0.0
    }
}

def load_images():
    pieces = ["p", "r", "n", "b", "q", "k"]
    images = {}
    for piece in pieces:
        for color in ["w", "b"]:
            key = color + piece
            try:
                img = pygame.image.load(f"images/{key}.png")
                images[key] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
            except Exception as e:
                print(f"Error loading image {key}: {e}")
                font = pygame.font.SysFont("Arial", 36)
                symbol = {
                    "wp": "♙", "wr": "♖", "wn": "♘", "wb": "♗", "wq": "♕", "wk": "♔",
                    "bp": "♟", "br": "♜", "bn": "♞", "bb": "♝", "bq": "♛", "bk": "♚"
                }.get(key, "?")
                if color == "w":
                    text = font.render(symbol, True, (0, 0, 0))
                else:
                    text = font.render(symbol, True, (255, 255, 255))
                images[key] = text
    return images

def load_sounds():
    sounds = {}
    sound_files = {
        "move": ["static/sounds/move.wav", "sounds/move.wav", "move.wav"],
        "capture": ["static/sounds/capture.wav", "sounds/capture.wav", "capture.wav"],
        "check": ["static/sounds/check.wav", "sounds/check.wav", "check.wav"],
        "castle": ["static/sounds/castle.wav", "sounds/castle.wav", "castle.wav"],
        "promote": ["static/sounds/promote.wav", "sounds/promote.wav", "promote.wav"]
    }
    
    for sound_name, paths in sound_files.items():
        loaded = False
        for path in paths:
            try:
                sounds[sound_name] = pygame.mixer.Sound(path)
                loaded = True
                break
            except:
                continue
        
        if not loaded:
            try:
                sample_rate = 22050
                duration = 0.1
                frames = int(duration * sample_rate)
                
                if sound_name == "move":
                    frequency = 440  # A note
                elif sound_name == "capture":
                    frequency = 660  # E note
                elif sound_name == "check":
                    frequency = 880  # High A
                elif sound_name == "castle":
                    frequency = 330  # E below middle C
                elif sound_name == "promote":
                    frequency = 1100  # High C#
                
                arr = []
                for i in range(frames):
                    wave = 4096 * (i % (sample_rate // frequency)) / (sample_rate // frequency)
                    arr.append([int(wave), int(wave)])
                
                sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
                sounds[sound_name] = sound
                print(f"Generated fallback sound for {sound_name}")
            except Exception as e:
                print(f"Could not create fallback sound for {sound_name}: {e}")
    
    if sounds:
        print(f"Loaded {len(sounds)} sounds successfully")
    else:
        print("No sounds loaded. Game will run silently.")
    
    return sounds

# Initialize game
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Chess")
images = load_images()
sounds = load_sounds() if pygame.mixer and pygame.mixer.get_init() else {}
print(f"Sound system status: {'Enabled' if sounds else 'Disabled'}")
board = chess.Board()
selected_square = None
legal_moves = []
last_move = None

game_over = False
show_popup = False
popup_message = ""
popup_buttons = []
timer_start = None
time_remaining = TIMER_DURATION
move_start_time = None
move_time_remaining = MOVE_TIME_LIMIT
difficulty = "Medium"
player_color = chess.WHITE
game_history = []
ai_thinking = False
show_promotion_dialog = False
promotion_square = None

try:
    # Try different possible paths for Stockfish
    stockfish_paths = [
        "stockfish.exe",
        "stockfish",
        "./stockfish.exe", 
        "./stockfish",
        "C:/Program Files/Stockfish/stockfish.exe",
        "C:/Program Files (x86)/Stockfish/stockfish.exe"
    ]
    
    stockfish = None
    for path in stockfish_paths:
        try:
            stockfish = Stockfish(path=path)
            # Test if stockfish is working
            stockfish.set_position(["e2e4"])
            stockfish.get_best_move()
            print(f"Stockfish found at: {path}")
            break
        except:
            continue
    
    if stockfish:
        # Set initial difficulty
        settings = DIFFICULTY_SETTINGS[difficulty]
        stockfish.set_skill_level(settings["skill_level"])
        stockfish.set_depth(settings["depth"])
    else:
        print("Stockfish not found in any common locations.")
        print("You can still play, but moves will be random.")
        stockfish = None
        
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    stockfish = None

def update_ai_difficulty():
    if stockfish:
        settings = DIFFICULTY_SETTINGS[difficulty]
        stockfish.set_skill_level(settings["skill_level"])
        stockfish.set_depth(settings["depth"])

def draw_board():
    global LIGHT, DARK
    current_theme_colors = THEMES[current_theme]
    LIGHT = current_theme_colors["light"]
    DARK = current_theme_colors["dark"]
    
    # Chess board
    for rank in range(8):
        for file in range(8):
            color = LIGHT if (rank + file) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    if last_move:
        for square in [last_move.from_square, last_move.to_square]:
            file, rank = chess.square_file(square), chess.square_rank(square)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(LAST_MOVE)
            screen.blit(s, (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))
    
    if selected_square:
        file, rank = chess.square_file(selected_square), chess.square_rank(selected_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(HIGHLIGHT)
        screen.blit(s, (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))
        
        for move in legal_moves:
            file, rank = chess.square_file(move.to_square), chess.square_rank(move.to_square)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((100, 255, 100, 100))
            screen.blit(s, (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))
    
    if board.is_check():
        king_square = board.king(board.turn)
        file, rank = chess.square_file(king_square), chess.square_rank(king_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(CHECK_RED)
        screen.blit(s, (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            file, rank = chess.square_file(square), chess.square_rank(square)
            key = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
            if isinstance(images[key], pygame.Surface):
                screen.blit(images[key], (file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE))
            else:
                screen.blit(images[key], (file * SQUARE_SIZE + 15, (7 - rank) * SQUARE_SIZE + 10))

def cycle_theme():
    global current_theme, LIGHT, DARK
    theme_list = list(THEMES.keys())
    current_index = theme_list.index(current_theme)
    next_index = (current_index + 1) % len(theme_list)
    current_theme = theme_list[next_index]
    
    theme_colors = THEMES[current_theme]
    LIGHT = theme_colors["light"]
    DARK = theme_colors["dark"]
    
    draw_board()
    pygame.display.flip()
    
    show_settings()

def cycle_difficulty():
    global difficulty
    difficulties = list(DIFFICULTY_SETTINGS.keys())
    current_index = difficulties.index(difficulty)
    next_index = (current_index + 1) % len(difficulties)
    difficulty = difficulties[next_index]
    
    update_ai_difficulty()
    
    show_settings()
    
def draw_info_panel():
    pygame.draw.rect(screen, PANEL_COLOR, (BOARD_SIZE, 0, INFO_PANEL_WIDTH, HEIGHT))
    
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)
    
    player_text = f"Playing as: {'White' if player_color == chess.WHITE else 'Black'}"
    text = font.render(player_text, True, TEXT_COLOR)
    screen.blit(text, (BOARD_SIZE + 20, 20))
    
    difficulty_text = f"Difficulty: {difficulty}"
    text = font.render(difficulty_text, True, TEXT_COLOR)
    screen.blit(text, (BOARD_SIZE + 20, 50))

    status = []
    if board.is_checkmate():
        status.append("Checkmate! " + ("Black" if board.turn == chess.WHITE else "White") + " wins!")
    elif board.is_stalemate():
        status.append("Draw by stalemate")
    elif board.is_insufficient_material():
        status.append("Draw by insufficient material")
    elif board.is_check():
        status.append("White's turn" if board.turn == chess.WHITE else "Black's turn")
        status.append("(Check!)")
    else:
        status.append("White's turn" if board.turn == chess.WHITE else "Black's turn")
    
    status_text = " ".join(status)
    text = font.render(status_text, True, TEXT_COLOR)
    screen.blit(text, (BOARD_SIZE + 20, 80))

    if timer_start is not None and not game_over:
        elapsed = time.time() - timer_start
        remaining = max(0, time_remaining - elapsed)
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
    else:
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
    
    timer_text = f"Game Time: {minutes:02d}:{seconds:02d}"
    text = font.render(timer_text, True, TEXT_COLOR)
    screen.blit(text, (BOARD_SIZE + 20, 120))
    
    if move_start_time is not None and not game_over:
        elapsed = time.time() - move_start_time
        remaining = max(0, move_time_remaining - elapsed)
        seconds = int(remaining)
        milliseconds = int((remaining - seconds) * 1000)
    else:
        seconds = int(move_time_remaining)
        milliseconds = 0
    
    move_timer_text = f"Move Time: {seconds:02d}.{milliseconds:03d}"
    text_color = (255, 100, 100) if seconds < 5 else TEXT_COLOR
    text = font.render(move_timer_text, True, text_color)
    screen.blit(text, (BOARD_SIZE + 20, 150))
    
    # Move history (last 5 moves)
    if game_history:
        history_text = "Move History:"
        text = small_font.render(history_text, True, TEXT_COLOR)
        screen.blit(text, (BOARD_SIZE + 20, 200))
        
        for i, move in enumerate(game_history[-5:]):
            move_text = f"{i+1}. {move}"
            text = small_font.render(move_text, True, TEXT_COLOR)
            screen.blit(text, (BOARD_SIZE + 20, 230 + i * 25))
    
    button_width, button_height = 150, 40
    button_y = HEIGHT - 200
    
    # New Game button
    pygame.draw.rect(screen, BUTTON_COLOR, (BOARD_SIZE + 20, button_y, button_width, button_height))
    text = font.render("New Game", True, BUTTON_TEXT)
    screen.blit(text, (BOARD_SIZE + 20 + (button_width - text.get_width()) // 2, 
                         button_y + (button_height - text.get_height()) // 2))
    
    # Give Up button
    pygame.draw.rect(screen, (200, 50, 50), (BOARD_SIZE + 20, button_y + 60, button_width, button_height))
    text = font.render("Give Up", True, BUTTON_TEXT)
    screen.blit(text, (BOARD_SIZE + 20 + (button_width - text.get_width()) // 2, 
                         button_y + 60 + (button_height - text.get_height()) // 2))
    
    # Settings button
    pygame.draw.rect(screen, BUTTON_COLOR, (BOARD_SIZE + 20, button_y + 120, button_width, button_height))
    text = font.render("Settings", True, BUTTON_TEXT)
    screen.blit(text, (BOARD_SIZE + 20 + (button_width - text.get_width()) // 2, 
                         button_y + 120 + (button_height - text.get_height()) // 2))
    
def draw_promotion_dialog():
    if not show_promotion_dialog or not promotion_square:
        return
    
    file, rank = chess.square_file(promotion_square), chess.square_rank(promotion_square)
    x = file * SQUARE_SIZE
    y = (7 - rank) * SQUARE_SIZE
    
    pygame.draw.rect(screen, (220, 220, 220), (x, y, SQUARE_SIZE, SQUARE_SIZE * 4))
    pygame.draw.rect(screen, (0, 0, 0), (x, y, SQUARE_SIZE, SQUARE_SIZE * 4), 2)
    
    pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    for i, piece in enumerate(pieces):
        key = "w" + chess.piece_symbol(piece).lower() if board.turn == chess.WHITE else "b" + chess.piece_symbol(piece).lower()
        screen.blit(images[key], (x, y + i * SQUARE_SIZE))

def square_at_pos(pos):
    x, y = pos
    if x < 0 or y < 0 or x >= BOARD_SIZE or y >= BOARD_SIZE:
        return None
    file = x // SQUARE_SIZE
    rank = 7 - (y // SQUARE_SIZE)
    return chess.square(file, rank)

def play_sound(move):
    if not sounds:
        return
    
    try:
        if board.is_checkmate() or board.is_stalemate():
            if "check" in sounds:
                sounds["check"].play()
        elif board.is_check():
            if "check" in sounds:
                sounds["check"].play()
        elif board.is_castling(move):
            if "castle" in sounds:
                sounds["castle"].play()
        elif board.is_capture(move):
            if "capture" in sounds:
                sounds["capture"].play()
        elif move.promotion:
            if "promote" in sounds:
                sounds["promote"].play()
        else:
            if "move" in sounds:
                sounds["move"].play()
    except Exception as e:
        print(f"Error playing sound: {e}")

def get_ai_move():
    if stockfish:
        stockfish.set_fen_position(board.fen())
        
        settings = DIFFICULTY_SETTINGS[difficulty]
        
        if random.random() < settings["random_factor"]:
            return random.choice(list(board.legal_moves))
        
        best_move = stockfish.get_best_move()
        if best_move:
            return chess.Move.from_uci(best_move)
        else:
            return random.choice(list(board.legal_moves))
    else:
        return random.choice(list(board.legal_moves))

def draw_popup(message, buttons=None):
    if buttons is None:
        buttons = [("OK", lambda: None)]
    
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    popup_width, popup_height = 400, 400
    popup_x = (WIDTH - popup_width) // 2
    popup_y = (HEIGHT - popup_height) // 2
    
    pygame.draw.rect(screen, POPUP_BG, (popup_x, popup_y, popup_width, popup_height))
    pygame.draw.rect(screen, (200, 200, 200), (popup_x, popup_y, popup_width, popup_height), 2)
    
    font = pygame.font.SysFont("Arial", 28)
    text_lines = message.split('\n')
    for i, line in enumerate(text_lines):
        text = font.render(line, True, POPUP_TEXT)
        text_rect = text.get_rect(center=(WIDTH // 2, popup_y + 40 + i * 30))
        screen.blit(text, text_rect)
    
    button_font = pygame.font.SysFont("Arial", 24)
    
    # First row: OK and Give Up
    for i in range(2):
        if i < len(popup_buttons):
            rect, callback = popup_buttons[i]
            label = buttons[i][0] if i < len(buttons) else "Give Up"
            
            mouse_pos = pygame.mouse.get_pos()
            hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)
            
            text = button_font.render(label, True, BUTTON_TEXT)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
    
    # Second row: Difficulty and Themes
    for i in range(2, 4):
        if i < len(popup_buttons):
            rect, callback = popup_buttons[i]
            label = "Difficulty" if i == 2 else "Theme"
            
            mouse_pos = pygame.mouse.get_pos()
            hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)
            
            text = button_font.render(label, True, BUTTON_TEXT)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
    
    # Cancel button
    if len(popup_buttons) > 4:
        rect, callback = popup_buttons[4]
        label = buttons[4][0] if len(buttons) > 4 else "Cancel"
        
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, rect)
        pygame.draw.rect(screen, (200, 200, 200), rect, 2)
        
        text = button_font.render(label, True, BUTTON_TEXT)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

def restart_game():
    global board, selected_square, legal_moves, game_over, show_popup, timer_start, time_remaining, move_start_time, move_time_remaining, last_move, game_history, ai_thinking, show_promotion_dialog, promotion_square, LIGHT, DARK
    
    board = chess.Board()
    selected_square = None
    legal_moves = []
    game_over = False
    show_popup = False
    time_remaining = TIMER_DURATION
    move_time_remaining = MOVE_TIME_LIMIT
    timer_start = time.time()
    move_start_time = time.time()
    last_move = None
    game_history = []
    ai_thinking = False
    show_promotion_dialog = False
    promotion_square = None
    
    theme_colors = THEMES[current_theme]
    LIGHT = theme_colors["light"]
    DARK = theme_colors["dark"]

    update_ai_difficulty()
    
    if player_color == chess.BLACK and stockfish:
        ai_thinking = True
        ai_move = get_ai_move()
        board.push(ai_move)
        last_move = ai_move
        game_history.append(ai_move.uci())
        ai_thinking = False
        move_start_time = time.time()

def check_info_panel_buttons(pos):
    x, y = pos
    button_width, button_height = 150, 40
    button_y = HEIGHT - 200
    
    if x < BOARD_SIZE:
        return None
    
    # New Game button
    if BOARD_SIZE + 20 <= x <= BOARD_SIZE + 20 + button_width and button_y <= y <= button_y + button_height:
        return "new_game"
    
    # Give Up button
    if BOARD_SIZE + 20 <= x <= BOARD_SIZE + 20 + button_width and button_y + 60 <= y <= button_y + 60 + button_height:
        return "give_up"
    
    # Settings button
    if BOARD_SIZE + 20 <= x <= BOARD_SIZE + 20 + button_width and button_y + 120 <= y <= button_y + 120 + button_height:
        return "settings"
    
    return None

def check_promotion_selection(pos):
    global show_promotion_dialog, promotion_square
    
    if not show_promotion_dialog or not promotion_square:
        return None
    
    file, rank = chess.square_file(promotion_square), chess.square_rank(promotion_square)
    x = file * SQUARE_SIZE
    y = (7 - rank) * SQUARE_SIZE
    
    if x <= pos[0] <= x + SQUARE_SIZE and y <= pos[1] <= y + SQUARE_SIZE * 4:
        index = (pos[1] - y) // SQUARE_SIZE
        pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        if 0 <= index < len(pieces):
            return pieces[index]
    
    return None

def show_settings():
    global show_popup, popup_message, popup_buttons
    
    show_popup = True
    popup_message = f"Game Settings\nCurrent Theme: {current_theme}\nDifficulty: {difficulty}"
    
    buttons = [
        ("OK", lambda: globals().update(show_popup=False)),
        ("Give Up", lambda: pygame.event.post(pygame.event.Event(pygame.QUIT))),
        ("Difficulty", cycle_difficulty),
        ("Change Theme", cycle_theme),
        ("Cancel", lambda: globals().update(show_popup=False))
    ]
    
    popup_buttons = []
    button_width, button_height = 120, 40
    button_spacing = 20
    popup_width = 400
    
    start_x = (WIDTH - popup_width) // 2 + (popup_width - (2 * button_width + button_spacing)) // 2
    start_y = (HEIGHT // 2) + 50
    
    # First row buttons (OK and Give Up)
    for i in range(2):
        button_x = start_x + i * (button_width + button_spacing)
        rect = pygame.Rect(button_x, start_y, button_width, button_height)
        popup_buttons.append((rect, buttons[i][1]))
    
    # Second row buttons (Difficulty and Change Theme)
    for i in range(2, 4):
        button_x = start_x + (i-2) * (button_width + button_spacing)
        rect = pygame.Rect(button_x, start_y + button_height + button_spacing, button_width, button_height)
        popup_buttons.append((rect, buttons[i][1]))
    
    # Cancel button (centered below)
    cancel_x = (WIDTH - button_width) // 2
    cancel_y = start_y + 2 * (button_height + button_spacing)
    popup_buttons.append((pygame.Rect(cancel_x, cancel_y, button_width, button_height), buttons[4][1]))

def check_timers():
    global game_over, show_popup, popup_message, time_remaining, move_time_remaining
    
    if timer_start is None or game_over:
        return
    
    # Game timer
    elapsed = time.time() - timer_start
    time_remaining = max(0, TIMER_DURATION - elapsed)
    
    # Move timer
    if move_start_time is not None:
        move_elapsed = time.time() - move_start_time
        move_time_remaining = max(0, MOVE_TIME_LIMIT - move_elapsed)
    
    if time_remaining <= 0 and not game_over:
        game_over = True
        show_popup = True
        popup_message = "Time's up!\nYou ran out of time"
    
    if move_time_remaining <= 0 and not game_over and not ai_thinking:
        game_over = True
        show_popup = True
        popup_message = "Move time exceeded!\nYou took too long"

def save_game_state():
    state = {
        "fen": board.fen(),
        "time_remaining": time_remaining,
        "move_time_remaining": move_time_remaining,
        "player_color": player_color,
        "difficulty": difficulty,
        "current_theme": current_theme,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        with open("saved_game.json", "w") as f:
            json.dump(state, f)
    except:
        print("Failed to save game state")

def load_game_state():
    global board, game_history, time_remaining, move_time_remaining, player_color, difficulty, current_theme
    try:
        with open("saved_game.json", "r") as f:
            state = json.load(f)
        
        board = chess.Board(state["fen"])
        time_remaining = state["time_remaining"]
        move_time_remaining = state["move_time_remaining"]
        player_color = state["player_color"]
        
        if "difficulty" in state:
            difficulty = state["difficulty"]
        if "current_theme" in state:
            current_theme = state["current_theme"]
        
        update_ai_difficulty()
        return True
    except:
        print("No saved game found or error loading")
        return False

# Main game 
def main():
    global running, selected_square, legal_moves, show_popup, game_over, popup_message, show_promotion_dialog, promotion_square, timer_start, move_start_time, ai_thinking
    
    running = True
    clock = pygame.time.Clock()
    timer_start = time.time()
    move_start_time = time.time()

    load_game_state()

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                save_game_state()
                running = False
            
            elif event.type == MOUSEBUTTONDOWN:
                if show_popup:
                    for button_rect, callback in popup_buttons:
                        if button_rect.collidepoint(event.pos):
                            callback()
                    continue
                
                if show_promotion_dialog:
                    promoted_to = check_promotion_selection(event.pos)
                    if promoted_to:
                        move = chess.Move(selected_square, promotion_square, promotion=promoted_to)
                        if move in legal_moves:
                            board.push(move)
                            play_sound(move)
                            game_history.append(move.uci())
                            last_move = move
                            
                            if board.is_game_over():
                                game_over = True
                                if board.is_checkmate():
                                    popup_message = "Checkmate!\nYou win!"
                                else:
                                    popup_message = "Game Over!\nDraw"
                                show_popup = True
                            else:
                                ai_thinking = True
                                ai_move = get_ai_move()
                                board.push(ai_move)
                                game_history.append(ai_move.uci())
                                last_move = ai_move
                                play_sound(ai_move)
                                ai_thinking = False
                                move_start_time = time.time()
                                
                                if board.is_game_over():
                                    game_over = True
                                    if board.is_checkmate():
                                        popup_message = "Checkmate!\nAI wins"
                                    else:
                                        popup_message = "Game Over!\nDraw"
                                    show_popup = True
                    
                    show_promotion_dialog = False
                    promotion_square = None
                    selected_square = None
                    legal_moves = []
                    continue
                
                button = check_info_panel_buttons(event.pos)
                if button == "new_game":
                    restart_game()
                    continue
                elif button == "give_up":
                    game_over = True
                    show_popup = True
                    popup_message = "You gave up!\nAI wins"
                    continue
                elif button == "settings":
                    show_settings()
                    continue
                
                if game_over or ai_thinking:
                    continue
                    
                square = square_at_pos(event.pos)
                if square is None:
                    continue
                
                if selected_square:
                    move = chess.Move(selected_square, square)
                    
                    piece = board.piece_at(selected_square)
                    if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in [0, 7]:
                        promotion_square = square
                        show_promotion_dialog = True
                        continue
                    
                    if move in legal_moves:
                        board.push(move)
                        play_sound(move)
                        game_history.append(move.uci())
                        last_move = move
                        selected_square = None
                        legal_moves = []
                        move_start_time = time.time()
                        
                        if board.is_game_over():
                            game_over = True
                            if board.is_checkmate():
                                popup_message = "Checkmate!\nYou win!"
                            else:
                                popup_message = "Game Over!\nDraw"
                            show_popup = True
                        else:
                            ai_thinking = True
                            ai_move = get_ai_move()
                            board.push(ai_move)
                            game_history.append(ai_move.uci())
                            last_move = ai_move
                            play_sound(ai_move)
                            ai_thinking = False
                            move_start_time = time.time()
                            
                            if board.is_game_over():
                                game_over = True
                                if board.is_checkmate():
                                    popup_message = "Checkmate!\nAI wins"
                                else:
                                    popup_message = "Game Over!\nDraw"
                                show_popup = True
                    else:
                        selected_square = None
                        legal_moves = []
                else:
                    piece = board.piece_at(square)
                    if piece and piece.color == player_color:
                        selected_square = square
                        legal_moves = [move for move in board.legal_moves if move.from_square == square]
        
        # Check timers
        if not game_over and not show_popup and not ai_thinking:
            check_timers()
        
        screen.fill((0, 0, 0))
        draw_board()
        draw_info_panel()
        draw_promotion_dialog()
        
        if show_popup:
            draw_popup(popup_message)
        
        pygame.display.flip()
        clock.tick(60)

    if stockfish:
        try:
            # Properly close stockfish
            if hasattr(stockfish, '_stockfish') and stockfish._stockfish:
                stockfish._stockfish.terminate()
                stockfish._stockfish.wait()
        except:
            pass

    pygame.quit()

if __name__ == '__main__':
    main()