# IMPORTS
import asyncio
import discord
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# CONFIG
intents = discord.Intents.default()
intents.message_content = True
FEED_CHANNEL_ID = 1461853646395408407
DATA_FILE = "jd_data.json"
EMOTE = ":feed_jd:"
DEFAULT_NAME = "JD"
MAX_DAYS_MISSED = 2
TESTING_MODE = False  # Set to True to enable testing commands

# BOT CLASS
class JDBot(discord.Client):
    def __init__(self):
        super().__init__(
            intents=intents,
            help_command=None,
        )
        self.jd_data = self.load_data()

    def load_data(self):
        """Load JD data from JSON file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load {DATA_FILE}: {e}")
                print("Starting with fresh data...")
        else:
            print(f"{DATA_FILE} not found. Starting with fresh data...")
        return {}

    def save_data(self):
        """Save JD data to JSON file"""
        with open(DATA_FILE, 'w') as f:
            json.dump(self.jd_data, f, indent=2)

    def check_jd_status(self, user_id):
        """Check if JD is alive or dead based on feeding history"""
        user_id_str = str(user_id)
        if user_id_str not in self.jd_data:
            return None
        
        jd = self.jd_data[user_id_str]
        if jd['dead'] == True:
            return 'dead'
        
        last_fed = datetime.fromisoformat(jd['last_fed'])
        now = datetime.now()
        days_missed = (now - last_fed).days

        if days_missed >= MAX_DAYS_MISSED:
            jd['dead'] = True
            jd['death_date'] = now.isoformat()
            self.save_data()


            return 'dead'


        return 'alive'

bot = JDBot()

@bot.event
async def on_ready():
    """Event handler for when the bot is ready and connected"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Monitoring channel ID: {FEED_CHANNEL_ID}')

@bot.event
async def on_message(message):
    """Event handler for new messages in the feed channel"""
    if TESTING_MODE:
        print(f"Message from {message.author}: {message.content}")
        # await message.add_reaction('👀')  # React to indicate message was seen

        # allow user id 299680580591943690 to use testing commands
        if message.author.id == 299680580591943690:
            if message.content.startswith('!cleardata'):
                bot.jd_data = {}
                bot.save_data()
                await message.add_reaction('✅')
                return



    if message.channel.id != FEED_CHANNEL_ID or message.author == bot.user:
        return # Ignore messages not in the feed channel or sent by the bot
    
    
    if EMOTE in message.content:
        if TESTING_MODE:
            print(f"{message.author} is attempting to feed their JD.")
        user_id_str = str(message.author.id)

        # Check if JD has been fed today
        jd = bot.jd_data.get(user_id_str)
        if jd and 'last_fed' in jd:
            if TESTING_MODE:
                print(f"JD data found for {message.author}.")
            last_fed = datetime.fromisoformat(jd['last_fed'])
            if last_fed.date() == datetime.now().date():
                return  # JD already fed today

        # If user not in jd_data.json, initialize new JD and prompt user for a name
        if user_id_str not in bot.jd_data:
            # Try to send DM to user for adoption process
            try:
                dm_channel = await message.author.create_dm()
                await dm_channel.send(f"What would you like to name your JD?")

                def check_name(m):
                    return m.author == message.author and isinstance(m.channel, discord.DMChannel)
                
                try:
                    name_msg = await bot.wait_for('message', check=check_name, timeout=60.0)
                    poll_msg = await dm_channel.send(f"Would you like to name your JD '{name_msg.content.strip()}'? (react with ✅ to confirm or ❌ to cancel)")

                    await poll_msg.add_reaction('✅')
                    await poll_msg.add_reaction('❌')

                    def check_reaction(reaction, user):
                        return user == message.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == poll_msg.id
                    reaction, user = await bot.wait_for('reaction_add', check=check_reaction, timeout=60.0)
                    if str(reaction.emoji) == '✅':
                        jd_name = name_msg.content.strip()
                    else:
                        jd_name = DEFAULT_NAME
                    
                    if not jd_name:
                        jd_name = DEFAULT_NAME
                        
                except asyncio.TimeoutError:
                    jd_name = DEFAULT_NAME

                bot.jd_data[user_id_str] = {
                    'name': jd_name,
                    'creation_time': datetime.now().isoformat(),
                    'last_fed': (datetime.now() - timedelta(days=1)).isoformat(), # yesterday to allow immediate feeding
                    'total_feedings': 0,
                    'dead': False,
                }
                # Announce adoption in the feed channel
                await message.channel.send(f"{message.author.mention} has adopted a new JD named '{jd_name}'! Don't fucking forget to feed him.")
                bot.save_data()            
                return
            except discord.Forbidden:
                # User has DMs disabled, fallback to feed channel
                await message.channel.send(f"{message.author.mention}, I couldn't DM you! Please enable DMs from server members to adopt a JD.")
                return
        # User has JD data, check status
        else:
            status = bot.check_jd_status(message.author.id)
            if status == 'dead':
                return # JD is dead, ignore feeding attempts
            elif status == 'alive':
                # Update last fed time and increment total feedings
                jd['last_fed'] = datetime.now().isoformat()
                jd['total_feedings'] += 1
                bot.save_data()
                # react to the message to confirm feeding
                await message.add_reaction('✅')
                return
            else:
                return # No JD dat a, ignore

bot.run(os.getenv('DISCORD_BOT_TOKEN'))