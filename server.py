"""
Powerball Simulator - Web Server
Flask + SocketIO server for player registration and admin controls.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from game_engine import game, WHITE_BALL_MAX, POWERBALL_MAX

app = Flask(__name__)
app.config['SECRET_KEY'] = 'powerball-party-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Admin password (simple, this is a party game)
ADMIN_PASSWORD = "admin123"


@app.route('/')
def player_page():
    """Main player registration page."""
    return render_template('player.html', 
                          white_max=WHITE_BALL_MAX, 
                          pb_max=POWERBALL_MAX)


@app.route('/watch')
def watch_page():
    """Remote viewing page for watching your stats."""
    return render_template('watch.html')


@app.route('/admin')
def admin_page():
    """Admin control panel."""
    return render_template('admin.html')


@app.route('/api/join', methods=['POST'])
def join_game():
    """API endpoint for joining the game."""
    data = request.json
    name = data.get('name', '').strip()
    numbers = data.get('numbers', [])
    powerball = data.get('powerball')
    
    if not name:
        return jsonify({"success": False, "error": "Name is required"})
    
    try:
        numbers = [int(n) for n in numbers]
        powerball = int(powerball)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid number format"})
    
    success, result = game.add_player(name, numbers, powerball)
    
    if success:
        # Notify all clients of new player
        socketio.emit('player_joined', {"name": name})
        return jsonify({"success": True, "player_id": result})
    else:
        return jsonify({"success": False, "error": result})


@app.route('/api/quickpick', methods=['GET'])
def quick_pick():
    """Generate quick pick numbers."""
    whites, pb = game.quick_pick()
    return jsonify({"numbers": whites, "powerball": pb})


@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current game state."""
    return jsonify(game.get_state())


@app.route('/api/admin/remove', methods=['POST'])
def admin_remove_player():
    """Remove a player (admin only)."""
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "Invalid password"})
    
    player_id = data.get('player_id')
    if game.remove_player(player_id):
        socketio.emit('player_removed', {"player_id": player_id})
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Player not found"})


@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    """Reset the entire game (admin only)."""
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "Invalid password"})
    
    game.reset_game()
    socketio.emit('game_reset', {})
    return jsonify({"success": True})


@app.route('/api/admin/speed', methods=['POST'])
def admin_set_speed():
    """Set game speed (admin only)."""
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "Invalid password"})
    
    speed = data.get('speed', 1)
    game.set_speed(speed)
    socketio.emit('speed_changed', {"speed": speed})
    return jsonify({"success": True, "speed": speed})


@app.route('/api/admin/resume', methods=['POST'])
def admin_resume():
    """Resume game after jackpot (admin only)."""
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "Invalid password"})
    
    game.resume_after_jackpot()
    socketio.emit('game_resumed', {})
    return jsonify({"success": True})


@socketio.on('connect')
def handle_connect():
    """Handle new socket connection."""
    emit('state_update', game.get_state())


def run_server(host='0.0.0.0', port=5000):
    """Start the Flask server."""
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_server()
