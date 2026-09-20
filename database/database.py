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
        # Mantém compatibilidade com fichas antigas
        # =================================================

        migracoes = [

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
        # CARTEIRA DE PONTOS %
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
        # ESPECIALIZAÇÕES
        #
        # Exemplos:
        # estilo -> Ittoryu
        # haki -> Busoshoku
        # profissao -> Navegador
        # akuma -> Mera Mera no Mi
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
    raca="Não definida",
    familia="Não definida",
    faccao="Civil",
    profissao="Nenhuma",
    classe="Nenhuma",
    estilo="Nenhum",
    akuma="Nenhuma",
    despertar="Não",
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
                    raca,
                    familia,
                    faccao,
                    profissao,
                    classe,
                    estilo,
                    akuma,
                    despertar,
                    forca,
                    resistencia,
                    velocidade,
                    pontos_atributo
                )

                VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9, $10,
                    $11, $12, $13, $14
                );
                """,
                user_id,
                nome,
                raca,
                familia,
                faccao,
                profissao,
                classe,
                estilo,
                akuma,
                despertar,
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

                VALUES ($1, 0)

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
# EDITAR FICHA
# =========================================================

async def alterar_nome(user_id, nome):

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


async def alterar_faccao(user_id, faccao):

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

            if ficha["pontos_atributo"] < quantidade:
                return False

            atual = ficha[atributo]

            if atual + quantidade > limite:
                return False

            await conn.execute(
                f"""
                UPDATE fichas

                SET
                    {atributo} = {atributo} + $1,
                    pontos_atributo =
                        pontos_atributo - $1

                WHERE user_id = $2;
                """,
                quantidade,
                user_id
            )

            return True


# =========================================================
# PONTOS PERCENTUAIS
# =========================================================

async def buscar_pontos_percentuais(user_id):

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
# Somente comandos administrativos deverão chamar
# desbloqueio/remoção.
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


async def buscar_especializacoes(user_id):

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
# O PLAYER PODE USAR ESTA FUNÇÃO PARA DISTRIBUIR
# OS PONTOS QUE O ADMIN CONCEDEU
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

            if carteira["disponiveis"] < quantidade:
                return False

            especializacao = await conn.fetchrow(
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

            if not especializacao:
                return False

            nova_porcentagem = (
                especializacao["porcentagem"]
                + quantidade
            )

            if nova_porcentagem > especializacao["limite"]:
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
# ATUALIZAR ATRIBUTOS
# =========================================================

async def atualizar_atributos(
    user_id,
    forca,
    resistencia,
    velocidade,
    pontos
):
    global pool

    async with pool.acquire() as conexao:
        await conexao.execute(
            """
            UPDATE personagens
            SET
                forca = $1,
                resistencia = $2,
                velocidade = $3,
                pontos_atributo = $4
            WHERE user_id = $5
            """,
            forca,
            resistencia,
            velocidade,
            pontos,
            user_id
        )
