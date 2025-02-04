import yt_dlp
from youtube_search import YoutubeSearch
import nextcord
from nextcord import Interaction


class Music:
    def __init__(self, bot):
        self.query = []
        self.bot: nextcord.Client = bot
        self.vp: nextcord.VoiceChannel = None
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    async def add_to_query(self, promt: str, interaction: Interaction):
        videosSearch = YoutubeSearch(promt, max_results=1).to_dict()
        print(videosSearch)
        result = videosSearch[0]
        finded_url = 'https://www.youtube.com' + result['url_suffix']
        await interaction.response.send_message(f'**Добавлено в конец очереди**\n{result["title"]}\n{finded_url}')

        self.query.append(finded_url)

    async def recursive_play(self, guild: nextcord.Guild, user: nextcord.User, textchannel: nextcord.TextChannel):
        await self.play(guild, user, textchannel)

    async def play(self, guild: nextcord.Guild, user: nextcord.Member, textchannel: nextcord.TextChannel):
        voice = nextcord.utils.get(guild.voice_channels, name=user.voice.channel.name)
        voice_client = nextcord.utils.get(self.bot.voice_clients, guild=guild)

        channel = await self.get_bot_voice_channel(guild.id)
        if not voice_client:
            channel = await voice.connect()
            self.vp = channel
        else:
            if voice.id != channel.id:
                channel = await voice_client.move_to(voice)
                self.vp = channel

        if not voice_client or not voice_client.is_playing():
            if self.query == []:
                text_channel = self.bot.get_channel(textchannel.id)
                await text_channel.send('Очередь закончилась!')
                await voice_client.disconnect()
                return

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                print(ydl)
                info = ydl.extract_info(self.query[0], download=False)

            for x in info['formats']:
                if x['format_id'] == '233':
                    play_url = x['url']
                    break

            vp = self.vp if self.vp else channel
            self.query.pop(0)

            vp.play(nextcord.FFmpegPCMAudio(executable='ffmpeg', source=play_url),
                    after=lambda e: self.play(guild, user, textchannel))

    async def get_bot_voice_channel(self, guild_id: int):
        guild: nextcord.Guild = self.bot.get_guild(guild_id)
        if guild and guild.voice_client:
            return guild.voice_client.channel
        return None
