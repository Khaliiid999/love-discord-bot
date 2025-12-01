import disnake
from disnake.ext import commands
import requests


class Joke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def getJoke(self):
        result = requests.get("https://v2.jokeapi.dev/joke/Any").json()

        # Two-part joke
        if result.get("type") == "twopart":
            setup = result.get("setup", "Here is a joke:")
            delivery = result.get("delivery", "")
            return f"> {setup}
- {delivery}"

        # Single-part joke
        joke = result.get("joke", "I tried to tell a joke, but the API was shy.")
        return f"> {joke}"

    @commands.command(name="joke")
    async def joke_command(self, ctx):
        text = self.getJoke()
        await ctx.send(text)

    @commands.slash_command(name="joke", description="Send a hilarious joke lol")
    async def joke_slash(self, inter: disnake.CommandInteraction):
        text = self.getJoke()
        await inter.response.send_message(text)


def setup(bot):
    bot.add_cog(Joke(bot))
