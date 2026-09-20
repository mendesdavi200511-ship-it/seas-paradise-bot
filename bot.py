import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"🏴‍☠️ Seas Paradise conectado como {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Bot online!")


@bot.command()
async def ping(ctx):
    await ctx.send("🏴‍☠️ **Pong! Seas Paradise está online.**")


@bot.command()
async def ajuda(ctx):
    embed = discord.Embed(
        title="🏴‍☠️ Seas Paradise",
        description="Sistema oficial do RP.",
    )

    embed.add_field(
        name="📜 Comandos",
        value=(
            "`!ping` — Testa se o bot está online.\n"
            "`!ajuda` — Mostra os comandos disponíveis."
        ),
        inline=False
    )

    await ctx.send(embed=embed)


if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
