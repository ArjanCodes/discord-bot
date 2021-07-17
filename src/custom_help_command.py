import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    async def send_command_help(self, command):
        if command.help is None:
            return await super().send_command_help(command)
        else:
            embed = discord.Embed.from_dict(
                self.transform_to_embed_dict(command.qualified_name, command.help)
            )
            embed.color = discord.Color.red()

            await self.get_destination().send(embed=embed)

    @staticmethod
    def transform_to_embed_dict(command_name: str, data: dict):
        title = command_name.capitalize() + " command"
        description = (
            f"**Info**\n{data['info']}\n\n"
            f"**Examples**\n{data['examples']}\n\n"
            f"**Parameters**"
        )
        fields = CustomHelpCommand.extract_embed_fields(data["parameters"])
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
