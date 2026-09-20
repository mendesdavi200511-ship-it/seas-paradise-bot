import random
import discord

from data.racas import RACAS
from data.familias import FAMILIAS
from data.profissoes import PROFISSOES
from data.classes import CLASSES
from data.skills import ESTILOS


# =========================================================
# SEA'S PARADISE
# VIEW — CRIAÇÃO DE PERSONAGEM
# =========================================================


# =========================================================
# CONFIGURAÇÕES
# =========================================================

PONTOS_INICIAIS = 30
ATRIBUTO_MAXIMO = 50000

CHANCE_HAOSHOKU = 2
CHANCE_PRODIGIO = 1

TIMEOUT_PAINEL = 20


# =========================================================
# ESCALA DE ATRIBUTOS
# =========================================================

ESCALA_ATRIBUTOS = [
    (50000, "Lendário"),
    (25000, "Titânico"),
    (10000, "Sobre-Humano"),
    (5000, "Monstruoso"),
    (2000, "Excepcional"),
    (1000, "Muito Forte"),
    (600, "Forte"),
    (350, "Bom"),
    (200, "Mediano"),
    (100, "Normal"),
    (50, "Fraco"),
    (20, "Muito Fraco"),
]


# =========================================================
# PESOS DAS RAÇAS
# Quanto MENOR, mais difícil.
# =========================================================

PESOS_RACAS = {
    "Humano": 100,
    "Homem-Peixe": 35,
    "Sereiano": 25,
    "Mink": 22,
    "Gigante": 15,
    "Tontatta": 14,
    "Skypiean": 18,
    "Birkan": 12,
    "Shandian": 16,
    "Lunarian": 1,
    "Kuja": 8,
    "Bucaneiro": 2,
    "Oni": 2,
    "Long-Leg": 15,
    "Long-Arm": 15,
    "Long-Neck": 15,
    "Corpo Modificado": 3,
}


# =========================================================
# PESOS INDIVIDUAIS DAS FAMÍLIAS
#
# Quanto MENOR o peso, mais difícil cair.
#
# Não usamos apenas "Rara / Lendária / Mítica".
# O personagem principal da linhagem também pesa.
# =========================================================

PESOS_FAMILIAS = {

    # -------------------------
    # EXTREMAMENTE RARAS
    # -------------------------

    "Nerona": 1,
    "Gol": 1,
    "Rocks": 1,

    # -------------------------
    # MÍTICAS / ALTÍSSIMO NÍVEL
    # -------------------------

    "Figarland": 2,

    # -------------------------
    # LENDÁRIAS MUITO FORTES
    # -------------------------

    "Kaido": 3,
    "Monkey": 4,
    "Charlotte": 4,
    "Shimotsuki": 5,
    "Kozuki": 6,

    # -------------------------
    # LENDÁRIAS
    # -------------------------

    "Sengoku": 7,
    "Sakazuki": 7,
    "Borsalino": 7,

    # -------------------------
    # RARAS PODEROSAS
    # -------------------------

    "Vinsmoke": 10,
    "Donquixote": 11,
    "Enel": 12,

    # -------------------------
    # RARAS
    # -------------------------

    "Crocodile": 16,
    "Smoker": 18,
    "Nefertari": 18,
    "Neptune": 18,
    "Riku": 20,

    # -------------------------
    # DRAGÕES CELESTIAIS
    # -------------------------

    "Rosward": 14,
    "Saint": 14,
    "Manmayer": 14,
}


# =========================================================
# ESTADO DAS CRIAÇÕES
# =========================================================

criando = {}


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor):
    return f"{valor:,}".replace(",", ".")


def nivel_atributo(valor):

    for minimo, nome in ESCALA_ATRIBUTOS:

        if valor >= minimo:
            return nome

    return "Muito Fraco"


def sortear_percentual(chance):

    return random.randint(
        1,
        100
    ) <= chance


