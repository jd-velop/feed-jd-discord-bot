import discord
from datetime import datetime, timedelta
import asyncio

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

    elif command == "status":
        user_id_str = self.user_key(message.author.id)
        jd = self.jd_data.get(user_id_str)
        if jd:
            status = self.check_jd_status(message.author.id)
            last_fed = datetime.fromisoformat(jd["last_fed"])
            days_since = (self.now() - last_fed).days

            response = (f"**Your JD Info:**\n"
            f"Name: {jd['name']}\n"
            f"Status: {status}\n"
            f"Last fed: {last_fed.strftime('%Y-%m-%d %H:%M:%S')} ({days_since} days ago)\n"
            f"Total feedings: {jd.get('total_feedings', 0)}\n"
            f"Created: {jd.get('creation_time', 'Unknown')}\n"
            )
            await message.channel.send(response)
        else:
            await message.channel.send("You do not have a JD yet. Adopt one using the emote.")

    elif command == "listall":
        response = "**JDs:**\n"
        for user_id_str, jd in self.jd_data.items():
            status = self.check_jd_status(int(user_id_str))
            last_fed = datetime.fromisoformat(jd["last_fed"]).strftime("%Y-%m-%d")
            response += f"<@{user_id_str}>: {jd['name']} ({status}) - Last fed: {last_fed} - Feedings: {jd.get('total_feedings')}\n"
        await message.channel.send(response)
    
    elif command == "nextcheck":
        now = self.now()
        target_time = datetime.combine(now.date(), self.when)
        if now >= target_time:
            target_time += timedelta(days=1) # if past today's check time, go to next day
        delta = target_time - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        await message.channel.send(f"Next daily check in `{hours}h {minutes}m {seconds}s`.")

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
        )
        await message.channel.send(response)

    else:
        await message.channel.send(f"Unknown command: {command}. Type `!help` for a list of commands.")

# --- Admin commands ------------------------------------------------
async def handle_admin_command(self, message: discord.Message) -> None:
    """Handle admin debugging commands."""
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
        await message.channel.send("This will clear all JD data in the database. Proceed? (yes/no).")

        def check_confirmation(dm_message: discord.Message) -> bool:
            return (
                dm_message.author == message.author
                and dm_message.content.lower() in ["yes", "no"]
            )

        try:
            reaction_msg = await self.wait_for("message", check=check_confirmation, timeout=60.0)
            if reaction_msg.content.lower() == "yes":
                self.jd_data = {}
                self.save_data()
                await message.channel.send("All data cleared.")
                return
            elif reaction_msg.content.lower() == "no":
                await message.channel.send("Data deletion cancelled.")
                return
        except asyncio.TimeoutError:
            return

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
        target_time = datetime.combine(now.date(), self.when)
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
            f"Testing mode: {'ON' if self.testing_mode else 'OFF'}\n"
        )
        await message.channel.send(response)


    elif command == "testmode":
        if len(args) != 1 or args[0].lower() not in ["on", "off"]:
            await message.channel.send("Usage: `!testmode <on|off>`")
            return
        self.testing_mode = args[0].lower() == "on"
        await message.channel.send(f"Testing mode set to {self.testing_mode}.")

    else:
        await message.channel.send(f"Unknown command: {command}. Type `!help` for a list of commands.")
