import os
import discord
import asyncpg
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

db = None

# Criações que ainda não foram confirmadas
criando = {}

ATRIBUTO_MAXIMO = 50000
PONTOS_INICIAIS = 100


# =========================================================
# BANCO DE DADOS
# =========================================================

async def conectar_banco():
    global db

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não foi configurado.")

    db = await asyncpg.create_pool(DATABASE_URL)

    async with db.acquire() as conn:

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fichas (
                user_id BIGINT PRIMARY KEY,
                nome TEXT NOT NULL,

                raca TEXT NOT NULL DEFAULT 'Não definida',
                familia TEXT NOT NULL DEFAULT 'Não definida',
                faccao TEXT NOT NULL DEFAULT 'Civil',
                profissao TEXT NOT NULL DEFAULT 'Nenhuma',
                classe TEXT NOT NULL DEFAULT 'Nenhuma',

                forca INTEGER NOT NULL DEFAULT 0,
                resistencia INTEGER NOT NULL DEFAULT 0,
                velocidade INTEGER NOT NULL DEFAULT 0,
                pontos_atributo INTEGER NOT NULL DEFAULT 0,

                berries BIGINT NOT NULL DEFAULT 0,
                reputacao INTEGER NOT NULL DEFAULT 0,

                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migrações caso a tabela já exista
        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS familia TEXT
            NOT NULL DEFAULT 'Não definida';
        """)

        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS pontos_atributo INTEGER
            NOT NULL DEFAULT 0;
        """)

    print("🐘 PostgreSQL conectado!")
    print("📦 Banco do Sea's Paradise pronto!")


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():
    global db

    if db is None:
        await conectar_banco()

    print(f"🏴‍☠️ Seas Paradise conectado como {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Bot online!")


# =========================================================
# FUNÇÕES
# =========================================================

async def possui_ficha(user_id):
    personagem = await db.fetchrow(
        "SELECT user_id FROM fichas WHERE user_id = $1",
        user_id
    )

    return personagem is not None


def novo_rascunho():
    return {
        "nome": None,
        "raca": "Não definida",
        "familia": "Não definida",
        "faccao": "Civil",
        "profissao": "Nenhuma",
        "classe": "Nenhuma",

        "forca": 0,
        "resistencia": 0,
        "velocidade": 0,
        "pontos": PONTOS_INICIAIS
    }


def criar_embed_criacao(usuario):
    dados = criando[usuario.id]

    embed = discord.Embed(
        title="🏴‍☠️ CRIAÇÃO DE PERSONAGEM",
        description=(
            "Monte seu personagem para entrar no mundo de "
            "**Sea's Paradise**.\n\n"
            "As escolhas bloqueadas serão liberadas conforme "
            "adicionarmos o catálogo oficial do RP."
        )
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Nome:** {dados['nome'] or 'Não definido'}\n"
            f"**Raça:** {dados['raca']}\n"
            f"**Família:** {dados['familia']}"
        ),
        inline=False
    )

    embed.add_field(
        name="🌊 Caminho",
        value=(
            f"**Facção:** {dados['faccao']}\n"
            f"**Profissão:** {dados['profissao']}\n"
            f"**Classe:** {dados['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** {dados['forca']:,}\n"
            f"🛡️ **Resistência:** {dados['resistencia']:,}\n"
            f"💨 **Velocidade/Agilidade:** {dados['velocidade']:,}\n\n"
            f"✨ **Pontos disponíveis:** {dados['pontos']:,}"
        ),
        inline=False
    )

    embed.set_footer(
        text="Sea's Paradise • Criação de Personagem"
    )

    return embed


# =========================================================
# MODAL DE NOME
# =========================================================

class NomeModal(discord.ui.Modal, title="Nome do Personagem"):

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Ex: Monkey D. Luffy",
        min_length=2,
        max_length=40
    )

    async def on_submit(self, interaction):
        if interaction.user.id not in criando:
            await interaction.response.send_message(
                "❌ Sua criação não está mais ativa. Use `!criar`.",
                ephemeral=True
            )
            return

        criando[interaction.user.id]["nome"] = self.nome.value.strip()

        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=CriacaoView(interaction.user.id)
        )


# =========================================================
# FACÇÃO
# =========================================================

class FaccaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label="Pirata",
                emoji="🏴‍☠️",
                description="Navegue pelos mares sob sua própria bandeira."
            ),
            discord.SelectOption(
                label="Marinha",
                emoji="⚓",
                description="Faça parte das forças da Marinha."
            ),
            discord.SelectOption(
                label="Revolucionário",
                emoji="🔥",
                description="Integre o Exército Revolucionário."
            ),
            discord.SelectOption(
                label="Civil",
                emoji="🏝️",
                description="Comece sua jornada como civil."
            )
        ]

        super().__init__(
            placeholder="Escolha sua facção...",
            options=opcoes
        )

    async def callback(self, interaction):

        user_id = interaction.user.id

        if user_id not in criando:
            await interaction.response.send_message(
                "❌ Sua criação não está mais ativa.",
                ephemeral=True
            )
            return

        criando[user_id]["faccao"] = self.values[0]

        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=CriacaoView(user_id)
        )


