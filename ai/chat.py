import json
import os
import aiohttp
import nextcord
from nextcord.ext import commands
from typing import List
import openai
from ai.parsers import build_tool
from fuzzywuzzy import process


class Chat:
    def __init__(self, bot: commands.Bot, thread: nextcord.Thread):
        """Init chat"""

        self.bot = bot
        self.thread = thread
        self.history_path = f'./ai/chats/{self.thread.id}.json'
        self.client = openai.AsyncOpenAI(
            api_key=os.environ.get("OAI"),
            base_url=os.environ.get("OAI_PROXY")
        )
        self.tools = [
            change_chat_name,
            get_server_channels,
            read_messages, save_data,
            get_data, get_user_info,
            get_server_users, get_server_emotes,
            get_emote_description, get_all_emote_descriptions
        ]

    def _read(self) -> List[dict]:
        """Read chat history from file"""

        data = []
        try:
            with open(self.history_path, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self._write([])

        return data

    def _read_instructions(self) -> List[dict]:
        """Read instructions from file"""

        data = {}
        with open('./ai/instructions.json', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def _write(self, data):
        """Write chat history to file"""

        with open(self.history_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))

    def start_chat(self, base_instruction: str, instructions: str):
        """Start new chat"""

        data = self._read()
        system_instructions = self._read_instructions()

        for instruction in system_instructions:
            data.append(
                {
                    'role': 'system',
                    'content': instruction['instruction']
                }
            )

        data.append(
            {
                'role': 'system',
                'content': base_instruction
            }
        )
        if instructions:
            data.append(
                {
                    'role': 'system',
                    'content': instructions
                }
            )

        self._write(data)

    def get_tool(self, name: str):
        """Get tool by name"""

        for tool in self.tools:
            if tool.__name__ == name:
                return tool
        return None

    async def single_message(self, message: dict) -> str:
        response_json = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[message],
        )
        return response_json.choices[0].message.content

    async def message(self, message: str | None = None, deep: int = 1, history: list | None = None):
        if deep > 5:
            return f'Max recursion depth reached: {deep}'

        if history is None:
            history = self._read()

        if message:
            history.append({
                "role": "user",
                "content": message
            })

        self._write(history)

        response_json = await self.client.chat.completions.create(
            model="gpt-4",
            messages=history,
            tools=[build_tool(t) for t in self.tools],
            tool_choice="auto"
        )

        response = response_json.choices[0].message
        if response.tool_calls:
            history.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": call.type,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    } for call in response.tool_calls
                ],
                "content": None
            })

            for call in response.tool_calls:
                try:
                    print(
                        f"Calling tool: {call.function.name} with args {call.function.arguments}")
                    tool_fn = self.get_tool(call.function.name)
                    args = json.loads(call.function.arguments)
                    result = str(await tool_fn(self, **args))

                    history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result
                    })

                except Exception as e:
                    print(f"Error calling tool {call.function.name}: {e}")
                    history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": f"Error calling tool: {e}"
                    })

            self._write(history)
            return await self.message(None, deep + 1, history)

        history.append({
            "role": "assistant",
            "content": response.content
        })

        self._write(history)
        return response.content

    def end_chat(self):
        os.remove(self.history_path)


async def change_chat_name(chat: Chat, name: str):
    """
        Changes current chat name. Max name length - 50 symbols

        Args:
            name (string): The chat name

        Returns:
            None

    """
    await chat.thread.edit(name=f'「AI」{name[:50]}')


async def get_server_channels(chat: Chat):
    """
        Return to you list of channels in current discord server
        You can send link to channel by sending it's name without formatting

        Args:
            -

        Returns:
            list: List names of server channels

    """
    channels = []
    for channel in chat.thread.guild.channels:
        if channel.type == nextcord.ChannelType.category:
            continue
        topic = 'Channel'
        try:
            topic = channel.topic
        except:
            ...

        channels.append(
            f'#{channel.name}({channel.type}): {topic}'
        )
    return channels


async def save_data(chat: Chat, data: str):
    """
        Save some data globally

        Args:
            data (string): Data to save

        Returns:
            None

    """
    with open('memory.txt', 'a', encoding='utf-8') as f:
        f.write(data + '\n')


async def get_data(chat: Chat):
    """
        Get all globally saved data between chats

        Args:
            -

        Returns:
            str - All saved data

    """

    with open('memory.txt', 'r', encoding='utf-8') as f:
        return f.read()


async def read_messages(chat: Chat, chat_name: str, count: int):
    """
        Read last `count` messages from the specified chat

        Args:
            chat_name (string): Name of the target chat
            count (integer): Count of messages to read. 0 < count < 50
    """
    _channel = None
    for channel in chat.thread.guild.channels:
        if chat_name.replace('#', '') == channel.name:
            _channel = channel

    if not _channel:
        raise Exception('Channel not found')

    return list(reversed([
        f'{message.author.global_name}:{message.author.id}:{message.content}'
        for message in await _channel.history(limit=min(max(count, 0), 50)).flatten()
    ]))


async def get_user_info(chat: Chat, id: str):
    """
    Get info about user: name, name on server, id, bio

    Args:
        id (string): User id

    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=f'https://discord.com/api/v9/users/{id}/profile?guild_id={chat.thread.guild.id}',
            headers={
                'Authorization': f'{os.environ.get("USER_TOKEN")}'
            }
        ) as resp:
            if resp.status != 200:
                raise Exception(
                    'Could not get data about user! User not found')

            response: dict = await resp.json()
            user: dict = response.get('user', {})
            global_name: str = user.get('global_name', '')
            return {
                "id": id,
                "bio": user.get('bio', ''),
                "global_name": global_name,
                "server_name": response.get('guild_member', {}).get('nick', global_name),
                "pronouns": response.get('user_profile', {}).get('pronouns', '')
            }


async def get_server_users(chat: Chat):
    """
    Get list of server's members

    Args:
        -

    """

    return [f'{member.global_name}:{member.id}' async for member in chat.thread.guild.fetch_members(limit=50)]


async def get_server_emotes(chat: Chat):
    """
    Get list of server's emotes

    Args:
        -

    """
    emojis = []
    for emoji in chat.thread.guild.emojis:
        e: nextcord.Emoji = emoji
        emojis.append({
            "id": e.id,
            "name": e.name,
        })
    return emojis


async def get_emote_description(chat: Chat, name: str):
    """
    Get emote description by name

    Args:
        name (string): Name of emote

    """

    with open('./ai/emotes_description.json') as f:
        emotes: dict = json.load(f)

    result, accuracy = process.extractOne(name.lower(), list(emotes.keys()))
    if accuracy <= 60:
        raise Exception('Emote not found')

    emote: dict = emotes[result]
    return {
        "id": emote.get('id'),
        "name": result,
        "name_accuracy": accuracy,
        "description": emote.get('description', '')
    }


async def get_all_emote_descriptions(chat: Chat):
    """
    Get all emotes descriptions

    Args:
        -

    """

    with open('./ai/emotes_description.json') as f:
        emotes: dict = json.load(f)

    return [{
        "id": emotes.get(emote, {}).get('id', ''),
        "name": emote,
        "description": emotes.get(emote, {}).get('description', '')
    } for emote in emotes]
