import discord
from discord.ext import commands

from database.database import (
    possui_ficha,
    buscar_ficha,
    adicionar_pontos_atributo,
    adicionar_pontos_percentuais,
    adicionar_especializacao,
    remover_especializacao,
    adicionar_berries,
    adicionar_reputacao,
    buscar_especializacoes,
)

from data.classes import CLASSES
from data.skills import ESTILOS
from data.profissoes import PROFISSOES


# =========================================================
# CONFIGURAÇÕES
# =========================================================

CATEGORIAS_CATALOGO = {
    "classe": CLASSES,
    "estilo": ESTILOS,
    "profissao": PROFISSOES,
}

LIMITES_PADRAO = {
    "classe": 100,
    "estilo": 100,
    "profissao": 200,
    "haki": None,
    "akuma": 200,
    "despertar": 200,
}


# =========================================================
# FUNÇÕES
# =========================================================

def formatar_numero(valor):
    return f"{valor:,}".replace(",", ".")


def obter_limite(categoria, nome):
    """
    Profissões podem possuir máximo próprio.
    Ex.: Cientista = 400%.
    """

    if categoria == "profissao":
        dados = PROFISSOES.get(nome)

        if dados:
            return dados.get("maximo", 200)

    return LIMITES_PADRAO.get(
        categoria,
        200
    )


def nomes_catalogo(categoria):
    """Aceita catálogos em dict, list, tuple ou set."""
    catalogo = CATEGORIAS_CATALOGO.get(categoria)
    if isinstance(catalogo, dict):
        return list(catalogo.keys())
    if isinstance(catalogo, (list, tuple, set)):
        return [str(item) for item in catalogo]
    return []


def obter_emoji(categoria, nome):

    catalogo = CATEGORIAS_CATALOGO.get(
        categoria
    )

    if not catalogo:
        return "📚"

    dados = catalogo.get(nome) if hasattr(catalogo, "get") else None

    # Alguns catálogos (especialmente ESTILOS) podem guardar
    # apenas o nome/string em vez de um dicionário com emoji.
    # Nunca deixamos isso quebrar a criação do Select do Discord.
    if not isinstance(dados, dict):
        return "📚"

    emoji = dados.get("emoji")
    return emoji if emoji else "📚"


# =========================================================
# EMBED ADMIN
# =========================================================

