import datetime
import re
from typing import Dict
import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv
from commands import *
from nextcord import Interaction, SlashOption
from music import Music
import random
import json
from ai.chat import Chat
import aiohttp
import asyncio
import emoji
import io
from mi.gen import generate_mi

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
voice_channels: dict[int, Voice] = {}
chats: Dict[int, Chat] = {}


@client.event
async def on_ready():
    await client.change_presence(
        status=nextcord.Status.dnd,
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching, name="телевизор и курит косячок"
        ),
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

    system_channel = member.guild.system_channel
    message = await Chat(client, system_channel).single_message(
        {
            'role': 'system',
            'content': f'К нашему серверу присоединился новый участник `{member.global_name}`, встреть его теплыми словами'
        }
    )
    await system_channel.send(f'{member.mention} {message}')


@client.event
async def on_member_remove(member: nextcord.Member):
    messages = [
        f"До свидания, {member.mention}",
        f"{member.mention} растворился",
        f"{member.mention} пропал",
        f"{member.mention} завершил процесс",
        f"{member.mention} словил segmentation fault",
        f"{member.mention} отправил SIGTERM самому себе",
        f"{member.mention} выполнил rm -rf / --no-preserve-root",
        f"{member.mention} поймал fatal error и завершился",
        f"{member.mention} завис и был принудительно завершён",
        f"{member.mention} закоммитил своё последнее изменение",
        f"{member.mention} отправился в /dev/null",
        f"{member.mention} выполнил rage quit()",
        f"{member.mention} отключился от сервера",
        f"{member.mention} закрыл последний тег </life>",
        f"{member.mention} не прошёл unit-тесты на выживание",
        f"{member.mention} словил 404: User Not Found",
        f"{member.mention} получил Error 410: Gone",
        f"{member.mention} отключился с кодом 0",
        f"{member.mention} ушёл в офлайн-мод",
        f"{member.mention} откатил себя до предыдущей версии",
        f"{member.mention} поймал BSOD и ушёл в перезагрузку",
        f"{member.mention} сделал git push --force в реальную жизнь",
        f"{member.mention} выполнил exit() без return",
        f"{member.mention} словил NullPointerException",
        f"{member.mention} достиг end of file",
        f"{member.mention} был удалён из базы данных",
        f"{member.mention} отправился на бэкап и не вернулся",
        f"{member.mention} выключил дебаг-режим и исчез",
        f"{member.mention} сбросил соединение",
        f"{member.mention} ушёл в suspend mode",
        f"{member.mention} поставил себя на cronjob раз в никогда",
        f"{member.mention} выполнил kill -9 на своё соединение",
        f"{member.mention} выключил логирование и пропал",
        f"{member.mention} выполнил sudo poweroff",
        f"{member.mention} был закоммичен, но не в этот репозиторий",
        f"{member.mention} нашёл баг в жизни и отвалился",
        f"{member.mention} вызвал undefined behavior и исчез",
        f"{member.mention} словил kernel panic и завис",
        f"{member.mention} запустил fork() без exec() и потерялся",
        f"{member.mention} выполнил git reset --hard и исчез",
        f"{member.mention} скомпилировался с ошибками и не запустился",
        f"{member.mention} обновился и больше не поддерживает этот сервер",
        f"{member.mention} вышел за пределы допустимого массива",
        f"{member.mention} больше не поддерживается текущей версией жизни",
        f"{member.mention} вызвал recursion() без выхода",
        f"{member.mention} достиг предела итераций и завершился",
        f"{member.mention} встретил unexpected token и пропал",
        f"{member.mention} закрыл все вкладки и ушёл",
        f"{member.mention} отключился из-за потери пакетов",
        f"{member.mention} совершил force quit()",
        f"{member.mention} превратился в zombie process",
        f"{member.mention} вызвал delete this и исчез"
    ]

    await member.guild.system_channel.send(random.choice(messages))


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
        emoji = client.get_emoji(1358422026867572908)
        await message.add_reaction(emoji)
        await asyncio.sleep(0.5)
        await message.add_reaction("\N{THUMBS UP SIGN}")
        await asyncio.sleep(0.5)
        await message.add_reaction("\N{THUMBS DOWN SIGN}")

    channel = message.channel
    if isinstance(channel, nextcord.Thread):
        if channel.owner == client.user:
            chat = chats.get(channel.id, Chat(client, channel))

            async with channel.typing():
                reply_mess = ''
                if message.reference:
                    r = await message.channel.fetch_message(message.reference.message_id)
                    reply_mess = f'<Replies to {r.author.global_name}\'s message> '

                response = await chat.message(f'{message.author.global_name}:{message.author.id}:{reply_mess}{message.content or "<attachment>"}')
                max_l = 1999
                for i in range(0, len(response), max_l):
                    if i == 0:
                        await message.reply(response[i:i+max_l])
                    else:
                        await message.channel.send(response[i:i+max_l])


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
        r, g, b = (int(hex_color_redacted[x:x + 2], 16)
                   for x in range(0, 6, 2))
        # Проходим по переданному цвету и преобразуем 16 основание в 10
    except:
        # Если что-то пошло не так
        await interaction.response.send_message(f"Некорректный HEX цвет: {hex_color}")
        return

    if roles:  # Если человек уже имеет цветную роль
        # Берём у него самую высокую в списке роль
        color_role = interaction.guild.get_role(roles[-1].id)
        bot_role_pos = (interaction.guild.get_member(
            client.user.id).roles[-1].position)  # Позиция самой высокой роли бота
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


