# Feed JD Discord Bot

A Discord bot that simulates ownership of a pet in a discord server. Users feed their JDs in the designated feed channel, and the bot tracks feeding history, announces deaths when JDs aren't fed enough, and manages daily check-ins. Each user can adopt and name their very own handsome JD.

## Features

- **Virtual Pet**: Adopt and name your own JD
- **Feeding Mechanics**: Feed your JD daily using the `:feed_jd:` emote
- **Death Detection**: JDs die if not fed for 2+ days; deaths are announced in the feed channel
- **Daily Check-ins**: Automated daily check at 8:00 PM EST to verify JD status
- **DM-based Adoption**: New users are prompted via DM to name their JD to avoid channel clutter
- **Data Storage**: JD data is stored in a JSON file for persistence across restarts
- **Testing Mode**: Built-in testing commands for development and debugging

## Setup

### Prerequisites

- Python 3.9+
- discord.py
- python-dotenv

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jd-velop/feed-jd-discord-bot.git
   cd feed-jd-discord-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your bot token:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

4. Run the bot:
   ```bash
   python FeedJDBot.py
   ```

## Configuration

Edit the constants in `FeedJDBot.py` to customize:

- `FEED_CHANNEL_ID`: The Discord channel where feeding happens
- `DATA_FILE`: JSON file for persisting JD data (default: `jd_data.json`)
- `EMOTE`: The string used to trigger feeding (default: `:feed_jd:`)
- `DEFAULT_NAME`: Name given to JDs if user gives a blank name (default: `JD`)
- `MAX_DAYS_MISSED`: Days before a JD dies (default: `2`)
- `WHEN`: Daily check time in EST (default: `20:00` / 8:00 PM)
- `TESTING_MODE`: Enable debug logging and test commands

## Testing Commands

When `TESTING_MODE` is enabled, the following commands are available to user ID `299680580591943690`:

- `!cleardata`: Clears all JD data and resets the bot

## Data Format

JD data is stored in `jd_data.json` as a JSON object mapping user IDs to JD objects:

```json
{
  "123456789": {
    "name": "JingleDingle",
    "creation_time": "2026-01-17T15:30:00",
    "last_fed": "2026-01-19T20:00:00",
    "total_feedings": 3,
    "dead": false
  }
}
```

## How It Works

1. **Adoption**: User posts the feed emote in the feed channel → bot sends DM prompting for name → user confirms → JD is created
2. **Feeding**: User posts feed emote once per day → bot confirms with ✅ reaction
3. **Death Check**: Daily at 8:00 PM EST, bot checks all JDs → notifies channel of deaths

## License

Unlicensed
