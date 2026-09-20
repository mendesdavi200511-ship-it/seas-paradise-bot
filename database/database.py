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
# CRIAÇÃO / MIGRAÇÃO DAS TABELAS
# =========================================================

async def criar_tabelas():

    db = get_pool()

    async with db.acquire() as conn:

        # -------------------------------------------------
        # FICHAS
        # -------------------------------------------------

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

                pontos_percentuais INTEGER NOT NULL
                    DEFAULT 0,

                berries BIGINT NOT NULL
                    DEFAULT 0,

                reputacao BIGINT NOT NULL
                    DEFAULT 0,

                criado_em TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -------------------------------------------------
        # MIGRAÇÕES
        #
        # Isso permite atualizar uma tabela antiga sem
        # precisar apagar as fichas existentes.
        # -------------------------------------------------

        migracoes = [

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS familia TEXT
            NOT NULL DEFAULT 'Não definida';
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
            ADD COLUMN IF NOT EXISTS pontos_atributo INTEGER
            NOT NULL DEFAULT 0;
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS pontos_percentuais INTEGER
            NOT NULL DEFAULT 0;
            """
        ]

        for migracao in migracoes:
            await conn.execute(migracao)

        # -------------------------------------------------
        # ESPECIALIZAÇÕES
        #
        # Aqui ficam estilos, Haki, profissão, Akuma etc.
        # separadamente da ficha principal.
        # -------------------------------------------------

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

                UNIQUE(user_id, categoria, nome),

                FOREIGN KEY (user_id)
                    REFERENCES fichas(user_id)
                    ON DELETE CASCADE
            );
        """)

        # -------------------------------------------------
        # PONTOS %
        # -------------------------------------------------

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


# =========================================================
# FICHAS
# =========================================================

async def possui_ficha(user_id):

    db = get_pool()

    resultado = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1
            FROM fichas
            WHERE user_id = $1
        )
        """,
        user_id
    )

    return resultado


async def buscar_ficha(user_id):

    db = get_pool()

    return await db.fetchrow(
        """
        SELECT *
        FROM fichas
        WHERE user_id = $1
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
    forca=0,
    resistencia=0,
    velocidade=0,
    pontos_atributo=0
):

    db = get_pool()

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

    # Cria automaticamente a carteira de %
    await db.execute(
        """
        INSERT INTO pontos_percentuais (
            user_id,
            disponiveis
        )
        VALUES ($1, 0)
        ON CONFLICT (user_id)
        DO NOTHING
        """,
        user_id
    )


async def deletar_ficha(user_id):

    db = get_pool()

    return await db.execute(
        """
        DELETE FROM fichas
        WHERE user_id = $1
        """,
        user_id
    )


# =========================================================
# ATRIBUTOS
# =========================================================

async def adicionar_pontos_atributo(
    user_id,
    quantidade
):

    if quantidade <= 0:
        raise ValueError(
            "A quantidade deve ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        UPDATE fichas
        SET pontos_atributo =
            pontos_atributo + $1
        WHERE user_id = $2
        """,
        quantidade,
        user_id
    )


# =========================================================
# PONTOS PERCENTUAIS
# =========================================================

async def buscar_pontos_percentuais(user_id):

    db = get_pool()

    return await db.fetchval(
        """
        SELECT disponiveis
        FROM pontos_percentuais
        WHERE user_id = $1
        """,
        user_id
    ) or 0


async def adicionar_pontos_percentuais(
    user_id,
    quantidade
):

    if quantidade <= 0:
        raise ValueError(
            "A quantidade deve ser maior que zero."
        )

    db = get_pool()

    await db.execute(
        """
        INSERT INTO pontos_percentuais (
            user_id,
            disponiveis
        )
        VALUES ($1, $2)

        ON CONFLICT (user_id)

        DO UPDATE SET
            disponiveis =
                pontos_percentuais.disponiveis
                + EXCLUDED.disponiveis
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

    db = get_pool()

    await db.execute(
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
            $1, $2, $3, 0, $4, $5
        )

        ON CONFLICT (
            user_id,
            categoria,
            nome
        )

        DO NOTHING
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
        ORDER BY categoria, nome
        """,
        user_id
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
        AND nome = $3
        """,
        user_id,
        categoria,
        nome
    )