@client.slash_command(name='mix', description='Mix two emojis')
async def mix(
    interaction: Interaction,
    emoji_1: str,
    emoji_2: str
):
    if emoji_1 not in emoji.EMOJI_DATA:
        await interaction.response.send_message("Первый аргумент не является эмоджи!", ephemeral=True)
        return

    if emoji_2 not in emoji.EMOJI_DATA:
        await interaction.response.send_message("Второй аргумент не является эмоджи!", ephemeral=True)
        return

    await interaction.response.send_message(f"https://emojik.vercel.app/s/{emoji_1}_{emoji_2}?size=48")

EXCLUDED_USERS = {707270170837778432, 472714545723342848,
                  730885117656039466, 1299512869649645634, 1265743807626874890, 1177230100685660170, 280414197706391562}


@client.slash_command(name='steal_emoji', description='Скопируйте эмоджи с одного сервера на другой! Формат <:name:id>')
async def se(
    interaction: Interaction,
    emoji: str,
):
    if not emoji.startswith('<:') or not emoji.endswith('>'):
        await interaction.response.send_message('Неправильный формат эмоджи!', ephemeral=True)
        return

    emoji_parts = emoji.replace('<:', '').replace('>', '').split(':')

    if len(emoji_parts) != 2:
        await interaction.response.send_message('Неправильный формат эмоджи!', ephemeral=True)
        return

    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_parts[1]}"
    emoji_data = None

    async with aiohttp.ClientSession() as session:
        async with session.get(emoji_url + '.gif') as resp:
            if resp.status == 200:
                emoji_data = await resp.read()

        if not emoji_data:
            async with session.get(emoji_url + '.png') as resp:
                if resp.status == 200:
                    emoji_data = await resp.read()

    if not emoji_data:
        await interaction.response.send_message('Не удалось получить эмоджи! Возможно, указан неверный id', ephemeral=True)
        return

    try:
        new_emoji = await interaction.guild.create_custom_emoji(name=emoji_parts[0], image=emoji_data)
    except Exception:
        await interaction.response.send_message('Не удалось создать эмоджи! Возможно, у бота нет прав на создание эмоджи', ephemeral=True)
        return

    embed = nextcord.Embed(
        title="Эмоджи успешно скопировано",
        description=f"Эмоджи {emoji} было успешно перенесено на сервер {interaction.guild.name}",
        color=nextcord.Color.blue()
    )
    embed.set_author(name=emoji_parts[0], icon_url=new_emoji.url)

    await interaction.response.send_message(embed=embed)


@client.slash_command(name='nextjs', description='Generate Next.Js error badge')
async def mi(
    interaction: Interaction,
    string: str,
):
    if not string:
        await interaction.response.send_message('Строка не может быть пустой!', ephemeral=True)
        return

    if len(string) > 200:
        await interaction.response.send_message('Строка слишком длинная', ephemeral=True)
        return

    mi = generate_mi(string)
    mi = mi.resize((mi.width // 7, mi.height // 7))
    image_bytes = io.BytesIO()
    mi.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    await interaction.response.send_message("", file=nextcord.File(fp=image_bytes, filename=f"{string}.png"))


@client.slash_command(description="DeepSeek")
async def ai(interaction: Interaction): ...


@ai.subcommand(description="Deletes current chat")
async def delete(interaction: Interaction):

    channel = interaction.channel
    if not isinstance(channel, nextcord.Thread):
        await interaction.send('**[ERROR]**: Это не ветка!')
        return

    if channel.owner != client.user:
        await interaction.send('**[ERROR]**: Эта ветка не принадлежит боту!')
        return

    chat = chats.get(interaction.channel.id, Chat(client, channel))
    try:
        chat.end_chat()
    except Exception as e:
        await interaction.send(f'**[ERROR]**: Не удалось удалить историю: {e}!')
        return
    await channel.delete()


@ai.subcommand(description="Start conversation")
async def start(
    interaction: Interaction,
    instructions: str = SlashOption(
        description="Системная инструкция боту (перезаписывает стандартную)",
        required=False,
        default=''
    ),
    is_private: bool = SlashOption(
        description="Создавать приватную ветку?",
        required=False,
        default=False
    )
):
    embed = nextcord.Embed(title="Новый чат создан")
    embed.set_author(name=interaction.user.global_name,
                     icon_url=interaction.user.avatar.url)

    embed.add_field(name="Instructions",
                    value=instructions or "Default",
                    inline=False)

    embed.add_field(name="Is private",
                    value=is_private,
                    inline=False)

    await interaction.send(embed=embed, ephemeral=is_private)
    thread = await interaction.channel.create_thread(
        name="「AI」Conversation",
        type=nextcord.ChannelType.private_thread if is_private else nextcord.ChannelType.public_thread
    )
    await thread.add_user(interaction.user)

    chats[thread.id] = Chat(client, thread)
    chat = chats.get(thread.id)

    async with thread.typing():
        chat.start_chat(
            base_instruction=f"Ты – искусственный интеллект на дискорд сервере, который называется {interaction.guild.name}. " +
            "В своих ответах можешь использовать Markdown. Тебя зовут Гена. Поддерживай диалог в любом случае.",
            instructions=instructions
        )
    response = await chat.message(f'{interaction.user.global_name}:{interaction.user.id}:Привет!')
    await thread.send(response)


def run_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start(API_TOKEN))


run_bot()
