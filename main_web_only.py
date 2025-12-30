#!/usr/bin/env python3
"""
Powerball Simulator - Web Only Mode
Runs just the Flask server without Pygame display.
Perfect for local PC testing.
"""

import threading
import time
import socket
from game_engine import game
from server import run_server


def get_local_ip():
    """Get the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def game_loop():
    """Main game loop - runs drawings without display."""
    last_draw_time = time.time()
    draws_this_second = 0
    
    while True:
        state = game.get_state()
        
        if state["running"] and state["player_count"] > 0:
            current_time = time.time()
            elapsed = current_time - last_draw_time
            
            target_draws = int(elapsed * state["speed"])
            
            if target_draws > draws_this_second:
                draws_to_do = min(target_draws - draws_this_second, state["speed"])
                for _ in range(draws_to_do):
                    game.run_drawing()
                draws_this_second += draws_to_do
            
            if elapsed >= 1.0:
                last_draw_time = current_time
                draws_this_second = 0
        
        time.sleep(0.01)


def main():
    ip = get_local_ip()
    port = 5000
    server_url = f"http://{ip}:{port}"
    admin_url = f"{server_url}/admin"
    
    print("=" * 50)
    print("🎱 POWERBALL SIMULATOR - WEB ONLY MODE")
    print("=" * 50)
    print(f"\n📱 Player URL:  {server_url}")
    print(f"👀 Watch URL:   {server_url}/watch")
    print(f"🔧 Admin URL:   {admin_url}")
    print(f"🔑 Admin Pass:  admin123")
    print("\nNo display window - access via browser only")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    # Start game loop in background thread
    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()
    
    # Run Flask server (blocks)
    run_server(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