class FaccaoView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=120)
        self.dono_id = dono_id
        self.add_item(FaccaoSelect())

    async def interaction_check(self, interaction):
        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse menu pertence a outro jogador.",
                ephemeral=True
            )
            return False

        return True


# =========================================================
# ATRIBUTOS
# =========================================================

class AtributosView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=180)
        self.dono_id = dono_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esses atributos pertencem a outro jogador.",
                ephemeral=True
            )
            return False

        return True

    async def atualizar(self, interaction):
        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=AtributosView(self.dono_id)
        )

    def adicionar(self, user_id, atributo, quantidade=1):
        dados = criando[user_id]

        if dados["pontos"] < quantidade:
            return False

        if dados[atributo] + quantidade > ATRIBUTO_MAXIMO:
            return False

        dados[atributo] += quantidade
        dados["pontos"] -= quantidade

        return True

    def remover(self, user_id, atributo, quantidade=1):
        dados = criando[user_id]

        if dados[atributo] < quantidade:
            return False

        dados[atributo] -= quantidade
        dados["pontos"] += quantidade

        return True

    @discord.ui.button(
        label="+ Força",
        emoji="💪",
        style=discord.ButtonStyle.primary
    )
    async def mais_forca(self, interaction, button):
        self.adicionar(
            interaction.user.id,
            "forca"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="- Força",
        style=discord.ButtonStyle.secondary
    )
    async def menos_forca(self, interaction, button):
        self.remover(
            interaction.user.id,
            "forca"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="+ Resistência",
        emoji="🛡️",
        style=discord.ButtonStyle.primary
    )
    async def mais_resistencia(self, interaction, button):
        self.adicionar(
            interaction.user.id,
            "resistencia"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="- Resistência",
        style=discord.ButtonStyle.secondary
    )
    async def menos_resistencia(self, interaction, button):
        self.remover(
            interaction.user.id,
            "resistencia"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="+ Velocidade",
        emoji="💨",
        style=discord.ButtonStyle.primary
    )
    async def mais_velocidade(self, interaction, button):
        self.adicionar(
            interaction.user.id,
            "velocidade"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="- Velocidade",
        style=discord.ButtonStyle.secondary
    )
    async def menos_velocidade(self, interaction, button):
        self.remover(
            interaction.user.id,
            "velocidade"
        )
        await self.atualizar(interaction)

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary
    )
    async def voltar(self, interaction, button):
        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=CriacaoView(self.dono_id)
        )


# =========================================================
# PAINEL PRINCIPAL
# =========================================================

