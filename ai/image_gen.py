import os
import disnake
import requests
from disnake.ext import commandsPERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")class ImageGen(commands.Cog):
def init(self, bot):
self.bot = bot

async def generate_response(self, text: str) -> str:
    if not PERPLEXITY_API_KEY:
        return "API key is missing. Please set PERPLEXITY_API_KEY in the bot host."

    try:
        url = "https://api.perplexity.ai/images"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "prompt": text,
            "size": "1024x1024",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        image_url = data["data"]["url"]
        return image_url
    except Exception as e:
        print(f"Error generating image: {e}")
        return "Sorry, I couldn't generate an image right now."

@commands.command(name="imagegen")
async def imagegen_text(self, ctx, *, message: str):
    async with ctx.channel.typing():
        response = await self.generate_response(message)
        await ctx.reply(response)

@commands.slash_command(name="imagegen", description="generate images :3")
async def imagegen(self, inter: disnake.CommandInteraction, message: str):
    await inter.response.defer()
    response = await self.generate_response(message)
    await inter.followup.send(response)
