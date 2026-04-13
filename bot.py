import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# ====================== TOKEN ======================
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("❌ ERREUR : Token non trouvé !")
    print("Crée un fichier .env avec DISCORD_TOKEN=ton_token")
    exit()
# =================================================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.title = data.get('title', 'Titre inconnu')
        self.webpage_url = data.get('webpage_url') or data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
        }

        data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data, volume=volume)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, guild):
        if guild.id not in self.players:
            self.players[guild.id] = {'queue': [], 'volume': 0.5, 'current_source': None, 'text_channel': None}
        return self.players[guild.id]

    async def play_next(self, guild):
        player = self.get_player(guild)
        if not player['queue']:
            return
        query = player['queue'].pop(0)
        vc = guild.voice_client
        if not vc or not vc.is_connected():
            return

        try:
            source = await YTDLSource.from_url(query, loop=self.bot.loop, volume=player['volume'])
            player['current_source'] = source

            def after(error):
                asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)

            vc.play(source, after=after)

            embed = discord.Embed(title="🎵 En cours", description=f"**{source.title}**", color=0x22c55e, url=source.webpage_url)
            if player['text_channel']:
                await player['text_channel'].send(embed=embed)
        except Exception as e:
            print(e)
            await self.play_next(guild)

    @app_commands.command(name="play", description="Joue une musique (YouTube / Spotify / SoundCloud)")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Tu dois être dans un salon vocal !", ephemeral=True)
            return

        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.user.voice.channel

        if not guild.voice_client:
            await channel.connect()
        else:
            if guild.voice_client.channel != channel:
                await guild.voice_client.move_to(channel)

        player = self.get_player(guild)
        player['queue'].append(query)
        player['text_channel'] = interaction.channel

        await interaction.followup.send(f"✅ Ajouté : {query}")

        if not guild.voice_client.is_playing() and not guild.voice_client.is_paused():
            await self.play_next(guild)

    @app_commands.command(name="dashboard", description="Affiche les boutons de contrôle")
    async def dashboard(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎵 MusicBot Dashboard", description="Utilise les boutons ou ouvre dashboard.html", color=0x22c55e)
        view = MusicControlView(self, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view)


class MusicControlView(discord.ui.View):
    def __init__(self, cog, guild):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild = guild

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Pausé", ephemeral=True)

    @discord.ui.button(label="▶️ Reprendre", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Repris", ephemeral=True)

    @discord.ui.button(label="🔊 +", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.get_player(self.guild)
        player['volume'] = min(1.0, player['volume'] + 0.1)
        if player.get('current_source'):
            player['current_source'].volume = player['volume']
        await interaction.response.send_message(f"Volume : {int(player['volume']*100)}%", ephemeral=True)

    @discord.ui.button(label="🔉 -", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.get_player(self.guild)
        player['volume'] = max(0.0, player['volume'] - 0.1)
        if player.get('current_source'):
            player['current_source'].volume = player['volume']
        await interaction.response.send_message(f"Volume : {int(player['volume']*100)}%", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.danger)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
            await self.cog.play_next(self.guild)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} est connecté !")
    await bot.tree.sync()
    print("Slash commands synchronisés")


if __name__ == "__main__":
    bot.add_cog(Music(bot))
    bot.run(TOKEN)
