import discord

from data.racas import RACAS
from data.familias import FAMILIAS
from data.profissoes import PROFISSOES
from data.classes import CLASSES


# =========================================================
# CONFIGURAÇÕES
# =========================================================

PONTOS_INICIAIS = 100
ATRIBUTO_MAXIMO = 50000

criando = {}


# =========================================================
# RASCUNHO
# =========================================================

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


# =========================================================
# EMBED PRINCIPAL
# =========================================================

def criar_embed(usuario):

    dados = criando.get(usuario.id)

    if not dados:
        return discord.Embed(
            title="❌ Criação encerrada",
            description="Use `!criar` para começar novamente."
        )

    embed = discord.Embed(
        title="🏴‍☠️ CRIAÇÃO DE PERSONAGEM",
        description=(
            "Monte seu personagem para entrar no mundo de "
            "**Sea's Paradise**."
        )
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Nome:** "
            f"{dados['nome'] or 'Não definido'}\n"

            f"**Raça:** "
            f"{dados['raca']}\n"

            f"**Família:** "
            f"{dados['familia']}"
        ),
        inline=False
    )

    embed.add_field(
        name="🌊 Caminho",
        value=(
            f"**Facção:** "
            f"{dados['faccao']}\n"

            f"**Profissão:** "
            f"{dados['profissao']}\n"

            f"**Classe:** "
            f"{dados['classe']}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** "
            f"{dados['forca']:,}\n"

            f"🛡️ **Resistência:** "
            f"{dados['resistencia']:,}\n"

            f"💨 **Velocidade/Agilidade:** "
            f"{dados['velocidade']:,}\n\n"

            f"✨ **Pontos disponíveis:** "
            f"{dados['pontos']:,}"
        ),
        inline=False
    )

    embed.set_footer(
        text="Sea's Paradise • Criação de Personagem"
    )

    return embed


# =========================================================
# BASE DAS VIEWS
# =========================================================

class ViewDoJogador(discord.ui.View):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):
        super().__init__(timeout=600)

        self.dono_id = dono_id
        self.confirmar_callback = confirmar_callback

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Esse painel pertence a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    def painel_principal(self):

        return CriacaoView(
            self.dono_id,
            self.confirmar_callback
        )


# =========================================================
# NOME
# =========================================================

class NomeModal(discord.ui.Modal):

    def __init__(
        self,
        confirmar_callback
    ):

        super().__init__(
            title="Nome do Personagem"
        )

        self.confirmar_callback = confirmar_callback

        self.nome = discord.ui.TextInput(
            label="Nome",
            placeholder="Ex: Monkey D. Luffy",
            min_length=2,
            max_length=40
        )

        self.add_item(self.nome)

    async def on_submit(
        self,
        interaction
    ):

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação não está mais ativa.",
                ephemeral=True
            )

            return

        dados["nome"] = (
            self.nome.value.strip()
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                interaction.user.id,
                self.confirmar_callback
            )
        )


# =========================================================
# CATÁLOGO GENÉRICO
# =========================================================

