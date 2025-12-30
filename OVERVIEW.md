# Powerball Simulator - Project Overview

## What Is This?

The Powerball Simulator is a party game designed for New Year's Eve (and similar gatherings). It runs on a Raspberry Pi connected to a 7-inch display, allowing guests to "play the lottery" together and watch their money evaporate in real-time.

The core premise is simple: demonstrate how nearly impossible it is to win the Powerball jackpot, even when playing at absurd speeds with multiple people.

## Why Does This Exist?

### The Educational Goal

Everyone knows the lottery is a long shot, but it's hard to *feel* just how long. This simulator makes it visceral:

- Watch drawings happen at 1,000+ per second
- See your "net" balance plummet into the red
- Get excited by the occasional $4 or $7 win
- Realize those small wins don't come close to covering the losses
- Maybe, just maybe, see someone hit a bigger prize ($100, $50,000)
- Almost certainly never see a jackpot

**Real Powerball odds**: 1 in 292,201,338 for the jackpot.

At 1,000 drawings per second, you'd need to run for about 3.4 days on average to hit the jackpot. At the end of a party? Extremely unlikely.

### The Fun Factor

Despite (or because of) the bleakness, it's entertaining:

- Guests join by scanning a QR code on their phones
- Everyone picks their own "lucky numbers" or uses Quick Pick
- Player cards appear on the main display
- You can watch the numbers fly by, tracking who's doing "best" (losing least)
- There's friendly competition even though everyone loses
- The rare possibility of a jackpot adds genuine suspense

If someone *does* hit the jackpot, there's a big celebration screen and the game ends triumphantly. But spoiler: they probably won't.

## How It Works

### The Flow

1. **Idle State**: The display shows a large QR code waiting for players
2. **Players Join**: Scan the QR code, enter your name, pick 5 numbers (1-69) plus a Powerball (1-26)
3. **Game Starts**: Once someone joins, drawings begin automatically
4. **Watch the Carnage**: The display shows:
   - Current winning numbers
   - All player cards with their numbers, matches, spending, and winnings
   - Running totals and time elapsed
5. **Jackpot** (if it ever happens): Celebration screen, game ends, everyone cheers

### Speed Controls

The host can adjust drawing speed via the admin panel:
- 1x = 1 drawing per second (realistic pace)
- 10x, 100x, 1,000x = progressively faster
- 10,000x = absolute chaos mode

Higher speeds mean more tickets "bought" per second, more money lost, and faster demonstration of futility.

### What's Tracked

For each player:
- Tickets bought (total drawings participated in)
- Money spent ($2 per ticket)
- Money won (from matches)
- Net result (almost always very negative)
- Best matches achieved
- Million-dollar near-misses (matching 5 without powerball)
- Time playing

## The Experience

A typical session looks like this:

1. First few minutes: "Ooh, I got $4!" excitement over small wins
2. Next 10 minutes: Realization that small wins are rare and don't cover losses
3. After 30 minutes: Watching net losses climb into thousands, then tens of thousands
4. By end of night: Six-figure "losses" per player, maybe one person hit $100 once

The visual of watching money disappear - even fake money - at high speed is surprisingly effective at communicating why lottery tickets are a bad investment.

## Current State (v1.0)

This is the first fully functional version:

- Runs on Raspberry Pi 5 with 7" display
- All core features working (joining, drawing, tracking, celebration)
- Remote access available via Cloudflare Tunnel (temporary URLs)
- Admin panel for speed control and player management
- Tested and ready for New Year's Eve deployment

### Development Workflow

- Development and testing happen on a local PC
- Deployment is on the Raspberry Pi
- This is intentional - part of the project is learning to work with the Pi
- Changes are made locally, then transferred to the Pi via SCP or USB

## Future Ideas

Things that could be added later:

- **Permanent hosting**: Custom domain or Firebase instead of temporary tunnel URLs
- **Sound effects**: Audio feedback for wins, losses, jackpots
- **Better celebrations**: Confetti animations, sound effects when big wins occur
- **Stats export**: Save session results for posterity
- **History tracking**: Compare across multiple sessions

## Technical Details

See `README.md` for:
- Hardware requirements
- Setup instructions
- Configuration options
- Troubleshooting

This document focuses on the "why" - the README covers the "how."

---

*Built for New Year's Eve 2024. May your numbers never come up.*
