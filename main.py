import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv
from commands import *
from nextcord import Interaction, SlashOption
from music import Music
import random
import json
import time
import aiohttp
import asyncio

load_dotenv()
API_TOKEN = os.getenv("TOKEN")

guild = nextcord.Guild
client = commands.Bot(intents=nextcord.Intents.all())
music_class: Music = Music(client)


roles_channel_id = 1177321519169421393  # id канала ролей
server_id = 1176560233984831591  # Id сервера
likes_list = [
    1176595296764055684,
    1258849737117925438,
    1177500296918872074,
    1179153688632246282,
    1249123146498445402
]  # Где бот лайкает
protected_chats = [1179153688632246282,
                   1176595296764055684, 1177500296918872074]
voice_settings_id = 1177551237860839444

roles = {"👍": 1176574853894115408, "❤️": 1269355401212727297}

spamblock = {}


class Guild_Spam_Protection:
    def __init__(self, member_id):
        self.member_id = member_id
        self.start_time = time.time()
        self.messages_count = 0


descriptions = [
    "Пора работать!",
    "Created by AndcoolSystems",
    "Я хочу услышать твой голос!",
    "Почему реакций так мало?",
    "А они сдались?",
    "Гайс, ай хэв э бэд ньювс",
    "Чебурашка выкурил весь косячок😢",
    "Мне так и не принесли полотенце!",
    "Пора помыться!",
    "Время автомодерации!",
    "Почему все молчат?",
    "Я НЕ ЛЮБЛЮ КАПС!",
    "ОБЩАТЬСЯ КАПСОМ – НИЗКО",
    "Я не знаю рецепт пороха",
    ":clueless:",
    "Цветастые ники!",
]

voice_channels: dict[int, Voice] = {}


@client.event
async def on_ready():
    await client.change_presence(
        status=nextcord.Status.dnd,
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching, name="телевизор и курит косячок"
        ),
    )
    async with aiohttp.ClientSession("https://discord.com") as session:
        await session.patch(
            f"/api/v9/applications/@me",
            json={"description": random.choice(descriptions)},
            headers={
                "Host": "discord.com",
                "Authorization": "Bot " + os.getenv("TOKEN"),
            },
        )


@client.event
async def on_member_update(before, after):
    # Проверяем изменения в ролях участника
    if before.roles != after.roles:
        added_roles = after.roles

        data = {}
        with open("roles.json") as f:
            data = json.load(f)
            data[str(after.id)] = [role.id for role in added_roles]

        with open("roles.json", "w") as f:
            json.dump(data, f, indent=4)


@client.event
async def on_member_join(member: nextcord.Member):
    data = {}
    with open("roles.json") as f:
        data = json.load(f)

    if str(member.id) in data:
        for role_id in data[str(member.id)]:
            try:
                role = member.guild.get_role(role_id)
                await member.add_roles(role)
            except:
                pass


@client.event
async def on_voice_state_update(member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
    channel = after.channel

    if channel != None:
        if channel.name == '➕Создать канал':
            channel = await channel.clone(name=f"Канал {member.global_name or member.nick or member.name}")
            await member.move_to(channel)
            voice_channels.update({channel.id: Voice(member)})

    if before.channel and not before.channel.members and before.channel.name != '➕Создать канал':
        await before.channel.delete()
        if before.channel.id in voice_channels:
            voice_channels.pop(before.channel.id)

    if before.channel != None:
        if before.channel.id in voice_channels and \
                voice_channels[before.channel.id].admin != None and \
                voice_channels[before.channel.id].admin.id == member.id:
            voice_channels[before.channel.id].admin = None

    voice_state = member.guild.voice_client
    if voice_state is not None and len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


@client.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent):
    if payload.channel_id == roles_channel_id:
        member = payload.member
        server = client.get_guild(payload.guild_id)

        if payload.emoji.name in roles:
            role = server.get_role(roles[payload.emoji.name])
            await member.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload: nextcord.RawReactionActionEvent):
    if payload.channel_id == roles_channel_id:
        member_id = payload.user_id

        server = client.get_guild(payload.guild_id)
        member = server.get_member(member_id)

        if payload.emoji.name in roles:
            role = server.get_role(roles[payload.emoji.name])
            await member.remove_roles(role)


def check_message(message: nextcord.Message):
    return message.attachments == [] and "http" not in message.content


