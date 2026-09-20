import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    deletar_ficha,
    buscar_especializacoes,
    buscar_pontos_percentuais,
    distribuir_percentual,
)

from views.criacao import (
    criando,
    novo_rascunho,
    criar_embed,
    CriacaoView,
)

from views.atributos import (
    AtributosView,
    embed_atributos,
)

from views.dominios import (
    DominiosView,
    criar_embed_dominios,
)


# =========================================================
# SEA'S PARADISE
# COG — PERSONAGEM
# =========================================================


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor):
    return f"{valor:,}".replace(",", ".")


# =========================================================
# EMBED DA FICHA
# =========================================================

async def criar_embed_ficha(membro, personagem):

    especializacoes = await buscar_especializacoes(
        membro.id
    )

    pontos_percentuais = await buscar_pontos_percentuais(
        membro.id
    )

    embed = discord.Embed(
        title=f"🏴‍☠️ {personagem['nome']}",
        description=(
            "**Ficha de Personagem — Sea's Paradise**"
        )
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    # =====================================================
    # IDENTIDADE
    # =====================================================

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Raça:** {personagem['raca']}\n"
            f"**Família:** {personagem['familia']}\n"
            f"**Facção:** {personagem['faccao']}"
        ),
        inline=False
    )

    # =====================================================
    # CAMINHO
    # =====================================================

    embed.add_field(
        name="🧭 Caminho",
        value=(
            f"**Profissão:** {personagem['profissao']}\n"
            f"**Classe:** {personagem['classe']}"
        ),
        inline=False
    )

    # =====================================================
    # ATRIBUTOS
    # =====================================================

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** "
            f"{formatar_numero(personagem['forca'])}\n"

            f"🛡️ **Resistência:** "
            f"{formatar_numero(personagem['resistencia'])}\n"

            f"💨 **Velocidade/Agilidade:** "
            f"{formatar_numero(personagem['velocidade'])}\n\n"

            f"✨ **Pontos disponíveis:** "
            f"{formatar_numero(personagem['pontos_atributo'])}"
        ),
        inline=False
    )

    # =====================================================
    # ESPECIALIZAÇÕES / DOMÍNIOS
    # =====================================================

    if especializacoes:

        categorias = {}

        for item in especializacoes:

            categoria = (
                item["categoria"]
                .strip()
                .lower()
            )

            categorias.setdefault(
                categoria,
                []
            ).append(item)

        emojis_categoria = {
            "estilo": "🥋",
            "classe": "⚔️",
            "profissao": "🛠️",
            "haki": "👁️",
            "akuma": "🍈",
            "akuma no mi": "🍈",
            "tecnica": "💥",
            "especializacao": "✨",
        }

        for categoria, itens in categorias.items():

            linhas = []

            for item in itens:

                linhas.append(
                    f"**{item['nome']}** — "
                    f"{item['porcentagem']}%"
                    f"/{item['limite']}%"
                )

            texto = "\n".join(linhas)

            if len(texto) > 1024:
                texto = (
                    texto[:1000]
                    + "\n..."
                )

            emoji = emojis_categoria.get(
                categoria,
                "📚"
            )

            embed.add_field(
                name=(
                    f"{emoji} "
                    f"{categoria.title()}"
                ),
                value=texto,
                inline=False
            )

    else:

        embed.add_field(
            name="📚 Domínios",
            value=(
                "Nenhuma especialização "
                "desbloqueada."
            ),
            inline=False
        )

    # =====================================================
    # PONTOS DE DOMÍNIO
    # =====================================================

    embed.add_field(
        name="📈 Pontos de Domínio",
        value=(
            f"**{formatar_numero(pontos_percentuais)}%** "
            "disponíveis"
        ),
        inline=False
    )

    # =====================================================
    # ECONOMIA
    # =====================================================

    embed.add_field(
        name="💰 Berries",
        value=(
            f"฿ "
            f"{formatar_numero(personagem['berries'])}"
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=(
            formatar_numero(
                personagem["reputacao"]
            )
        ),
        inline=True
    )

    embed.set_footer(
        text=(
            "Sea's Paradise • "
            f"ID: {membro.id}"
        )
    )

    return embed


# =========================================================
# MODAL — EDITAR NOME
# =========================================================

class EditarNomeModal(
    discord.ui.Modal,
    title="Editar Nome"
):

    nome = discord.ui.TextInput(
        label="Novo nome",
        placeholder="Nome do personagem",
        min_length=2,
        max_length=40
    )

    async def on_submit(
        self,
        interaction
    ):

        from database.database import alterar_nome

        await alterar_nome(
            interaction.user.id,
            self.nome.value.strip()
        )

        ficha = await buscar_ficha(
            interaction.user.id
        )

        if not ficha:

            await interaction.response.send_message(
                "❌ Ficha não encontrada.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=await criar_embed_ficha(
                interaction.user,
                ficha
            ),
            view=EditarFichaView(
                interaction.user.id
            )
        )


