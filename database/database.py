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

        for migracao_mundo in [
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS area TEXT;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS nivel_acesso TEXT NOT NULL DEFAULT 'normal';",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS encontravel_aleatoriamente BOOLEAN NOT NULL DEFAULT TRUE;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS forca INTEGER;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS resistencia INTEGER;",
            "ALTER TABLE npcs_mundo ADD COLUMN IF NOT EXISTS velocidade INTEGER;",
        ]:
            await conn.execute(migracao_mundo)

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