def sortear_ponderado(
    catalogo,
    pesos
):

    nomes = list(
        catalogo.keys()
    )

    lista_pesos = [
        pesos.get(
            nome,
            10
        )
        for nome in nomes
    ]

    return random.choices(
        nomes,
        weights=lista_pesos,
        k=1
    )[0]


def sortear_raca():

    return sortear_ponderado(
        RACAS,
        PESOS_RACAS
    )


def sortear_familia():

    return sortear_ponderado(
        FAMILIAS,
        PESOS_FAMILIAS
    )


# =========================================================
# RASCUNHO
# =========================================================

def novo_rascunho():

    return {
        "nome": None,
        "idade": None,
        "imagem": None,

        "raca": "Não sorteada",
        "familia": "Não sorteada",

        "raca_sorteada": False,
        "familia_sorteada": False,

        "haoshoku": None,
        "haoshoku_sorteado": False,

        "prodigio": None,
        "prodigio_sorteado": False,

        "faccao": "Civil",

        "profissao": "Nenhuma",
        "classe": "Nenhuma",
        "estilo": "Nenhum",

        "forca": 0,
        "resistencia": 0,
        "velocidade": 0,

        "pontos": PONTOS_INICIAIS
    }


# =========================================================
# RESULTADO HAOUSHOKU / PRODÍGIO
# =========================================================

def texto_resultado(valor, sorteado):

    if not sorteado:
        return "Não sorteado"

    if valor:
        return "✅ Sim"

    return "❌ Não"


# =========================================================
# EMBED PRINCIPAL
# =========================================================

def criar_embed(usuario):

    dados = criando.get(
        usuario.id
    )

    if not dados:

        return discord.Embed(
            title="❌ Criação encerrada",
            description=(
                "Use `!criar` para começar novamente."
            )
        )

    embed = discord.Embed(
        title="🏴‍☠️ CRIAÇÃO DE PERSONAGEM",
        description=(
            "Monte seu personagem para entrar no mundo de "
            "**Sea's Paradise**.\n\n"
            "🧬 Raça, 🩸 Família, 👑 Haoshoku e "
            "🌟 Prodígio são definidos por **sorteio único**."
        )
    )

    # =====================================================
    # IMAGEM
    # =====================================================

    if dados.get("imagem"):

        embed.set_thumbnail(
            url=dados["imagem"]
        )

    else:

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

    # =====================================================
    # IDENTIDADE
    # =====================================================

    idade = dados.get(
        "idade"
    )

    idade_texto = (
        f"{idade} anos"
        if idade is not None
        else "Não definida"
    )

    embed.add_field(
        name="👤 Identidade",
        value=(
            f"**Nome:** "
            f"{dados['nome'] or 'Não definido'}\n"

            f"**Idade:** "
            f"{idade_texto}\n"

            f"**Raça:** "
            f"{dados['raca']}\n"

            f"**Família:** "
            f"{dados['familia']}"
        ),
        inline=False
    )

    # =====================================================
    # CAMINHO
    # =====================================================

    embed.add_field(
        name="🌊 Caminho",
        value=(
            f"**Facção:** "
            f"{dados['faccao']}\n"

            f"**Profissão:** "
            f"{dados['profissao']}\n"

            f"**Classe:** "
            f"{dados['classe']}\n"

            f"**Estilo Inicial:** "
            f"{dados['estilo']}"
        ),
        inline=False
    )

    # =====================================================
    # TALENTOS
    # =====================================================

    embed.add_field(
        name="✨ Talentos",
        value=(
            f"👑 **Haoshoku:** "
            f"{texto_resultado(
                dados['haoshoku'],
                dados['haoshoku_sorteado']
            )}\n"

            f"🌟 **Prodígio:** "
            f"{texto_resultado(
                dados['prodigio'],
                dados['prodigio_sorteado']
            )}"
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
            f"{formatar_numero(dados['forca'])} "
            f"— {nivel_atributo(dados['forca'])}\n"

            f"🛡️ **Resistência:** "
            f"{formatar_numero(dados['resistencia'])} "
            f"— {nivel_atributo(dados['resistencia'])}\n"

            f"💨 **Velocidade/Agilidade:** "
            f"{formatar_numero(dados['velocidade'])} "
            f"— {nivel_atributo(dados['velocidade'])}\n\n"

            f"✨ **Pontos disponíveis:** "
            f"{formatar_numero(dados['pontos'])}"
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "Sea's Paradise • "
            "Painel expira após 20 segundos"
        )
    )

    return embed