async def criar_embed_admin(membro):

    ficha = await buscar_ficha(
        membro.id
    )

    if not ficha:

        return discord.Embed(
            title="❌ Ficha não encontrada",
            description=(
                f"{membro.mention} ainda "
                "não possui personagem."
            )
        )

    especializacoes = (
        await buscar_especializacoes(
            membro.id
        )
    )

    embed = discord.Embed(
        title="👑 PAINEL ADMINISTRATIVO",
        description=(
            f"Gerenciando **{ficha['nome']}**\n"
            f"Jogador: {membro.mention}"
        )
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 Força: "
            f"**{formatar_numero(ficha['forca'])}**\n"

            f"🛡️ Resistência: "
            f"**{formatar_numero(ficha['resistencia'])}**\n"

            f"💨 Velocidade/Agilidade: "
            f"**{formatar_numero(ficha['velocidade'])}**\n\n"

            f"✨ Pontos disponíveis: "
            f"**{formatar_numero(ficha['pontos_atributo'])}**"
        ),
        inline=False
    )

    embed.add_field(
        name="📚 Especializações",
        value=(
            f"**{len(especializacoes)}** "
            "desbloqueadas"
        ),
        inline=True
    )

    embed.add_field(
        name="💰 Berries",
        value=(
            f"฿ "
            f"{formatar_numero(ficha['berries'])}"
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ Reputação",
        value=formatar_numero(
            ficha["reputacao"]
        ),
        inline=True
    )

    embed.set_footer(
        text="Sea's Paradise • Administração"
    )

    return embed


# =========================================================
# PONTOS DE ATRIBUTO
# =========================================================

class PontosAtributoModal(
    discord.ui.Modal,
    title="Dar Pontos de Atributo"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 300",
        min_length=1,
        max_length=8
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

            if quantidade <= 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite uma quantidade válida.",
                ephemeral=True
            )

            return

        await adicionar_pontos_atributo(
            self.membro.id,
            quantidade
        )

        await interaction.response.send_message(
            f"✨ **{formatar_numero(quantidade)} pontos** "
            f"de atributo adicionados para "
            f"{self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# PONTOS DE DOMÍNIO
# =========================================================

class PontosPercentuaisModal(
    discord.ui.Modal,
    title="Dar Pontos de Domínio"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade de %",
        placeholder="Ex: 50",
        min_length=1,
        max_length=8
    )

    def __init__(self, membro):
        super().__init__()
        self.membro = membro

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

            if quantidade <= 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite uma quantidade válida.",
                ephemeral=True
            )

            return

        await adicionar_pontos_percentuais(
            self.membro.id,
            quantidade
        )

        await interaction.response.send_message(
            f"📈 **{formatar_numero(quantidade)}%** "
            f"adicionados para "
            f"{self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# ADICIONAR ITEM DO CATÁLOGO
# =========================================================

async def desbloquear_item(
    interaction,
    membro,
    categoria,
    nome
):
    # Reconhece a interação imediatamente para evitar
    # "o aplicativo não respondeu a tempo" enquanto o banco salva.
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    limite = obter_limite(
        categoria,
        nome
    )

    try:
        resultado = (
            await adicionar_especializacao(
                user_id=membro.id,
                categoria=categoria,
                nome=nome,
                limite=limite,
                desbloqueado_por=str(
                    interaction.user.id
                )
            )
        )
    except Exception as erro:
        print(
            "❌ ERRO AO DESBLOQUEAR ESPECIALIZAÇÃO:",
            categoria, nome, type(erro).__name__, erro
        )
        await interaction.followup.send(
            f"❌ Erro ao adicionar **{nome}** à ficha.",
            ephemeral=True
        )
        return

    if resultado == "INSERT 0 0":
        await interaction.followup.send(
            f"⚠️ **{nome}** já está "
            f"desbloqueado para "
            f"{membro.mention}.",
            ephemeral=True
        )
        return

    limite_texto = "∞" if limite is None else f"{limite}%"

    await interaction.followup.send(
        f"✅ **{nome}** desbloqueado para "
        f"{membro.mention}.\n"
        f"📈 Limite de domínio: "
        f"**{limite_texto}**",
        ephemeral=True
    )


# =========================================================
# SELECT DE ITEM
# =========================================================

class ItemCatalogoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        membro,
        categoria,
        itens
    ):

        self.membro = membro
        self.categoria = categoria

        opcoes = []

        for nome in itens[:25]:

            emoji = obter_emoji(
                categoria,
                nome
            )

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    value=nome,
                    emoji=emoji
                )
            )

        super().__init__(
            placeholder=(
                f"Escolha "
                f"{categoria}..."
            ),
            options=opcoes
        )

    async def callback(
        self,
        interaction
    ):

        nome = self.values[0]

        await desbloquear_item(
            interaction,
            self.membro,
            self.categoria,
            nome
        )


# =========================================================
# VIEW DO CATÁLOGO
# =========================================================

