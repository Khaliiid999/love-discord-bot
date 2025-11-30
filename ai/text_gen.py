import os
import re
import disnake
from disnake.ext import commands
from openai import OpenAI  # Perplexity is OpenAI-compatible

# Perplexity client: uses PERPLEXITY_API_KEY and Perplexity base URL
perplexity_client = OpenAI(
    api_key=os.environ.get("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai",
)


class TextGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Persona for Love (no external credits)
        self.system_message = {
            "role": "system",
            "content": (
                "You are Love, a friendly, slightly kawaii Discord AI assistant. "
                "You speak casually, can help with math, coding, engineering, and general questions. "
                "You keep answers safe, respectful, and concise, and you remember small personal details "
                "to make conversations feel more personal."
            ),
        }

    # ===== MEMORY FUNCTIONS =====

    def get_user_memory(self, user_id: int):
        try:
            self.bot.cursor.execute(
                "SELECT name, info FROM user_memory WHERE user_id = ?",
                (user_id,),
            )
            result = self.bot.cursor.fetchone()
            return {"name": result[0], "info": result[1]} if result else {}
        except Exception as e:
            print(f"Error fetching user memory: {e}")
            return {}

    def save_user_memory(self, user_id: int, name: str, info: str):
        try:
            self.bot.cursor.execute(
                """
                INSERT INTO user_memory (user_id, name, info)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET name = ?, info = ?
                """,
                (user_id, name, info, name, info),
            )
            self.bot.conn.commit()
        except Exception as e:
            print(f"Error saving user memory: {e}")

    def delete_user_memory(self, user_id: int):
        try:
            self.bot.cursor.execute(
                "DELETE FROM user_memory WHERE user_id = ?",
                (user_id,),
            )
            self.bot.conn.commit()
        except Exception as e:
            print(f"Error deleting user memory: {e}")

    # ===== CORE: Perplexity CHAT =====

    async def generate_response(
        self,
        channel_id: int,
        user_id: int,
        user_name: str,
        user_message: str,
    ):
        # Channel context
        channel_context = self.bot.channel_conversations.get(
            channel_id, [self.system_message.copy()]
        )

        # User message
        channel_context.append(
            {"role": "user", "content": f"{user_name}: {user_message}"}
        )

        # Personal info extraction
        personal_info = self.extract_personal_info(user_message)
        if personal_info:
            self.save_user_memory(user_id, user_name, personal_info)
            channel_context.append(
                {
                    "role": "system",
                    "content": f"You now know this about {user_name}: {personal_info}.",
                }
            )

        # Existing memory
        user_memory = self.get_user_memory(user_id)
        if user_memory:
            channel_context.append(
                {
                    "role": "system",
                    "content": f"{user_name}'s personal info: {user_memory['info']}.",
                }
            )

        try:
            if not os.environ.get("PERPLEXITY_API_KEY"):
                raise RuntimeError("PERPLEXITY_API_KEY env var is not set.")

            response = perplexity_client.chat.completions.create(
                model="sonar-pro",  # change model here if you want
                messages=channel_context,
                max_tokens=512,
               ειτουργ_temperature=0.7,
            )

            ai_response = (
                response.choices[0].message.content.strip().replace("\
", "
")
            )
        except Exception as e:
            print(f"Error generating response: {e}")
            ai_response = (
                "Sorry, I couldn't generate a response right now. "
                "Please try again later."
            )

        # Save conversation
        channel_context.append({"role": "assistant", "content": ai_response})
        self.bot.channel_conversations[channel_id] = channel_context

        return ai_response

    def extract_personal_info(self, message: str):
        """Extract simple personal info using regex."""
        patterns = {
            "name": re.compile(r"(my name is|i am|call me|I'm) (w+)", re.IGNORECASE),
            "hobby": re.compile(r"(i love|i like|i enjoy) (w+)", re.IGNORECASE),
            "job": re.compile(r"(i work as|i am a|I'm a) (w+)", re.IGNORECASE),
        }

        for key, pattern in patterns.items():
            match = pattern.search(message)
            if match:
                return f"{key}: {match.group(2)}"
        return None

    # ===== COMMANDS =====

    @commands.command(name="textgen")
    async def textgen_text(self, ctx, *, message: str):
        async with ctx.channel.typing():
            response = await self.generate_response(
                ctx.channel.id, ctx.author.id, ctx.author.name, message
            )
        chunks = [response[i : i + 2000] for i in range(0, len(response), 2000)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await ctx.reply(chunk)
            else:
                await ctx.channel.send(chunk)

    @commands.slash_command(
        name="textgen",
        description="Chat with Love, your AI assistant.",
    )
    async def textgen(self, inter: disnake.CommandInteraction, message: str):
        await inter.response.defer()
        response = await self.generate_response(
            inter.channel.id, inter.author.id, inter.author.name, message
        )
        chunks = [response[i : i + 2000] for i in range(0, len(response), 2000)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await inter.followup.send(chunk)
            else:
                await inter.channel.send(chunk)

    @commands.slash_command(
        name="textreset",
        description="Reset the conversation history in this channel.",
    )
    async def reset(self, inter: disnake.CommandInteraction):
        self.bot.channel_conversations.pop(inter.channel_id, None)
        await inter.response.send_message(
            "Conversation history cleared!", ephemeral=False
        )

    @commands.slash_command(
        name="reset_memory",
        description="Reset your stored personal info.",
    )
    async def reset_memory(self, inter: disnake.CommandInteraction):
        self.delete_user_memory(inter.author.id)
        await inter.response.send_message(
            "Your personal information has been reset!", ephemeral=True
        )

    @commands.slash_command(
        name="view_memory",
        description="View your stored personal info.",
    )
    async def view_memory(self, inter: disnake.CommandInteraction):
        user_memory = self.get_user_memory(inter.author.id)
        if user_memory:
            await inter.response.send_message(
                f"Your personal information: {user_memory['info']}",
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                "No personal information saved.",
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            return

        if message.reference and message.reference.resolved:
            referenced_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            if referenced_message.author == self.bot.user:
                async with message.channel.typing():
                    response = await self.generate_response(
                        message.channel.id,
                        message.author.id,
                        message.author.name,
                        message.content,
                    )
                chunks = [
                    response[i : i + 2000] for i in range(0, len(response), 2000)
                ]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await message.reply(chunk)
                    else:
                        await message.channel.send(chunk)


def setup(bot):
    bot.add_cog(TextGen(bot))