class CatalogoSelect(discord.ui.Select):

    def __init__(
        self,
        campo,
        catalogo,
        placeholder
    ):

        self.campo = campo

        opcoes = []

        # Discord permite no máximo
        # 25 opções por Select.
        for nome, dados in list(
            catalogo.items()
        )[:25]:

            emoji = None
            descricao = None

            if isinstance(dados, dict):

                emoji = dados.get(
                    "emoji"
                )

                descricao_original = dados.get(
                    "descricao"
                )

                if descricao_original:

                    descricao = (
                        descricao_original[:97]
                        + "..."
                        if len(descricao_original) > 100
                        else descricao_original
                    )

            opcoes.append(
                discord.SelectOption(
                    label=str(nome)[:100],
                    value=str(nome)[:100],
                    emoji=emoji,
                    description=descricao
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=opcoes,
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        dados[self.campo] = (
            self.values[0]
        )

        view = self.view

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=view.painel_principal()
        )


class CatalogoView(ViewDoJogador):

    def __init__(
        self,
        dono_id,
        confirmar_callback,
        campo,
        catalogo,
        placeholder
    ):

        super().__init__(
            dono_id,
            confirmar_callback
        )

        self.add_item(
            CatalogoSelect(
                campo,
                catalogo,
                placeholder
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
            embed=criar_embed(
                interaction.user
            ),
            view=self.painel_principal()
        )


# =========================================================
# FACÇÕES
# =========================================================

FACCOES = {
    "Pirata": "🏴‍☠️",
    "Marinha": "⚓",
    "Revolucionário": "🔥",
    "Civil": "🏝️"
}


class FaccaoSelect(discord.ui.Select):

    def __init__(self):

        opcoes = [
            discord.SelectOption(
                label=nome,
                value=nome,
                emoji=emoji
            )
            for nome, emoji
            in FACCOES.items()
        ]

        super().__init__(
            placeholder="Escolha sua facção...",
            options=opcoes,
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        dados["faccao"] = (
            self.values[0]
        )

        view = self.view

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=view.painel_principal()
        )


class FaccaoView(ViewDoJogador):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        super().__init__(
            dono_id,
            confirmar_callback
        )

        self.add_item(
            FaccaoSelect()
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
            embed=criar_embed(
                interaction.user
            ),
            view=self.painel_principal()
        )


# =========================================================
# SELETOR DE ATRIBUTO
# =========================================================

class CriacaoAtributoSelect(
    discord.ui.Select
):

    def __init__(self):

        super().__init__(
            placeholder=(
                "Escolha o atributo..."
            ),
            options=[
                discord.SelectOption(
                    label="Força",
                    value="forca",
                    emoji="💪"
                ),

                discord.SelectOption(
                    label="Resistência",
                    value="resistencia",
                    emoji="🛡️"
                ),

                discord.SelectOption(
                    label="Velocidade/Agilidade",
                    value="velocidade",
                    emoji="💨"
                )
            ],
            row=0
        )

    async def callback(
        self,
        interaction
    ):

        self.view.atributo = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=self.view
        )


# =========================================================
# BOTÕES DE QUANTIDADE
# =========================================================

class CriacaoQuantidadeButton(
    discord.ui.Button
):

    def __init__(
        self,
        quantidade
    ):

        super().__init__(
            label=f"+{quantidade}",
            style=discord.ButtonStyle.primary,
            row=1
        )

        self.quantidade = quantidade

    async def callback(
        self,
        interaction
    ):

        view = self.view

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        atributo = view.atributo

        if atributo is None:

            await interaction.response.send_message(
                "❌ Primeiro escolha um atributo.",
                ephemeral=True
            )

            return

        if (
            dados["pontos"]
            < self.quantidade
        ):

            await interaction.response.send_message(
                "❌ Você não possui pontos suficientes.",
                ephemeral=True
            )

            return

        if (
            dados[atributo]
            + self.quantidade
            > ATRIBUTO_MAXIMO
        ):

            await interaction.response.send_message(
                "❌ O limite máximo por atributo "
                "é **50.000**.",
                ephemeral=True
            )

            return

        dados[atributo] += (
            self.quantidade
        )

        dados["pontos"] -= (
            self.quantidade
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=view
        )


# =========================================================
# ATRIBUTOS DA CRIAÇÃO
# =========================================================

class CriacaoAtributosView(
    ViewDoJogador
):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        super().__init__(
            dono_id,
            confirmar_callback
        )

        self.atributo = None

        self.add_item(
            CriacaoAtributoSelect()
        )

        for quantidade in (
            1,
            5,
            50,
            100,
            300
        ):

            self.add_item(
                CriacaoQuantidadeButton(
                    quantidade
                )
            )

    @discord.ui.button(
        label="Resetar",
        emoji="♻️",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def resetar(
        self,
        interaction,
        button
    ):

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        total_distribuido = (
            dados["forca"]
            + dados["resistencia"]
            + dados["velocidade"]
        )

        dados["pontos"] += (
            total_distribuido
        )

        dados["forca"] = 0
        dados["resistencia"] = 0
        dados["velocidade"] = 0

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoAtributosView(
                self.dono_id,
                self.confirmar_callback
            )
        )

    @discord.ui.button(
        label="Voltar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def voltar(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=self.painel_principal()
        )


# =========================================================
# PAINEL PRINCIPAL
# =========================================================

class CriacaoView(ViewDoJogador):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        super().__init__(
            dono_id,
            confirmar_callback
        )

    # -----------------------------------------------------
    # NOME
    # -----------------------------------------------------

    @discord.ui.button(
        label="Nome",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def nome(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            NomeModal(
                self.confirmar_callback
            )
        )

    # -----------------------------------------------------
    # RAÇA
    # -----------------------------------------------------

    @discord.ui.button(
        label="Raça",
        emoji="🧬",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def raca(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CatalogoView(
                self.dono_id,
                self.confirmar_callback,
                "raca",
                RACAS,
                "Escolha sua raça..."
            )
        )

    # -----------------------------------------------------
    # FAMÍLIA
    # -----------------------------------------------------

    @discord.ui.button(
        label="Família",
        emoji="🩸",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def familia(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CatalogoView(
                self.dono_id,
                self.confirmar_callback,
                "familia",
                FAMILIAS,
                "Escolha sua família..."
            )
        )

    # -----------------------------------------------------
    # FACÇÃO
    # -----------------------------------------------------

    @discord.ui.button(
        label="Facção",
        emoji="🌊",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def faccao(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=FaccaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )

    # -----------------------------------------------------
    # PROFISSÃO
    # -----------------------------------------------------

    @discord.ui.button(
        label="Profissão",
        emoji="🛠️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def profissao(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CatalogoView(
                self.dono_id,
                self.confirmar_callback,
                "profissao",
                PROFISSOES,
                "Escolha sua profissão..."
            )
        )

    # -----------------------------------------------------
    # CLASSE
    # -----------------------------------------------------

    @discord.ui.button(
        label="Classe",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def classe(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CatalogoView(
                self.dono_id,
                self.confirmar_callback,
                "classe",
                CLASSES,
                "Escolha sua classe..."
            )
        )

    # -----------------------------------------------------
    # ATRIBUTOS
    # -----------------------------------------------------

    @discord.ui.button(
        label="Atributos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=2
    )
    async def atributos(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoAtributosView(
                self.dono_id,
                self.confirmar_callback
            )
        )

    # -----------------------------------------------------
    # CONFIRMAR
    # -----------------------------------------------------

    @discord.ui.button(
        label="Confirmar Personagem",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def confirmar(
        self,
        interaction,
        button
    ):

        if not self.confirmar_callback:

            await interaction.response.send_message(
                "❌ A confirmação não está disponível.",
                ephemeral=True
  