# =========================================================
# BASE DAS VIEWS
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
            timeout=TIMEOUT_PAINEL
        )

        self.dono_id = dono_id
        self.confirmar_callback = confirmar_callback

        self.message = None

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
                "a outro jogador.",
                ephemeral=True
            )

            return False

        return True

    async def on_timeout(self):

        criando.pop(
            self.dono_id,
            None
        )

        if self.message:

            try:

                await self.message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

    def painel_principal(self):

        return CriacaoView(
            self.dono_id,
            self.confirmar_callback
        )


# =========================================================
# MODAL — NOME
# =========================================================

class NomeModal(
    discord.ui.Modal
):

    def __init__(
        self,
        confirmar_callback
    ):

        super().__init__(
            title="Nome do Personagem"
        )

        self.confirmar_callback = (
            confirmar_callback
        )

        self.nome = discord.ui.TextInput(
            label="Nome",
            placeholder="Ex: Monkey D. Luffy",
            min_length=2,
            max_length=40
        )

        self.add_item(
            self.nome
        )

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
# MODAL — IDADE
# =========================================================

class IdadeModal(
    discord.ui.Modal
):

    def __init__(
        self,
        confirmar_callback
    ):

        super().__init__(
            title="Idade do Personagem"
        )

        self.confirmar_callback = (
            confirmar_callback
        )

        self.idade = discord.ui.TextInput(
            label="Idade",
            placeholder="Ex: 21",
            min_length=1,
            max_length=3
        )

        self.add_item(
            self.idade
        )

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

        if idade < 1 or idade > 999:

            await interaction.response.send_message(
                "❌ A idade precisa estar entre "
                "**1 e 999 anos**.",
                ephemeral=True
            )

            return

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
    discord.ui.Modal
):

    def __init__(
        self,
        confirmar_callback
    ):

        super().__init__(
            title="Imagem do Personagem"
        )

        self.confirmar_callback = (
            confirmar_callback
        )

        self.imagem = discord.ui.TextInput(
            label="Link da imagem",
            placeholder="https://...",
            min_length=8,
            max_length=500
        )

        self.add_item(
            self.imagem
        )

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

        url = (
            self.imagem.value.strip()
        )

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):

            await interaction.response.send_message(
                "❌ Envie um link válido começando "
                "com `http://` ou `https://`.",
                ephemeral=True
            )

            return

        dados["imagem"] = url

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
# FACÇÕES
# =========================================================

FACCOES = {
    "Pirata": "🏴‍☠️",
    "Marinha": "⚓",
    "Revolucionário": "🔥",
    "Civil": "🏝️"
}


class FaccaoSelect(
    discord.ui.Select
):

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
# CATÁLOGO GENÉRICO
# PROFISSÃO / CLASSE / ESTILO
# =========================================================

class CatalogoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        campo,
        catalogo,
        placeholder
    ):

        self.campo = campo

        opcoes = []

        for nome, dados in list(
            catalogo.items()
        )[:25]:

            emoji = None
            descricao = None

            if isinstance(
                dados,
                dict
            ):

                emoji = dados.get(
                    "emoji"
                )

                descricao_original = (
                    dados.get(
                        "descricao"
                    )
                )

                if descricao_original:

                    if (
                        len(descricao_original)
                        > 100
                    ):

                        descricao = (
                            descricao_original[:97]
                            + "..."
                        )

                    else:

                        descricao = (
                            descricao_original
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

        dados[
            self.campo
        ] = self.values[0]

        view = self.view

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=view.painel_principal()
        )