class CatalogoView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        membro,
        categoria
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.membro = membro
        self.categoria = categoria

        nomes = nomes_catalogo(categoria)

        self.paginas = [
            nomes[i:i + 25]
            for i in range(
                0,
                len(nomes),
                25
            )
        ]

        self.pagina = 0

        self.montar()

    def montar(self):

        self.clear_items()

        if not self.paginas:
            return

        self.add_item(
            ItemCatalogoSelect(
                self.membro,
                self.categoria,
                self.paginas[
                    self.pagina
                ]
            )
        )

        if len(self.paginas) > 1:

            anterior = discord.ui.Button(
                label="Anterior",
                emoji="⬅️",
                style=discord.ButtonStyle.secondary,
                row=1,
                disabled=(
                    self.pagina == 0
                )
            )

            proximo = discord.ui.Button(
                label="Próximo",
                emoji="➡️",
                style=discord.ButtonStyle.secondary,
                row=1,
                disabled=(
                    self.pagina
                    >= len(self.paginas) - 1
                )
            )

            anterior.callback = (
                self.anterior
            )

            proximo.callback = (
                self.proximo
            )

            self.add_item(
                anterior
            )

            self.add_item(
                proximo
            )

        voltar = discord.ui.Button(
            label="Voltar",
            emoji="↩️",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        voltar.callback = self.voltar

        self.add_item(
            voltar
        )

    async def interaction_check(
        self,
        interaction
    ):

        if (
            interaction.user.id
            != self.dono_id
        ):

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro administrador.",
                ephemeral=True
            )

            return False

        if not (
            interaction.user
            .guild_permissions
            .administrator
        ):

            await interaction.response.send_message(
                "❌ Apenas administradores "
                "podem usar esse painel.",
                ephemeral=True
            )

            return False

        return True

    async def anterior(
        self,
        interaction
    ):

        if self.pagina > 0:
            self.pagina -= 1

        self.montar()

        await interaction.response.edit_message(
            embed=self.gerar_embed(),
            view=self
        )

    async def proximo(
        self,
        interaction
    ):

        if (
            self.pagina
            < len(self.paginas) - 1
        ):
            self.pagina += 1

        self.montar()

        await interaction.response.edit_message(
            embed=self.gerar_embed(),
            view=self
        )

    async def voltar(
        self,
        interaction
    ):

        await interaction.response.edit_message(
            embed=criar_embed_especializacoes(
                self.membro
            ),
            view=EspecializacoesAdminView(
                self.dono_id,
                self.membro
            )
        )

    def gerar_embed(self):

        titulo = {
            "classe": "⚔️ CLASSES",
            "estilo": "🥋 ESTILOS DE LUTA",
            "profissao": "🛠️ PROFISSÕES"
        }

        embed = discord.Embed(
            title=titulo.get(
                self.categoria,
                "📚 CATÁLOGO"
            ),
            description=(
                f"Jogador: "
                f"{self.membro.mention}\n\n"
                "Selecione o que deseja "
                "desbloquear."
            )
        )

        embed.set_footer(
            text=(
                f"Página "
                f"{self.pagina + 1}/"
                f"{len(self.paginas)}"
            )
        )

        return embed


# =========================================================
# HAKI / AKUMA / DESPERTAR MANUAL
# =========================================================

class EspecializacaoManualModal(
    discord.ui.Modal
):

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Digite o nome",
        min_length=2,
        max_length=100
    )

    limite = discord.ui.TextInput(
        label="Limite de domínio (%)",
        placeholder="200",
        default="200",
        min_length=1,
        max_length=4
    )

    def __init__(
        self,
        membro,
        categoria
    ):

        self.membro = membro
        self.categoria = categoria

        super().__init__(
            title=(
                f"Adicionar "
                f"{categoria.title()}"
            )[:45]
        )

    async def on_submit(
        self,
        interaction
    ):

        nome = (
            self.nome.value.strip()
        )

        try:

            limite = int(
                self.limite.value
            )

            if limite <= 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite um limite válido.",
                ephemeral=True
            )

            return

        resultado = (
            await adicionar_especializacao(
                user_id=self.membro.id,
                categoria=self.categoria,
                nome=nome,
                limite=limite,
                desbloqueado_por=str(
                    interaction.user.id
                )
            )
        )

        if resultado == "INSERT 0 0":

            await interaction.response.send_message(
                f"⚠️ **{nome}** já está "
                "desbloqueado.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            f"✅ **{nome}** desbloqueado "
            f"para {self.membro.mention}.\n"
            f"📈 Limite: **{limite}%**",
            ephemeral=True
        )


