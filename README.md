# Feed JD Discord Bot

A Discord bot that simulates ownership of a 'pet' in a discord text channel. Users adopt and feed their JDs in a dedicated channel; the bot tracks feedings, calls out neglect, and announces death if a JD is ignored for too long.

## Features
- Adopt and name your own JD via DM prompt
- Feed daily using the `:feed_jd:` emote; bot confirms with a ✅ reaction
- Death detection after 2+ missed days, with death announcements
- Automated daily check at 8:00 PM EST (America/New_York)
- DM adoption flow keeps the text channel clean
- JSON JD data storage for persistence across restarts
- Admin/debug commands for live troubleshooting

## Prerequisites
- Python 3.9+
- `discord.py`
- `python-dotenv`

## Installation
```bash
git clone https://github.com/jd-velop/feed-jd-discord-bot.git
cd feed-jd-discord-bot
pip install -r requirements.txt
```

## Configuration (.env)
Rename and refactor `example.env` to `.env` in the project root with:
```
DISCORD_BOT_TOKEN=your_bot_token
FEED_CHANNEL_ID=123456789012345678   # channel where feeding happens
ADMIN_USER_ID=123456789012345678    # user allowed to run admin commands
```

## Running
```bash
python FeedJDBot.py
```

## Admin Commands (ADMIN_USER_ID only)

- `!help` Show commands
- `!checkuser <user_id>` Check JD status for a user
- `!cleardata` Clear all JD data
- `!forcedaily` Force a daily JD check
- `!listall` List all JDs
- `!nextcheck` Show time until next daily check
- `!rename <user_id> <new_name>` Rename a user's JD
- `!revive <user_id>` Revive a dead JD
- `!setfed <user_id> <days_ago>` Set last fed date for a JD
- `!stats` Display bot usage stats
- `!testmode <on|off>` Toggle testing mode

## Data Format
Stored in `jd_data.json` mapping Discord user IDs to JD objects:
```json
{
   "123456789": {
      "name": "JingleDingle",
      "creation_time": "2026-01-17T15:30:00-05:00",
      "last_fed": "2026-01-19T20:00:00-05:00",
      "total_feedings": 3,
      "dead": false
   }
}
```

## How It Works
1. User posts `:feed_jd:` in the feed channel → bot DMs for a name → JD is created after confirmation.
2. Daily feeding: posting `:feed_jd:` marks JD fed for that day and reacts ✅.
3. Daily at 8:00 PM EST, the bot checks for neglected JDs and announces deaths.

## Notes
- Timezone: America/New_York (EST/EDT handled by `zoneinfo`).
- Persistence: JSON file `jd_data.json` in the repo root.