def check_forwarded(message: nextcord.Message):
    for mess in message.snapshots:
        if not check_message(mess):
            return False
    return True


@client.event
async def on_message(message: nextcord.Message):
    if message.author == client.user:
        if message.channel.id in protected_chats:
            await message.delete()
        return

    deleted = False
    if message.channel.id in protected_chats:
        if check_message(message) and check_forwarded(message):
            await message.delete()
            deleted = True

    if message.channel.id in likes_list and not deleted:
        await message.add_reaction("\N{THUMBS UP SIGN}")
        await message.add_reaction("\N{THUMBS DOWN SIGN}")


@client.slash_command(description="Найти в Википедии")
async def wikipedia(interaction: Interaction, promt: str):
    await interaction.response.send_message(wiki_search(promt))


@client.slash_command(description="Идите нахуй", guild_ids=[1213234812458897460])
async def ping(interaction: Interaction, user: nextcord.User, count: int):
    await interaction.response.defer()
    for _ in range(count):
        await interaction.channel.send(f'<@{user.id}>')
        await asyncio.sleep(0.1)


@client.slash_command(description="Настройки голосовых каналов")
async def voice(interaction: Interaction): ...


@voice.subcommand(description="Установить лимит голосового канала (0-99)")
async def limit(interaction: Interaction, amount: int):
    if amount > 99:
        await interaction.response.send_message(
            "**Значение amount должно быть в диапазоне от 0 до 99**\nГде 0 — Нет ограничения",
            ephemeral=True,
        )
        return

    if interaction.channel.name != "voice-settings":
        await interaction.response.send_message(f"Эта команда недоступна в данном канале!", ephemeral=True)
        return

    if interaction.user.voice == None:
        await interaction.response.send_message(f"Вы не подключены ни к одному каналу!", ephemeral=True)
        return

    if voice_channels[interaction.user.voice.channel.id].admin.id != interaction.user.id:
        await interaction.response.send_message(f"Вы не владелец этого канала!", ephemeral=True)
        return

    voice_channel = client.get_channel(interaction.user.voice.channel.id)
    await voice_channel.edit(user_limit=amount)
    await interaction.response.send_message(
        (
            f"Количество пользователей изменено до {amount}"
            if amount != 0
            else "Ограничение пользователей выключено!"
        ),
        ephemeral=True,
    )


@voice.subcommand(description="Стать владельцем голосового канала")
async def claim(interaction: Interaction):

    if interaction.channel.name != "voice-settings":
        await interaction.response.send_message(f"Эта команда недоступна в данном канале!", ephemeral=True)
        return

    if interaction.user.voice == None:
        await interaction.response.send_message(f"Вы не подключены ни к одному каналу!", ephemeral=True)
        return

    if voice_channels[interaction.user.voice.channel.id].admin:
        await interaction.response.send_message(f"У этого канала уже есть владелец!", ephemeral=True)
        return

    voice_id = interaction.user.voice.channel.id

    voice_channels[voice_id].admin = interaction.user
    await interaction.response.send_message("**Вы стали владельцем канала!**", ephemeral=True)

    voice_channel = client.get_channel(voice_id)
    await voice_channel.edit(name=f"Канал {interaction.user.name}")


@client.slash_command(description="Музыкальный бот")
async def music(interaction: Interaction):
    """
    This is the main slash command that will be the prefix of all commands below.
    This will never get called since it has subcommands.
    """


@music.subcommand(description="Добавить музыку в очередь")
async def play(interaction: Interaction, promt: str):
    if not interaction.user.voice:
        await interaction.response.send_message("Вы не подключены ни к одному голосовому каналу!", ephemeral=True)
        return

    await music_class.add_to_query(interaction=interaction, promt=promt)
    await music_class.recursive_play(guild=interaction.guild, user=interaction.user, textchannel=interaction.channel)


@music.subcommand(description="Остановить музыку и очистить очередь")
async def stop(interaction: Interaction):
    if music_class.vp != None:
        await interaction.guild.voice_client.disconnect()

        music_class.query = []
        music_class.vp.stop()

        await interaction.response.send_message("Остановлено!")
    else:
        await interaction.response.send_message("Сейчас ничего не играет!")


@music.subcommand(description="Пропустить текущий трек")
async def skip(interaction: Interaction):
    music_class.vp.stop()
    await music_class.play(guild=interaction.guild, user=interaction.user, textchannel=interaction.channel)
    await interaction.response.send_message("Пропущено!")


