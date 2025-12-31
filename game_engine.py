"""
Powerball Simulator - Game Engine
Handles all game state, player management, and lottery logic.
"""

import random
import threading
import time
import json
import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta

STATE_FILE = "state.json"

# Powerball rules
WHITE_BALL_MAX = 69
POWERBALL_MAX = 26
TICKET_COST = 2

# Prize structure (white ball matches, powerball match) -> prize amount
PRIZES = {
    (5, True): 1_800_000_000,  # Jackpot ($1.8B)
    (5, False): 1_000_000,
    (4, True): 50_000,
    (4, False): 100,
    (3, True): 100,
    (3, False): 7,
    (2, True): 7,
    (1, True): 4,
    (0, True): 4,
}

@dataclass
class Player:
    id: str
    name: str
    numbers: list[int]  # 5 white balls
    powerball: int
    tickets: int = 0
    spent: int = 0
    winnings: int = 0
    million_plus_wins: int = 0
    jackpot_wins: int = 0
    joined_at: datetime = field(default_factory=datetime.now)
    last_matches: tuple[int, bool] = (0, False)  # (white_matches, pb_match)
    last_prize: int = 0
    best_white_matches: int = 0  # Track highest white ball matches ever

    def check_ticket(self, drawn_whites: list[int], drawn_pb: int) -> int:
        """Check this player's numbers against drawn numbers. Returns prize amount."""
        white_matches = len(set(self.numbers) & set(drawn_whites))
        pb_match = self.powerball == drawn_pb
        
        self.last_matches = (white_matches, pb_match)
        prize = PRIZES.get((white_matches, pb_match), 0)
        self.last_prize = prize
        
        # Track best white ball matches
        if white_matches > self.best_white_matches:
            self.best_white_matches = white_matches
        
        self.tickets += 1
        self.spent += TICKET_COST
        self.winnings += prize
        
        if prize >= 1_000_000 and prize < 1_800_000_000:
            self.million_plus_wins += 1
        elif prize >= 1_800_000_000:
            self.jackpot_wins += 1
            
        return prize

    def get_elapsed_time(self) -> str:
        """Return formatted elapsed time since joining."""
        delta = datetime.now() - self.joined_at
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "numbers": self.numbers,
            "powerball": self.powerball,
            "tickets": self.tickets,
            "spent": self.spent,
            "winnings": self.winnings,
            "million_plus_wins": self.million_plus_wins,
            "jackpot_wins": self.jackpot_wins,
            "elapsed_time": self.get_elapsed_time(),
            "last_matches": self.last_matches,
            "last_prize": self.last_prize,
            "best_white_matches": self.best_white_matches,
            "net": self.winnings - self.spent,
        }