# =========================================================
# REMOVER ESPECIALIZAÇÃO
# =========================================================

class RemoverEspecializacaoModal(
    discord.ui.Modal,
    title="Remover Especialização"
):

    categoria = discord.ui.TextInput(
        label="Categoria",
        placeholder="Ex: estilo"
    )

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Ex: Ittoryu"
    )

    def __init__(
        self,
        membro
    ):

        super().__init__()

        self.membro = membro

    async def on_submit(
        self,
        interaction
    ):

        categoria = (
            self.categoria.value
            .strip()
            .lower()
        )

        nome = (
            self.nome.value.strip()
        )

        resultado = (
            await remover_especializacao(
                self.membro.id,
                categoria,
                nome
            )
        )

        if resultado == "DELETE 0":

            await interaction.response.send_message(
                "❌ Essa especialização "
                "não foi encontrada.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            f"🗑️ **{nome}** removido de "
            f"{self.membro.mention}.",
            ephemeral=True
        )


# =========================================================
# BERRIES
# =========================================================

class BerriesModal(
    discord.ui.Modal,
    title="Alterar Berries"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 100000 ou -50000",
        min_length=1,
        max_length=20
    )

    def __init__(
        self,
        membro
    ):

        super().__init__()

        self.membro = membro

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite um número válido.",
                ephemeral=True
            )

            return

        await adicionar_berries(
            self.membro.id,
            quantidade
        )

        sinal = (
            "+"
            if quantidade >= 0
            else ""
        )

        await interaction.response.send_message(
            f"💰 Berries de "
            f"{self.membro.mention}: "
            f"**{sinal}"
            f"{formatar_numero(quantidade)}**",
            ephemeral=True
        )


# =========================================================
# REPUTAÇÃO
# =========================================================

class ReputacaoModal(
    discord.ui.Modal,
    title="Alterar Reputação"
):

    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 100 ou -50",
        min_length=1,
        max_length=15
    )

    def __init__(
        self,
        membro
    ):

        super().__init__()

        self.membro = membro

    async def on_submit(
        self,
        interaction
    ):

        try:

            quantidade = int(
                self.quantidade.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite um número válido.",
                ephemeral=True
            )

            return

        await adicionar_reputacao(
            self.membro.id,
            quantidade
        )

        sinal = (
            "+"
            if quantidade >= 0
            else ""
        )

        await interaction.response.send_message(
            f"⭐ Reputação de "
            f"{self.membro.mention}: "
            f"**{sinal}"
            f"{formatar_numero(quantidade)}**",
            ephemeral=True
        )


# =========================================================
# EMBED ESPECIALIZAÇÕES
# =========================================================

def criar_embed_especializacoes(
    membro
):

    return discord.Embed(
        title="📚 ESPECIALIZAÇÕES",
        description=(
            f"Gerenciando "
            f"{membro.mention}\n\n"
            "Escolha a categoria que "
            "deseja desbloquear."
        )
    )


# =================
# MENU DE CATEGORIA
# =========================================================

class EspecializacaoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        membro
    ):

        self.membro = membro

        opcoes = [
            discord.SelectOption(
                label="Classe",
                value="classe",
                emoji="⚔️"
            ),
            discord.SelectOption(
                label="Estilo",
                value="estilo",
                emoji="🥋"
            ),
            discord.SelectOption(
                label="Profissão",
                value="profissao",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Haki",
                value="haki",
                emoji="👁️"
            ),
            discord.SelectOption(
                label="Akuma no Mi",
                value="akuma",
                emoji="🍈"
            ),
            discord.SelectOption(
                label="Despertar",
                value="despertar",
                emoji="🌟"
            )
        ]

        super().__init__(
            placeholder=(
                "O que deseja desbloquear?"
            ),
            options=opcoes
        )

    async def callback(
        self,
        interaction
    ):

        categoria = self.values[0]

        # Catálogos oficiais: reconhece a interação ANTES de montar
        # o catálogo. Isso evita o aviso "não respondeu a tempo".
        if categoria in CATEGORIAS_CATALOGO:
            if not interaction.response.is_done():
                await interaction.response.defer()

            try:
                view = CatalogoView(
                    self.view.dono_id,
                    self.membro,
                    categoria
                )

                await interaction.edit_original_response(
                    embed=view.gerar_embed(),
                    view=view
                )
            except Exception as erro:
                print(
                    "❌ ERRO AO ABRIR CATÁLOGO ADMIN:",
                    categoria,
                    type(erro).__name__,
                    erro
                )
                await interaction.followup.send(
                    f"❌ Não consegui abrir o catálogo de {categoria}.",
                    ephemeral=True
                )
            return

        # Categorias manuais precisam abrir o modal como resposta inicial.
        await interaction.response.send_modal(
            EspecializacaoManualModal(
                self.membro,
                categoria
            )
        )


# =========================================================
# VIEW ESPECIALIZAÇÕES
# =========================================================

class EspecializacoesAdminView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        membro
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.membro = membro

        self.add_item(
            EspecializacaoSelect(
                membro
            )
        )

    async def interaction_check(
        self,
        interaction
    ):

        if (
            interaction.user.id
            != self.dono_id
        ):

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro administrador.",
                ephemeral=True
            )

            return False

        if not (
            interaction.user
            .guild_permissions
            .administrator
        ):

            await interaction.response.send_message(
                "❌ Apenas administradores "
                "podem usar esse painel.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Remover",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        row=1
    )
    async def remover(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            RemoverEspecializacaoModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def voltar(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=(
                await criar_embed_admin(
                    self.membro
                )
            ),
            view=AdminView(
                self.dono_id,
                self.membro
            )
        )


# =========================================================
# PAINEL PRINCIPAL ADMIN
# =========================================================

class AdminView(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        membro
    ):

        super().__init__(
            timeout=300
        )

        self.dono_id = dono_id
        self.membro = membro

    async def interaction_check(
        self,
        interaction
    ):

        if (
            interaction.user.id
            != self.dono_id
        ):

            await interaction.response.send_message(
                "❌ Esse painel pertence "
                "a outro administrador.",
                ephemeral=True
            )

            return False

        if not (
            interaction.user
            .guild_permissions
            .administrator
        ):

            await interaction.response.send_message(
                "❌ Apenas administradores "
                "podem usar esse painel.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Pontos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def pontos(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            PontosAtributoModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Pontos %",
        emoji="📈",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def pontos_percentuais(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            PontosPercentuaisModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Especializações",
        emoji="📚",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def especializacoes(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed_especializacoes(
                self.membro
            ),
            view=EspecializacoesAdminView(
                self.dono_id,
                self.membro
            )
        )

    @discord.ui.button(
        label="Berries",
        emoji="💰",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def berries(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            BerriesModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Reputação",
        emoji="⭐",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def reputacao(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            ReputacaoModal(
                self.membro
            )
        )

    @discord.ui.button(
        label="Atualizar",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def atualizar(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=(
                await criar_embed_admin(
                    self.membro
                )
            ),
            view=AdminView(
                self.dono_id,
                self.membro
            )
        )


# =========================================================
# COG
# =========================================================

class Admin(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

    @commands.command()
    @commands.has_permissions(
        administrator=True
    )
    async def admin(
        self,
        ctx,
        membro: discord.Member = None
    ):

        if membro is None:

            await ctx.send(
                "❌ Use:\n"
                "`!admin @jogador`"
            )

            return

        if not await possui_ficha(
            membro.id
        ):

            await ctx.send(
                f"❌ {membro.mention} "
                "não possui ficha."
            )

            return

        await ctx.send(
            embed=(
                await criar_embed_admin(
                    membro
                )
            ),
            view=AdminView(
                ctx.author.id,
                membro
            )
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    await bot.add_cog(
        Admin(bot)
        )
