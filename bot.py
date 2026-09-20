import os
import asyncio
import discord

from discord.ext import commands

from database.database import (
    conectar_banco,
    fechar_banco
)


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

        # =================================================
        # BANCO DE DADOS
        # =================================================

        try:

            await conectar_banco()

            print("🐘 PostgreSQL conectado.")

        except Exception as erro:

            print(
                "❌ Erro ao conectar ao banco:"
            )

            print(
                f"{type(erro).__name__}: {erro}"
            )

            raise

        # =================================================
        # COGS
        # =================================================

        extensoes = [
            "cogs.personagem",
            "cogs.admin"
        ]

        for extensao in extensoes:

            try:

                await self.load_extension(
                    extensao
                )

                print(
                    f"✅ {extensao} carregado."
                )

            except Exception as erro:

                print(
                    f"❌ Erro ao carregar "
                    f"{extensao}:"
                )

                print(
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )

                raise

    async def close(self):

        print(
            "🔌 Encerrando Sea's Paradise..."
        )

        try:

            await fechar_banco()

            print(
                "🐘 PostgreSQL desconectado."
            )

        except Exception as erro:

            print(
                "⚠️ Erro ao fechar banco:"
            )

            print(
                f"{type(erro).__name__}: "
                f"{erro}"
            )

        await super().close()


# =========================================================
# INSTÂNCIA
# =========================================================

bot = SeasParadiseBot()


# =========================================================
# COMANDOS BÁSICOS
# =========================================================

@bot.command(name="ping")
async def ping(ctx):

    latencia = round(
        bot.latency * 1000
    )

    await ctx.send(
        f"🏓 Pong! `{latencia}ms`"
    )


@bot.command(name="ajuda")
async def ajuda(ctx):

    embed = discord.Embed(
        title="🏴‍☠️ Sea's Paradise",
        description=(
            "Central de ajuda do Sea's Paradise."
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🏓 !ping",
        value=(
            "Verifica se o bot está "
            "respondendo."
        ),
        inline=False
    )

    embed.add_field(
        name="📜 !ajuda",
        value=(
            "Mostra esta mensagem "
            "de ajuda."
        ),
        inline=False
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print()
    print("=" * 50)
    print("🏴‍☠️ SEA'S PARADISE ONLINE")
    print("=" * 50)

    print(
        f"🤖 Bot: {bot.user}"
    )

    print(
        f"🆔 ID: {bot.user.id}"
    )

    print(
        f"🌊 Servidores: "
        f"{len(bot.guilds)}"
    )

    print(
        f"📜 Comandos carregados: "
        f"{len(bot.commands)}"
    )

    print("=" * 50)
    print()


# =========================================================
# ERROS DE COMANDO
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    # =====================================================
    # COMANDO NÃO EXISTE
    # =====================================================

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    # =====================================================
    # SEM PERMISSÃO
    # =====================================================

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Você não possui permissão "
            "para usar esse comando."
        )

        return

    # =====================================================
    # USUÁRIO NÃO ENCONTRADO
    # =====================================================

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Não encontrei esse usuário."
        )

        return

    # =====================================================
    # ARGUMENTO FALTANDO
    # =====================================================

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Está faltando uma informação "
            "nesse comando."
        )

        return

    # =====================================================
    # ARGUMENTO INVÁLIDO
    # =====================================================

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Alguma informação enviada "
            "nesse comando é inválida."
        )

        return

    # =====================================================
    # ERRO INTERNO DO COMANDO
    # =====================================================

    erro_original = getattr(
        error,
        "original",
        error
    )

    print()
    print("=" * 50)

    print(
        f"❌ ERRO NO COMANDO: "
        f"{ctx.command}"
    )

    print(
        f"Tipo: "
        f"{type(erro_original).__name__}"
    )

    print(
        f"Erro: "
        f"{erro_original}"
    )

    print("=" * 50)
    print()

    await ctx.send(
        "⚠️ Ocorreu um erro interno "
        "ao executar esse comando."
    )


# =========================================================
# INICIAR BOT
# =========================================================

async def main():

    # =====================================================
    # TOKEN
    # =====================================================

    if not TOKEN:

        raise RuntimeError(
            "DISCORD_TOKEN não foi configurado."
        )

    # =====================================================
    # EXECUTAR
    # =====================================================

    async with bot:

        await bot.start(
            TOKEN
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 Sea's Paradise encerrado."
        )
