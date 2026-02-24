from typing import List

import glitch.glitch as glit
from PIL import UnidentifiedImageError
import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv
from commands import *
from nextcord import Interaction, SlashOption
import random
import json
import aiohttp
import asyncio
import io
from mi.gen import generate_mi

load_dotenv()
API_TOKEN = os.getenv("TOKEN")

guild = nextcord.Guild
client = commands.Bot(intents=nextcord.Intents.all())

roles_channel_id = 1177321519169421393  # id канала ролей
server_id = 1176560233984831591  # Id сервера
likes_list = [
    1176595296764055684,
    1258849737117925438,
    1177500296918872074,
    1179153688632246282,
    1249123146498445402,
]  # Где бот лайкает
protected_chats = [
    1179153688632246282,
    1176595296764055684,
    1177500296918872074,
    1258849737117925438,
]
roles = {"👍": 1176574853894115408, "❤️": 1269355401212727297}
voice_channels: dict[int, Voice] = {}


@client.event
async def on_ready():
    await client.change_presence(
        status=nextcord.Status.dnd,
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching, name="телевизор и курит косячок"
        ),
    )


@client.event
async def on_member_update(before: nextcord.Member, after: nextcord.Member):
    # Проверяем изменения в ролях участника
    if before.roles != after.roles:
        added_roles = after.roles

        try:
            with open("roles.json", "x") as f:
                f.write("{}")
        except Exception:
            pass

        data = {}
        with open("roles.json") as f:
            data = json.load(f)
            data[str(after.id)] = [role.id for role in added_roles]

        with open("roles.json", "w") as f:
            json.dump(data, f, indent=4)


@client.event
async def on_member_join(member: nextcord.Member):
    try:
        with open("roles.json", "x") as f:
            f.write("{}")
    except Exception:
        pass

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
async def on_member_remove(member: nextcord.Member):
    with open("./res/greetings.json", encoding="utf-8") as f:
        messages: List[str] = json.load(f)

    await member.guild.system_channel.send(
        random.choice(messages).replace("{{NAME}}", member.mention)
    )


@client.event
async def on_voice_state_update(
    member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState
):
    before_channel = before.channel
    after_channel = after.channel
    create_chanel_name = "➕Создать канал"

    if after_channel != None:
        if after_channel.name == create_chanel_name:
            new_channel = await after_channel.clone(
                name=f"Канал {member.global_name or member.nick or member.name}"
            )
            await member.move_to(new_channel)
            voice_channels.update({new_channel.id: Voice(member)})

    if (
        before_channel
        and not before_channel.members
        and before_channel.name != create_chanel_name
    ):

        channels_names = map(lambda x: x.name, before_channel.category.channels)
        if create_chanel_name in channels_names:
            await before_channel.delete()
        if before_channel.id in voice_channels:
            voice_channels.pop(before_channel.id)

    if before_channel != None:
        if (
            before_channel.id in voice_channels
            and voice_channels[before_channel.id].admin != None
            and voice_channels[before_channel.id].admin.id == member.id
        ):
            voice_channels[before_channel.id].admin = None

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


def check_is_forwarded(message: nextcord.Message):
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
        if check_message(message) and check_is_forwarded(message):
            await message.delete()
            deleted = True

    if message.channel.id in likes_list and not deleted:
        emoji = client.get_emoji(1358422026867572908)
        await message.add_reaction(emoji)
        await asyncio.sleep(0.5)
        await message.add_reaction("\N{THUMBS UP SIGN}")
        await asyncio.sleep(0.5)
        await message.add_reaction("\N{THUMBS DOWN SIGN}")


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

    if interaction.user.voice == None:
        await interaction.response.send_message(
            f"Вы не подключены ни к одному каналу!", ephemeral=True
        )
        return

    if (
        voice_channels[interaction.user.voice.channel.id].admin.id
        != interaction.user.id
    ):
        await interaction.response.send_message(
            f"Вы не владелец этого канала!", ephemeral=True
        )
        return

    voice_channel = client.get_channel(interaction.user.voice.channel.id)
    await voice_channel.edit(user_limit=amount)
    await interaction.response.send_message(
        (
            f"Количество пользователей изменено до {amount}"
            if amount != 0
            else "Ограничение пользователей выключено"
        ),
        ephemeral=True,
    )


