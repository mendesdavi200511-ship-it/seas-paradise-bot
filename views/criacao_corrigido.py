import random
import discord

from data.skills import ESTILOS as CATALOGO_ESTILOS


# =========================================================
# SEA'S PARADISE
# SISTEMA DE CRIAÇÃO DE PERSONAGEM
# =========================================================


# =========================================================
# CONFIGURAÇÕES
# =========================================================

PONTOS_INICIAIS = 30

CHANCE_HAOSHOKU = 2       # 2%
CHANCE_PRODIGIO = 1       # 1%

IDADE_MINIMA = 10
IDADE_MAXIMA = 100


# =========================================================
# ESTADO DAS CRIAÇÕES
# =========================================================

# IMPORTANTE:
# personagem.py importa exatamente este dicionário.
# Não criar outro "criando" em nenhum outro arquivo.

criando = {}


# =========================================================
# OPÇÕES
# =========================================================

RACAS = [
    "Humano",
    "Homem-Peixe",
    "Tritão",
    "Gigante",
    "Mink",
    "Skypiean",
    "Birkan",
    "Shandian",
    "Longarm",
    "Longleg",
    "Three-Eye",
]

FAMILIAS = [
    "Monkey",
    "Nefertari",
    "Kozuki",
    "Shimotsuki",
    "Vinsmoke",
    "Donquixote",
    "Figarland",
    "Charlotte",
    "Rocks",
    "Gol",
    "Neptune",
    "Rosward",
    "Saint",
    "Manmayer",
    "Riku",
    "Nerona",
    "Kaido",
    "Crocodile",
    "Enel",
    "Sengoku",
    "Sakazuki",
    "Borsalino",
    "Smoker",
]

FACCOES = [
    "Pirata",
    "Marinha",
    "Revolucionário",
    "Caçador de Recompensas",
    "Civil",
]

PROFISSOES = [
    "Navegador",
    "Carpinteiro",
    "Médico",
    "Cozinheiro",
    "Arqueólogo",
    "Cientista",
]

CLASSES = [
    "Espadachim",
    "Lutador",
    "Atirador",
    "Guardião",
    "Berserker",
    "Usuário de Akuma no Mi",
    "Usuário de Haki",
]


def _nomes_estilos():
    if isinstance(CATALOGO_ESTILOS, dict):
        return list(CATALOGO_ESTILOS.keys())
    if isinstance(CATALOGO_ESTILOS, (list, tuple, set)):
        return [str(item) for item in CATALOGO_ESTILOS]
    return []

ESTILOS = _nomes_estilos()


# =========================================================
# FAMÍLIAS COM BENEFÍCIOS AUTOMÁTICOS
# =========================================================

FAMILIAS_HAOSHOKU = {
    "Monkey",
    "Rocks",
    "Gol",
}

FAMILIAS_PRODIGIO = {
    "Rocks",
    "Sengoku",
}


# =========================================================
# RASCUNHO
# =========================================================

def novo_rascunho():

    return {
        "nome": None,
        "idade": None,
        "imagem": None,

        "raca": None,
        "familia": None,
        "faccao": None,
        "profissao": None,
        "classe": None,
        "estilo": None,

        "forca": 20,
        "resistencia": 20,
        "velocidade": 20,

        "pontos": PONTOS_INICIAIS,

        "haoshoku": False,
        "haoshoku_sorteado": False,

        "prodigio": False,
        "prodigio_sorteado": False,

        "raca_sorteada": False,
        "familia_sorteada": False,
    }


# =========================================================
# GARANTIR RASCUNHO
# =========================================================

def obter_rascunho(user_id):

    if user_id not in criando:
        criando[user_id] = novo_rascunho()

    return criando[user_id]


# =========================================================
# APLICAR BENEFÍCIOS DA FAMÍLIA
# =========================================================

def aplicar_beneficios_familia(dados):

    familia = dados.get("familia")

    if familia in FAMILIAS_HAOSHOKU:
        dados["haoshoku"] = True
        dados["haoshoku_sorteado"] = True

    if familia in FAMILIAS_PRODIGIO:
        dados["prodigio"] = True
        dados["prodigio_sorteado"] = True


# =========================================================
# SORTEAR TALENTOS
# =========================================================

