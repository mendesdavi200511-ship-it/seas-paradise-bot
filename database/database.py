import os
import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


# =========================================================
# CONEXÃO
# =========================================================

async def conectar():
    global pool

    if pool is not None:
        return pool

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não foi configurado."
        )

    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5
    )

    await criar_tabelas()

    print("🐘 PostgreSQL conectado!")
    print("📦 Banco do Sea's Paradise pronto!")

    return pool


# =========================================================
# CRIAÇÃO / MIGRAÇÃO DAS TABELAS
# =========================================================

async def criar_tabelas():

    async with pool.acquire() as conn:

        # -------------------------------------------------
        # FICHA PRINCIPAL
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
                    DEFAULT 'Nenhum',

                forca INTEGER NOT NULL
                    DEFAULT 0,

                resistencia INTEGER NOT NULL
                    DEFAULT 0,

                velocidade INTEGER NOT NULL
                    DEFAULT 0,

                pontos_atributo INTEGER NOT NULL
                    DEFAULT 0,

                pontos_porcentagem INTEGER NOT NULL
                    DEFAULT 0,

                berries BIGINT NOT NULL
                    DEFAULT 0,

                reputacao INTEGER NOT NULL
                    DEFAULT 0,

                criado_em TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -------------------------------------------------
        # MIGRAÇÕES
        # Para banco antigo continuar funcionando
        # -------------------------------------------------

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

        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS estilo TEXT
            NOT NULL DEFAULT 'Nenhum';
        """)

        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS akuma TEXT
            NOT NULL DEFAULT 'Nenhuma';
        """)

        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS despertar TEXT
            NOT NULL DEFAULT 'Nenhum';
        """)

        await conn.execute("""
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS pontos_porcentagem INTEGER
            NOT NULL DEFAULT 0;
        """)

        # -------------------------------------------------
        # ESPECIALIZAÇÕES
        #
        # Aqui ficam coisas que podem existir várias vezes:
        # classes, estilos, haki, akuma, profissão etc.
        # -------------------------------------------------

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS especializacoes (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT NOT NULL,

                tipo TEXT NOT NULL,

                nome TEXT NOT NULL,

                porcentagem INTEGER NOT NULL
                    DEFAULT 0,

                despertar BOOLEAN NOT NULL
                    DEFAULT FALSE,

                criado_em TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, tipo, nome)
            );
        """)


# =========================================================
# FICHAS
# =========================================================

async def possui_ficha(user_id):

    async with pool.acquire() as conn:

        resultado = await conn.fetchval(
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

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM fichas
            WHERE user_id = $1
            """,
            user_id
        )


async def criar_ficha(dados):

    async with pool.acquire() as conn:

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
                pontos_atributo,
                pontos_porcentagem,
                berries,
                reputacao
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15,
                $16, $17
            )
            """,

            dados["user_id"],
            dados["nome"],
            dados.get("raca", "Não definida"),
            dados.get("familia", "Não definida"),
            dados.get("faccao", "Civil"),
            dados.get("profissao", "Nenhuma"),
            dados.get("classe", "Nenhuma"),
            dados.get("estilo", "Nenhum"),
            dados.get("akuma", "Nenhuma"),
            dados.get("despertar", "Nenhum"),
            dados.get("forca", 0),
            dados.get("resistencia", 0),
            dados.get("velocidade", 0),
            dados.get("pontos_atributo", 0),
            dados.get("pontos_porcentagem", 0),
            dados.get("berries", 0),
            dados.get("reputacao", 0)
        )


async def deletar_ficha(user_id):

    async with pool.acquire() as conn:

        async with conn.transaction():

            await conn.execute(
                """
                DELETE FROM especializacoes
                WHERE user_id = $1
                """,
                user_id
            )

            return await conn.execute(
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

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE fichas
            SET pontos_atributo =
                pontos_atributo + $1
            WHERE user_id = $2
            """,
            quantidade,
            user_id
        )


async def atualizar_atributos(
    user_id,
    forca,
    resistencia,
    velocidade,
    pontos
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE fichas
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


# =========================================================
# PONTOS DE PORCENTAGEM
# =========================================================

async def adicionar_pontos_porcentagem(
    user_id,
    quantidade
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE fichas
            SET pontos_porcentagem =
                pontos_porcentagem + $1
            WHERE user_id = $2
            """,
            quantidade,
            user_id
        )


# =========================================================
# ESPECIALIZAÇÕES
# =========================================================

async def adicionar_especializacao(
    user_id,
    tipo,
    nome
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO especializacoes (
                user_id,
                tipo,
                nome
            )

            VALUES ($1, $2, $3)

            ON CONFLICT (
                user_id,
                tipo,
                nome
            )

            DO NOTHING
            """,
            user_id,
            tipo,
            nome
        )


async def remover_especializacao(
    user_id,
    tipo,
    nome
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            DELETE FROM especializacoes

            WHERE user_id = $1
            AND tipo = $2
            AND nome = $3
            """,
            user_id,
            tipo,
            nome
        )


async def buscar_especializacoes(user_id):

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *
            FROM especializacoes

            WHERE user_id = $1

            ORDER BY
                tipo,
                nome
            """,
            user_id
        )


async def atualizar_porcentagem(
    user_id,
    especializacao_id,
    porcentagem
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE especializacoes

            SET porcentagem = $1

            WHERE id = $2
            AND user_id = $3
            """,
            porcentagem,
            especializacao_id,
            user_id
        )


# =========================================================
# ECONOMIA
# =========================================================

async def alterar_berries(
    user_id,
    quantidade
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE fichas

            SET berries =
                berries + $1

            WHERE user_id = $2
            """,
            quantidade,
            user_id
        )


# =========================================================
# REPUTAÇÃO
# =========================================================

async def alterar_reputacao(
    user_id,
    quantidade
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE fichas

            SET reputacao =
                reputacao + $1

            WHERE user_id = $2
            """,
            quantidade,
            user_id
        )
