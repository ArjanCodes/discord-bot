import discord
from discord.ext import commands
from typing import Union


class CommandWithDocs(commands.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = kwargs.get("docs")


class CustomHelpCommand(commands.DefaultHelpCommand):
    async def send_command_help(
        self, command: Union[commands.Command, CommandWithDocs]
    ):
        if not hasattr(command, "docs"):
            return await super().send_command_help(command)
        else:
            embed = discord.Embed.from_dict(
                self.transform_to_embed_dict(command.qualified_name, command.docs)
            )
            embed.color = discord.Color.red()

            await self.get_destination().send(embed=embed)

    @staticmethod
    def transform_to_embed_dict(command_name: str, data: dict):
        title = command_name.capitalize() + " command"
        description = (
            f"**Info**\n{data.get('info', 'No information provided')}\n\n"
            f"**Examples**\n{data.get('examples', 'No examples provided')}\n\n"
            f"**Parameters**"
        )
        fields = CustomHelpCommand.extract_embed_fields(
            data.get("parameters", "No parameters provided")
        )
        thumbnail = {"url": data["icon"]}

        return {
            "title": title,
            "description": description,
            "fields": fields,
            "thumbnail": thumbnail,
            "footer": {"text": "[] = optional parameter, <> = required parameter"},
        }

    @staticmethod
    def extract_embed_fields(data: dict):
        return [{"name": k, "value": v, "inline": False} for k, v in data.items()]
