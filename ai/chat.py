import json
import re
import g4f
from g4f.client import AsyncClient
import nextcord
from nextcord.ext import commands
from typing import List

from ai.parsers import build_tool


class Chat:
    def __init__(self, bot: commands.Bot, thread: nextcord.Thread):
        """Init chat"""

        self.bot = bot
        self.thread = thread
        self.model = g4f.models.deepseek_v3
        self.history_path = f'./ai/chats/{self.thread.id}.json'
        self.client = AsyncClient(
            provider=self.model.best_provider
        )
        self.tools = [reprocess, greet, change_chat_name,
                      get_server_channels, read_messages, save_data, get_data]

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

    def start_chat(self, instructions: str):
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

        tools = '\n\n'.join(map(build_tool, self.tools))
        data.append(
            {
                'role': 'system',
                'content': tools
            }
        )

        data.append(
            {
                'role': 'system',
                'content': instructions
            }
        )
        self._write(data)

    def parse_message(self, message: str):
        print(message)
        function_pattern = r'<call function="(\S+)"(?: args=(?:"({[^}]*})"|({[^}]*})))?\s*/>'
        functions = []
        matches = re.findall(function_pattern, message.replace("'", '"'))

        for func_name, quoted_args, raw_args in matches:
            args_str = quoted_args or raw_args
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}
            functions.append({
                "function_name": func_name,
                "args": args
            })

        text = re.sub(function_pattern, '', message.replace("'", '"')).strip()
        pattern = r'Started thinking\.\.\..*?Done in .*?s\.'
        cleaned = re.sub(pattern, '', text, flags=re.DOTALL).strip()
        return cleaned, functions

    def get_tool(self, name: str):
        """Get tool by name"""

        for tool in self.tools:
            if tool.__name__ == name:
                return tool
        return None

    async def message(self, message: str, depth: int = 0):
        if depth > 2:
            return message

        history = self._read()
        history.append({
            'role': 'user',
            'content': message
        })
        self._write(history)

        response_json = await self.client.chat.completions.create(
            messages=history,
            model=self.model.name
        )

        content = response_json.choices[0].message.content
        text, tools = self.parse_message(content)

        _tools_results = {}
        for tool in tools:
            try:
                print(f'calling {tool}')
                name = tool['function_name']
                _tool = self.get_tool(name)
                if not _tool:
                    _tools_results[name] = 'Function not found'

                _tools_results[name] = str(await _tool(self, **tool['args']))
            except Exception as e:
                _tools_results[name] = str(e)
                print(f'Cannot call tool {tool}: {e}')

        history.append({
            'role': 'assistant',
            'content': text
        })

        if any([x != 'None' for x in _tools_results.values()]):
            return await self.message(str(_tools_results), depth=depth + 1)
        elif _tools_results:
            history.append({
                'role': 'user',
                'content': str(_tools_results)
            })

        self._write(history)
        return text


async def greet(chat: Chat, user: str):
    """
        Greet user by name

        Args:
            user (string): The user name to greet

        Returns:
            None

    """
    print(f'Greet, {user}')


async def change_chat_name(chat: Chat, name: str):
    """
        Changes current chat name. Max name length - 50 symbols

        Args:
            name (string): The chat name

        Returns:
            None

    """
    await chat.thread.edit(name=f'[AI] {name[:50]}')


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


async def save_data(chat: Chat, user: str, data: str):
    """
        Save some data globally

        Args:
            user (str): User id, whom the data to save
            data (str): Data to save

        Returns:
            None

    """
    d = {}
    try:
        with open('memory.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}

    if user not in d:
        d[user] = []
    d[user].append(data)

    with open('memory.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


async def get_data(chat: Chat, user: str):
    """
        Get all globally saved data between chats

        Args:
            user (str): User id, whom the data to read

        Returns:
            str - All saved data

    """

    with open('memory.json', 'r', encoding='utf-8') as f:
        return json.load(f).get(user, [])
    return []


async def read_messages(chat: Chat, chat_name: str):
    """
        Read last 10 messages from the specified chat

        Args:
            chat_name (str): Name of the target chat

        Returns:
            list: List names of latest 10 messages

    """
    _channel = None
    for channel in chat.thread.guild.channels:
        if chat_name.replace('#', '') == channel.name:
            _channel = channel

    if not _channel:
        raise Exception('Channel not found')

    return list(reversed([message.content for message in await _channel.history(limit=10).flatten()]))


async def reprocess(chat: Chat):
    """
        Send back a message with the results of calling other functions

        Args:
            -

        Returns:
            Other function call results

    """
    ...
