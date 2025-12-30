#!/usr/bin/env python3
"""
Powerball Simulator - Main Entry Point
Runs both the Pygame display and Flask server in parallel.
"""

import threading
import time
import socket
import os
from game_engine import game
from display import Display
from server import run_server

def get_local_ip():
    """Get the Pi's local IP address for QR code generation."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def game_loop(display):
    """Main game loop - runs drawings and updates display."""
    last_draw_time = time.time()
    draws_this_second = 0
    
    while True:
        state = game.get_state()
        
        # Run drawings based on speed setting
        if state["running"] and state["player_count"] > 0:
            current_time = time.time()
            elapsed = current_time - last_draw_time
            
            # Calculate how many draws we should do
            target_draws = int(elapsed * state["speed"])
            
            if target_draws > draws_this_second:
                # Batch draws for high speeds
                draws_to_do = min(target_draws - draws_this_second, state["speed"])
                for _ in range(draws_to_do):
                    game.run_drawing()
                draws_this_second += draws_to_do
            
            # Reset counter each second
            if elapsed >= 1.0:
                last_draw_time = current_time
                draws_this_second = 0
        
        # Update display (always runs at ~30fps)
        if not display.update(game.get_state()):
            break
        
        # Small sleep to prevent CPU spinning
        time.sleep(0.01)


def main():
    # Determine server URL
    ip = get_local_ip()
    port = 5000
    server_url = f"http://{ip}:{port}"
    admin_url = f"{server_url}/admin"
    
    print("=" * 50)
    print("🎱 POWERBALL SIMULATOR")
    print("=" * 50)
    print(f"\n📱 Player URL: {server_url}")
    print(f"🔧 Admin URL:  {admin_url}")
    print(f"🔑 Admin Pass: admin123")
    print("\nPress ESC on the display to exit")
    print("=" * 50)
    
    # Start Flask server in background thread
    server_thread = threading.Thread(
        target=run_server,
        kwargs={"host": "0.0.0.0", "port": port},
        daemon=True
    )
    server_thread.start()
    
    # Give server a moment to start
    time.sleep(1)
    
    # Initialize display
    display = Display(server_url)
    
    try:
        game_loop(display)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        display.quit()


if __name__ == "__main__":
    main()