# =========================================================
# PAINEL DE EDIÇÃO
# =========================================================

class EditarFichaView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    # =====================================================
    # EDITAR NOME
    # =====================================================

    @discord.ui.button(
        label="Editar Nome",
        emoji="✏️",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def editar_nome(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            EditarNomeModal()
        )

    # =====================================================
    # ATRIBUTOS
    # =====================================================

    @discord.ui.button(
        label="Atributos",
        emoji="💪",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def atributos(
        self,
        interaction,
        button
    ):

        await abrir_atributos(
            interaction
        )

    # =====================================================
    # DOMÍNIOS
    # =====================================================

    @discord.ui.button(
        label="Domínios",
        emoji="📈",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def dominios(
        self,
        interaction,
        button
    ):

        await abrir_dominios(
            interaction
        )


# =========================================================
# VOLTAR PARA PAINEL DE EDIÇÃO
# =========================================================

async def voltar_edicao(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.edit_message(
            content="❌ Ficha não encontrada.",
            embed=None,
            view=None
        )

        return

    await interaction.response.edit_message(
        content=None,
        embed=await criar_embed_ficha(
            interaction.user,
            ficha
        ),
        view=EditarFichaView(
            interaction.user.id
        )
    )


# =========================================================
# ABRIR PAINEL DE ATRIBUTOS
# =========================================================

async def abrir_atributos(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.send_message(
            "❌ Você ainda não possui ficha.",
            ephemeral=True
        )

        return

    dados = {
        "forca": ficha["forca"],
        "resistencia": ficha["resistencia"],
        "velocidade": ficha["velocidade"],
        "pontos": ficha["pontos_atributo"],
    }

    view = AtributosView(
        interaction.user.id,
        dados,
        voltar_callback=voltar_edicao
    )

    await interaction.response.edit_message(
        embed=embed_atributos(
            view.dados
        ),
        view=view
    )


# =========================================================
# SALVAR ALTERAÇÕES DE DOMÍNIO
# =========================================================

async def salvar_dominios(
    user_id,
    dados
):

    especializacoes = list(
        await buscar_especializacoes(
            user_id
        )
    )

    atuais = {
        item["id"]: item
        for item in especializacoes
    }

    for dominio in dados.get(
        "dominios",
        []
    ):

        especializacao_id = dominio.get(
            "id"
        )

        if especializacao_id not in atuais:
            continue

        porcentagem_banco = atuais[
            especializacao_id
        ]["porcentagem"]

        porcentagem_nova = dominio.get(
            "porcentagem",
            0
        )

        diferenca = (
            porcentagem_nova
            - porcentagem_banco
        )

        # -------------------------------------------------
        # ADICIONAR %
        # -------------------------------------------------

        if diferenca > 0:

            sucesso = await distribuir_percentual(
                user_id,
                especializacao_id,
                diferenca
            )

            if not sucesso:
                return False

        # -------------------------------------------------
        # OBS:
        # Retirada de % depende de função específica
        # do database.
        #
        # Por enquanto não alteramos diretamente o banco
        # aqui para evitar duplicar pontos ou quebrar saldo.
        # -------------------------------------------------

        elif diferenca < 0:

            return False

    return True


# =========================================================
# CONVERTER ESPECIALIZAÇÕES PARA VIEW
# =========================================================

def montar_dados_dominios(
    especializacoes,
    pontos
):

    dominios = []

    for item in especializacoes:

        dominios.append({
            "id": item["id"],
            "nome": item["nome"],
            "tipo": item["categoria"],
            "porcentagem": item["porcentagem"],
        })

    return {
        "pontos_dominio": pontos,
        "dominios": dominios,
    }


# =========================================================
# ABRIR PAINEL DE DOMÍNIOS
# =========================================================

async def abrir_dominios(
    interaction
):

    ficha = await buscar_ficha(
        interaction.user.id
    )

    if not ficha:

        await interaction.response.send_message(
            "❌ Você ainda não possui ficha.",
            ephemeral=True
        )

        return

    especializacoes = list(
        await buscar_especializacoes(
            interaction.user.id
        )
    )

    pontos = await buscar_pontos_percentuais(
        interaction.user.id
    )

    dados = montar_dados_dominios(
        especializacoes,
        pontos
    )

    view = DominiosView(
        interaction.user.id,
        dados,
        salvar_callback=salvar_dominios,
        voltar_callback=voltar_edicao
    )

    await interaction.response.edit_message(
        embed=criar_embed_dominios(
            dados
        ),
        view=view
    )


# =========================================================
# COG — PERSONAGEM
# =========================================================

class Personagem(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    # =====================================================
    # !CRIAR
    # =====================================================

    @commands.command()
    async def criar(
        self,
        ctx
    ):

        if await possui_ficha(
            ctx.author.id
        ):

            await ctx.send(
                "❌ Você já possui um personagem.\n"
                "Use `!ficha` para visualizá-lo."
            )

            return

        criando[
            ctx.author.id
        ] = novo_rascunho()

        await ctx.send(
            embed=criar_embed(
                ctx.author
            ),
            view=CriacaoView(
                ctx.author.id
            )
        )


    # =====================================================
    # !FICHA
    # =====================================================

    @commands.command()
    async def ficha(
        self,
        ctx,
        membro: discord.Member = None
    ):

        membro = (
            membro
            or ctx.author
        )

        personagem = await buscar_ficha(
            membro.id
        )

        if not personagem:

            await ctx.send(
                f"❌ {membro.mention} "
                "ainda não possui ficha."
            )

            return

        await ctx.send(
            embed=await criar_embed_ficha(
                membro,
                personagem
            )
        )


    # =====================================================
    # !EDITAR
    # =====================================================

    @commands.command()
    async def editar(
        self,
        ctx
    ):

        personagem = await buscar_ficha(
            ctx.author.id
        )

        if not personagem:

            await ctx.send(
                "❌ Você ainda não possui ficha.\n"
                "Use `!criar` primeiro."
            )

            return

        await ctx.send(
            embed=await criar_embed_ficha(
                ctx.author,
                personagem
            ),
            view=EditarFichaView(
                ctx.author.id
            )
        )


    # =====================================================
    # !ATRIBUTOS
    # =====================================================

    @commands.command(
        aliases=[
            "atributo"
        ]
    )
    async def atributos(
        self,
        ctx
    ):

        ficha = await buscar_ficha(
            ctx.author.id
        )

        if not ficha:

            await ctx.send(
                "❌ Você ainda não possui ficha."
            )

            return

        dados = {
            "forca": ficha["forca"],
            "resistencia": ficha["resistencia"],
            "velocidade": ficha["velocidade"],
            "pontos": ficha["pontos_atributo"],
        }

        view = AtributosView(
            ctx.author.id,
            dados
        )

        await ctx.send(
            embed=embed_atributos(
                view.dados
            ),
            view=view
        )


    # =====================================================
    # !DOMINIOS
    # =====================================================

    @commands.command(
        aliases=[
            "dominio",
            "domínios",
            "domínio"
        ]
    )
    async def dominios(
        self,
        ctx
    ):

        if not await possui_ficha(
            ctx.author.id
        ):

            await ctx.send(
                "❌ Você ainda não possui ficha."
            )

            return

        especializacoes = list(
            await buscar_especializacoes(
                ctx.author.id
            )
        )

        pontos = await buscar_pontos_percentuais(
            ctx.author.id
        )

        dados = montar_dados_dominios(
            especializacoes,
            pontos
        )

        view = DominiosView(
            ctx.author.id,
            dados,
            salvar_callback=salvar_dominios
        )

        await ctx.send(
            embed=criar_embed_dominios(
                dados
            ),
            view=view
        )


    # =====================================================
    # !RESETARFICHA
    # SOMENTE ADMIN
    # =====================================================

    @commands.command()
    @commands.has_permissions(
        administrator=True
    )
    async def resetarficha(
        self,
        ctx,
        membro: discord.Member = None
    ):

        membro = (
            membro
            or ctx.author
        )

        resultado = await deletar_ficha(
            membro.id
        )

        criando.pop(
            membro.id,
            None
        )

        if resultado == "DELETE 0":

            await ctx.send(
                f"❌ {membro.mention} "
                "não possui ficha."
            )

            return

        await ctx.send(
            f"🗑️ Ficha de "
            f"{membro.mention} resetada."
        )


# =========================================================
# SETUP
# =========================================================

async def setup(
    bot
):

    await bot.add_cog(
        Personagem(bot)
    )