class CriacaoView(discord.ui.View):

    def __init__(self, dono_id):
        super().__init__(timeout=300)
        self.dono_id = dono_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Esse painel pertence a outro jogador.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        label="Definir Nome",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def definir_nome(self, interaction, button):
        await interaction.response.send_modal(
            NomeModal()
        )

    @discord.ui.button(
        label="Raça",
        emoji="🧬",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def escolher_raca(self, interaction, button):
        await interaction.response.send_message(
            "🧬 O catálogo oficial de **Raças** "
            "será adicionado na próxima etapa.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Família",
        emoji="🩸",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def escolher_familia(self, interaction, button):
        await interaction.response.send_message(
            "🩸 O sistema oficial de **Famílias/Roll** "
            "será adicionado na próxima etapa.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Facção",
        emoji="🌊",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def escolher_faccao(self, interaction, button):
        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=FaccaoView(self.dono_id)
        )

    @discord.ui.button(
        label="Profissão",
        emoji="🛠️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def escolher_profissao(self, interaction, button):
        await interaction.response.send_message(
            "🛠️ O catálogo oficial de **Profissões** "
            "será adicionado na próxima etapa.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Classe",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def escolher_classe(self, interaction, button):
        await interaction.response.send_message(
            "⚔️ O catálogo oficial de **Classes** "
            "será adicionado na próxima etapa.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Atributos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=2
    )
    async def atributos(self, interaction, button):
        await interaction.response.edit_message(
            embed=criar_embed_criacao(interaction.user),
            view=AtributosView(self.dono_id)
        )

    @discord.ui.button(
        label="Confirmar Personagem",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def confirmar(self, interaction, button):

        user_id = interaction.user.id
        dados = criando.get(user_id)

        if not dados:
            await interaction.response.send_message(
                "❌ Sua criação expirou. "
                "Use `!criar` novamente.",
                ephemeral=True
            )
            return

        if not dados["nome"]:
            await interaction.response.send_message(
                "❌ Você precisa definir o "
                "**nome do personagem**.",
                ephemeral=True
            )
            return

        if dados["pontos"] > 0:
            await interaction.response.send_message(
                f"❌ Você ainda possui "
                f"**{dados['pontos']} pontos de atributo** "
                "para distribuir.",
                ephemeral=True
            )
            return

        if await possui_ficha(user_id):
            await interaction.response.send_message(
                "❌ Você já possui uma ficha registrada.",
                ephemeral=True
            )
            return

        await db.execute(
            """
            INSERT INTO fichas (
                user_id,
                nome,
                raca,
                familia,
                faccao,
                profissao,
                classe,
                forca,
                resistencia,
                velocidade,
                pontos_atributo
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10, $11
            )
            """,
            user_id,
            dados["nome"],
            dados["raca"],
            dados["familia"],
            dados["faccao"],
            dados["profissao"],
            dados["classe"],
            dados["forca"],
            dados["resistencia"],
            dados["velocidade"],
            dados["pontos"]
        )

        nome = dados["nome"]

        del criando[user_id]

        embed = discord.Embed(
            title="🏴‍☠️ PERSONAGEM CRIADO!",
            description=(
                f"**{nome}** entrou oficialmente no mundo de "
                "**Sea's Paradise**."
            )
        )

        embed.add_field(
            name="📜 Ficha",
            value=(
                "Use `!ficha` para visualizar "
                "seu personagem."
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )


# =========================================================
# COMANDO !CRIAR
# =========================================================

@bot.command()
async def criar(ctx):

    if await possui_ficha(ctx.author.id):
        await ctx.send(
            "❌ Você já possui um personagem registrado.\n"
            "Use `!ficha` para visualizá-lo."
        )
        return

    criando[ctx.author.id] = novo_rascunho()

    await ctx.send(
        embed=criar_embed_criacao(ctx.author),
        view=CriacaoView(ctx.author.id)
    )


# =========================================================
# FICHA
# =========================================================

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
            "Use `!criar` para iniciar sua ficha."
        )
        return

    embed = discord.Embed(
        title=f"🏴‍☠️ {personagem['nome']}",
        description=(
            "**Ficha de Personagem — Sea's Paradise**"
        )
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="🌊 Informações",
        value=(
            f"**Raça:** {personagem['raca']}\n"
            f"**Família:** {personagem['familia']}\n"
            f"**Facção:** {personagem['faccao']}\n"
            f"**Profissão:** {personagem['profissao']}\n"
            f"**Classe:** {personagem['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** {personagem['forca']:,}\n"
            f"🛡️ **Resistência:** "
            f"{personagem['resistencia']:,}\n"
            f"💨 **Velocidade/Agilidade:** "
            f"{personagem['velocidade']:,}"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 Berries",
        value=f"฿ {personagem['berries']:,}",
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=f"{personagem['reputacao']:,}",
        inline=True
    )

    embed.set_footer(
        text=f"Sea's Paradise • ID: {membro.id}"
    )

    await ctx.send(embed=embed)


# =========================================================
# RESET DE TESTE
# Temporário enquanto construímos o sistema
# =========================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def resetarficha(ctx, membro: discord.Member = None):

    membro = membro or ctx.author

    resultado = await db.execute(
        "DELETE FROM fichas WHERE user_id = $1",
        membro.id
    )

    criando.pop(membro.id, None)

    if resultado == "DELETE 0":
        await ctx.send(
            f"❌ {membro.mention} não possui ficha registrada."
        )
        return

    await ctx.send(
        f"🗑️ A ficha de {membro.mention} foi resetada."
    )


# =========================================================
# TESTE
# =========================================================

@bot.command()
async def ping(ctx):
    await ctx.send(
        "🏴‍☠️ **Pong! Seas Paradise está online!**"
    )


# =========================================================
# AJUDA
# =========================================================

@bot.command()
async def ajuda(ctx):

    embed = discord.Embed(
        title="🏴‍☠️ SEA'S PARADISE",
        description="Sistema oficial do RP"
    )

    embed.add_field(
        name="📜 Personagem",
        value=(
            "`!criar` — Inicia a criação do personagem\n"
            "`!ficha` — Visualiza sua ficha\n"
            "`!ficha @usuário` — Visualiza outra ficha"
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 Sistema",
        value=(
            "`!ping` — Verifica se o bot está online"
        ),
        inline=False
    )

    await ctx.send(embed=embed)


# =========================================================
# INICIAR BOT
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não foi configurado."
    )

bot.run(TOKEN)