@client.slash_command(description="Цвет ника")
async def color(interaction: Interaction):
    # Это основная слеш-команда, отвечающая за /color
    ...


@color.subcommand(description="Изменить цвет")
async def change(interaction: Interaction, hex_color: str):
    # Это слеш-ПОДкоманда у команды /color, отвечающая за /color change
    # hex_color: str выше, это аргумент, который будет запрашивать дс при вводе команды
    roles = [x for x in interaction.user.roles if x.name == "Кастомный цвет"]
    # Получение списка всех цветных ролей человека (по идее должна быть одна, но на всякий)

    hex_color_redacted = hex_color.replace("#", "")  # Жахаем решётку из цвета
    if len(hex_color_redacted) != 6:  # Если цвет состоит не из 6 символов - выходим
        await interaction.response.send_message(f"Некорректный HEX цвет: {hex_color}")
        return

    try:
        r, g, b = (int(hex_color_redacted[x:x + 2], 16) for x in range(0, 6, 2))
        # Проходим по переданному цвету и преобразуем 16 основание в 10
    except:
        # Если что-то пошло не так
        await interaction.response.send_message(f"Некорректный HEX цвет: {hex_color}")
        return

    if roles:  # Если человек уже имеет цветную роль
        # Берём у него самую высокую в списке роль
        color_role = interaction.guild.get_role(roles[-1].id)
        bot_role_pos = (interaction.guild.get_member(client.user.id).roles[-1].position)  # Позиция самой высокой роли бота
        # Присваиваем роли цвет в ргб и позицию на 1 ниже роли бота
        await color_role.edit(color=nextcord.Color.from_rgb(r, g, b), position=bot_role_pos - 1)

        embed = nextcord.Embed(  # Тут просто эмбед
            title=f"Цвет ника изменён на #{hex_color_redacted}",
            color=nextcord.Color.from_rgb(r, g, b),
        )
        # Отправляем сообщение об успешном изменении
        await interaction.response.send_message(embed=embed)

    else:  # Если ролей нет
        role = await interaction.guild.create_role(
            name="Кастомный цвет",
            color=nextcord.Color.from_rgb(r, g, b),
            mentionable=False,
        )  # Создаём роль с цветом и именем
        bot_role_pos = interaction.guild.get_member(
            client.user.id).roles[-1].position  # Позиция самой высокой роли бота
        await role.edit(position=bot_role_pos - 1)
        # Делаем это именно тут, так как после создания роли всё в списке сдвинется, и что бы быть точно уверенным, делаем это тут
        await interaction.user.add_roles(role)  # Добавляем человеку роль

        embed = nextcord.Embed(  # Тоже эмбед
            title=f"Цвет ника изменён на #{hex_color_redacted}",
            color=nextcord.Color.from_rgb(r, g, b),
        )
        await interaction.response.send_message(embed=embed)  # Тоже отправка


@color.subcommand(description="Удалить цвет")
async def delete(interaction: Interaction):
    roles = [x for x in interaction.user.roles if x.name == "Кастомный цвет"]
    if not roles:
        await interaction.response.send_message(f"У вас не установлен цвет ника")
        return

    color_role = interaction.guild.get_role(roles[-1].id)
    await color_role.delete()

    await interaction.response.send_message("Цвет удалён")


options = {}
with open('wfs.json') as f:
    waifus = json.load(f)
    for w_type in waifus:
        for category in waifus[w_type]:
            options[f"{w_type} {category}"] = f"{w_type}-{category}"


@client.slash_command(name='waifu', description='Get waifu from waifu.pics')
async def waifu(
    interaction: Interaction,
    category: str = SlashOption(
        name="category",
        description="Категория",
        choices=options,
    ),
):
    w_type, w_category = category.split('-')
    if w_type == "NSFW" and not interaction.channel.nsfw:
        await interaction.response.send_message('Вы не в NSFW канале!', ephemeral=True)
        return

    url = ''
    async with aiohttp.ClientSession("https://api.waifu.pics") as session:
        async with session.get(f"/{w_type.lower()}/{w_category}") as response:
            if response.status == 200:
                url = (await response.json())['url']

    if not url:
        await interaction.response.send_message('Ошибка при получении изображения!', ephemeral=True)
        return
    await interaction.response.send_message(f"|| {url} ||")


if __name__ == "__main__":
    client.run(API_TOKEN)
