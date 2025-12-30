"""
Powerball Simulator - Display Module
Pygame-based display for the 7" monitor.
"""

import pygame
import qrcode
import io
import os
from game_engine import game

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 30

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
RED = (220, 53, 69)
GREEN = (40, 167, 69)
BLUE = (0, 123, 255)
CYAN = (0, 188, 212)  # Best match indicator
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (100, 100, 100)
POWERBALL_RED = (198, 40, 40)

class Display:
    def __init__(self, server_url: str):
        pygame.init()
        
        # Try fullscreen, fall back to windowed for testing
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        except:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Powerball Simulator")
        self.clock = pygame.time.Clock()
        self.server_url = server_url
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Generate QR code
        self.qr_large = self._generate_qr(server_url, 200)
        self.qr_small = self._generate_qr(server_url, 100)  # Larger for easier scanning on 7" screen
        
        # Animation state
        self.ball_animation_frame = 0
        self.celebration_frame = 0
        self.scroll_offset = 0
        self.scroll_timer = 0
        self.scroll_page = 0
        
        # QR overlay timing (show for 5-7 sec once per minute)
        self.qr_overlay_timer = 0
        self.qr_overlay_active = False
        self.qr_overlay_duration = FPS * 6  # 6 seconds
        self.qr_overlay_interval = FPS * 60  # Every 60 seconds

        # Million dollar win flash effect
        self.million_flash_timer = 0
        
    def _generate_qr(self, url: str, size: int) -> pygame.Surface:
        """Generate a QR code as a Pygame surface."""
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert PIL image to Pygame surface
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        surface = pygame.image.load(img_bytes)
        return pygame.transform.scale(surface, (size, size))

    def _get_card_dimensions(self, num_players: int) -> tuple:
        """Get card width, height, and font scale based on player count."""
        if num_players == 1:
            return 350, 300, 1.8  # Large card, ~2x fonts
        elif num_players == 2:
            return 300, 280, 1.5  # Medium-large cards
        elif num_players == 3:
            return 220, 200, 1.2  # Medium cards
        else:
            return 175, 165, 1.0  # Default small cards (4+)

    def draw_idle_screen(self):
        """Draw the idle screen with large QR code."""
        self.screen.fill(DARK_GRAY)
        
        # Title
        title = self.font_large.render("POWERBALL SIMULATOR", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH//2, y=30)
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_medium.render("How long until you win?", True, WHITE)
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH//2, y=80)
        self.screen.blit(subtitle, subtitle_rect)
        
        # QR Code (centered)
        qr_rect = self.qr_large.get_rect(centerx=SCREEN_WIDTH//2, centery=SCREEN_HEIGHT//2 + 20)
        self.screen.blit(self.qr_large, qr_rect)
        
        # Instructions
        scan_text = self.font_medium.render("Scan to Play!", True, WHITE)
        scan_rect = scan_text.get_rect(centerx=SCREEN_WIDTH//2, y=SCREEN_HEIGHT - 80)
        self.screen.blit(scan_text, scan_rect)
        
        # URL as fallback
        url_text = self.font_small.render(self.server_url, True, LIGHT_GRAY)
        url_rect = url_text.get_rect(centerx=SCREEN_WIDTH//2, y=SCREEN_HEIGHT - 40)
        self.screen.blit(url_text, url_rect)
    
    def draw_ball(self, x: int, y: int, number: int, is_powerball: bool = False, matched: bool = False):
        """Draw a lottery ball."""
        radius = 22 if is_powerball else 20
        
        if matched:
            color = GREEN
        elif is_powerball:
            color = POWERBALL_RED
        else:
            color = WHITE
        
        # Ball circle
        pygame.draw.circle(self.screen, color, (x, y), radius)
        pygame.draw.circle(self.screen, BLACK, (x, y), radius, 2)
        
        # Number
        num_text = self.font_small.render(str(number), True, BLACK if not (is_powerball and not matched) else WHITE)
        num_rect = num_text.get_rect(center=(x, y))
        self.screen.blit(num_text, num_rect)
    
    def draw_winning_numbers(self, whites: list, powerball: int, y_pos: int):
        """Draw the current winning numbers."""
        start_x = SCREEN_WIDTH // 2 - 70  # Shifted right for better spacing from label

        # Label - fixed left margin for even spacing
        label = self.font_small.render("WINNING NUMBERS:", True, GOLD)
        self.screen.blit(label, (10, y_pos - 8))
        
        # White balls
        for i, num in enumerate(whites):
            self.draw_ball(start_x + i * 50, y_pos, num)
        
        # Separator
        pygame.draw.line(self.screen, LIGHT_GRAY, 
                        (start_x + 235, y_pos - 15), 
                        (start_x + 235, y_pos + 15), 2)
        
        # Powerball
        self.draw_ball(start_x + 280, y_pos, powerball, is_powerball=True)
    
    def draw_player_card(self, player: dict, x: int, y: int, width: int, height: int, scale: float = 1.0):
        """Draw a single player's stats card with optional scaling."""
        # Card background
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, width, height), 1)

        # Scale-adjusted fonts
        name_font = pygame.font.Font(None, int(24 * scale))
        nums_font = pygame.font.Font(None, int(18 * scale))
        stats_font = pygame.font.Font(None, int(18 * scale))

        padding = int(8 * scale)
        line_height = int(18 * scale)
        indicator_radius = int(5 * scale)
        indicator_spacing = int(16 * scale)
        curr_y = y + padding

        # Player name (truncate based on card size)
        max_name_len = 12 if scale < 1.3 else 16
        name_text = name_font.render(player["name"][:max_name_len], True, GOLD)
        self.screen.blit(name_text, (x + padding, curr_y))
        curr_y += line_height + int(4 * scale)

        # Player's numbers
        nums_str = " ".join(str(n).zfill(2) for n in player["numbers"])
        nums_str += f" | {str(player['powerball']).zfill(2)}"
        nums_text = nums_font.render(nums_str, True, LIGHT_GRAY)
        self.screen.blit(nums_text, (x + padding, curr_y))
        curr_y += line_height

        # Match indicators (current match = green, best match = cyan, miss = red)
        white_matches, pb_match = player["last_matches"]
        best_white = player.get("best_white_matches", 0)
        for i in range(5):
            if i < white_matches:
                color = GREEN  # Current match
            elif i < best_white:
                color = CYAN   # Best ever (but not current)
            else:
                color = RED    # Never matched
            pygame.draw.circle(self.screen, color,
                             (x + padding + int(8 * scale) + i * indicator_spacing, curr_y + int(6 * scale)),
                             indicator_radius)
        # PB match indicator
        pb_color = GREEN if pb_match else RED
        pygame.draw.circle(self.screen, pb_color,
                          (x + padding + int(8 * scale) + 5 * indicator_spacing + int(10 * scale), curr_y + int(6 * scale)),
                          indicator_radius)
        curr_y += line_height

        # Stats
        stats = [
            f"Tickets: {player['tickets']:,}",
            f"Spent: ${player['spent']:,}",
            f"Won: ${player['winnings']:,}",
        ]

        for stat in stats:
            stat_text = stats_font.render(stat, True, WHITE)
            self.screen.blit(stat_text, (x + padding, curr_y))
            curr_y += line_height - int(2 * scale)

        # Net (colored)
        net = player["net"]
        net_color = GREEN if net >= 0 else RED
        net_text = stats_font.render(f"Net: ${net:,}", True, net_color)
        self.screen.blit(net_text, (x + padding, curr_y))
        curr_y += line_height - int(2 * scale)

        # Time and near-wins
        time_text = stats_font.render(f"Time: {player['elapsed_time']}", True, LIGHT_GRAY)
        self.screen.blit(time_text, (x + padding, curr_y))
        curr_y += line_height - int(2 * scale)

        # Best matches (in cyan)
        best_text = stats_font.render(f"Best: {player.get('best_white_matches', 0)}/5", True, CYAN)
        self.screen.blit(best_text, (x + padding, curr_y))

        if player["million_plus_wins"] > 0:
            mil_text = stats_font.render(f"$1M+: {player['million_plus_wins']}", True, GOLD)
            self.screen.blit(mil_text, (x + padding + int(60 * scale), curr_y))

        # Last prize flash
        if player["last_prize"] > 0:
            prize_text = name_font.render(f"+${player['last_prize']:,}", True, GREEN)
            prize_rect = prize_text.get_rect(right=x + width - padding, top=y + padding)
            self.screen.blit(prize_text, prize_rect)
    
    def draw_game_screen(self, state: dict):
        """Draw the active game screen."""
        self.screen.fill(DARK_GRAY)
        
        # Header bar
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, 50))
        
        # Title
        title = self.font_medium.render("POWERBALL SIMULATOR", True, GOLD)
        self.screen.blit(title, (10, 12))
        
        # Drawing counter
        drawing_text = self.font_small.render(f"Drawing #{state['total_drawings']:,}", True, WHITE)
        drawing_rect = drawing_text.get_rect(centerx=SCREEN_WIDTH//2, y=15)
        self.screen.blit(drawing_text, drawing_rect)
        
        # Last jackpot banner (if exists)
        if state.get('last_jackpot_rolls', 0) > 0:
            jackpot_text = self.font_tiny.render(
                f"LAST JACKPOT: {state['last_jackpot_rolls']:,} rolls by {state['last_jackpot_winner']}", 
                True, GOLD
            )
            jackpot_rect = jackpot_text.get_rect(centerx=SCREEN_WIDTH//2, y=38)
            self.screen.blit(jackpot_text, jackpot_rect)
        
        # Speed indicator
        speed_text = self.font_tiny.render(f"{state['speed']}x", True, LIGHT_GRAY)
        self.screen.blit(speed_text, (SCREEN_WIDTH - 100, 18))
        
        # Paused indicator
        if not state.get("running") and state.get("player_count", 0) > 0:
            paused_text = self.font_small.render("⏸ PAUSED", True, GOLD)
            self.screen.blit(paused_text, (SCREEN_WIDTH - 100, 32))
        
        # Small QR code (100x100, positioned in top-right)
        self.screen.blit(self.qr_small, (SCREEN_WIDTH - 105, 45))
        
        # Winning numbers section
        if state["current_whites"]:
            self.draw_winning_numbers(state["current_whites"], state["current_powerball"], 80)
        
        # Divider (account for larger QR code)
        pygame.draw.line(self.screen, LIGHT_GRAY, (10, 115), (SCREEN_WIDTH - 115, 115), 1)
        
        # Player grid
        players = state["players"]
        num_players = len(players)

        if num_players == 0:
            # No players message
            msg = self.font_medium.render("Waiting for players...", True, WHITE)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(msg, msg_rect)
            return

        # Get dynamic card dimensions based on player count
        grid_top = 125
        card_width, card_height, scale = self._get_card_dimensions(num_players)

        # Determine visible players (4 at a time if > 4)
        if num_players <= 4:
            visible_players = players
            cols = num_players
        else:
            # Paginate through players every 5 seconds
            self.scroll_timer += 1
            if self.scroll_timer >= FPS * 5:  # 5 seconds
                self.scroll_timer = 0
                self.scroll_page = (self.scroll_page + 1) % 2

            start_idx = self.scroll_page * 4
            visible_players = players[start_idx:start_idx + 4]
            cols = min(len(visible_players), 4)

            # Page indicator
            page_text = self.font_tiny.render(f"Page {self.scroll_page + 1}/2", True, LIGHT_GRAY)
            self.screen.blit(page_text, (10, SCREEN_HEIGHT - 20))

        # Calculate card layout (account for larger QR code on right side)
        available_width = SCREEN_WIDTH - 110  # Space for QR code
        total_width = cols * card_width + (cols - 1) * 10
        start_x = (available_width - total_width) // 2

        # Center vertically in available space
        available_height = SCREEN_HEIGHT - grid_top - 10
        start_y = grid_top + (available_height - card_height) // 2

        for i, player in enumerate(visible_players):
            col = i % cols
            x = start_x + col * (card_width + 10)
            y = start_y
            self.draw_player_card(player, x, y, card_width, card_height, scale)
    
    def draw_jackpot_celebration(self, winner_name: str):
        """Draw the jackpot celebration screen."""
        self.celebration_frame += 1
        
        # Flashing background
        if (self.celebration_frame // 5) % 2 == 0:
            self.screen.fill(GOLD)
        else:
            self.screen.fill(RED)
        
        # Giant text
        winner_text = self.font_large.render("JACKPOT!!!", True, WHITE)
        winner_rect = winner_text.get_rect(centerx=SCREEN_WIDTH//2, y=100)
        self.screen.blit(winner_text, winner_rect)
        
        name_text = self.font_large.render(f"{winner_name} WINS!", True, BLACK)
        name_rect = name_text.get_rect(centerx=SCREEN_WIDTH//2, y=200)
        self.screen.blit(name_text, name_rect)
        
        amount_text = self.font_large.render("$1,800,000,000", True, WHITE)
        amount_rect = amount_text.get_rect(centerx=SCREEN_WIDTH//2, y=300)
        self.screen.blit(amount_text, amount_rect)
    
    def draw_qr_overlay(self, state: dict):
        """Draw a semi-transparent QR overlay with drawing counter still visible."""
        # Semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(DARK_GRAY)
        overlay.set_alpha(230)
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("JOIN THE GAME!", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH//2, y=40)
        self.screen.blit(title, title_rect)
        
        # Large QR code
        qr_rect = self.qr_large.get_rect(centerx=SCREEN_WIDTH//2, centery=SCREEN_HEIGHT//2)
        self.screen.blit(self.qr_large, qr_rect)
        
        # Drawing counter at bottom
        drawing_text = self.font_medium.render(f"Drawing #{state['total_drawings']:,}", True, WHITE)
        drawing_rect = drawing_text.get_rect(centerx=SCREEN_WIDTH//2, y=SCREEN_HEIGHT - 60)
        self.screen.blit(drawing_text, drawing_rect)
        
        # URL
        url_text = self.font_small.render(self.server_url, True, LIGHT_GRAY)
        url_rect = url_text.get_rect(centerx=SCREEN_WIDTH//2, y=SCREEN_HEIGHT - 30)
        self.screen.blit(url_text, url_rect)
    
    def update(self, state: dict):
        """Main update function - call each frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        # Update QR overlay timer
        if state.get("running") and state.get("player_count", 0) > 0:
            self.qr_overlay_timer += 1
            if self.qr_overlay_timer >= self.qr_overlay_interval:
                self.qr_overlay_active = True
            if self.qr_overlay_active and self.qr_overlay_timer >= self.qr_overlay_interval + self.qr_overlay_duration:
                self.qr_overlay_active = False
                self.qr_overlay_timer = 0

        # Check for million dollar wins (persistent flag survives batched drawings)
        if state.get("million_win_pending"):
            self.million_flash_timer = 90  # 3 seconds at 30fps
            game.clear_million_flash()  # Acknowledge the win

        # Decide which screen to show
        if state.get("jackpot_hit"):
            self.draw_jackpot_celebration(state.get("jackpot_winner", "Someone"))
        elif state.get("player_count", 0) > 0:
            # Show game screen if there are players (running or paused)
            self.draw_game_screen(state)

            # Million dollar win flash effect (subtle gold overlay)
            if self.million_flash_timer > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill(GOLD)
                overlay.set_alpha(128)  # 50% opacity
                self.screen.blit(overlay, (0, 0))
                self.million_flash_timer -= 1

            # Show QR overlay periodically (only when running)
            if state.get("running") and self.qr_overlay_active:
                self.draw_qr_overlay(state)
        else:
            self.draw_idle_screen()

        pygame.display.flip()
        self.clock.tick(FPS)
        return True
    
    def quit(self):
        pygame.quit()