@voice.subcommand(description="Стать владельцем голосового канала")
async def claim(interaction: Interaction):

    if interaction.user.voice == None:
        await interaction.response.send_message(
            f"Вы не подключены ни к одному каналу!", ephemeral=True
        )
        return

    if voice_channels[interaction.user.voice.channel.id].admin:
        await interaction.response.send_message(
            f"У этого канала уже есть владелец!", ephemeral=True
        )
        return

    voice_id = interaction.user.voice.channel.id

    voice_channels[voice_id].admin = interaction.user
    await interaction.response.send_message(
        "**Вы стали владельцем канала!**", ephemeral=True
    )

    voice_channel = client.get_channel(voice_id)
    await voice_channel.edit(name=f"Канал {interaction.user.name}")


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
        r, g, b = (int(hex_color_redacted[x : x + 2], 16) for x in range(0, 6, 2))
        # Проходим по переданному цвету и преобразуем 16 основание в 10
    except:
        # Если что-то пошло не так
        await interaction.response.send_message(f"Некорректный HEX цвет: {hex_color}")
        return

    if roles:  # Если человек уже имеет цветную роль
        # Берём у него самую высокую в списке роль
        color_role = interaction.guild.get_role(roles[-1].id)
        bot_role_pos = (
            interaction.guild.get_member(client.user.id).roles[-1].position
        )  # Позиция самой высокой роли бота
        # Присваиваем роли цвет в ргб и позицию на 1 ниже роли бота
        await color_role.edit(
            color=nextcord.Color.from_rgb(r, g, b), position=bot_role_pos - 1
        )

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
        bot_role_pos = (
            interaction.guild.get_member(client.user.id).roles[-1].position
        )  # Позиция самой высокой роли бота
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


@client.slash_command(
    name="steal_emoji",
    description="Скопируйте эмоджи с одного сервера на другой! Формат <:name:id>",
)
async def se(
    interaction: Interaction,
    emoji: str,
):
    if not emoji.startswith("<:") or not emoji.endswith(">"):
        await interaction.response.send_message(
            "Неправильный формат эмоджи!", ephemeral=True
        )
        return

    emoji_parts = emoji.replace("<:", "").replace(">", "").split(":")

    if len(emoji_parts) != 2:
        await interaction.response.send_message(
            "Неправильный формат эмоджи!", ephemeral=True
        )
        return

    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_parts[1]}"
    emoji_data = None

    async with aiohttp.ClientSession() as session:
        async with session.get(emoji_url + ".gif") as resp:
            if resp.status == 200:
                emoji_data = await resp.read()

        if not emoji_data:
            async with session.get(emoji_url + ".png") as resp:
                if resp.status == 200:
                    emoji_data = await resp.read()

    if not emoji_data:
        await interaction.response.send_message(
            "Не удалось получить эмоджи! Возможно, указан неверный id", ephemeral=True
        )
        return

    try:
        new_emoji = await interaction.guild.create_custom_emoji(
            name=emoji_parts[0], image=emoji_data
        )
    except Exception:
        await interaction.response.send_message(
            "Не удалось создать эмоджи! Возможно, у бота нет прав на создание эмоджи",
            ephemeral=True,
        )
        return

    embed = nextcord.Embed(
        title="Эмоджи успешно скопировано",
        description=f"Эмоджи {emoji} было успешно перенесено на сервер {interaction.guild.name}",
        color=nextcord.Color.blue(),
    )
    embed.set_author(name=emoji_parts[0], icon_url=new_emoji.url)

    await interaction.response.send_message(embed=embed)


@client.slash_command(name="nextjs", description="Generate Next.Js error badge")
async def mi(
    interaction: Interaction,
    string: str,
):
    if not string:
        await interaction.response.send_message(
            "Строка не может быть пустой!", ephemeral=True
        )
        return

    if len(string) > 200:
        await interaction.response.send_message(
            "Строка слишком длинная", ephemeral=True
        )
        return

    mi = generate_mi(string)
    mi = mi.resize((mi.width // 7, mi.height // 7))
    image_bytes = io.BytesIO()
    mi.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    await interaction.response.send_message(
        "", file=nextcord.File(fp=image_bytes, filename=f"{string}.png")
    )


@client.slash_command(description="Glitch Image")
async def glitch(
    interaction: Interaction,
    attachment: nextcord.Attachment,
    max_offset: int = SlashOption(
        description="Максимальный сдвиг линий", required=False, default=20
    ),
    glitch_lines: int = SlashOption(
        description="Количество линий", required=False, default=30
    ),
):
    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await interaction.response.send_message(
            "Ты че мне скинул, полудурок?", ephemeral=True
        )
        return

    await interaction.response.defer()
    image_bytes = await attachment.read()

    try:
        glitched_image = glit.glitch_image(image_bytes, max_offset, glitch_lines)
    except UnidentifiedImageError:
        await interaction.followup.send(
            "Ты ебанутая, нет? А ниче тот факт что это не то что я прошу?",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        file=nextcord.File(glitched_image, filename="glitched.png")
    )


def run_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start(API_TOKEN))


run_bot()