class GameState:
    def __init__(self):
        self.lock = threading.Lock()
        self.players: dict[str, Player] = {}
        self.player_order: list[str] = []  # Maintain join order
        self.total_drawings: int = 0
        self.current_whites: list[int] = []
        self.current_powerball: int = 0
        self.running: bool = False
        self.speed: int = 1  # Drawings per second
        self.max_players: int = 8
        self.jackpot_hit: bool = False
        self.jackpot_winner: Optional[str] = None
        # Jackpot history
        self.last_jackpot_rolls: int = 0
        self.last_jackpot_winner: str = ""
        # Million dollar win flash (persists until display acknowledges)
        self.million_win_pending: bool = False
        # Jackpot winner stats (captured at win time for display)
        self.jackpot_winner_spent: int = 0
        self.jackpot_winner_time: str = ""
        self.jackpot_winner_tickets: int = 0

    def add_player(self, name: str, numbers: list[int], powerball: int) -> tuple[bool, str]:
        """Add a new player. Returns (success, message/player_id)."""
        with self.lock:
            if len(self.players) >= self.max_players:
                return False, "Game is full (8 players max)"
            
            # Validate numbers
            if len(numbers) != 5:
                return False, "Must pick exactly 5 numbers"
            if not all(1 <= n <= WHITE_BALL_MAX for n in numbers):
                return False, f"White balls must be 1-{WHITE_BALL_MAX}"
            if len(set(numbers)) != 5:
                return False, "White ball numbers must be unique"
            if not 1 <= powerball <= POWERBALL_MAX:
                return False, f"Powerball must be 1-{POWERBALL_MAX}"
            
            player_id = f"player_{int(time.time() * 1000)}"
            player = Player(
                id=player_id,
                name=name[:20],  # Truncate long names
                numbers=sorted(numbers),
                powerball=powerball
            )
            self.players[player_id] = player
            self.player_order.append(player_id)
            
            # Auto-start when first player joins
            if len(self.players) == 1:
                self.running = True
                
            return True, player_id
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player by ID."""
        with self.lock:
            if player_id in self.players:
                del self.players[player_id]
                self.player_order.remove(player_id)
                
                # Stop if no players left
                if len(self.players) == 0:
                    self.running = False
                return True
            return False
    
    def reset_game(self):
        """Reset all game state."""
        with self.lock:
            self.players.clear()
            self.player_order.clear()
            self.total_drawings = 0
            self.current_whites = []
            self.current_powerball = 0
            self.running = False
            self.jackpot_hit = False
            self.jackpot_winner = None
            # Clear winner stats
            self.jackpot_winner_spent = 0
            self.jackpot_winner_time = ""
            self.jackpot_winner_tickets = 0
            # Keep jackpot history for the banner

        # Delete state file to prevent reload of old state
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    def resume_after_jackpot(self):
        """Resume game after jackpot celebration."""
        with self.lock:
            self.jackpot_hit = False
            self.jackpot_winner = None
            if len(self.players) > 0:
                self.running = True

    def clear_million_flash(self):
        """Clear the million dollar win flash flag (called by display after showing effect)."""
        with self.lock:
            self.million_win_pending = False

    def set_speed(self, speed: int):
        """Set drawings per second (1, 10, 100, 1000, 10000)."""
        with self.lock:
            self.speed = max(1, min(10000, speed))
    
    def draw_numbers(self) -> tuple[list[int], int]:
        """Draw new Powerball numbers."""
        whites = sorted(random.sample(range(1, WHITE_BALL_MAX + 1), 5))
        pb = random.randint(1, POWERBALL_MAX)
        return whites, pb
    
    def run_drawing(self) -> dict:
        """Execute one drawing and check all players. Returns results."""
        with self.lock:
            if not self.running or not self.players:
                return {"active": False}
            
            self.current_whites, self.current_powerball = self.draw_numbers()
            self.total_drawings += 1
            
            results = {
                "active": True,
                "drawing_num": self.total_drawings,
                "whites": self.current_whites,
                "powerball": self.current_powerball,
                "players": [],
                "jackpot_hit": False,
                "jackpot_winner": None,
            }
            
            for player_id in self.player_order:
                player = self.players[player_id]
                prize = player.check_ticket(self.current_whites, self.current_powerball)
                
                if prize >= 1_800_000_000:
                    self.jackpot_hit = True
                    self.jackpot_winner = player.name
                    # Log jackpot history
                    self.last_jackpot_rolls = self.total_drawings
                    self.last_jackpot_winner = player.name
                    # Capture winner stats for display
                    self.jackpot_winner_spent = player.spent
                    self.jackpot_winner_time = player.get_elapsed_time()
                    self.jackpot_winner_tickets = player.tickets
                    # Stop the game on jackpot
                    self.running = False
                    results["jackpot_hit"] = True
                    results["jackpot_winner"] = player.name
                elif prize >= 1_000_000:
                    # Set flag for million dollar flash (display will clear it)
                    self.million_win_pending = True

                results["players"].append(player.to_dict())
            
            return results
    
    def get_state(self) -> dict:
        """Get current game state for display."""
        with self.lock:
            return {
                "running": self.running,
                "total_drawings": self.total_drawings,
                "current_whites": self.current_whites,
                "current_powerball": self.current_powerball,
                "speed": self.speed,
                "player_count": len(self.players),
                "jackpot_hit": self.jackpot_hit,
                "jackpot_winner": self.jackpot_winner,
                "last_jackpot_rolls": self.last_jackpot_rolls,
                "last_jackpot_winner": self.last_jackpot_winner,
                "jackpot_winner_spent": self.jackpot_winner_spent,
                "jackpot_winner_time": self.jackpot_winner_time,
                "jackpot_winner_tickets": self.jackpot_winner_tickets,
                "million_win_pending": self.million_win_pending,
                "players": [self.players[pid].to_dict() for pid in self.player_order],
            }

    @staticmethod
    def quick_pick() -> tuple[list[int], int]:
        """Generate random numbers for quick pick."""
        whites = sorted(random.sample(range(1, WHITE_BALL_MAX + 1), 5))
        pb = random.randint(1, POWERBALL_MAX)
        return whites, pb

    def save_state(self, filepath: str = STATE_FILE) -> bool:
        """Save game state to JSON file for persistence across restarts."""
        with self.lock:
            try:
                state_data = {
                    "saved_at": datetime.now().isoformat(),
                    "total_drawings": self.total_drawings,
                    "speed": self.speed,
                    "last_jackpot_rolls": self.last_jackpot_rolls,
                    "last_jackpot_winner": self.last_jackpot_winner,
                    "player_order": self.player_order,
                    "players": []
                }

                for pid in self.player_order:
                    player = self.players[pid]
                    # Calculate elapsed seconds to restore later
                    elapsed_seconds = (datetime.now() - player.joined_at).total_seconds()
                    state_data["players"].append({
                        "id": player.id,
                        "name": player.name,
                        "numbers": player.numbers,
                        "powerball": player.powerball,
                        "tickets": player.tickets,
                        "spent": player.spent,
                        "winnings": player.winnings,
                        "million_plus_wins": player.million_plus_wins,
                        "jackpot_wins": player.jackpot_wins,
                        "elapsed_seconds": elapsed_seconds,
                        "best_white_matches": player.best_white_matches,
                    })

                with open(filepath, "w") as f:
                    json.dump(state_data, f, indent=2)
                print(f"State saved to {filepath}")
                return True
            except Exception as e:
                print(f"Error saving state: {e}")
                return False

    def load_state(self, filepath: str = STATE_FILE) -> bool:
        """Load game state from JSON file."""
        if not os.path.exists(filepath):
            print(f"No state file found at {filepath}")
            return False

        with self.lock:
            try:
                with open(filepath, "r") as f:
                    state_data = json.load(f)

                # Restore game state
                self.total_drawings = state_data.get("total_drawings", 0)
                self.speed = state_data.get("speed", 1)
                self.last_jackpot_rolls = state_data.get("last_jackpot_rolls", 0)
                self.last_jackpot_winner = state_data.get("last_jackpot_winner", "")

                # Restore players
                self.players.clear()
                self.player_order.clear()

                for pdata in state_data.get("players", []):
                    # Calculate joined_at by subtracting elapsed time from now
                    elapsed_seconds = pdata.get("elapsed_seconds", 0)
                    joined_at = datetime.now() - timedelta(seconds=elapsed_seconds)

                    player = Player(
                        id=pdata["id"],
                        name=pdata["name"],
                        numbers=pdata["numbers"],
                        powerball=pdata["powerball"],
                        tickets=pdata.get("tickets", 0),
                        spent=pdata.get("spent", 0),
                        winnings=pdata.get("winnings", 0),
                        million_plus_wins=pdata.get("million_plus_wins", 0),
                        jackpot_wins=pdata.get("jackpot_wins", 0),
                        joined_at=joined_at,
                        best_white_matches=pdata.get("best_white_matches", 0),
                    )
                    self.players[player.id] = player
                    self.player_order.append(player.id)

                # Auto-start if players exist
                if len(self.players) > 0:
                    self.running = True

                saved_at = state_data.get("saved_at", "unknown")
                print(f"State restored from {filepath} (saved: {saved_at})")
                print(f"  - {len(self.players)} players, {self.total_drawings:,} drawings")
                return True
            except Exception as e:
                print(f"Error loading state: {e}")
                return False


# Global game instance
game = GameState()