class CatalogoView(
    ViewDoJogador
):

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
# ATRIBUTOS — SELECT
# =========================================================

class CriacaoAtributoSelect(
    discord.ui.Select
):

    def __init__(self):

        super().__init__(
            placeholder="Escolha o atributo...",
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
# ATRIBUTOS — QUANTIDADE
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

        atributo = (
            view.atributo
        )

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
# ATRIBUTOS — VIEW
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

        # Como a criação agora começa com 30,
        # não há motivo para +50/+100/+300 aqui.
        for quantidade in (
            1,
            5,
            10,
            20,
            30
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
# APLICAR EFEITOS AUTOMÁTICOS DA FAMÍLIA
# =========================================================

def aplicar_efeitos_familia(
    dados
):

    familia = dados[
        "familia"
    ]

    # =====================================================
    # VINSMOKE
    # Raça obrigatória
    # =====================================================

    if familia == "Vinsmoke":

        dados["raca"] = (
            "Corpo Modificado"
        )

        dados["raca_sorteada"] = True

    # =====================================================
    # ENEL
    # Raça obrigatória
    # =====================================================

    elif familia == "Enel":

        dados["raca"] = (
            "Birkan"
        )

        dados["raca_sorteada"] = True

    # =====================================================
    # FAMÍLIAS COM QUALIDADE DE REI / HAOUSHOKU
    # =====================================================

    if familia in {
        "Monkey",
        "Rocks",
        "Gol"
    }:

        dados["haoshoku"] = True
        dados["haoshoku_sorteado"] = True

    # =====================================================
    # FAMÍLIAS COM PRODÍGIO AUTOMÁTICO
    # =====================================================

    if familia in {
        "Rocks",
        "Sengoku"
    }:

        dados["prodigio"] = True
        dados["prodigio_sorteado"] = True


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

    #
    =====================================================
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
        style=discord.ButtonStyle.primary,
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
    # RAÇA — SORTEIO ÚNICO
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

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        if dados[
            "raca_sorteada"
        ]:

            await interaction.response.send_message(
                "❌ Sua raça já foi definida.",
                ephemeral=True
            )

            return

        dados["raca"] = (
            sortear_raca()
        )

        dados[
            "raca_sorteada"
        ] = True

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                interaction.user.id,
                self.confirmar_callback
            )
        )

    # =====================================================
    # FAMÍLIA — SORTEIO ÚNICO
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

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação expirou.",
                ephemeral=True
            )

            return

        if dados[
            "familia_sorteada"
        ]:

            await interaction.response.send_message(
                "❌ Sua família já foi definida.",
                ephemeral=True
            )

            return

        dados["familia"] = (
            sortear_familia()
        )

        dados[
            "familia_sorteada"
        ] = True

        aplicar_efeitos_familia(
            dados
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

    # =====================================================
    # HAOUSHOKU — 2%
    # =====================================================

    @discord.ui.button(
        label="Sortear Haoshoku",
        emoji="👑",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def haoshoku(
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

        if dados[
            "haoshoku_sorteado"
        ]:

            await interaction.response.send_message(
                "❌ O Haoshoku deste personagem "
                "já foi definido.",
                ephemeral=True
            )

            return

        dados["haoshoku"] = (
            sortear_percentual(
                CHANCE_HAOSHOKU
            )
        )

        dados[
            "haoshoku_sorteado"
        ] = True

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                interaction.user.id,
                self.confirmar_callback
            )
        )

    # =====================================================
    # PRODÍGIO — 1%
    # =====================================================

    @discord.ui.button(
        label="Sortear Prodígio",
        emoji="🌟",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def prodigio(
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

        if dados[
            "prodigio_sorteado"
        ]:

            await interaction.response.send_message(
                "❌ O Prodígio deste personagem "
                "já foi definido.",
                ephemeral=True
            )

            return

        dados["prodigio"] = (
            sortear_percentual(
                CHANCE_PRODIGIO
            )
        )

        dados[
            "prodigio_sorteado"
        ] = True

        await interaction.response.edit_message(
            embed=criar_embed(
                interaction.user
            ),
            view=CriacaoView(
                interaction.user.id,
                self.confirmar_callback
            )
        )

    # =====================================================
    # FACÇÃO
    # =====================================================

    @discord.ui.button(
        label="Facção",
        emoji="🌊",
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
        row=3
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

    # =====================================================
    # CLASSE
    # =====================================================

    @discord.ui.button(
        label="Classe",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary,
        row=3
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

    #
        # ESTILO INICIAL
    # =====================================================

    @discord.ui.button(
        label="Estilo",
        emoji="🥋",
        style=discord.ButtonStyle.secondary,
        row=3
    )
    async def estilo(
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
                "estilo",
                ESTILOS,
                "Escolha seu estilo inicial..."
            )
        )

    # =====================================================
    # ATRIBUTOS
    # =====================================================

    @discord.ui.button(
        label="Atributos",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        row=4
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

    # =====================================================
    # CONFIRMAR
    # =====================================================

    @discord.ui.button(
        label="Confirmar Personagem",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=4
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
            )

            return

        dados = criando.get(
            interaction.user.id
        )

        if not dados:

            await interaction.response.send_message(
                "❌ Sua criação não está mais ativa.",
                ephemeral=True
            )

            return

        # =================================================
        # NOME
        # =================================================

        if not dados[
            "nome"
        ]:

            await interaction.response.send_message(
                "❌ Defina o **nome** do personagem.",
                ephemeral=True
            )

            return

        # =================================================
        # IDADE
        # =================================================

        if dados[
            "idade"
        ] is None:

            await interaction.response.send_message(
                "❌ Defina a **idade** do personagem.",
                ephemeral=True
            )

            return

        # =================================================
        # RAÇA
        # =================================================

        if not dados[
            "raca_sorteada"
        ]:

            await interaction.response.send_message(
                "❌ Faça o sorteio da **raça**.",
                ephemeral=True
            )

            return

        # =================================================
        # FAMÍLIA
        # =================================================

        if not dados[
            "familia_sorteada"
        ]:

            await interaction.response.send_message(
                "❌ Faça o sorteio da **família**.",
                ephemeral=True
            )

            return

        # =================================================
        # HAOUSHOKU
        # =================================================

        if not dados[
            "haoshoku_sorteado"
        ]:

            await interaction.response.send_message(
                "❌ Faça o sorteio de **Haoshoku**.",
                ephemeral=True
            )

            return

        # =================================================
        # PRODÍGIO
        # =================================================

        if not dados[
            "prodigio_sorteado"
        ]:

            await interaction.response.send_message(
                "❌ Faça o sorteio de **Prodígio**.",
                ephemeral=True
            )

            return

        # =================================================
        # PROFISSÃO
        # =================================================

        if (
            dados["profissao"]
            == "Nenhuma"
        ):

            await interaction.response.send_message(
                "❌ Escolha uma **profissão**.",
                ephemeral=True
            )

            return

        # =================================================
        # CLASSE
        # =================================================

        if (
            dados["classe"]
            == "Nenhuma"
        ):

            await interaction.response.send_message(
                "❌ Escolha uma **classe**.",
                ephemeral=True
            )

            return

        # =================================================
        # ESTILO
        # =================================================

        if (
            dados["estilo"]
            == "Nenhum"
        ):

            await interaction.response.send_message(
                "❌ Escolha um **estilo inicial**.",
                ephemeral=True
            )

            return

        # =================================================
        # ATRIBUTOS
        # =================================================

        if dados[
            "pontos"
        ] > 0:

            await interaction.response.send_message(
                (
                    "❌ Você ainda possui "
                    f"**{dados['pontos']} pontos de atributo** "
                    "para distribuir."
                ),
                ephemeral=True
            )

            return

        # =================================================
        # SALVAR
        # =================================================

        await self.confirmar_callback(
            interaction
                )
