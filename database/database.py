import os
import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None


# =========================================================
# CONEXÃO
# =========================================================

async def conectar_banco():
    global _pool

    if _pool is not None:
        return _pool

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não foi configurado."
        )

    print("🐘 Conectando ao PostgreSQL...")

    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5
    )

    await criar_tabelas()

    print("🐘 PostgreSQL conectado!")
    print("📦 Banco do Sea's Paradise pronto!")

    return _pool


async def fechar_banco():
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None

        print("🔌 PostgreSQL desconectado.")


def get_pool():

    if _pool is None:
        raise RuntimeError(
            "O banco de dados ainda não foi conectado."
        )

    return _pool


# =========================================================
# TABELAS
# =========================================================

async def criar_tabelas():

    db = get_pool()

    async with db.acquire() as conn:

        # =================================================
        # FICHAS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fichas (
                user_id BIGINT PRIMARY KEY,

                nome TEXT NOT NULL,

                idade INTEGER NOT NULL
                    DEFAULT 18,

                imagem TEXT,

                raca TEXT NOT NULL
                    DEFAULT 'Não definida',

                familia TEXT NOT NULL
                    DEFAULT 'Não definida',

                faccao TEXT NOT NULL
                    DEFAULT 'Civil',

                profissao TEXT NOT NULL
                    DEFAULT 'Nenhuma',

                classe TEXT NOT NULL
                    DEFAULT 'Nenhuma',

                estilo TEXT NOT NULL
                    DEFAULT 'Nenhum',

                akuma TEXT NOT NULL
                    DEFAULT 'Nenhuma',

                despertar TEXT NOT NULL
                    DEFAULT 'Não',

                haoshoku BOOLEAN NOT NULL
                    DEFAULT FALSE,

                prodigio BOOLEAN NOT NULL
                    DEFAULT FALSE,

                forca INTEGER NOT NULL
                    DEFAULT 0,

                resistencia INTEGER NOT NULL
                    DEFAULT 0,

                velocidade INTEGER NOT NULL
                    DEFAULT 0,

                pontos_atributo INTEGER NOT NULL
                    DEFAULT 0,

                berries BIGINT NOT NULL
                    DEFAULT 0,

                reputacao BIGINT NOT NULL
                    DEFAULT 0,

                criado_em TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # MIGRAÇÕES
        # Compatibilidade com fichas antigas
        # =================================================

        migracoes = [

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS idade INTEGER
            NOT NULL DEFAULT 18;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS imagem TEXT;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS familia TEXT
            NOT NULL DEFAULT 'Não definida';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS faccao TEXT
            NOT NULL DEFAULT 'Civil';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS profissao TEXT
            NOT NULL DEFAULT 'Nenhuma';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS classe TEXT
            NOT NULL DEFAULT 'Nenhuma';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS estilo TEXT
            NOT NULL DEFAULT 'Nenhum';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS akuma TEXT
            NOT NULL DEFAULT 'Nenhuma';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS despertar TEXT
            NOT NULL DEFAULT 'Não';
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS haoshoku BOOLEAN
            NOT NULL DEFAULT FALSE;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS prodigio BOOLEAN
            NOT NULL DEFAULT FALSE;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS forca INTEGER
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS resistencia INTEGER
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS velocidade INTEGER
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS pontos_atributo INTEGER
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS berries BIGINT
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS reputacao BIGINT
            NOT NULL DEFAULT 0;
            """
        ]

        for migracao in migracoes:
            await conn.execute(migracao)

        # =================================================
        # CARTEIRA DE PONTOS DE DOMÍNIO
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pontos_percentuais (
                user_id BIGINT PRIMARY KEY,

                disponiveis INTEGER NOT NULL
                    DEFAULT 0,

                FOREIGN KEY (user_id)
                    REFERENCES fichas(user_id)
                    ON DELETE CASCADE
            );
        """)

        # =================================================
        # ROLAGENS DA CRIAÇÃO
        # Impede reroll ao fechar/reabrir o painel ou reiniciar o bot.
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS rolagens_criacao (
                user_id BIGINT PRIMARY KEY,
                raca TEXT,
                familia TEXT,
                haoshoku BOOLEAN,
                prodigio BOOLEAN,
                raca_sorteada BOOLEAN NOT NULL DEFAULT FALSE,
                familia_sorteada BOOLEAN NOT NULL DEFAULT FALSE,
                haoshoku_sorteado BOOLEAN NOT NULL DEFAULT FALSE,
                prodigio_sorteado BOOLEAN NOT NULL DEFAULT FALSE,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # ESPECIALIZAÇÕES / DOMÍNIOS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS especializacoes (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT NOT NULL,

                categoria TEXT NOT NULL,

                nome TEXT NOT NULL,

                porcentagem INTEGER NOT NULL
                    DEFAULT 0,

                limite INTEGER NOT NULL
                    DEFAULT 200,

                desbloqueado_por TEXT NOT NULL
                    DEFAULT 'admin',

                criado_em TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    user_id,
                    categoria,
                    nome
                ),

                FOREIGN KEY (user_id)
                    REFERENCES fichas(user_id)
                    ON DELETE CASCADE
            );
        """)

        # =================================================
        # MUNDO PERSISTENTE — NPCS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS npcs_mundo (
                id BIGSERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                nome_chave TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'vivo',
                localizacao TEXT,
                faccao TEXT,
                recrutado_por BIGINT,
                disponivel BOOLEAN NOT NULL DEFAULT TRUE,
                dados TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memorias_npc (
                id BIGSERIAL PRIMARY KEY,
                npc_id BIGINT NOT NULL,
                user_id BIGINT,
                personagem_nome TEXT,
                resumo TEXT NOT NULL,
                importancia INTEGER NOT NULL DEFAULT 1,
                permanente BOOLEAN NOT NULL DEFAULT FALSE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (npc_id) REFERENCES npcs_mundo(id) ON DELETE CASCADE
            );
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memorias_npc_npc_id
            ON memorias_npc(npc_id, criado_em DESC);
        """)

        # =================================================
        # LOCALIZAÇÃO PERSISTENTE — JOGADORES / ACESSO NPC
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS localizacoes_jogador (
                user_id BIGINT PRIMARY KEY,
                localizacao TEXT,
                area TEXT,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES fichas(user_id) ON DELETE CASCADE
            );
        """)

        # Estado autoritativo do personagem. O canal do Discord nunca sobrescreve
        # automaticamente estes campos depois que a localização foi estabelecida.
        for migracao_estado_player in [
            "ALTER TABLE localizacoes_jogador ADD COLUMN IF NOT EXISTS estado TEXT NOT NULL DEFAULT 'livre';",
            "ALTER TABLE localizacoes_jogador ADD COLUMN IF NOT EXISTS custodia TEXT;",
            "ALTER TABLE localizacoes_jogador ADD COLUMN IF NOT EXISTS restricoes TEXT;",
            "ALTER TABLE localizacoes_jogador ADD COLUMN IF NOT EXISTS combate_ativo BOOLEAN NOT NULL DEFAULT FALSE;",
        ]:
            await conn.execute(migracao_estado_player)

        # =================================================
        # MUNDO PERSISTENTE — EVENTOS E CONSEQUÊNCIAS GLOBAIS
        # Estes registros NÃO possuem FK para fichas de propósito:
        # a história causada por um personagem continua existindo após sua morte.
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS eventos_mundo (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                personagem_nome TEXT NOT NULL,
                localizacao TEXT,
                area TEXT,
                tipo TEXT NOT NULL DEFAULT 'acontecimento',
                resumo TEXT NOT NULL,
                gravidade INTEGER NOT NULL DEFAULT 1,
                alcance TEXT NOT NULL DEFAULT 'local',
                testemunhas BOOLEAN NOT NULL DEFAULT FALSE,
                marinha_sabe BOOLEAN NOT NULL DEFAULT FALSE,
                governo_sabe BOOLEAN NOT NULL DEFAULT FALSE,
                piratas_sabem BOOLEAN NOT NULL DEFAULT FALSE,
                publico_sabe BOOLEAN NOT NULL DEFAULT FALSE,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_eventos_mundo_local
            ON eventos_mundo(localizacao, ativo, criado_em DESC);
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_eventos_mundo_personagem
            ON eventos_mundo(personagem_nome, criado_em DESC);
        """)

        for migracao_mundo in [
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS area TEXT;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS nivel_acesso TEXT NOT NULL DEFAULT 'normal';",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS encontravel_aleatoriamente BOOLEAN NOT NULL DEFAULT TRUE;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS forca INTEGER;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS resistencia INTEGER;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS velocidade INTEGER;",
        ]:
            await conn.execute(migracao_mundo)


        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reputacoes_mundo (
                personagem_nome TEXT PRIMARY KEY,
                procurado BOOLEAN NOT NULL DEFAULT FALSE,
                recompensa BIGINT NOT NULL DEFAULT 0,
                nivel_ameaca INTEGER NOT NULL DEFAULT 0,
                marinha INTEGER NOT NULL DEFAULT 0,
                governo INTEGER NOT NULL DEFAULT 0,
                piratas INTEGER NOT NULL DEFAULT 0,
                civis INTEGER NOT NULL DEFAULT 0,
                ultima_localizacao TEXT,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS noticias_mundo (
                id BIGSERIAL PRIMARY KEY,
                evento_id BIGINT,
                personagem_nome TEXT NOT NULL,
                manchete TEXT NOT NULL,
                corpo TEXT NOT NULL,
                alcance TEXT NOT NULL DEFAULT 'regional',
                publicado BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # SESSÕES DE NARRAÇÃO — MULTIPLAYER PERSISTENTE
        # Sem limite artificial de participantes.
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_narracao (
                id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT,
                channel_id BIGINT NOT NULL,
                localizacao TEXT,
                area TEXT,
                status TEXT NOT NULL DEFAULT 'ativa',
                resumo_final TEXT,
                criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                encerrada_em TIMESTAMP
            );
        """)
        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS jogadores_esperados INTEGER;")
        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS iniciada BOOLEAN NOT NULL DEFAULT FALSE;")
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_sessao_ativa_canal
            ON sessoes_narracao(channel_id)
            WHERE status = 'ativa';
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS participantes_sessao (
                sessao_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                personagem_nome TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ativo',
                entrou_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                saiu_em TIMESTAMP,
                PRIMARY KEY (sessao_id, user_id),
                FOREIGN KEY (sessao_id) REFERENCES sessoes_narracao(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_participantes_sessao_ativos
            ON participantes_sessao(sessao_id, status);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS turnos_sessao (
                id BIGSERIAL PRIMARY KEY,
                sessao_id BIGINT NOT NULL,
                user_id BIGINT,
                personagem_nome TEXT NOT NULL,
                acao TEXT NOT NULL,
                narracao TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sessao_id) REFERENCES sessoes_narracao(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_turnos_sessao
            ON turnos_sessao(sessao_id, id DESC);
        """)


        # =================================================
        # COMBATE COLETIVO — rodadas sem limite de players
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS combates_sessao (
                id BIGSERIAL PRIMARY KEY, sessao_id BIGINT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ativo', rodada INTEGER NOT NULL DEFAULT 1,
                primeira_rodada BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, encerrado_em TIMESTAMP,
                FOREIGN KEY (sessao_id) REFERENCES sessoes_narracao(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_combate_ativo_sessao
            ON combates_sessao(sessao_id) WHERE status='ativo';
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS participantes_combate (
                combate_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
                personagem_nome TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ativo',
                entrou_rodada INTEGER NOT NULL DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(combate_id,user_id),
                FOREIGN KEY (combate_id) REFERENCES combates_sessao(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acoes_rodada (
                combate_id BIGINT NOT NULL, rodada INTEGER NOT NULL, user_id BIGINT NOT NULL,
                personagem_nome TEXT NOT NULL, acao TEXT, pulou BOOLEAN NOT NULL DEFAULT FALSE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(combate_id,rodada,user_id),
                FOREIGN KEY (combate_id) REFERENCES combates_sessao(id) ON DELETE CASCADE
            );
        """)

        # =================================================
        # GARANTIR CARTEIRA PARA FICHAS ANTIGAS
        # =================================================

        await conn.execute("""
            INSERT INTO pontos_percentuais (
                user_id,
                disponiveis
            )

            SELECT
                user_id,
                0

            FROM fichas

            ON CONFLICT (user_id)
            DO NOTHING;
        """)


# =========================================================
# ROLAGENS PERSISTENTES DA CRIAÇÃO
# =========================================================

async def buscar_rolagem_criacao(user_id):
    db = get_pool()
    return await db.fetchrow(
        """
        SELECT * FROM rolagens_criacao
        WHERE user_id = $1;
        """,
        user_id
    )


async def salvar_rolagem_criacao(
    user_id,
    raca=None,
    familia=None,
    haoshoku=None,
    prodigio=None,
    raca_sorteada=False,
    familia_sorteada=False,
    haoshoku_sorteado=False,
    prodigio_sorteado=False
):
    db = get_pool()
    await db.execute(
        """
        INSERT INTO rolagens_criacao (
            user_id, raca, familia, haoshoku, prodigio,
            raca_sorteada, familia_sorteada,
            haoshoku_sorteado, prodigio_sorteado
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        ON CONFLICT (user_id) DO UPDATE SET
            raca = COALESCE(EXCLUDED.raca, rolagens_criacao.raca),
            familia = COALESCE(EXCLUDED.familia, rolagens_criacao.familia),
            haoshoku = COALESCE(EXCLUDED.haoshoku, rolagens_criacao.haoshoku),
            prodigio = COALESCE(EXCLUDED.prodigio, rolagens_criacao.prodigio),
            raca_sorteada = rolagens_criacao.raca_sorteada OR EXCLUDED.raca_sorteada,
            familia_sorteada = rolagens_criacao.familia_sorteada OR EXCLUDED.familia_sorteada,
            haoshoku_sorteado = rolagens_criacao.haoshoku_sorteado OR EXCLUDED.haoshoku_sorteado,
            prodigio_sorteado = rolagens_criacao.prodigio_sorteado OR EXCLUDED.prodigio_sorteado,
            atualizado_em = CURRENT_TIMESTAMP;
        """,
        user_id, raca, familia, haoshoku, prodigio,
        raca_sorteada, familia_sorteada,
        haoshoku_sorteado, prodigio_sorteado
    )


async def resetar_rolagem_criacao(user_id):
    db = get_pool()
    return await db.execute(
        "DELETE FROM rolagens_criacao WHERE user_id = $1;",
        user_id
    )


# =========================================================
# FICHAS
# =========================================================

async def possui_ficha(user_id):

    db = get_pool()

    return await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1
            FROM fichas
            WHERE user_id = $1
        );
        """,
        user_id
    )


async def buscar_ficha(user_id):

    db = get_pool()

    return await db.fetchrow(
        """
        SELECT *
        FROM fichas
        WHERE user_id = $1;
        """,
        user_id
    )


async def criar_ficha(
    user_id,
    nome,
    idade=18,
    raca="Não definida",
    familia="Não definida",
    faccao="Civil",
    profissao="Nenhuma",
    classe="Nenhuma",
    estilo="Nenhum",
    akuma="Nenhuma",
    despertar="Não",
    haoshoku=False,
    prodigio=False,
    imagem=None,
    forca=0,
    resistencia=0,
    velocidade=0,
    pontos_atributo=0
):

    db = get_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            await conn.execute(
                """
                INSERT INTO fichas (
                    user_id,
                    nome,
                    idade,
                    imagem,
                    raca,
                    familia,
                    faccao,
                    profissao,
                    classe,
                    estilo,
                    akuma,
                    despertar,
                    haoshoku,
                    prodigio,
                    forca,
                    resistencia,
                    velocidade,
                    pontos_atributo
                )

                VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18
                );
                """,
                user_id,
                nome,
                idade,
                imagem,
                raca,
                familia,
                faccao,
                profissao,
                classe,
                estilo,
                akuma,
                despertar,
                haoshoku,
                prodigio,
                forca,
                resistencia,
                velocidade,
                pontos_atributo
            )

            await conn.execute(
                """
                INSERT INTO pontos_percentuais (
                    user_id,
                    disponiveis
                )

                VALUES (
                    $1,
                    0
                )

                ON CONFLICT (user_id)
                DO NOTHING;
                """,
                user_id
            )


async def deletar_ficha(user_id):

    db = get_pool()

    return await db.execute(
        """
        DELETE FROM fichas
        WHERE user_id = $1;
        """,
        user_id
    )



# =========================================================
# MORTE DO PLAYER — RESET TOTAL DA FICHA
# =========================================================

async def resetar_ficha_por_morte(user_id):
    """Reseta permanentemente a ficha após morte confirmada."""
    db = get_pool()

    async with db.acquire() as conn:
        async with conn.transaction():

            # Libera somente NPCs vivos recrutados pelo personagem morto.
            # NPCs mortos continuam mortos/indisponíveis.
            await conn.execute(
                """
                UPDATE npcs_mundo
                SET recrutado_por = NULL,
                    disponivel = TRUE,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE recrutado_por = $1
                  AND status = 'vivo';
                """,
                user_id
            )

            # Esta tabela não possui FK para fichas.
            await conn.execute(
                """
                DELETE FROM rolagens_criacao
                WHERE user_id = $1;
                """,
                user_id
            )

            # pontos_percentuais, especializacoes e localizacoes_jogador
            # possuem ON DELETE CASCADE e serão apagados junto com a ficha.
            resultado = await conn.execute(
                """
                DELETE FROM fichas
                WHERE user_id = $1;
                """,
                user_id
            )

            # memorias_npc são preservadas de propósito.
            return resultado != "DELETE 0"



# =========================================================
# EDITAR IDENTIDADE
# =========================================================

async def alterar_nome(
    user_id,
    nome
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET nome = $1
        WHERE user_id = $2;
        """,
        nome,
        user_id
    )


async def alterar_idade(
    user_id,
    idade
):

    if idade <= 0:
        raise ValueError(
            "A idade precisa ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET idade = $1
        WHERE user_id = $2;
        """,
        idade,
        user_id
    )


async def alterar_imagem(
    user_id,
    imagem
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET imagem = $1
        WHERE user_id = $2;
        """,
        imagem,
        user_id
    )


async def alterar_faccao(
    user_id,
    faccao
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET faccao = $1
        WHERE user_id = $2;
        """,
        faccao,
        user_id
    )


# =========================================================
# HAOUSHOKU
# =========================================================

async def alterar_haoshoku(
    user_id,
    possui
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET haoshoku = $1
        WHERE user_id = $2;
        """,
        possui,
        user_id
    )


# =========================================================
# PRODÍGIO
# =========================================================

async def alterar_prodigio(
    user_id,
    possui
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET prodigio = $1
        WHERE user_id = $2;
        """,
        possui,
        user_id
    )


# =========================================================
# PONTOS DE ATRIBUTO
# =========================================================

async def adicionar_pontos_atributo(
    user_id,
    quantidade
):

    if quantidade <= 0:
        raise ValueError(
            "A quantidade precisa ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas

        SET pontos_atributo =
            pontos_atributo + $1

        WHERE user_id = $2;
        """,
        quantidade,
        user_id
    )


async def remover_pontos_atributo(
    user_id,
    quantidade
):

    if quantidade <= 0:
        raise ValueError(
            "A quantidade precisa ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas

        SET pontos_atributo =
            GREATEST(
                pontos_atributo - $1,
                0
            )

        WHERE user_id = $2;
        """,
        quantidade,
        user_id
    )


# =========================================================
# DISTRIBUIÇÃO DE ATRIBUTOS
# =========================================================

async def distribuir_atributo(
    user_id,
    atributo,
    quantidade,
    limite=50000
):

    atributos_validos = {
        "forca",
        "resistencia",
        "velocidade"
    }

    if atributo not in atributos_validos:

        raise ValueError(
            "Atributo inválido."
        )

    if quantidade <= 0:
        return False

    db = get_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            ficha = await conn.fetchrow(
                """
                SELECT
                    forca,
                    resistencia,
                    velocidade,
                    pontos_atributo

                FROM fichas

                WHERE user_id = $1

                FOR UPDATE;
                """,
                user_id
            )

            if not ficha:
                return False

            if (
                ficha["pontos_atributo"]
                < quantidade
            ):
                return False

            atual = ficha[
                atributo
            ]

            if (
                atual + quantidade
                > limite
            ):
                return False

            await conn.execute(
                f"""
                UPDATE fichas

                SET
                    {atributo} =
                        {atributo} + $1,

                    pontos_atributo =
                        pontos_atributo - $1

                WHERE user_id = $2;
                """,
                quantidade,
                user_id
            )

            return True


# =========================================================
# ATUALIZAR ATRIBUTOS
# =========================================================

async def atualizar_atributos(
    user_id,
    forca,
    resistencia,
    velocidade,
    pontos
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas

        SET
            forca = $1,
            resistencia = $2,
            velocidade = $3,
            pontos_atributo = $4

        WHERE user_id = $5;
        """,
        forca,
        resistencia,
        velocidade,
        pontos,
        user_id
    )


# =========================================================
# PONTOS PERCENTUAIS
# =========================================================

async def buscar_pontos_percentuais(
    user_id
):

    db = get_pool()

    pontos = await db.fetchval(
        """
        SELECT disponiveis

        FROM pontos_percentuais

        WHERE user_id = $1;
        """,
        user_id
    )

    return pontos or 0


async def adicionar_pontos_percentuais(
    user_id,
    quantidade
):

    if quantidade <= 0:

        raise ValueError(
            "A quantidade precisa ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        INSERT INTO pontos_percentuais (
            user_id,
            disponiveis
        )

        VALUES (
            $1,
            $2
        )

        ON CONFLICT (user_id)

        DO UPDATE SET
            disponiveis =
                pontos_percentuais.disponiveis
                + EXCLUDED.disponiveis;
        """,
        user_id,
        quantidade
    )


# =========================================================
# ESPECIALIZAÇÕES
# =========================================================

async def adicionar_especializacao(
    user_id,
    categoria,
    nome,
    limite=200,
    desbloqueado_por="admin"
):

    if limite <= 0:

        raise ValueError(
            "O limite precisa ser maior que zero."
        )

    db = get_pool()

    return await db.execute(
        """
        INSERT INTO especializacoes (
            user_id,
            categoria,
            nome,
            porcentagem,
            limite,
            desbloqueado_por
        )

        VALUES (
            $1,
            $2,
            $3,
            0,
            $4,
            $5
        )

        ON CONFLICT (
            user_id,
            categoria,
            nome
        )

        DO NOTHING;
        """,
        user_id,
        categoria,
        nome,
        limite,
        desbloqueado_por
    )


async def buscar_especializacoes(
    user_id
):

    db = get_pool()

    return await db.fetch(
        """
        SELECT *

        FROM especializacoes

        WHERE user_id = $1

        ORDER BY
            categoria,
            nome;
        """,
        user_id
    )


async def buscar_especializacao(
    user_id,
    categoria,
    nome
):

    db = get_pool()

    return await db.fetchrow(
        """
        SELECT *

        FROM especializacoes

        WHERE user_id = $1
        AND categoria = $2
        AND nome = $3;
        """,
        user_id,
        categoria,
        nome
    )


async def remover_especializacao(
    user_id,
    categoria,
    nome
):

    db = get_pool()

    return await db.execute(
        """
        DELETE FROM especializacoes

        WHERE user_id = $1
        AND categoria = $2
        AND nome = $3;
        """,
        user_id,
        categoria,
        nome
    )


# =========================================================
# DISTRIBUIR %
# =========================================================

async def distribuir_percentual(
    user_id,
    especializacao_id,
    quantidade
):

    if quantidade <= 0:
        return False

    db = get_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            carteira = await conn.fetchrow(
                """
                SELECT disponiveis

                FROM pontos_percentuais

                WHERE user_id = $1

                FOR UPDATE;
                """,
                user_id
            )

            if not carteira:
                return False

            if (
                carteira["disponiveis"]
                < quantidade
            ):
                return False

            especializacao = (
                await conn.fetchrow(
                    """
                    SELECT
                        id,
                        porcentagem,
                        limite

                    FROM especializacoes

                    WHERE id = $1
                    AND user_id = $2

                    FOR UPDATE;
                    """,
                    especializacao_id,
                    user_id
                )
            )

            if not especializacao:
                return False

            nova_porcentagem = (
                especializacao[
                    "porcentagem"
                ]
                + quantidade
            )

            if (
                nova_porcentagem
                > especializacao["limite"]
            ):
                return False

            await conn.execute(
                """
                UPDATE especializacoes

                SET porcentagem =
                    porcentagem + $1

                WHERE id = $2
                AND user_id = $3;
                """,
                quantidade,
                especializacao_id,
                user_id
            )

            await conn.execute(
                """
                UPDATE pontos_percentuais

                SET disponiveis =
                    disponiveis - $1

                WHERE user_id = $2;
                """,
                quantidade,
                user_id
            )

            return True


# =========================================================
# BERRIES
# =========================================================

async def adicionar_berries(
    user_id,
    quantidade
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas

        SET berries =
            berries + $1

        WHERE user_id = $2;
        """,
        quantidade,
        user_id
    )


# =========================================================
# REPUTAÇÃO
# =========================================================

async def adicionar_reputacao(
    user_id,
    quantidade
):

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas

        SET reputacao =
            reputacao + $1

        WHERE user_id = $2;
        """,
        quantidade,
        user_id
                )


# =========================================================
# MUNDO PERSISTENTE — NPCS / MEMÓRIAS
# =========================================================

def normalizar_nome_npc(nome):
    return " ".join(str(nome).strip().lower().split())


async def buscar_npc(nome):
    db = get_pool()
    return await db.fetchrow(
        """
        SELECT * FROM npcs_mundo
        WHERE nome_chave = $1;
        """,
        normalizar_nome_npc(nome)
    )


async def registrar_npc(
    nome,
    status="vivo",
    localizacao=None,
    faccao=None,
    dados=None
):
    db = get_pool()
    chave = normalizar_nome_npc(nome)
    return await db.fetchrow(
        """
        INSERT INTO npcs_mundo (
            nome, nome_chave, status, localizacao, faccao, dados
        ) VALUES ($1,$2,$3,$4,$5,$6)
        ON CONFLICT (nome_chave) DO UPDATE SET
            nome = EXCLUDED.nome,
            atualizado_em = CURRENT_TIMESTAMP
        RETURNING *;
        """,
        nome, chave, status, localizacao, faccao, dados
    )


async def atualizar_estado_npc(
    nome,
    status=None,
    localizacao=None,
    faccao=None,
    recrutado_por=None,
    disponivel=None,
    dados=None
):
    db = get_pool()
    npc = await registrar_npc(nome)

    await db.execute(
        """
        UPDATE npcs_mundo SET
            status = COALESCE($1, status),
            localizacao = COALESCE($2, localizacao),
            faccao = COALESCE($3, faccao),
            recrutado_por = COALESCE($4, recrutado_por),
            disponivel = COALESCE($5, disponivel),
            dados = COALESCE($6, dados),
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = $7;
        """,
        status, localizacao, faccao, recrutado_por,
        disponivel, dados, npc["id"]
    )
    return await buscar_npc(nome)


async def recrutar_npc(nome, user_id, localizacao=None):
    db = get_pool()
    npc = await registrar_npc(nome)

    async with db.acquire() as conn:
        async with conn.transaction():
            atual = await conn.fetchrow(
                "SELECT * FROM npcs_mundo WHERE id=$1 FOR UPDATE;",
                npc["id"]
            )
            if atual["status"] != "vivo":
                return False, "npc_indisponivel"
            if atual["recrutado_por"] is not None:
                if atual["recrutado_por"] == user_id:
                    return True, "ja_recrutado_por_voce"
                return False, "ja_recrutado"
            if not atual["disponivel"]:
                return False, "npc_indisponivel"

            await conn.execute(
                """
                UPDATE npcs_mundo SET
                    recrutado_por=$1,
                    disponivel=FALSE,
                    localizacao=COALESCE($2, localizacao),
                    atualizado_em=CURRENT_TIMESTAMP
                WHERE id=$3;
                """,
                user_id, localizacao, npc["id"]
            )
            return True, "recrutado"


async def liberar_npc(nome, localizacao=None):
    db = get_pool()
    npc = await buscar_npc(nome)
    if not npc:
        return False
    await db.execute(
        """
        UPDATE npcs_mundo SET
            recrutado_por=NULL,
            disponivel=TRUE,
            localizacao=COALESCE($1, localizacao),
            atualizado_em=CURRENT_TIMESTAMP
        WHERE id=$2;
        """,
        localizacao, npc["id"]
    )
    return True


async def registrar_memoria_npc(
    nome_npc,
    resumo,
    user_id=None,
    personagem_nome=None,
    importancia=1,
    permanente=False
):
    db = get_pool()
    npc = await registrar_npc(nome_npc)
    return await db.fetchrow(
        """
        INSERT INTO memorias_npc (
            npc_id, user_id, personagem_nome, resumo,
            importancia, permanente
        ) VALUES ($1,$2,$3,$4,$5,$6)
        RETURNING *;
        """,
        npc["id"], user_id, personagem_nome, resumo,
        importancia, permanente
    )


async def buscar_memorias_npc(nome_npc, limite=12):
    db = get_pool()
    npc = await buscar_npc(nome_npc)
    if not npc:
        return []
    return await db.fetch(
        """
        SELECT * FROM memorias_npc
        WHERE npc_id=$1
        ORDER BY permanente DESC, importancia DESC, criado_em DESC
        LIMIT $2;
        """,
        npc["id"], limite
    )


async def definir_atributos_npc(nome, forca, resistencia, velocidade):
    """Define os 3 atributos físicos de um NPC persistente. None = ainda não configurado."""
    valores = (int(forca), int(resistencia), int(velocidade))
    if any(v < 0 or v > 50000 for v in valores):
        raise ValueError("Atributos de NPC devem ficar entre 0 e 50.000.")
    db = get_pool()
    npc = await registrar_npc(nome)
    await db.execute(
        """
        UPDATE npcs_mundo SET
            forca=$1, resistencia=$2, velocidade=$3,
            atualizado_em=CURRENT_TIMESTAMP
        WHERE id=$4;
        """,
        valores[0], valores[1], valores[2], npc["id"]
    )
    return await buscar_npc(nome)


async def listar_npcs_mundo(limite=500):
    db = get_pool()
    return await db.fetch(
        """
        SELECT * FROM npcs_mundo
        ORDER BY nome ASC
        LIMIT $1;
        """,
        limite
    )


# =========================================================
# LOCALIZAÇÃO PERSISTENTE — JOGADORES / ACESSO DE NPC
# =========================================================

async def buscar_localizacao_jogador(user_id):
    db = get_pool()
    return await db.fetchrow(
        "SELECT * FROM localizacoes_jogador WHERE user_id=$1;", user_id
    )

async def definir_localizacao_jogador(user_id, localizacao, area=None):
    db = get_pool()
    return await db.fetchrow(
        """
        INSERT INTO localizacoes_jogador (user_id, localizacao, area, atualizado_em)
        VALUES ($1,$2,$3,CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE SET
            localizacao=EXCLUDED.localizacao,
            area=EXCLUDED.area,
            atualizado_em=CURRENT_TIMESTAMP
        RETURNING *;
        """, user_id, localizacao, area
    )

async def atualizar_estado_jogador(
    user_id,
    estado=None,
    custodia=None,
    restricoes=None,
    combate_ativo=None
):
    """Atualiza somente o estado físico/social persistente do personagem."""
    db = get_pool()
    atual = await buscar_localizacao_jogador(user_id)
    if not atual:
        return None

    return await db.fetchrow(
        """
        UPDATE localizacoes_jogador
        SET estado = COALESCE($2, estado),
            custodia = CASE WHEN $3::TEXT = '__MANTER__' THEN custodia ELSE $3 END,
            restricoes = CASE WHEN $4::TEXT = '__MANTER__' THEN restricoes ELSE $4 END,
            combate_ativo = COALESCE($5, combate_ativo),
            atualizado_em = CURRENT_TIMESTAMP
        WHERE user_id = $1
        RETURNING *;
        """,
        user_id,
        estado,
        "__MANTER__" if custodia is ... else custodia,
        "__MANTER__" if restricoes is ... else restricoes,
        combate_ativo
    )


async def definir_estado_jogador(
    user_id,
    estado="livre",
    custodia=None,
    restricoes=None,
    combate_ativo=False
):
    """Define explicitamente todo o estado persistente do personagem."""
    db = get_pool()
    return await db.fetchrow(
        """
        UPDATE localizacoes_jogador
        SET estado=$2,
            custodia=$3,
            restricoes=$4,
            combate_ativo=$5,
            atualizado_em=CURRENT_TIMESTAMP
        WHERE user_id=$1
        RETURNING *;
        """,
        user_id, estado, custodia, restricoes, bool(combate_ativo)
    )

async def definir_acesso_npc(nome, localizacao=None, area=None, nivel_acesso='normal', encontravel_aleatoriamente=True, faccao=None):
    db = get_pool()
    npc = await registrar_npc(nome, localizacao=localizacao, faccao=faccao)
    await db.execute(
        """
        UPDATE npcs_mundo SET
            localizacao=COALESCE($1, localizacao),
            area=COALESCE($2, area),
            nivel_acesso=$3,
            encontravel_aleatoriamente=$4,
            faccao=COALESCE($5, faccao),
            atualizado_em=CURRENT_TIMESTAMP
        WHERE id=$6;
        """, localizacao, area, nivel_acesso, encontravel_aleatoriamente, faccao, npc['id']
    )
    return await buscar_npc(nome)


# =========================================================
# PERFIL MECÂNICO AUTOMÁTICO — NPCS
# =========================================================

async def buscar_perfil_npc(nome):
    """Retorna o perfil mecânico persistido em npcs_mundo.dados, se existir."""
    import json
    npc = await buscar_npc(nome)
    if not npc or not npc["dados"]:
        return None
    try:
        dados = json.loads(npc["dados"]) if isinstance(npc["dados"], str) else dict(npc["dados"])
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    perfil = dados.get("perfil_combate")
    return perfil if isinstance(perfil, dict) else None


async def salvar_perfil_npc(nome, perfil):
    """Persiste o perfil uma única vez; seguro contra dois players gerando ao mesmo tempo."""
    import json
    npc = await registrar_npc(nome)
    db = get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            atual = await conn.fetchrow(
                "SELECT * FROM npcs_mundo WHERE id=$1 FOR UPDATE;", npc["id"]
            )
            dados = {}
            if atual["dados"]:
                try:
                    dados = json.loads(atual["dados"]) if isinstance(atual["dados"], str) else dict(atual["dados"])
                except (TypeError, ValueError, json.JSONDecodeError):
                    dados = {}
            if isinstance(dados.get("perfil_combate"), dict):
                return dados["perfil_combate"]
            dados["perfil_combate"] = perfil
            await conn.execute(
                "UPDATE npcs_mundo SET dados=$1, atualizado_em=CURRENT_TIMESTAMP WHERE id=$2;",
                json.dumps(dados, ensure_ascii=False), npc["id"]
            )
            return perfil


# =========================================================
# MUNDO PERSISTENTE — EVENTOS / CONSEQUÊNCIAS
# =========================================================

async def registrar_evento_mundo(
    personagem_nome, resumo, user_id=None, localizacao=None, area=None,
    tipo="acontecimento", gravidade=1, alcance="local", testemunhas=False,
    marinha_sabe=False, governo_sabe=False, piratas_sabem=False, publico_sabe=False
):
    db = get_pool()
    gravidade = max(1, min(10, int(gravidade)))
    alcance = alcance if alcance in {"local", "regional", "faccao", "mundial"} else "local"
    return await db.fetchrow(
        """
        INSERT INTO eventos_mundo (
            user_id, personagem_nome, localizacao, area, tipo, resumo, gravidade, alcance,
            testemunhas, marinha_sabe, governo_sabe, piratas_sabem, publico_sabe
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        RETURNING *;
        """,
        user_id, personagem_nome, localizacao, area, tipo, resumo, gravidade, alcance,
        bool(testemunhas), bool(marinha_sabe), bool(governo_sabe), bool(piratas_sabem), bool(publico_sabe)
    )

async def buscar_eventos_mundo(localizacao=None, personagem_nome=None, limite=30):
    db = get_pool()
    limite = max(1, min(100, int(limite)))
    return await db.fetch(
        """
        SELECT * FROM eventos_mundo
        WHERE ativo = TRUE
          AND (
            alcance = 'mundial'
            OR ($1::TEXT IS NOT NULL AND LOWER(localizacao) = LOWER($1))
            OR ($2::TEXT IS NOT NULL AND LOWER(personagem_nome) = LOWER($2))
            OR alcance IN ('regional','faccao')
          )
        ORDER BY gravidade DESC, criado_em DESC
        LIMIT $3;
        """, localizacao, personagem_nome, limite
    )

async def buscar_notoriedade_personagem(personagem_nome):
    db = get_pool()
    return await db.fetchrow(
        """
        SELECT
            COALESCE(SUM(gravidade),0)::INTEGER AS impacto_total,
            COALESCE(SUM(gravidade) FILTER (WHERE marinha_sabe),0)::INTEGER AS atencao_marinha,
            COALESCE(SUM(gravidade) FILTER (WHERE governo_sabe),0)::INTEGER AS atencao_governo,
            COALESCE(SUM(gravidade) FILTER (WHERE piratas_sabem),0)::INTEGER AS notoriedade_pirata,
            COALESCE(SUM(gravidade) FILTER (WHERE publico_sabe),0)::INTEGER AS fama_publica
        FROM eventos_mundo
        WHERE LOWER(personagem_nome)=LOWER($1);
        """, personagem_nome
    )


# =========================================================
# SESSÕES DE NARRAÇÃO — MULTIPLAYER
# =========================================================

async def buscar_sessao_ativa(channel_id):
    db = get_pool()
    return await db.fetchrow(
        """
        SELECT * FROM sessoes_narracao
        WHERE channel_id=$1 AND status='ativa'
        ORDER BY id DESC LIMIT 1;
        """,
        int(channel_id)
    )


async def obter_ou_criar_sessao(guild_id, channel_id, localizacao=None, area=None):
    """Uma realidade compartilhada ativa por canal. Não impõe limite de participantes."""
    db = get_pool()
    atual = await buscar_sessao_ativa(channel_id)
    if atual:
        return atual

    criada = await db.fetchrow(
        """
        INSERT INTO sessoes_narracao(guild_id, channel_id, localizacao, area)
        SELECT $1,$2,$3,$4
        WHERE NOT EXISTS (
            SELECT 1 FROM sessoes_narracao
            WHERE channel_id=$2 AND status='ativa'
        )
        RETURNING *;
        """,
        int(guild_id) if guild_id is not None else None,
        int(channel_id), localizacao, area
    )
    return criada or await buscar_sessao_ativa(channel_id)


async def entrar_sessao(sessao_id, user_id, personagem_nome):
    db = get_pool()
    return await db.fetchrow(
        """
        INSERT INTO participantes_sessao(sessao_id,user_id,personagem_nome,status,saiu_em)
        VALUES($1,$2,$3,'ativo',NULL)
        ON CONFLICT(sessao_id,user_id) DO UPDATE SET
            personagem_nome=EXCLUDED.personagem_nome,
            status='ativo',
            saiu_em=NULL
        RETURNING *;
        """,
        int(sessao_id), int(user_id), str(personagem_nome)
    )


async def listar_participantes_sessao(sessao_id, somente_ativos=True):
    db = get_pool()
    if somente_ativos:
        return await db.fetch(
            """
            SELECT * FROM participantes_sessao
            WHERE sessao_id=$1 AND status='ativo'
            ORDER BY entrou_em ASC;
            """,
            int(sessao_id)
        )
    return await db.fetch(
        """
        SELECT * FROM participantes_sessao
        WHERE sessao_id=$1
        ORDER BY entrou_em ASC;
        """,
        int(sessao_id)
    )


async def marcar_participante_sessao(sessao_id, user_id, status):
    db = get_pool()
    status = str(status or "ativo")[:30]
    return await db.fetchrow(
        """
        UPDATE participantes_sessao
        SET status=$3,
            saiu_em=CASE WHEN $3='ativo' THEN NULL ELSE CURRENT_TIMESTAMP END
        WHERE sessao_id=$1 AND user_id=$2
        RETURNING *;
        """,
        int(sessao_id), int(user_id), status
    )


async def registrar_turno_sessao(sessao_id, user_id, personagem_nome, acao, narracao):
    db = get_pool()
    await db.execute(
        "UPDATE sessoes_narracao SET atualizada_em=CURRENT_TIMESTAMP WHERE id=$1;",
        int(sessao_id)
    )
    return await db.fetchrow(
        """
        INSERT INTO turnos_sessao(sessao_id,user_id,personagem_nome,acao,narracao)
        VALUES($1,$2,$3,$4,$5)
        RETURNING *;
        """,
        int(sessao_id), int(user_id), str(personagem_nome),
        str(acao)[:3000], str(narracao)[:12000]
    )


async def buscar_turnos_sessao(sessao_id, limite=24):
    db = get_pool()
    limite = max(1, min(100, int(limite)))
    rows = await db.fetch(
        """
        SELECT * FROM turnos_sessao
        WHERE sessao_id=$1
        ORDER BY id DESC
        LIMIT $2;
        """,
        int(sessao_id), limite
    )
    return list(reversed(rows))


async def encerrar_sessao_narracao(sessao_id, resumo_final=None):
    db = get_pool()
    row = await db.fetchrow(
        """
        UPDATE sessoes_narracao
        SET status='encerrada',
            resumo_final=$2,
            encerrada_em=CURRENT_TIMESTAMP,
            atualizada_em=CURRENT_TIMESTAMP
        WHERE id=$1 AND status='ativa'
        RETURNING *;
        """,
        int(sessao_id), resumo_final
    )
    if row:
        await db.execute(
            """
            UPDATE participantes_sessao
            SET status=CASE WHEN status='ativo' THEN 'encerrado' ELSE status END,
                saiu_em=COALESCE(saiu_em,CURRENT_TIMESTAMP)
            WHERE sessao_id=$1;
            """,
            int(sessao_id)
        )
    return row


# =========================================================
# COMBATE COLETIVO — RODADAS
# =========================================================
async def buscar_combate_ativo(sessao_id):
    db=get_pool()
    return await db.fetchrow("SELECT * FROM combates_sessao WHERE sessao_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1;",int(sessao_id))

async def iniciar_combate_sessao(sessao_id):
    db=get_pool(); atual=await buscar_combate_ativo(sessao_id)
    if atual: return atual
    criado=await db.fetchrow("""INSERT INTO combates_sessao(sessao_id)
        SELECT $1 WHERE NOT EXISTS(SELECT 1 FROM combates_sessao WHERE sessao_id=$1 AND status='ativo')
        RETURNING *;""",int(sessao_id))
    return criada if False else (criado or await buscar_combate_ativo(sessao_id))

async def entrar_combate(combate_id,user_id,personagem_nome,rodada):
    db=get_pool()
    return await db.fetchrow("""INSERT INTO participantes_combate(combate_id,user_id,personagem_nome,status,entrou_rodada)
        VALUES($1,$2,$3,'ativo',$4)
        ON CONFLICT(combate_id,user_id) DO UPDATE SET personagem_nome=EXCLUDED.personagem_nome,
        status=CASE WHEN participantes_combate.status IN ('morto','incapacitado','saiu') THEN participantes_combate.status ELSE 'ativo' END
        RETURNING *;""",int(combate_id),int(user_id),str(personagem_nome),int(rodada))

async def listar_combatentes(combate_id,somente_ativos=True):
    db=get_pool()
    sql="SELECT * FROM participantes_combate WHERE combate_id=$1"
    if somente_ativos: sql+=" AND status='ativo'"
    sql+=" ORDER BY criado_em;"
    return await db.fetch(sql,int(combate_id))

async def registrar_acao_combate(combate_id,rodada,user_id,personagem_nome,acao=None,pulou=False):
    db=get_pool()
    return await db.fetchrow("""INSERT INTO acoes_rodada(combate_id,rodada,user_id,personagem_nome,acao,pulou)
        VALUES($1,$2,$3,$4,$5,$6)
        ON CONFLICT(combate_id,rodada,user_id) DO UPDATE SET acao=EXCLUDED.acao,pulou=EXCLUDED.pulou,
        personagem_nome=EXCLUDED.personagem_nome,criado_em=CURRENT_TIMESTAMP RETURNING *;""",
        int(combate_id),int(rodada),int(user_id),str(personagem_nome),acao,bool(pulou))

async def listar_acoes_rodada(combate_id,rodada):
    db=get_pool()
    return await db.fetch("SELECT * FROM acoes_rodada WHERE combate_id=$1 AND rodada=$2 ORDER BY criado_em;",int(combate_id),int(rodada))

async def atualizar_status_combatente(combate_id,user_id,status):
    db=get_pool()
    return await db.fetchrow("UPDATE participantes_combate SET status=$3 WHERE combate_id=$1 AND user_id=$2 RETURNING *;",
        int(combate_id),int(user_id),str(status)[:30])

async def avancar_rodada_combate(combate_id):
    db=get_pool()
    return await db.fetchrow("""UPDATE combates_sessao SET rodada=rodada+1,primeira_rodada=FALSE,
        atualizado_em=CURRENT_TIMESTAMP WHERE id=$1 AND status='ativo' RETURNING *;""",int(combate_id))

async def encerrar_combate_sessao(combate_id):
    db=get_pool()
    return await db.fetchrow("""UPDATE combates_sessao SET status='encerrado',encerrado_em=CURRENT_TIMESTAMP,
        atualizado_em=CURRENT_TIMESTAMP WHERE id=$1 AND status='ativo' RETURNING *;""",int(combate_id))


async def buscar_reputacao_mundo(personagem_nome):
    db = get_pool()
    return await db.fetchrow(
        "SELECT * FROM reputacoes_mundo WHERE LOWER(personagem_nome)=LOWER($1);",
        personagem_nome
    )


async def aplicar_impacto_reputacao(
    personagem_nome, gravidade, localizacao=None,
    marinha_sabe=False, governo_sabe=False, piratas_sabem=False, publico_sabe=False,
    hostil_marinha=False, hostil_governo=False, hostil_piratas=False, ajuda_publica=False,
    ajuda_marinha=False, ajuda_governo=False, ajuda_piratas=False
):
    """Converte um evento confirmado em pressão persistente. Não depende do user_id."""
    db = get_pool()
    g = max(1, min(10, int(gravidade)))

    # Saber do fato gera reconhecimento leve; ajudar diretamente uma facção gera reconhecimento maior.
    # Isso permite, por exemplo, um Marinheiro ganhar reputação na Marinha por serviço confirmado
    # mesmo quando o acontecimento não virou notícia pública.
    delta_marinha = (g * 2 if marinha_sabe else 0) + (g * 3 if ajuda_marinha else 0) + (g * 3 if hostil_marinha else 0)
    delta_governo = (g * 2 if governo_sabe else 0) + (g * 3 if ajuda_governo else 0) + (g * 3 if hostil_governo else 0)
    delta_piratas = (g * 2 if piratas_sabem else 0) + (g * 3 if ajuda_piratas else 0) + (-g if hostil_piratas else 0)
    delta_civis = (g if publico_sabe else 0) + (g * 2 if ajuda_publica else 0)

    # "relação" positiva = reconhecimento/favor; negativa = hostilidade.
    if hostil_marinha:
        delta_marinha = -abs(delta_marinha)
    if hostil_governo:
        delta_governo = -abs(delta_governo)
    if hostil_piratas:
        delta_piratas = -max(g * 2, abs(delta_piratas))

    row = await db.fetchrow(
        """
        INSERT INTO reputacoes_mundo (
            personagem_nome, marinha, governo, piratas, civis, ultima_localizacao
        ) VALUES ($1,$2,$3,$4,$5,$6)
        ON CONFLICT (personagem_nome) DO UPDATE SET
            marinha=reputacoes_mundo.marinha + EXCLUDED.marinha,
            governo=reputacoes_mundo.governo + EXCLUDED.governo,
            piratas=reputacoes_mundo.piratas + EXCLUDED.piratas,
            civis=reputacoes_mundo.civis + EXCLUDED.civis,
            ultima_localizacao=COALESCE(EXCLUDED.ultima_localizacao, reputacoes_mundo.ultima_localizacao),
            atualizado_em=CURRENT_TIMESTAMP
        RETURNING *;
        """,
        personagem_nome, delta_marinha, delta_governo, delta_piratas, delta_civis, localizacao
    )

    # Pressão estatal nasce de hostilidade/registro, não de "fama" genérica.
    pressao = max(0, -int(row["marinha"])) + max(0, -int(row["governo"]))
    nivel = min(5, pressao // 20)
    procurado = pressao >= 15

    # Recompensa é consequência mecânica simples e crescente; pode ser ajustada por mestre depois.
    recompensa = 0
    if procurado:
        recompensa = max(1_000_000, pressao * 250_000)

    return await db.fetchrow(
        """
        UPDATE reputacoes_mundo
        SET procurado=$2, recompensa=$3, nivel_ameaca=$4, atualizado_em=CURRENT_TIMESTAMP
        WHERE personagem_nome=$1
        RETURNING *;
        """, personagem_nome, procurado, recompensa, nivel
    )


async def registrar_noticia_mundo(evento_id, personagem_nome, manchete, corpo, alcance="regional"):
    db = get_pool()
    alcance = alcance if alcance in {"local","regional","faccao","mundial"} else "regional"
    return await db.fetchrow(
        """
        INSERT INTO noticias_mundo(evento_id, personagem_nome, manchete, corpo, alcance)
        VALUES ($1,$2,$3,$4,$5)
        RETURNING *;
        """, evento_id, personagem_nome, manchete[:180], corpo[:1500], alcance
    )


async def buscar_noticias_mundo(limite=10):
    db = get_pool()
    limite = max(1, min(30, int(limite)))
    return await db.fetch(
        """
        SELECT * FROM noticias_mundo
        WHERE publicado=TRUE
        ORDER BY criado_em DESC
        LIMIT $1;
        """, limite
    )

async def configurar_sessao_narracao(sessao_id,jogadores_esperados):
    db=get_pool(); jogadores_esperados=max(1,int(jogadores_esperados))
    return await db.fetchrow("UPDATE sessoes_narracao SET jogadores_esperados=$2,iniciada=FALSE,atualizada_em=CURRENT_TIMESTAMP WHERE id=$1 RETURNING *;",int(sessao_id),jogadores_esperados)

async def marcar_sessao_iniciada(sessao_id):
    db=get_pool()
    return await db.fetchrow("UPDATE sessoes_narracao SET iniciada=TRUE,atualizada_em=CURRENT_TIMESTAMP WHERE id=$1 RETURNING *;",int(sessao_id))
