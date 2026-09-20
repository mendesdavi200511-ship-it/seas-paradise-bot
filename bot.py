import os
import discord
import asyncpg
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==========================================
# SEAS PARADISE
# Sistema de RP
# ==========================================

db = None


# ==========================================
# BANCO DE DADOS
# ==========================================

async def conectar_banco():
    global db

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não foi configurado."
        )

    db = await asyncpg.create_pool(DATABASE_URL)

    async with db.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fichas (
                user_id BIGINT PRIMARY KEY,
                nome TEXT NOT NULL,

                raca TEXT NOT NULL DEFAULT 'Não definida',
                faccao TEXT NOT NULL DEFAULT 'Civil',
                profissao TEXT NOT NULL DEFAULT 'Nenhuma',
                classe TEXT NOT NULL DEFAULT 'Nenhuma',

                forca INTEGER NOT NULL DEFAULT 0,
                resistencia INTEGER NOT NULL DEFAULT 0,
                velocidade INTEGER NOT NULL DEFAULT 0,

                berries BIGINT NOT NULL DEFAULT 0,
                reputacao INTEGER NOT NULL DEFAULT 0,

                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    print("🐘 PostgreSQL conectado!")
    print("📦 Tabela de fichas pronta!")


# ==========================================
# INICIALIZAÇÃO
# ==========================================

@bot.event
async def on_ready():

    global db

    if db is None:
        await conectar_banco()

    print(f"🏴‍☠️ Seas Paradise conectado como {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Bot online!")


# ==========================================
# TESTE
# ==========================================

@bot.command()
async def ping(ctx):

    await ctx.send(
        "🏴‍☠️ **Pong! Seas Paradise está online!**"
    )


# ==========================================
# REGISTRAR PERSONAGEM
# ==========================================

@bot.command()
async def registrar(ctx, *, nome=None):

    if nome is None:

        await ctx.send(
            "❌ Informe o nome do personagem.\n"
            "Exemplo: `!registrar Monkey D. Luffy`"
        )

        return

    user_id = ctx.author.id

    personagem = await db.fetchrow(
        """
        SELECT user_id
        FROM fichas
        WHERE user_id = $1
        """,
        user_id
    )

    if personagem:

        await ctx.send(
            "❌ Você já possui um personagem registrado."
        )

        return

    await db.execute(
        """
        INSERT INTO fichas (
            user_id,
            nome
        )
        VALUES ($1, $2)
        """,
        user_id,
        nome
    )

    embed = discord.Embed(
        title="🏴‍☠️ PERSONAGEM REGISTRADO",
        description=(
            f"**{nome}** entrou oficialmente "
            "no mundo de **Sea's Paradise**!"
        )
    )

    embed.add_field(
        name="👤 Jogador",
        value=ctx.author.mention,
        inline=False
    )

    embed.add_field(
        name="📜 Próximo passo",
        value="Use `!ficha` para visualizar seu personagem.",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# VISUALIZAR FICHA
# ==========================================

@bot.command()
async def ficha(ctx, membro: discord.Member = None):

    membro = membro or ctx.author

    personagem = await db.fetchrow(
        """
        SELECT *
        FROM fichas
        WHERE user_id = $1
        """,
        membro.id
    )

    if not personagem:

        await ctx.send(
            f"❌ {membro.mention} ainda não possui personagem.\n"
            "Use `!registrar Nome do Personagem`."
        )

        return

    embed = discord.Embed(
        title=f"🏴‍☠️ {personagem['nome']}",
        description="**Ficha de Personagem — Sea's Paradise**"
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="🌊 Informações",
        value=(
            f"**Raça:** {personagem['raca']}\n"
            f"**Facção:** {personagem['faccao']}\n"
            f"**Profissão:** {personagem['profissao']}\n"
            f"**Classe:** {personagem['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"**Força:** {personagem['forca']:,}\n"
            f"**Resistência:** {personagem['resistencia']:,}\n"
            f"**Velocidade/Agilidade:** "
            f"{personagem['velocidade']:,}"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 Economia",
        value=f"**Berries:** ฿ {personagem['berries']:,}",
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=f"{personagem['reputacao']:,}",
        inline=True
    )

    embed.set_footer(
        text=f"Sea's Paradise • ID do jogador: {membro.id}"
    )

    await ctx.send(embed=embed)


# ==========================================
# AJUDA
# ==========================================

@bot.command()
async def ajuda(ctx):

    embed = discord.Embed(
        title="🏴‍☠️ SEA'S PARADISE",
        description="Sistema oficial do RP"
    )

    embed.add_field(
        name="📜 Personagem",
        value=(
            "`!registrar Nome` — Cria seu personagem\n"
            "`!ficha` — Mostra sua ficha\n"
            "`!ficha @usuário` — Mostra a ficha de outro jogador"
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 Sistema",
        value="`!ping` — Testa se o bot está online",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# INICIAR BOT
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não foi configurado."
    )

bot.run(TOKEN)
