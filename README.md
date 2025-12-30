# Powerball Simulator

A New Year's Eve party game that demonstrates how unlikely you are to win the lottery. Players scan a QR code, pick their numbers, and watch as the Pi continuously "buys tickets" for them - tracking their losses (and very occasional small wins) in real-time.

## Hardware Requirements

- Raspberry Pi 5
- 7" display (800x480 or 1024x600)
- MicroSD card (16GB+)
- Power supplies for Pi and monitor
- HDMI cable (mini or micro depending on your Pi)
- WiFi network (Pi and phones must be on same network)

Optional:
- Heatsink or case with cooling (for extended operation)
- Speaker (if you want audio feedback - not implemented yet)

## Internet Access (Remote Players)

To let people join from outside your local network (different WiFi, mobile data, etc.), use Cloudflare Tunnel. It's free and works behind any router without port forwarding.

### One-Time Setup

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

### Run with Tunnel

Instead of just `python main.py`, run with the tunnel script:

```bash
./run_with_tunnel.sh
```

This will:
1. Start the Powerball simulator
2. Create a temporary public URL (like `https://random-words.trycloudflare.com`)
3. Print that URL - share it with remote players!

The QR code on the display will still show the local URL. For remote players, share the tunnel URL separately (text it to them, etc.).

### Tunnel URL Changes

Each time you restart, you get a new random URL. For a permanent URL, you'd need a Cloudflare account and domain, but for a party the temporary URL works great.

## Quick Start

### 1. Transfer Files to Pi

From your computer, copy the entire `powerball_simulator` folder to your Pi:

```bash
# Option A: SCP (replace pi@raspberrypi.local with your Pi's address)
scp -r powerball_simulator/ pi@raspberrypi.local:~/

# Option B: USB drive, copy the folder, then move to home directory
```

### 2. Run Setup

SSH into your Pi or open a terminal:

```bash
cd ~/powerball_simulator
chmod +x setup.sh
./setup.sh
```

This installs all dependencies and creates a virtual environment.

### 3. Run the Simulator

```bash
cd ~/powerball_simulator
source venv/bin/activate
python main.py
```

The display will show a QR code. The terminal will print the URLs:
- **Player URL**: `http://192.168.x.x:5000` - guests scan this
- **Admin URL**: `http://192.168.x.x:5000/admin` - your control panel
- **Admin Password**: `admin123` (change in `server.py` if you want)

## How It Works

1. **Idle State**: Display shows large QR code, waiting for players
2. **Player Joins**: Scan QR, enter name, pick numbers (or Quick Pick)
3. **Game Running**: Pi draws winning numbers every second (configurable)
4. **Display Updates**: Shows all players' tickets, spending, winnings, and match status
5. **Jackpot**: If someone hits all 6 numbers, celebration screen (extremely rare!)

## Admin Panel Features

Access via `http://[pi-ip]:5000/admin`

- **Speed Control**: 1x, 10x, 100x, 500x, 1000x drawings per second
- **Player Management**: Remove individual players
- **Reset Game**: Clear everything and start fresh

## Display Layout

With players active, the screen shows:
- Header: Title, drawing counter, speed indicator
- Small QR code in corner (so more players can still join)
- Current winning numbers (animated ball display)
- Player cards (up to 4 visible, scrolls if 5-8 players):
  - Name and their numbers
  - Match indicators (green/red dots)
  - Ticket count, money spent, winnings, net
  - Time playing
  - $1M+ near-wins counter

## Auto-Start on Boot (Optional)

Create a systemd service to run automatically:

```bash
sudo nano /etc/systemd/system/powerball.service
```

Paste this content:

```ini
[Unit]
Description=Powerball Simulator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/powerball_simulator
ExecStart=/home/pi/powerball_simulator/venv/bin/python main.py
Restart=always
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl enable powerball.service
sudo systemctl start powerball.service
```

Now it runs on every boot.

## Customization

### Change Admin Password
Edit `server.py`, line ~15:
```python
ADMIN_PASSWORD = "your_new_password"
```

### Change Jackpot Amount
Edit `game_engine.py`, line ~13:
```python
(5, True): 500_000_000,  # Change this value
```

### Adjust Display Resolution
Edit `display.py`, lines ~13-14:
```python
SCREEN_WIDTH = 800   # or 1024
SCREEN_HEIGHT = 480  # or 600
```

## Troubleshooting

**Display not showing?**
- Make sure DISPLAY=:0 is set if running via SSH
- Try: `export DISPLAY=:0` before running

**Can't connect from phone?**
- Verify Pi and phone are on same WiFi network
- Check Pi's IP: `hostname -I`
- Make sure port 5000 isn't blocked by firewall

**Pygame errors?**
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall pygame: `pip install --force-reinstall pygame`

**Performance issues?**
- Reduce speed setting
- Add a heatsink if CPU is throttling
- Check with: `vcgencmd measure_temp`

## Technical Notes

- **Odds**: Real Powerball jackpot odds are 1 in 292,201,338
- **At 1 draw/second**: ~9.26 years average to win jackpot
- **At 1000 draws/second**: ~3.4 days average
- **$2 per ticket**: Most players will accumulate significant "losses" quickly

The whole point is to viscerally demonstrate why lottery tickets are a bad investment!

## License

Do whatever you want with this. It's a party game.
