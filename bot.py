import os
import asyncio
import discord
from discord.ext import commands

from database.database import conectar_banco, fechar_banco


TOKEN = os.getenv("DISCORD_TOKEN")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# =========================================================
# BOT
# =========================================================

class SeasParadiseBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):

        print("⚙️ Iniciando Sea's Paradise...")

        # Banco de dados
        await conectar_banco()

        # Cogs
        extensoes = [
    "cogs.personagem",
    "cogs.admin",
        ]

        for extensao in extensoes:
            try:
                await self.load_extension(extensao)
                print(f"✅ {extensao} carregado.")
            except Exception as erro:
                print(f"❌ Erro ao carregar {extensao}: {erro}")
                raise

    async def close(self):
        await fechar_banco()
        await super().close()


bot = SeasParadiseBot()


# =========================================================
# ONLINE
# =========================================================

@bot.event
async def on_ready():

    print("=" * 45)
    print("🏴‍☠️ SEA'S PARADISE ONLINE")
    print(f"🤖 Bot: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌊 Servidores: {len(bot.guilds)}")
    print("=" * 45)


# =========================================================
# ERROS DE COMANDO
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Você não possui permissão para usar esse comando."
        )
        return

    if isinstance(error, commands.MemberNotFound):
        await ctx.send(
            "❌ Não encontrei esse usuário."
        )
        return

    print(
        f"❌ Erro no comando "
        f"{ctx.command}: {type(error).__name__}: {error}"
    )


# =========================================================
# INICIAR
# =========================================================

async def main():

    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN não foi configurado."
        )

    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