def sortear_talentos(dados):

    aplicar_beneficios_familia(dados)

    if not dados["haoshoku_sorteado"]:

        dados["haoshoku"] = (
            random.randint(1, 100)
            <= CHANCE_HAOSHOKU
        )

        dados["haoshoku_sorteado"] = True

    if not dados["prodigio_sorteado"]:

        dados["prodigio"] = (
            random.randint(1, 100)
            <= CHANCE_PRODIGIO
        )

        dados["prodigio_sorteado"] = True


# =========================================================
# EMBED PRINCIPAL
# =========================================================

def criar_embed(usuario):

    dados = obter_rascunho(
        usuario.id
    )

    nome = (
        dados["nome"]
        or "Não definido"
    )

    idade = (
        f"{dados['idade']} anos"
        if dados["idade"]
        else "Não definida"
    )

    raca = (
        dados["raca"]
        or "Não sorteada"
    )

    familia = (
        dados["familia"]
        or "Não sorteada"
    )

    faccao = (
        dados["faccao"]
        or "Não definida"
    )

    profissao = (
        dados["profissao"]
        or "Não definida"
    )

    classe = (
        dados["classe"]
        or "Não definida"
    )

    estilo = (
        dados.get("estilo")
        or "Não definido"
    )

    embed = discord.Embed(
        title="🏴‍☠️ Criação de Personagem",
        description=(
            "**Sea's Paradise**\n\n"
            "Configure seu personagem usando "
            "os botões abaixo."
        )
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Nome:** {nome}\n"
            f"**Idade:** {idade}\n"
            f"**Raça:** {raca}\n"
            f"**Família:** {familia}"
        ),
        inline=False
    )

    embed.add_field(
        name="🌊 Caminho",
        value=(
            f"**Facção:** {faccao}\n"
            f"**Profissão:** {profissao}\n"
            f"**Classe:** {classe}\n"
            f"**Estilo inicial:** {estilo}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Atributos",
        value=(
            f"💪 **Força:** {dados['forca']}\n"
            f"🛡️ **Resistência:** "
            f"{dados['resistencia']}\n"
            f"💨 **Velocidade/Agilidade:** "
            f"{dados['velocidade']}\n\n"
            f"✨ **Pontos:** {dados['pontos']}"
        ),
        inline=False
    )

    haoshoku = (
        "👑 Sim"
        if dados["haoshoku"]
        else "❔ Oculto"
    )

    prodigio = (
        "🌟 Sim"
        if dados["prodigio"]
        else "❔ Oculto"
    )

    embed.add_field(
        name="✨ Potenciais",
        value=(
            f"**Haoshoku:** {haoshoku}\n"
            f"**Prodígio:** {prodigio}"
        ),
        inline=False
    )

    if dados.get("imagem"):

        embed.set_image(
            url=dados["imagem"]
        )

    embed.set_footer(
        text=(
            "Sea's Paradise • "
            "Criação de Personagem"
        )
    )

    return embed


# =========================================================
# VIEW BASE
# =========================================================

class ViewDoJogador(
    discord.ui.View
):

    def __init__(
        self,
        dono_id,
        confirmar_callback=None
    ):

        super().__init__(
            timeout=600
        )

        self.dono_id = dono_id
        self.confirmar_callback = confirmar_callback

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.dono_id:

            await interaction.response.send_message(
                "❌ Este painel pertence "
                "a outro jogador.",
                ephemeral=True
            )

            return False

        # NÃO encerramos a criação caso o rascunho
        # tenha sumido por algum motivo.
        # Recuperamos um rascunho para evitar
        # o antigo "criação não está mais ativa".

        obter_rascunho(
            self.dono_id
        )

        return True


# =========================================================
# MODAL — NOME
# =========================================================

class NomeModal(
    discord.ui.Modal,
    title="Nome do Personagem"
):

    nome = discord.ui.TextInput(
        label="Nome",
        placeholder="Digite o nome do personagem",
        min_length=2,
        max_length=40
    )

    def __init__(
        self,
        confirmar_callback=None
    ):

        super().__init__()

        self.confirmar_callback = (
            confirmar_callback
        )

    async def on_submit(
        self,
        interaction
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

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
# MODAL — IDADE
# =========================================================

class IdadeModal(
    discord.ui.Modal,
    title="Idade do Personagem"
):

    idade = discord.ui.TextInput(
        label="Idade",
        placeholder="Exemplo: 19",
        min_length=1,
        max_length=3
    )

    def __init__(
        self,
        confirmar_callback=None
    ):

        super().__init__()

        self.confirmar_callback = (
            confirmar_callback
        )

    async def on_submit(
        self,
        interaction
    ):

        try:

            idade = int(
                self.idade.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite uma idade válida.",
                ephemeral=True
            )

            return

        if not (
            IDADE_MINIMA
            <= idade
            <= IDADE_MAXIMA
        ):

            await interaction.response.send_message(
                f"❌ A idade deve ficar entre "
                f"{IDADE_MINIMA} e "
                f"{IDADE_MAXIMA} anos.",
                ephemeral=True
            )

            return

        dados = obter_rascunho(
            interaction.user.id
        )

        dados["idade"] = idade

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
# MODAL — IMAGEM
# =========================================================

class ImagemModal(
    discord.ui.Modal,
    title="Imagem do Personagem"
):

    imagem = discord.ui.TextInput(
        label="URL da imagem",
        placeholder="https://...",
        required=False,
        max_length=500
    )

    def __init__(
        self,
        confirmar_callback=None
    ):

        super().__init__()

        self.confirmar_callback = (
            confirmar_callback
        )

    async def on_submit(
        self,
        interaction
    ):

        url = (
            self.imagem.value.strip()
        )

        dados = obter_rascunho(
            interaction.user.id
        )

        dados["imagem"] = (
            url
            if url
            else None
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
# SELECT — FACÇÃO
# =========================================================

class FaccaoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        self.dono_id = dono_id
        self.confirmar_callback = (
            confirmar_callback
        )

        options = [
            discord.SelectOption(
                label=item
            )
            for item in FACCOES
        ]

        super().__init__(
            placeholder="Escolha sua facção",
            options=options
        )

    async def callback(
        self,
        interaction
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        dados["faccao"] = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


class FaccaoView(
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

        self.add_item(
            FaccaoSelect(
                dono_id,
                confirmar_callback
            )
        )


# =========================================================
# SELECT — PROFISSÃO
# =========================================================

class ProfissaoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        self.dono_id = dono_id
        self.confirmar_callback = (
            confirmar_callback
        )

        options = [
            discord.SelectOption(
                label=item
            )
            for item in PROFISSOES
        ]

        super().__init__(
            placeholder="Escolha sua profissão",
            options=options
        )

    async def callback(
        self,
        interaction
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        dados["profissao"] = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


class ProfissaoView(
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

        self.add_item(
            ProfissaoSelect(
                dono_id,
                confirmar_callback
            )
        )


# =========================================================
# SELECT — CLASSE
# =========================================================

class ClasseSelect(
    discord.ui.Select
):

    def __init__(
        self,
        dono_id,
        confirmar_callback
    ):

        self.dono_id = dono_id
        self.confirmar_callback = (
            confirmar_callback
        )

        options = [
            discord.SelectOption(
                label=item
            )
            for item in CLASSES
        ]

        super().__init__(
            placeholder="Escolha sua classe",
            options=options
        )

    async def callback(
        self,
        interaction
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        dados["classe"] = (
            self.values[0]
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


class ClasseView(
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

        self.add_item(
            ClasseSelect(
                dono_id,
                confirmar_callback
            )
        )


# =========================================================
# SELECT — ESTILO INICIAL
# =========================================================

class EstiloSelect(discord.ui.Select):
    def __init__(self, dono_id, confirmar_callback):
        self.dono_id = dono_id
        self.confirmar_callback = confirmar_callback
        options = [discord.SelectOption(label=item[:100], value=item) for item in ESTILOS[:25]]
        super().__init__(placeholder="Escolha seu estilo de luta inicial", options=options)

    async def callback(self, interaction):
        dados = obter_rascunho(interaction.user.id)
        dados["estilo"] = self.values[0]
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=CriacaoView(self.dono_id, self.confirmar_callback)
        )


class EstiloView(ViewDoJogador):
    def __init__(self, dono_id, confirmar_callback):
        super().__init__(dono_id, confirmar_callback)
        self.add_item(EstiloSelect(dono_id, confirmar_callback))


# =========================================================
# VIEW PRINCIPAL
# =========================================================

class CriacaoView(
    ViewDoJogador
):

    def __init__(
        self,
        dono_id,
        confirmar_callback=None
    ):

        super().__init__(
            dono_id,
            confirmar_callback
        )


    # =====================================================
    # NOME
    # =====================================================

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


    # =====================================================
    # IDADE
    # =====================================================

    @discord.ui.button(
        label="Idade",
        emoji="🎂",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def idade(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            IdadeModal(
                self.confirmar_callback
            )
        )


    # =====================================================
    # IMAGEM
    # =====================================================

    @discord.ui.button(
        label="Imagem",
        emoji="🖼️",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def imagem(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            ImagemModal(
                self.confirmar_callback
            )
        )


    # =====================================================
    # RAÇA
    # =====================================================

    @discord.ui.button(
        label="Sortear Raça",
        emoji="🧬",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def raca(
        self,
        interaction,
        button
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        if dados["raca_sorteada"]:

            await interaction.response.send_message(
                "❌ Sua raça já foi sorteada.",
                ephemeral=True
            )

            return

        dados["raca"] = random.choice(
            RACAS
        )

        dados["raca_sorteada"] = True

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


    # =====================================================
    # FAMÍLIA
    # =====================================================

    @discord.ui.button(
        label="Sortear Família",
        emoji="🩸",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def familia(
        self,
        interaction,
        button
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        if dados["familia_sorteada"]:

            await interaction.response.send_message(
                "❌ Sua família já foi sorteada.",
                ephemeral=True
            )

            return

        dados["familia"] = (
            random.choice(
                FAMILIAS
            )
        )

        dados["familia_sorteada"] = True

        aplicar_beneficios_familia(
            dados
        )

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


    # =====================================================
    # FACÇÃO
    # =====================================================

    @discord.ui.button(
        label="Facção",
        emoji="🏴‍☠️",
        style=discord.ButtonStyle.secondary,
        row=2
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


    # =====================================================
    # PROFISSÃO
    # =====================================================

    @discord.ui.button(
        label="Profissão",
        emoji="🛠️",
        style=discord.ButtonStyle.secondary,
        row=2
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
            view=ProfissaoView(
                self.dono_id,
                self.confirmar_callback
            )
        )


    # =====================================================
    # CLASSE
    # =====================================================

    @discord.ui.button(
        label="Classe",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary,
        row=2
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
            view=ClasseView(
                self.dono_id,
                self.confirmar_callback
            )
        )


    # =====================================================
    # ESTILO INICIAL
    # =====================================================

    @discord.ui.button(
        label="Estilo",
        emoji="🥋",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def estilo(self, interaction, button):
        if not ESTILOS:
            await interaction.response.send_message(
                "❌ O catálogo de estilos está vazio.",
                ephemeral=True
            )
            return
        await interaction.response.edit_message(
            embed=criar_embed(interaction.user),
            view=EstiloView(self.dono_id, self.confirmar_callback)
        )


    # =====================================================
    # CONFIRMAR
    # =====================================================

    @discord.ui.button(
        label="Criar Personagem",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def confirmar(
        self,
        interaction,
        button
    ):

        dados = obter_rascunho(
            interaction.user.id
        )

        obrigatorios = {
            "nome": "Nome",
            "idade": "Idade",
            "raca": "Raça",
            "familia": "Família",
            "faccao": "Facção",
            "profissao": "Profissão",
            "classe": "Classe",
            "estilo": "Estilo de luta inicial",
        }

        faltando = []

        for chave, nome in obrigatorios.items():

            if not dados.get(chave):
                faltando.append(nome)

        if faltando:

            await interaction.response.send_message(
                "❌ Ainda falta definir: "
                + ", ".join(faltando)
                + ".",
                ephemeral=True
            )

            return

        sortear_talentos(
            dados
        )

        if not self.confirmar_callback:

            await interaction.response.send_message(
                "❌ Callback de confirmação "
                "não configurado.",
                ephemeral=True
            )

            return

        await self.confirmar_callback(
            interaction
        )
