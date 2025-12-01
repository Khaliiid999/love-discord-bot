import os
import re
import disnake
import requests
from disnake.ext import commands


PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


class TextGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.system_message = {
            "role": "system",
            "content": (
                "Konnichiwa! I'm Love, your kawaii Discord AI assistant. "
                "I'm helpful with math, coding, and engineering problems, and I answer concisely. "
                "Use a cute, friendly style with emoticons like ^~^, x3, :3 and X) when appropriate."
            ),
        }

    def get_user_memory(self, user_id: int):
