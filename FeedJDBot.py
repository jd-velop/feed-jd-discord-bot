# IMPORTS
import asyncio
import json
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import random

import discord
from dotenv import load_dotenv

load_dotenv()

INTENTS = discord.Intents.default()
INTENTS.message_content = True

# --- Config -----------------------------------------------------
FEED_CHANNEL_ID = int(os.getenv("FEED_CHANNEL_ID"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
DATA_FILE = "jd_data.json"
EMOTE = ":feed_jd:"
DEFAULT_NAME = "JD"
MAX_DAYS_MISSED = 3
TESTING_MODE = True
EST = ZoneInfo("America/New_York")
WHEN = time(hour=20, tzinfo=EST)  # 8:00 PM EST


class JDBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=INTENTS, help_command=None)
        self.jd_data = self.load_data()

    # --- Bot -----------------------------------------------------
    async def setup_hook(self) -> None:
        """Start background jobs once the bot is ready."""
        self.loop.create_task(self.background_job()) # self.background_job() is an async function

    async def on_ready(self) -> None:
        print(f"{self.user} has connected to Discord!")
        print(f"Monitoring channel ID: {FEED_CHANNEL_ID}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        if TESTING_MODE:
            print(f"Message from {message.author}: {message.content}")

        # Admin commands
        if message.author.id == ADMIN_USER_ID and message.content.startswith("!"):
            await self.handle_admin_command(message)
            return

        if message.channel.id != FEED_CHANNEL_ID:
            return

        if EMOTE not in message.content:
            return

        await self.handle_feed(message)

    # --- Data ---------------------------------------------------
    def load_data(self) -> dict:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as file:
                    content = file.read().strip()
                if content:
                    return json.loads(content)
            except (json.JSONDecodeError, Exception) as err:
                print(f"Warning: Could not load {DATA_FILE}: {err}")
                print("Starting with fresh data...")
        else:
            print(f"{DATA_FILE} not found. Starting with fresh data...")
        return {}

    def save_data(self) -> None:
        with open(DATA_FILE, "w") as file:
            json.dump(self.jd_data, file, indent=2)

    # --- Utilities -----------------------------------------------------
    @staticmethod
    def user_key(user_id: int) -> str:
        return str(user_id)

    @staticmethod
    def iso(dt: datetime) -> str:
        return dt.isoformat()

    def now(self) -> datetime:
        return datetime.now(EST)

    # --- JD state ------------------------------------------------------
    def check_jd_status(self, user_id: int) -> str | None:
        user_id_str = self.user_key(user_id)
        jd = self.jd_data.get(user_id_str)
        if not jd:
            return None

        if jd.get("dead"):
            return "dead"

        last_fed = datetime.fromisoformat(jd["last_fed"])
        days_missed = (self.now() - last_fed).days
        if days_missed >= MAX_DAYS_MISSED:
            jd["dead"] = True
            jd["death_date"] = self.iso(self.now())
            self.save_data()
            return "dead"

        return "alive"

    def record_feeding(self, jd: dict) -> None:
        jd["last_fed"] = self.iso(self.now())
        jd["total_feedings"] = jd.get("total_feedings", 0) + 1
        self.save_data()

    def get_random_cause(self) -> str:
        causes = [
            "Neglect",
            "Starvation",
            "Lack of attention",
            "Emotional abandonment",
            "Failure to provide daily sustenance",
            "Chronic underfeeding",
            "Prolonged hunger",
            "Tried to eat cleaning supplies under the sink",
            "Malnutrition",
            "Ignoring basic needs",
            "Underdose",
        ]
        return random.choice(causes)
    
    # ---- User commands ------------------------------------------------
    async def handle_user_command(self, message: discord.Message) -> None:
        command = message.content.split()[0].lower()[1:] # Skip the "!" prefix
        args = message.content.split()[1:]

        if len(args) > 0:
            await message.channel.send("Too many arguments provided.")
            return
        
        if command == "help":
            help_text = (
                "**User Commands:**\n"
                "- `!help` Show this help message\n"
                "- `!status` Check your JD status\n"
                "- `!listall` List all JDs\n"
                "- `!nextcheck` Show time until next daily check\n"
                "- `!stats` Display bot usage stats\n"
            )
            await message.channel.send(help_text)

        else:
            await message.channel.send(f"Unknown command: {command}. Type `!help` for a list of commands.")

    # --- Admin commands ------------------------------------------------
    async def handle_admin_command(self, message: discord.Message) -> None:
        """Handle admin debugging commands."""
        global TESTING_MODE
        command = message.content.split()[0].lower()[1:] # Skip the "!" prefix
        args = message.content.split()[1:]

        if command == "help":
            help_text = (
                "**Admin Commands:**\n"
                "- `!help` Show this help message\n"
                "- `!checkuser <user_id>` Check JD status for a user\n"
                "- `!cleardata` Clear all JD data\n"
                "- `!forcedaily` Force a daily JD check\n"
                "- `!listall` List all JDs\n"
                "- `!nextcheck` Show time until next daily check\n"
                "- `!rename <user_id> <new_name>` Rename a user's JD\n"
                "- `!revive <user_id>` Revive a dead JD\n"
                "- `!setfed <user_id> <days_ago>` Set last fed date for a JD\n"
                "- `!stats` Display bot usage stats\n"
                "- `!testmode <on|off>` Toggle testing mode\n"
            )
            await message.channel.send(help_text)

        elif command == "checkuser":
            if len(args) != 1:
                await message.channel.send("Usage: `!checkuser <user_id>`")
                return

            user_id_str = args[0].strip("<>@!")
            jd = self.jd_data.get(user_id_str)
            if jd:
                status = self.check_jd_status(int(user_id_str))
                last_fed = datetime.fromisoformat(jd["last_fed"])
                days_since = (self.now() - last_fed).days

                response = (f"**JD Info for <@{user_id_str}>:**\n"
                f"Name: {jd['name']}\n"
                f"Status: {status}\n"
                f"Last fed: {last_fed.strftime('%Y-%m-%d %H:%M:%S')} ({days_since} days ago)\n"
                f"Total feedings: {jd.get('total_feedings', 0)}\n"
                f"Created: {jd.get('creation_time', 'Unknown')}\n"
                )
                await message.channel.send(response)
            else:
                await message.channel.send(f"No JD found for user ID {user_id_str}.")

        elif command == "cleardata":
            self.jd_data = {}
            self.save_data()
            await message.channel.send("All data cleared.")

        elif command == "forcedaily":
            await self.daily_jd_check()
            await message.channel.send("Forced daily JD check.")

        elif command == "listall":
            response = "**JDs:**\n"
            for user_id_str, jd in self.jd_data.items():
                status = self.check_jd_status(int(user_id_str))
                last_fed = datetime.fromisoformat(jd["last_fed"]).strftime("%Y-%m-%d")
                response += f"<@{user_id_str}>: {jd['name']} ({status}) - Last fed: {last_fed} - Feedings: {jd.get('total_feedings')}\n"
            await message.channel.send(response)

        elif command == "nextcheck":
            now = self.now()
            target_time = datetime.combine(now.date(), WHEN)
            if now >= target_time:
                target_time += timedelta(days=1) # if past today's check time, go to next day
            delta = target_time - now
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            await message.channel.send(f"Next daily check in `{hours}h {minutes}m {seconds}s`.")

        elif command == "rename":
            if len(args) != 2:
                await message.channel.send("Usage: `!rename <user_id> <new_name>`")
                return
            user_id_str = args[0]
            new_name = args[1]
            jd = self.jd_data.get(user_id_str)
            if jd:
                old_name = jd["name"]
                jd["name"] = new_name
                self.save_data()
                await message.channel.send(f"Renamed JD from '{old_name}' to '{new_name}'.")
            else:
                await message.channel.send(f"No JD found for user ID {user_id_str}.")

        elif command == "revive":
            if len(args) != 1:
                await message.channel.send("Usage: `!revive <user_id>`")
                return
            user_id_str = args[0]
            jd = self.jd_data.get(user_id_str)
            if jd:
                if jd.get("dead"): # if jd is dead
                    jd["dead"] = False
                    jd["last_fed"] = self.iso(self.now() - timedelta(days=1))  # allow immediate feeding
                    jd.pop("death_date", None) # None so that it doesn't error if key not present
                    jd.pop("death_notified", None) 
                    jd.pop("cause_of_death", None)
                    self.save_data()
                    await message.channel.send(f"Revived {jd['name']}.")

        elif command == "setfed":
            if len(args) != 2:
                await message.channel.send("Usage: `!setfed <user_id> <days_ago>`")
                return
            user_id_str = args[0]
            try:
                days_ago = int(args[1])
            except ValueError:
                await message.channel.send("arg 2 <days_ago> must be a number.")
                return

            jd = self.jd_data.get(user_id_str)
            if jd:
                jd["last_fed"] = self.iso(self.now() - timedelta(days=days_ago))
                self.save_data()
                await message.channel.send(f"Set {jd['name']}'s last fed time to {days_ago} days ago.")
            else:
                await message.channel.send("No JD found for that user")
                return
            
        elif command == "stats":
            total_jds = len(self.jd_data)
            alive = sum(1 for uid, jd in self.jd_data.items() if self.check_jd_status(int(uid)) == "alive")
            dead = sum(1 for uid, jd in self.jd_data.items() if self.check_jd_status(int(uid)) == "dead")
            total_feedings = sum(jd.get("total_feedings", 0) for jd in self.jd_data.values())

            response = (
                f"Total JDs: {total_jds}\n"
                f"Alive: {alive}\n"
                f"Dead: {dead}\n"
                f"Total feedings: {total_feedings}\n"
                f"Testing mode: {'ON' if TESTING_MODE else 'OFF'}\n"
            )
            await message.channel.send(response)


        elif command == "testmode":
            if len(args) != 1 or args[0].lower() not in ["on", "off"]:
                await message.channel.send("Usage: `!testmode <on|off>`")
                return
            TESTING_MODE = args[0].lower() == "on"
            await message.channel.send(f"Testing mode set to {TESTING_MODE}.")

        else:
            await message.channel.send(f"Unknown command: {command}. Type `!help` for a list of commands.")

    # --- Message handling ---------------------------------------------
    async def handle_feed(self, message: discord.Message) -> None:
        user_id_str = self.user_key(message.author.id)
        jd = self.jd_data.get(user_id_str)

        if jd:
            status = self.check_jd_status(message.author.id)
            if status == "dead":
                return # cannot feed a dead JD :(
            
            if datetime.fromisoformat(jd["last_fed"]).date() == self.now().date():
                return  # already fed today

            self.record_feeding(jd)
            await message.add_reaction("✅")
            return

        await self.start_adoption_flow(message)

    async def start_adoption_flow(self, message: discord.Message) -> None:
        await message.author.send(f"{message.author.mention}, what would you like to name your JD?")

        def check_name(dm_message: discord.Message) -> bool:
            return dm_message.author == message.author and dm_message.channel == message.author.dm_channel

        try:
            name_msg = await self.wait_for("message", check=check_name, timeout=60.0)
            proposed_name = name_msg.content.strip()
            await message.author.send(
                f"Would you like to name your JD '{proposed_name}'? (reply with 'yes' or 'no')"
            )

            def check_confirmation(dm_message: discord.Message) -> bool:
                return (
                    dm_message.author == message.author
                    and dm_message.channel == message.author.dm_channel
                    and dm_message.content.lower() in ["yes", "no"]
                )

            try:
                reaction_msg = await self.wait_for("message", check=check_confirmation, timeout=60.0)
                if reaction_msg.content.lower() == "yes":
                    jd_name = proposed_name or DEFAULT_NAME
                elif reaction_msg.content.lower() == "no":
                    return await self.start_adoption_flow(message)
            except asyncio.TimeoutError:
                return
        except asyncio.TimeoutError:
            return

        user_id_str = self.user_key(message.author.id)
        self.jd_data[user_id_str] = {
            "name": jd_name,
            "creation_time": self.iso(self.now()),
            "last_fed": self.iso(self.now() - timedelta(days=1)),  # allow immediate feeding
            "total_feedings": 0,
            "dead": False,
        }
        self.save_data()
        await message.channel.send(
            f"{message.author.mention} has adopted a new JD named '{jd_name}'! Don't forget to feed him! {EMOTE}"
        )

    # --- Daily checks --------------------------------------------------
    async def daily_jd_check(self) -> None:
        await self.wait_until_ready()
        feed_channel = self.get_channel(FEED_CHANNEL_ID)
        if not feed_channel:
            print("Feed channel not found; skipping daily check.")
            return

        for user_id_str, jd in self.jd_data.items():
            status = self.check_jd_status(int(user_id_str))
            if status == "dead" and "death_notified" not in jd:
                death_date = datetime.fromisoformat(jd["death_date"]).strftime("%Y-%m-%d")
                jd_name = jd["name"]
                cause = self.get_random_cause()
                await feed_channel.send(
                    f"<@{user_id_str}> Your poor, innocent JD, {jd_name}, has died. \nDate of death: {death_date}. \nCause of death: {cause}."
                    )
                jd["death_notified"] = True
                jd["cause_of_death"] = cause
                self.save_data()

    async def background_job(self) -> None:
        while True:
            now = self.now()
            target_time = datetime.combine(now.date(), WHEN)
            if now >= target_time:
                target_time += timedelta(days=1)

            seconds_until_target = (target_time - now).total_seconds()
            await asyncio.sleep(max(seconds_until_target, 0))
            await self.daily_jd_check()


def main() -> None:
    bot = JDBot()
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    main()