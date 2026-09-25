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
        max_size=max(5, int(os.getenv('DB_POOL_MAX', '20'))),
        command_timeout=float(os.getenv('DB_COMMAND_TIMEOUT', '30'))
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

                vontade_d BOOLEAN NOT NULL DEFAULT FALSE,
                joyboy BOOLEAN NOT NULL DEFAULT FALSE,

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

            """ALTER TABLE fichas ADD COLUMN IF NOT EXISTS vontade_d BOOLEAN NOT NULL DEFAULT FALSE;""",
            """ALTER TABLE fichas ADD COLUMN IF NOT EXISTS joyboy BOOLEAN NOT NULL DEFAULT FALSE;""",

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
            """,

            """
            ALTER TABLE fichas
            ADD COLUMN IF NOT EXISTS rank_manual TEXT;
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

        # Migração aditiva: Akuma no Mi evolui até 300% (100% kit normal; 300% condição de despertar).
        # Corrige fichas antigas criadas quando o limite padrão ainda era 200%.
        await conn.execute("""
            UPDATE especializacoes
            SET limite = 300
            WHERE LOWER(categoria) IN ('akuma', 'akuma no mi')
              AND limite < 300;
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
        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS conflito_ativo BOOLEAN NOT NULL DEFAULT FALSE;")
        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS estado_cena TEXT;")
        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS ciclo_deadline TIMESTAMPTZ;")
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

        await conn.execute("ALTER TABLE sessoes_narracao ADD COLUMN IF NOT EXISTS ciclo_cena INTEGER NOT NULL DEFAULT 1;")
        await conn.execute("ALTER TABLE participantes_sessao ADD COLUMN IF NOT EXISTS participa_desde_ciclo INTEGER NOT NULL DEFAULT 1;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acoes_cena_sessao (
                sessao_id BIGINT NOT NULL, ciclo INTEGER NOT NULL, user_id BIGINT NOT NULL,
                personagem_nome TEXT NOT NULL, acao TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(sessao_id,ciclo,user_id),
                FOREIGN KEY (sessao_id) REFERENCES sessoes_narracao(id) ON DELETE CASCADE
            );
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
        # ECONOMIA — INVENTÁRIO / TRANSAÇÕES / EMBARCAÇÕES
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                user_id BIGINT NOT NULL,
                item_id TEXT NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_id),
                FOREIGN KEY (user_id) REFERENCES fichas(user_id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transacoes_economia (
                id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, tipo TEXT NOT NULL,
                valor BIGINT NOT NULL DEFAULT 0, item_id TEXT, quantidade INTEGER NOT NULL DEFAULT 1,
                detalhes TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES fichas(user_id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transacoes_economia_user
            ON transacoes_economia(user_id, criado_em DESC);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS embarcacoes (
                id BIGSERIAL PRIMARY KEY, proprietario_id BIGINT NOT NULL, tipo TEXT NOT NULL,
                nome TEXT NOT NULL DEFAULT 'Sem nome', integridade_atual INTEGER NOT NULL,
                integridade_max INTEGER NOT NULL, capacidade INTEGER NOT NULL, carga_max INTEGER NOT NULL,
                localizacao TEXT, ativa BOOLEAN NOT NULL DEFAULT FALSE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proprietario_id) REFERENCES fichas(user_id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_embarcacao_ativa_proprietario
            ON embarcacoes(proprietario_id) WHERE ativa=TRUE;
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS viagens (
                id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, embarcacao_id BIGINT NOT NULL,
                origem TEXT NOT NULL, destino TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'viajando',
                canal_id BIGINT, inicio_em TIMESTAMPTZ NOT NULL DEFAULT NOW(), chegada_em TIMESTAMPTZ NOT NULL,
                proximo_evento_em TIMESTAMPTZ, eventos_restantes INTEGER NOT NULL DEFAULT 0,
                suprimentos_gastos INTEGER NOT NULL DEFAULT 0, desgaste INTEGER NOT NULL DEFAULT 0,
                criado_em TIMESTAMPTZ DEFAULT NOW(), atualizado_em TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES fichas(user_id) ON DELETE CASCADE,
                FOREIGN KEY(embarcacao_id) REFERENCES embarcacoes(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_viagem_ativa_user ON viagens(user_id) WHERE status IN ('viajando','obstaculo');""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS rotas_liberadas (user_id BIGINT NOT NULL, destino TEXT NOT NULL, origem TEXT, motivo TEXT, criado_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(user_id,destino), FOREIGN KEY(user_id) REFERENCES fichas(user_id) ON DELETE CASCADE);""")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS eventos_viagem (
                id BIGSERIAL PRIMARY KEY, viagem_id BIGINT NOT NULL, titulo TEXT NOT NULL, descricao TEXT NOT NULL,
                resolvido BOOLEAN NOT NULL DEFAULT FALSE, acao_player TEXT, resultado TEXT,
                criado_em TIMESTAMPTZ DEFAULT NOW(), resolvido_em TIMESTAMPTZ,
                FOREIGN KEY(viagem_id) REFERENCES viagens(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS treinamentos (
                id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, tipo TEXT NOT NULL, alvo TEXT NOT NULL,
                ganho INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'ativo', canal_id BIGINT,
                inicio_em TIMESTAMPTZ NOT NULL DEFAULT NOW(), fim_em TIMESTAMPTZ NOT NULL,
                criado_em TIMESTAMPTZ DEFAULT NOW(), concluido_em TIMESTAMPTZ,
                FOREIGN KEY(user_id) REFERENCES fichas(user_id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_treino_ativo_user ON treinamentos(user_id) WHERE status='ativo';""")

        # =================================================
        # MUNDO AUTÔNOMO — EVENTOS / BOSSES / ILHAS / NPCS
        # =================================================
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS eventos_globais (
                id BIGSERIAL PRIMARY KEY, tipo TEXT NOT NULL, titulo TEXT NOT NULL, descricao TEXT,
                localizacao TEXT NOT NULL, rank TEXT NOT NULL, recompensa JSONB NOT NULL DEFAULT '{}'::jsonb,
                canal_id BIGINT, mensagem_id BIGINT, thread_id BIGINT, sessao_id BIGINT,
                status TEXT NOT NULL DEFAULT 'aberto', exclusivo_marinha BOOLEAN NOT NULL DEFAULT FALSE,
                criado_em TIMESTAMPTZ DEFAULT NOW(), expira_em TIMESTAMPTZ NOT NULL, encerrado_em TIMESTAMPTZ
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS participantes_evento_global (
                evento_id BIGINT NOT NULL REFERENCES eventos_globais(id) ON DELETE CASCADE, user_id BIGINT NOT NULL,
                personagem_nome TEXT, status TEXT NOT NULL DEFAULT 'participando', entrou_em TIMESTAMPTZ DEFAULT NOW(),
                finalizado_em TIMESTAMPTZ, PRIMARY KEY(evento_id,user_id)
            );
        """)
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_evento_user_status ON participantes_evento_global(user_id,status);""")
        await conn.execute("ALTER TABLE eventos_globais ADD COLUMN IF NOT EXISTS hp_max INTEGER;")
        await conn.execute("ALTER TABLE eventos_globais ADD COLUMN IF NOT EXISTS hp_atual INTEGER;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dominacao_ilhas (
                localizacao TEXT PRIMARY KEY, dono_user_id BIGINT, dono_nome TEXT, faccao TEXT, estado TEXT NOT NULL DEFAULT 'livre',
                integridade INTEGER NOT NULL DEFAULT 100, atualizado_em TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subordinados (
                id BIGSERIAL PRIMARY KEY, dono_user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE,
                nome TEXT NOT NULL, funcao TEXT NOT NULL, rank TEXT NOT NULL DEFAULT 'E', salario BIGINT NOT NULL DEFAULT 1000,
                lealdade INTEGER NOT NULL DEFAULT 50, personalidade TEXT, memoria TEXT, ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cacadas_ativas (
                id BIGSERIAL PRIMARY KEY, alvo_user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE,
                cacador_nome TEXT NOT NULL, rank TEXT NOT NULL, motivo TEXT, status TEXT NOT NULL DEFAULT 'ativa',
                ultima_localizacao TEXT, criado_em TIMESTAMPTZ DEFAULT NOW(), atualizado_em TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS descobertas_ilha (
                user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, localizacao TEXT NOT NULL, chave TEXT NOT NULL,
                descoberto_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(user_id,localizacao,chave)
            );
        """)
        await conn.execute("""CREATE TABLE IF NOT EXISTS cooldowns_gameplay (user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, chave TEXT NOT NULL, disponivel_em TIMESTAMPTZ NOT NULL, atualizado_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(user_id,chave));""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS formas_personagem (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, nome TEXT NOT NULL, bonus_forca INTEGER NOT NULL DEFAULT 0, bonus_resistencia INTEGER NOT NULL DEFAULT 0, bonus_velocidade INTEGER NOT NULL DEFAULT 0, capacidades TEXT, requisitos TEXT, ativa BOOLEAN NOT NULL DEFAULT FALSE, desbloqueada BOOLEAN NOT NULL DEFAULT TRUE, criado_em TIMESTAMPTZ DEFAULT NOW(), UNIQUE(user_id,nome));""")
        # Embarque coletivo: plano antes da partida + passageiros da viagem real.
        await conn.execute("""CREATE TABLE IF NOT EXISTS planos_viagem (
            id BIGSERIAL PRIMARY KEY, proprietario_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE,
            embarcacao_id BIGINT NOT NULL REFERENCES embarcacoes(id) ON DELETE CASCADE,
            origem TEXT NOT NULL, destino TEXT NOT NULL, canal_id BIGINT, vagas INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'embarque', criado_em TIMESTAMPTZ DEFAULT NOW()
        );""")
        await conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_plano_viagem_owner_aberto ON planos_viagem(proprietario_id) WHERE status='embarque';""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS embarques_viagem (
            plano_id BIGINT NOT NULL REFERENCES planos_viagem(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE,
            embarcou_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(plano_id,user_id)
        );""")
        await conn.execute("DROP INDEX IF EXISTS uq_embarque_user_aberto;")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_embarque_user ON embarques_viagem(user_id);")
        await conn.execute("""CREATE TABLE IF NOT EXISTS viagem_passageiros (
            viagem_id BIGINT NOT NULL REFERENCES viagens(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE,
            PRIMARY KEY(viagem_id,user_id)
        );""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_viagem_passageiro_user ON viagem_passageiros(user_id);""")

        await conn.execute("""CREATE TABLE IF NOT EXISTS tripulacoes (id BIGSERIAL PRIMARY KEY, nome TEXT UNIQUE NOT NULL, capitao_user_id BIGINT NOT NULL, reputacao BIGINT NOT NULL DEFAULT 0, criado_em TIMESTAMPTZ DEFAULT NOW());""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS membros_tripulacao (tripulacao_id BIGINT REFERENCES tripulacoes(id) ON DELETE CASCADE, user_id BIGINT UNIQUE NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, cargo TEXT NOT NULL DEFAULT 'Tripulante', entrou_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(tripulacao_id,user_id));""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS alcunhas (user_id BIGINT REFERENCES fichas(user_id) ON DELETE CASCADE, alcunha TEXT NOT NULL, motivo TEXT, ativa BOOLEAN DEFAULT TRUE, criada_em TIMESTAMPTZ DEFAULT NOW(), UNIQUE(user_id,alcunha));""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS prisoes (user_id BIGINT PRIMARY KEY REFERENCES fichas(user_id) ON DELETE CASCADE, local TEXT NOT NULL, motivo TEXT, status TEXT NOT NULL DEFAULT 'preso', preso_em TIMESTAMPTZ DEFAULT NOW(), execucao_em TIMESTAMPTZ);""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS organizacoes (id BIGSERIAL PRIMARY KEY, nome TEXT UNIQUE NOT NULL, tipo TEXT NOT NULL, lider_user_id BIGINT, criado_em TIMESTAMPTZ DEFAULT NOW());""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS membros_organizacao (organizacao_id BIGINT REFERENCES organizacoes(id) ON DELETE CASCADE, user_id BIGINT UNIQUE NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, cargo TEXT NOT NULL DEFAULT 'Membro', entrou_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(organizacao_id,user_id));""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS akumas_encontradas (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, item_id TEXT NOT NULL, nome TEXT NOT NULL, tipo TEXT NOT NULL, encontrada_em TIMESTAMPTZ DEFAULT NOW(), expira_em TIMESTAMPTZ NOT NULL, consumida BOOLEAN DEFAULT FALSE);""")
        # Drops espontâneos de Akuma no Mi em canais de ilhas. Persistem entre redeploys.
        await conn.execute("""CREATE TABLE IF NOT EXISTS akuma_spawns_mundo (id BIGSERIAL PRIMARY KEY, guild_id BIGINT NOT NULL, channel_id BIGINT NOT NULL, localizacao TEXT NOT NULL, nome TEXT NOT NULL, tipo TEXT NOT NULL, mensagem_id BIGINT, status TEXT NOT NULL DEFAULT 'ativo', criado_em TIMESTAMPTZ DEFAULT NOW(), expira_em TIMESTAMPTZ NOT NULL, coletado_por BIGINT, coletado_em TIMESTAMPTZ);""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_akuma_spawns_status_expira ON akuma_spawns_mundo(status,expira_em);""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS akuma_spawn_controle (id SMALLINT PRIMARY KEY DEFAULT 1 CHECK(id=1), proximo_spawn_em TIMESTAMPTZ NOT NULL);""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS execucoes_diarias (chave TEXT PRIMARY KEY, executado_em TIMESTAMPTZ DEFAULT NOW());""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS sorteios_diarios (id BIGSERIAL PRIMARY KEY, premio TEXT NOT NULL, valor INTEGER NOT NULL DEFAULT 0, mensagem_id BIGINT, encerra_em TIMESTAMPTZ NOT NULL, status TEXT DEFAULT 'aberto', vencedor_user_id BIGINT);""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS participantes_sorteio (sorteio_id BIGINT REFERENCES sorteios_diarios(id) ON DELETE CASCADE, user_id BIGINT NOT NULL, PRIMARY KEY(sorteio_id,user_id));""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS bosses_rp_ativos (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, boss_nome TEXT NOT NULL, localizacao TEXT NOT NULL, rank TEXT NOT NULL, hp_max INTEGER NOT NULL, hp_atual INTEGER NOT NULL, falhas INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'ativo', iniciado_em TIMESTAMPTZ DEFAULT NOW(), finalizado_em TIMESTAMPTZ);""")
        # Boss de progressão 56: combate completo, sem afetar o mundo canônico.
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS player_hp_max INTEGER;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS player_hp_atual INTEGER;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS boss_estilo TEXT;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS turno INTEGER NOT NULL DEFAULT 1;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS player_focus INTEGER NOT NULL DEFAULT 0;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS boss_forca INTEGER;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS boss_resistencia INTEGER;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS boss_velocidade INTEGER;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS estado_contexto TEXT;")
        await conn.execute("ALTER TABLE bosses_rp_ativos ADD COLUMN IF NOT EXISTS historico_contexto TEXT;")
        await conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_boss_rp_user_ativo ON bosses_rp_ativos(user_id) WHERE status='ativo';""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS recompensas_npc_marcante (user_id BIGINT NOT NULL REFERENCES fichas(user_id) ON DELETE CASCADE, npc_nome TEXT NOT NULL, instancia TEXT NOT NULL DEFAULT 'mundo', recebido_em TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(user_id,npc_nome,instancia));""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_boss_rp_user_status ON bosses_rp_ativos(user_id,status);""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_sorteios_status_fim ON sorteios_diarios(status,encerra_em);""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_viagens_status_evento ON viagens(status,proximo_evento_em,chegada_em);""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_treinos_status_fim ON treinamentos(status,fim_em);""")
        await conn.execute("""CREATE INDEX IF NOT EXISTS idx_eventos_globais_status_expira ON eventos_globais(status,expira_em);""")



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
    vontade_d=False,
    joyboy=False,
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
                    vontade_d,
                    joyboy,
                    forca,
                    resistencia,
                    velocidade,
                    pontos_atributo
                )

                VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20
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
                vontade_d,
                joyboy,
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


async def definir_rank_manual(user_id, rank):
    db = get_pool()
    return await db.execute("UPDATE fichas SET rank_manual=$1 WHERE user_id=$2;", rank, user_id)


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


async def buscar_sessao_ativa_usuario(user_id):
    """Retorna a sessão ativa da qual o jogador participa ativamente."""
    db = get_pool()
    return await db.fetchrow(
        """
        SELECT s.* FROM sessoes_narracao s
        JOIN participantes_sessao p ON p.sessao_id=s.id
        WHERE p.user_id=$1 AND p.status='ativo' AND s.status='ativa'
        ORDER BY s.id DESC LIMIT 1;
        """, int(user_id)
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

async def atualizar_estado_cena_sessao(sessao_id, conflito_ativo=None, estado_cena=None):
    db=get_pool()
    return await db.fetchrow("""UPDATE sessoes_narracao SET
        conflito_ativo=COALESCE($2,conflito_ativo),
        estado_cena=COALESCE($3,estado_cena),
        atualizada_em=CURRENT_TIMESTAMP WHERE id=$1 RETURNING *;""",
        int(sessao_id), conflito_ativo, estado_cena)

async def buscar_evento_por_thread(thread_id):
    return await get_pool().fetchrow("SELECT * FROM eventos_globais WHERE thread_id=$1 AND status IN ('aberto','andamento') ORDER BY id DESC LIMIT 1;",int(thread_id))

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

    # A ficha usa reputação geral para Rank. Cada acontecimento confirmado
    # acrescenta reputação pela relevância, sem substituir relações por facção.
    await db.execute(
        "UPDATE fichas SET reputacao = reputacao + $1 WHERE LOWER(nome)=LOWER($2);",
        g * 10, personagem_nome
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

async def definir_deadline_ciclo(sessao_id, segundos=90):
    db=get_pool()
    return await db.fetchrow("""UPDATE sessoes_narracao SET ciclo_deadline=NOW()+($2 * INTERVAL '1 second'), atualizada_em=NOW() WHERE id=$1 AND status='ativa' RETURNING *;""", int(sessao_id), int(segundos))

async def limpar_deadline_ciclo(sessao_id):
    return await get_pool().execute("UPDATE sessoes_narracao SET ciclo_deadline=NULL WHERE id=$1;", int(sessao_id))

async def listar_ciclos_expirados():
    return await get_pool().fetch("""SELECT * FROM sessoes_narracao WHERE status='ativa' AND iniciada=TRUE AND ciclo_deadline IS NOT NULL AND ciclo_deadline<=NOW() ORDER BY ciclo_deadline LIMIT 30;""")

async def registrar_acao_cena_sessao(sessao_id,ciclo,user_id,personagem_nome,acao):
    db=get_pool()
    return await db.fetchrow("""INSERT INTO acoes_cena_sessao(sessao_id,ciclo,user_id,personagem_nome,acao)
        VALUES($1,$2,$3,$4,$5) ON CONFLICT(sessao_id,ciclo,user_id) DO UPDATE SET
        personagem_nome=EXCLUDED.personagem_nome,acao=EXCLUDED.acao,criado_em=CURRENT_TIMESTAMP RETURNING *;""",
        int(sessao_id),int(ciclo),int(user_id),str(personagem_nome),str(acao))

async def listar_acoes_cena_sessao(sessao_id,ciclo):
    db=get_pool()
    return await db.fetch("SELECT * FROM acoes_cena_sessao WHERE sessao_id=$1 AND ciclo=$2 ORDER BY criado_em;",
                          int(sessao_id),int(ciclo))

async def avancar_ciclo_cena_sessao(sessao_id):
    db=get_pool()
    return await db.fetchrow("UPDATE sessoes_narracao SET ciclo_cena=ciclo_cena+1,ciclo_deadline=NULL,atualizada_em=CURRENT_TIMESTAMP WHERE id=$1 RETURNING *;",
                             int(sessao_id))

async def definir_inicio_ciclo_participante(sessao_id,user_id,ciclo):
    db=get_pool()
    return await db.fetchrow("UPDATE participantes_sessao SET participa_desde_ciclo=$3 WHERE sessao_id=$1 AND user_id=$2 RETURNING *;",
                             int(sessao_id),int(user_id),int(ciclo))

async def listar_participantes_ciclo(sessao_id,ciclo):
    db=get_pool()
    return await db.fetch("""SELECT * FROM participantes_sessao WHERE sessao_id=$1 AND status='ativo'
        AND participa_desde_ciclo <= $2 ORDER BY entrou_em;""",int(sessao_id),int(ciclo))

# =========================================================
# ECONOMIA — INVENTÁRIO / LOJA / EMBARCAÇÕES
# =========================================================

async def buscar_inventario(user_id):
    return await get_pool().fetch("SELECT * FROM inventario WHERE user_id=$1 AND quantidade>0 ORDER BY item_id;", user_id)

async def buscar_item_inventario(user_id, item_id):
    return await get_pool().fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND item_id=$2 AND quantidade>0;", user_id, item_id)

async def registrar_transacao_economia(user_id, tipo, valor=0, item_id=None, quantidade=1, detalhes=None, conn=None):
    db = conn or get_pool()
    await db.execute("""INSERT INTO transacoes_economia(user_id,tipo,valor,item_id,quantidade,detalhes) VALUES($1,$2,$3,$4,$5,$6);""",
                     user_id, tipo, int(valor), item_id, int(quantidade), detalhes)

async def adicionar_item_inventario(user_id, item_id, quantidade=1, conn=None):
    db=conn or get_pool()
    await db.execute("""INSERT INTO inventario(user_id,item_id,quantidade,atualizado_em) VALUES($1,$2,$3,CURRENT_TIMESTAMP)
        ON CONFLICT(user_id,item_id) DO UPDATE SET quantidade=inventario.quantidade+EXCLUDED.quantidade, atualizado_em=CURRENT_TIMESTAMP;""",
        user_id,item_id,int(quantidade))

async def consumir_item(user_id,item_id,quantidade=1):
    db=get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            row=await conn.fetchrow("SELECT quantidade FROM inventario WHERE user_id=$1 AND item_id=$2 FOR UPDATE;",user_id,item_id)
            if not row or row['quantidade']<quantidade:return False
            await conn.execute("UPDATE inventario SET quantidade=quantidade-$3,atualizado_em=CURRENT_TIMESTAMP WHERE user_id=$1 AND item_id=$2;",user_id,item_id,quantidade)
            await registrar_transacao_economia(user_id,"consumo",0,item_id,quantidade,None,conn)
            return True

async def comprar_item(user_id,item_id,preco,quantidade=1):
    total=int(preco)*int(quantidade); db=get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            ficha=await conn.fetchrow("SELECT berries FROM fichas WHERE user_id=$1 FOR UPDATE;",user_id)
            if not ficha:return False,"Ficha não encontrada."
            if ficha['berries']<total:return False,f"Berries insuficientes. Necessário: ฿ {total:,}.".replace(',', '.')
            await conn.execute("UPDATE fichas SET berries=berries-$1 WHERE user_id=$2;",total,user_id)
            await adicionar_item_inventario(user_id,item_id,quantidade,conn)
            await registrar_transacao_economia(user_id,"compra",-total,item_id,quantidade,None,conn)
            return True,"Compra concluída. O item foi enviado ao seu inventário."

async def vender_item(user_id,item_id,valor_unitario,quantidade=1):
    total=int(valor_unitario)*int(quantidade); db=get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            row=await conn.fetchrow("SELECT quantidade FROM inventario WHERE user_id=$1 AND item_id=$2 FOR UPDATE;",user_id,item_id)
            if not row or row['quantidade']<quantidade:return False,"Você não possui esse item em quantidade suficiente."
            await conn.execute("UPDATE inventario SET quantidade=quantidade-$3,atualizado_em=CURRENT_TIMESTAMP WHERE user_id=$1 AND item_id=$2;",user_id,item_id,quantidade)
            await conn.execute("UPDATE fichas SET berries=berries+$1 WHERE user_id=$2;",total,user_id)
            await registrar_transacao_economia(user_id,"venda",total,item_id,quantidade,None,conn)
            return True,f"Venda concluída. Você recebeu ฿ {total:,}.".replace(',', '.')

async def comprar_embarcacao(user_id,tipo,dados,localizacao):
    preco=int(dados['preco']); db=get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            ficha=await conn.fetchrow("SELECT berries FROM fichas WHERE user_id=$1 FOR UPDATE;",user_id)
            if not ficha:return False,"Ficha não encontrada."
            if ficha['berries']<preco:return False,"Berries insuficientes para essa embarcação."
            existe=await conn.fetchval("SELECT EXISTS(SELECT 1 FROM embarcacoes WHERE proprietario_id=$1 AND ativa=TRUE);",user_id)
            await conn.execute("UPDATE fichas SET berries=berries-$1 WHERE user_id=$2;",preco,user_id)
            nome=f"{dados['nome']} de bordo"
            await conn.execute("""INSERT INTO embarcacoes(proprietario_id,tipo,nome,integridade_atual,integridade_max,capacidade,carga_max,localizacao,ativa)
                VALUES($1,$2,$3,$4,$4,$5,$6,$7,$8);""",user_id,tipo,nome,int(dados['integridade']),int(dados['capacidade']),int(dados['carga']),localizacao,not existe)
            await registrar_transacao_economia(user_id,"compra_embarcacao",-preco,tipo,1,localizacao,conn)
            return True,f"{dados['nome']} adquirido. Use `!nomearnavio <nome>` para nomear sua embarcação ativa."

async def buscar_embarcacoes(user_id):
    return await get_pool().fetch("SELECT * FROM embarcacoes WHERE proprietario_id=$1 ORDER BY ativa DESC,id;",user_id)

async def buscar_embarcacao_ativa(user_id):
    return await get_pool().fetchrow("SELECT * FROM embarcacoes WHERE proprietario_id=$1 AND ativa=TRUE LIMIT 1;",user_id)

async def renomear_embarcacao(embarcacao_id,user_id,nome):
    return await get_pool().execute("UPDATE embarcacoes SET nome=$1,atualizado_em=CURRENT_TIMESTAMP WHERE id=$2 AND proprietario_id=$3;",nome,embarcacao_id,user_id)

async def mover_embarcacao(embarcacao_id,localizacao):
    return await get_pool().execute("UPDATE embarcacoes SET localizacao=$1,atualizado_em=CURRENT_TIMESTAMP WHERE id=$2;",localizacao,embarcacao_id)

async def reparar_embarcacao(embarcacao_id,quantidade):
    return await get_pool().fetchrow("""UPDATE embarcacoes SET integridade_atual=LEAST(integridade_max,integridade_atual+$1), atualizado_em=CURRENT_TIMESTAMP WHERE id=$2 RETURNING *;""",int(quantidade),embarcacao_id)

async def contar_itens_inventario(user_id):
    return await get_pool().fetchval("SELECT COALESCE(SUM(quantidade),0) FROM inventario WHERE user_id=$1 AND quantidade>0;",user_id)


# =========================================================
# VIAGENS / NAVEGAÇÃO PERSISTENTE
# =========================================================
async def buscar_viagem_ativa(user_id):
    return await get_pool().fetchrow("""SELECT v.* FROM viagens v
        LEFT JOIN viagem_passageiros vp ON vp.viagem_id=v.id
        WHERE v.status IN ('viajando','obstaculo') AND (v.user_id=$1 OR vp.user_id=$1)
        ORDER BY v.id DESC LIMIT 1;""",user_id)

async def criar_viagem(user_id, embarcacao_id, origem, destino, canal_id, chegada_em, proximo_evento_em, eventos, suprimentos, desgaste, passageiros=None):
    db=get_pool(); passageiros=list(dict.fromkeys([int(user_id)]+[int(x) for x in (passageiros or [])]))
    async with db.acquire() as c:
        async with c.transaction():
            v=await c.fetchrow("""INSERT INTO viagens(user_id,embarcacao_id,origem,destino,canal_id,chegada_em,proximo_evento_em,eventos_restantes,suprimentos_gastos,desgaste)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING *;""",user_id,embarcacao_id,origem,destino,canal_id,chegada_em,proximo_evento_em,eventos,suprimentos,desgaste)
            for uid in passageiros:
                await c.execute("INSERT INTO viagem_passageiros(viagem_id,user_id) VALUES($1,$2) ON CONFLICT DO NOTHING",v['id'],uid)
            return v

async def criar_plano_viagem(proprietario_id, embarcacao_id, origem, destino, canal_id, vagas):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            if await c.fetchrow("SELECT 1 FROM planos_viagem WHERE proprietario_id=$1 AND status='embarque'",proprietario_id): return None
            if await c.fetchrow("SELECT 1 FROM embarques_viagem e JOIN planos_viagem p ON p.id=e.plano_id WHERE e.user_id=$1 AND p.status='embarque'",proprietario_id): return None
            p=await c.fetchrow("INSERT INTO planos_viagem(proprietario_id,embarcacao_id,origem,destino,canal_id,vagas) VALUES($1,$2,$3,$4,$5,$6) RETURNING *",proprietario_id,embarcacao_id,origem,destino,canal_id,int(vagas))
            await c.execute("INSERT INTO embarques_viagem(plano_id,user_id) VALUES($1,$2)",p['id'],proprietario_id)
            return p

async def buscar_plano_viagem_user(user_id):
    return await get_pool().fetchrow("""SELECT p.* FROM planos_viagem p JOIN embarques_viagem e ON e.plano_id=p.id
        WHERE e.user_id=$1 AND p.status='embarque' ORDER BY p.id DESC LIMIT 1""",user_id)

async def buscar_plano_viagem_canal(canal_id):
    return await get_pool().fetchrow("SELECT * FROM planos_viagem WHERE canal_id=$1 AND status='embarque' ORDER BY id DESC LIMIT 1",canal_id)

async def listar_embarques(plano_id):
    return await get_pool().fetch("SELECT e.*,f.nome FROM embarques_viagem e JOIN fichas f ON f.user_id=e.user_id WHERE e.plano_id=$1 ORDER BY e.embarcou_em",plano_id)

async def embarcar_plano(plano_id,user_id):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            p=await c.fetchrow("SELECT * FROM planos_viagem WHERE id=$1 AND status='embarque' FOR UPDATE",plano_id)
            if not p:return False,'Embarque encerrado.'
            outro=await c.fetchrow("SELECT 1 FROM embarques_viagem e JOIN planos_viagem p ON p.id=e.plano_id WHERE e.user_id=$1 AND p.status='embarque'",user_id)
            if outro:return False,'Você já está em outro embarque aberto.'
            qtd=await c.fetchval("SELECT COUNT(*) FROM embarques_viagem WHERE plano_id=$1",plano_id)
            if qtd>=p['vagas']:return False,'A embarcação já atingiu o número definido para esta viagem.'
            try: await c.execute("INSERT INTO embarques_viagem(plano_id,user_id) VALUES($1,$2)",plano_id,user_id)
            except Exception:return False,'Você já está em outro embarque ou nesta viagem.'
            return True,'Embarque confirmado.'

async def desembarcar_plano(user_id):
    p=await buscar_plano_viagem_user(user_id)
    if not p:return False
    if p['proprietario_id']==user_id:return False
    await get_pool().execute("DELETE FROM embarques_viagem WHERE plano_id=$1 AND user_id=$2",p['id'],user_id); return True

async def cancelar_plano_viagem(proprietario_id):
    return await get_pool().fetchrow("UPDATE planos_viagem SET status='cancelado' WHERE proprietario_id=$1 AND status='embarque' RETURNING *",proprietario_id)

async def fechar_plano_viagem(plano_id):
    return await get_pool().fetchrow("UPDATE planos_viagem SET status='partiu' WHERE id=$1 AND status='embarque' RETURNING *",plano_id)

async def passageiros_viagem(viagem_id):
    return await get_pool().fetch("SELECT vp.user_id,f.nome FROM viagem_passageiros vp JOIN fichas f ON f.user_id=vp.user_id WHERE vp.viagem_id=$1",viagem_id)

async def viagens_pendentes():
    return await get_pool().fetch("SELECT * FROM viagens WHERE status IN ('viajando','obstaculo') ORDER BY chegada_em;")

async def criar_evento_viagem(viagem_id,titulo,descricao):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            ev=await c.fetchrow("INSERT INTO eventos_viagem(viagem_id,titulo,descricao) VALUES($1,$2,$3) RETURNING *;",viagem_id,titulo,descricao)
            await c.execute("UPDATE viagens SET status='obstaculo', atualizado_em=NOW() WHERE id=$1;",viagem_id)
            return ev

async def evento_aberto_viagem(viagem_id):
    return await get_pool().fetchrow("SELECT * FROM eventos_viagem WHERE viagem_id=$1 AND resolvido=FALSE ORDER BY id DESC LIMIT 1;",viagem_id)

async def resolver_evento_viagem(viagem_id,acao,resultado,atraso_min=0,dano=0):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            ev=await c.fetchrow("SELECT * FROM eventos_viagem WHERE viagem_id=$1 AND resolvido=FALSE ORDER BY id DESC LIMIT 1 FOR UPDATE;",viagem_id)
            if not ev:return None
            await c.execute("UPDATE eventos_viagem SET resolvido=TRUE,acao_player=$2,resultado=$3,resolvido_em=NOW() WHERE id=$1;",ev['id'],acao,resultado)
            v=await c.fetchrow("UPDATE viagens SET status='viajando', chegada_em=chegada_em+make_interval(mins => $2), eventos_restantes=GREATEST(0,eventos_restantes-1), proximo_evento_em=NULL, atualizado_em=NOW() WHERE id=$1 RETURNING *;",viagem_id,int(atraso_min))
            if dano>0: await c.execute("UPDATE embarcacoes SET integridade_atual=GREATEST(0,integridade_atual-$2),atualizado_em=NOW() WHERE id=$1;",v['embarcacao_id'],int(dano))
            return v

async def agendar_proximo_evento_viagem(viagem_id,quando):
    return await get_pool().execute("UPDATE viagens SET proximo_evento_em=$2 WHERE id=$1;",viagem_id,quando)

async def concluir_viagem(viagem_id):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            v=await c.fetchrow("SELECT * FROM viagens WHERE id=$1 FOR UPDATE;",viagem_id)
            if not v or v['status'] not in ('viajando','obstaculo'):return None
            if v['status']=='obstaculo':return None
            await c.execute("UPDATE viagens SET status='concluida',atualizado_em=NOW() WHERE id=$1;",viagem_id)
            await c.execute("UPDATE embarcacoes SET localizacao=$2,integridade_atual=GREATEST(0,integridade_atual-$3),atualizado_em=NOW() WHERE id=$1;",v['embarcacao_id'],v['destino'],v['desgaste'])
            passageiros=await c.fetch("SELECT user_id FROM viagem_passageiros WHERE viagem_id=$1",viagem_id)
            ids={int(v['user_id'])}|{int(x['user_id']) for x in passageiros}
            for uid in ids:
                await c.execute("INSERT INTO localizacoes_jogador(user_id,localizacao,area,atualizado_em) VALUES($1,$2,NULL,NOW()) ON CONFLICT(user_id) DO UPDATE SET localizacao=EXCLUDED.localizacao,area=NULL,atualizado_em=NOW();",uid,v['destino'])
            return v

async def danificar_embarcacao(embarcacao_id,quantidade):
    return await get_pool().fetchrow("UPDATE embarcacoes SET integridade_atual=GREATEST(0,integridade_atual-$2),atualizado_em=NOW() WHERE id=$1 RETURNING *;",embarcacao_id,int(quantidade))

# =========================================================
# TREINAMENTOS PERSISTENTES
# =========================================================
async def buscar_treinamento_ativo(user_id):
    return await get_pool().fetchrow("SELECT * FROM treinamentos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1;",user_id)
async def criar_treinamento(user_id,tipo,alvo,ganho,canal_id,fim_em):
    return await get_pool().fetchrow("INSERT INTO treinamentos(user_id,tipo,alvo,ganho,canal_id,fim_em) VALUES($1,$2,$3,$4,$5,$6) RETURNING *;",user_id,tipo,alvo,int(ganho),canal_id,fim_em)
async def cancelar_treinamento(user_id):
    return await get_pool().fetchrow(
        """UPDATE treinamentos SET status='cancelado', concluido_em=NOW()
           WHERE id=(SELECT id FROM treinamentos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1)
           RETURNING *;""", int(user_id)
    )

async def treinamentos_prontos():
    return await get_pool().fetch("SELECT * FROM treinamentos WHERE status='ativo' AND fim_em<=NOW() ORDER BY fim_em;")
async def concluir_treinamento(treino_id):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            t=await c.fetchrow("SELECT * FROM treinamentos WHERE id=$1 AND status='ativo' FOR UPDATE;",treino_id)
            if not t:return None
            if t['tipo']=='atributo':
                col={'forca':'forca','resistencia':'resistencia','velocidade':'velocidade'}.get(t['alvo'])
                if not col:return None
                await c.execute(f"UPDATE fichas SET {col}=LEAST(50000,{col}+$1) WHERE user_id=$2;",t['ganho'],t['user_id'])
            elif t['tipo']=='dominio':
                await c.execute("UPDATE especializacoes SET porcentagem=LEAST(limite,porcentagem+$1) WHERE user_id=$2 AND LOWER(nome)=LOWER($3);",t['ganho'],t['user_id'],t['alvo'])
            await c.execute("UPDATE treinamentos SET status='concluido',concluido_em=NOW() WHERE id=$1;",treino_id)
            return t

async def pagar_reparo_embarcacao(user_id,embarcacao_id,custo):
    db=get_pool(); custo=int(custo)
    async with db.acquire() as c:
        async with c.transaction():
            f=await c.fetchrow("SELECT berries FROM fichas WHERE user_id=$1 FOR UPDATE;",user_id)
            if not f or f['berries']<custo:return False
            n=await c.fetchrow("SELECT * FROM embarcacoes WHERE id=$1 AND proprietario_id=$2 FOR UPDATE;",embarcacao_id,user_id)
            if not n:return False
            await c.execute("UPDATE fichas SET berries=berries-$1 WHERE user_id=$2;",custo,user_id)
            await c.execute("UPDATE embarcacoes SET integridade_atual=integridade_max,atualizado_em=NOW() WHERE id=$1;",embarcacao_id)
            await registrar_transacao_economia(user_id,'reparo_estaleiro',-custo,None,1,n['nome'],c)
            return True

async def liberar_rota_especial(user_id,destino,origem=None,motivo="admin"):
    return await get_pool().execute("INSERT INTO rotas_liberadas(user_id,destino,origem,motivo) VALUES($1,$2,$3,$4) ON CONFLICT(user_id,destino) DO UPDATE SET origem=EXCLUDED.origem,motivo=EXCLUDED.motivo;",user_id,destino,origem,motivo)
async def rota_especial_liberada(user_id,destino):
    return await get_pool().fetchval("SELECT EXISTS(SELECT 1 FROM rotas_liberadas WHERE user_id=$1 AND destino=$2);",user_id,destino)


# =========================================================
# MUNDO AUTÔNOMO — HELPERS
# =========================================================
async def criar_evento_global(tipo,titulo,descricao,localizacao,rank,recompensa,canal_id,expira_em,exclusivo_marinha=False):
    import json
    return await get_pool().fetchrow("""INSERT INTO eventos_globais(tipo,titulo,descricao,localizacao,rank,recompensa,canal_id,expira_em,exclusivo_marinha)
        VALUES($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9) RETURNING *;""",tipo,titulo,descricao,localizacao,rank,json.dumps(recompensa),canal_id,expira_em,exclusivo_marinha)

async def listar_eventos_globais_abertos():
    return await get_pool().fetch("SELECT * FROM eventos_globais WHERE status='aberto' AND expira_em>NOW() ORDER BY id DESC;")

async def buscar_evento_global(evento_id):
    return await get_pool().fetchrow("SELECT * FROM eventos_globais WHERE id=$1;",int(evento_id))

async def vincular_evento_thread(evento_id,thread_id,sessao_id):
    return await get_pool().execute("UPDATE eventos_globais SET thread_id=$2,sessao_id=$3 WHERE id=$1;",int(evento_id),int(thread_id),int(sessao_id))

async def participar_evento_global(evento_id,user_id,nome):
    return await get_pool().fetchrow("""INSERT INTO participantes_evento_global(evento_id,user_id,personagem_nome,status) VALUES($1,$2,$3,'participando')
        ON CONFLICT(evento_id,user_id) DO UPDATE SET personagem_nome=EXCLUDED.personagem_nome RETURNING *;""",int(evento_id),int(user_id),nome)

async def status_participacao_evento(evento_id,user_id):
    return await get_pool().fetchrow("SELECT * FROM participantes_evento_global WHERE evento_id=$1 AND user_id=$2;",int(evento_id),int(user_id))

async def evento_ativo_usuario(user_id):
    return await get_pool().fetchrow("""SELECT e.*,p.status AS participante_status FROM eventos_globais e JOIN participantes_evento_global p ON p.evento_id=e.id
        WHERE p.user_id=$1 AND p.status='participando' AND e.status IN ('aberto','andamento') ORDER BY e.id DESC LIMIT 1;""",int(user_id))

async def participantes_evento(evento_id,status=None):
    if status:return await get_pool().fetch("SELECT * FROM participantes_evento_global WHERE evento_id=$1 AND status=$2 ORDER BY entrou_em;",int(evento_id),status)
    return await get_pool().fetch("SELECT * FROM participantes_evento_global WHERE evento_id=$1 ORDER BY entrou_em;",int(evento_id))

async def marcar_evento_andamento(evento_id):
    return await get_pool().execute("UPDATE eventos_globais SET status='andamento' WHERE id=$1 AND status='aberto';",int(evento_id))

async def desistir_evento(evento_id,user_id):
    return await get_pool().fetchrow("UPDATE participantes_evento_global SET status='desistiu',finalizado_em=NOW() WHERE evento_id=$1 AND user_id=$2 AND status='participando' RETURNING *;",int(evento_id),int(user_id))

async def buscar_sessao_por_id(sessao_id):
    return await get_pool().fetchrow("SELECT * FROM sessoes_narracao WHERE id=$1;",int(sessao_id))

async def concluir_evento_global(evento_id):
    return await get_pool().fetchrow("UPDATE eventos_globais SET status='concluido',encerrado_em=NOW() WHERE id=$1 AND status<>'concluido' RETURNING *;",int(evento_id))

async def finalizar_participantes_evento(evento_id):
    return await get_pool().execute("UPDATE participantes_evento_global SET status='concluido',finalizado_em=NOW() WHERE evento_id=$1 AND status='participando';",int(evento_id))

async def eventos_para_finalizar():
    return await get_pool().fetch("""SELECT e.* FROM eventos_globais e JOIN sessoes_narracao s ON s.id=e.sessao_id
        WHERE e.status='andamento' AND s.status='encerrada';""")

async def definir_dominacao_ilha(localizacao,user_id,nome,faccao,estado='dominada',integridade=100):
    return await get_pool().fetchrow("""INSERT INTO dominacao_ilhas(localizacao,dono_user_id,dono_nome,faccao,estado,integridade) VALUES($1,$2,$3,$4,$5,$6)
        ON CONFLICT(localizacao) DO UPDATE SET dono_user_id=EXCLUDED.dono_user_id,dono_nome=EXCLUDED.dono_nome,faccao=EXCLUDED.faccao,estado=EXCLUDED.estado,integridade=EXCLUDED.integridade,atualizado_em=NOW() RETURNING *;""",localizacao,user_id,nome,faccao,estado,integridade)

async def buscar_dominacao_ilha(localizacao):
    return await get_pool().fetchrow("SELECT * FROM dominacao_ilhas WHERE LOWER(localizacao)=LOWER($1);",localizacao)

async def criar_subordinado(user_id,nome,funcao,rank,salario,personalidade):
    return await get_pool().fetchrow("INSERT INTO subordinados(dono_user_id,nome,funcao,rank,salario,personalidade) VALUES($1,$2,$3,$4,$5,$6) RETURNING *;",user_id,nome,funcao,rank,salario,personalidade)

async def listar_subordinados(user_id):
    return await get_pool().fetch("SELECT * FROM subordinados WHERE dono_user_id=$1 AND ativo=TRUE ORDER BY id;",user_id)

async def criar_cacada(alvo_user_id,cacador_nome,rank,motivo,localizacao=None):
    return await get_pool().fetchrow("INSERT INTO cacadas_ativas(alvo_user_id,cacador_nome,rank,motivo,ultima_localizacao) VALUES($1,$2,$3,$4,$5) RETURNING *;",alvo_user_id,cacador_nome,rank,motivo,localizacao)

async def listar_cacadas(alvo_user_id):
    return await get_pool().fetch("SELECT * FROM cacadas_ativas WHERE alvo_user_id=$1 AND status='ativa' ORDER BY id DESC;",alvo_user_id)

async def registrar_descoberta(user_id,localizacao,chave):
    return await get_pool().execute("INSERT INTO descobertas_ilha(user_id,localizacao,chave) VALUES($1,$2,$3) ON CONFLICT DO NOTHING;",user_id,localizacao,chave)

async def listar_descobertas(user_id,localizacao):
    return await get_pool().fetch("SELECT chave FROM descobertas_ilha WHERE user_id=$1 AND LOWER(localizacao)=LOWER($2);",user_id,localizacao)


async def definir_hp_evento(evento_id,hp):
    return await get_pool().execute("UPDATE eventos_globais SET hp_max=$2,hp_atual=$2 WHERE id=$1;",int(evento_id),int(hp))

async def candidatos_cacada():
    return await get_pool().fetch("""SELECT f.user_id,f.nome,f.reputacao,l.localizacao FROM fichas f LEFT JOIN localizacoes_jogador l ON l.user_id=f.user_id
        WHERE f.reputacao>=500 AND NOT EXISTS(SELECT 1 FROM cacadas_ativas c WHERE c.alvo_user_id=f.user_id AND c.status='ativa') ORDER BY f.reputacao DESC LIMIT 10;""")


async def buscar_cooldown(user_id,chave): return await get_pool().fetchrow("SELECT * FROM cooldowns_gameplay WHERE user_id=$1 AND chave=$2;",user_id,chave)
async def definir_cooldown(user_id,chave,disponivel_em): return await get_pool().execute("INSERT INTO cooldowns_gameplay(user_id,chave,disponivel_em) VALUES($1,$2,$3) ON CONFLICT(user_id,chave) DO UPDATE SET disponivel_em=EXCLUDED.disponivel_em,atualizado_em=NOW();",user_id,chave,disponivel_em)
async def incrementar_especializacao_direto(user_id,nome,quantidade): return await get_pool().fetchrow("UPDATE especializacoes SET porcentagem=LEAST(limite,porcentagem+$3) WHERE user_id=$1 AND LOWER(nome)=LOWER($2) RETURNING *;",user_id,nome,int(quantidade))
async def liberar_forma(user_id,nome,bf=0,br=0,bv=0,capacidades='',requisitos=''): return await get_pool().fetchrow("INSERT INTO formas_personagem(user_id,nome,bonus_forca,bonus_resistencia,bonus_velocidade,capacidades,requisitos) VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(user_id,nome) DO UPDATE SET bonus_forca=EXCLUDED.bonus_forca,bonus_resistencia=EXCLUDED.bonus_resistencia,bonus_velocidade=EXCLUDED.bonus_velocidade,capacidades=EXCLUDED.capacidades,requisitos=EXCLUDED.requisitos,desbloqueada=TRUE RETURNING *;",user_id,nome,int(bf),int(br),int(bv),capacidades,requisitos)
async def listar_formas(user_id): return await get_pool().fetch("SELECT * FROM formas_personagem WHERE user_id=$1 AND desbloqueada=TRUE ORDER BY id;",user_id)
async def forma_ativa(user_id): return await get_pool().fetchrow("SELECT * FROM formas_personagem WHERE user_id=$1 AND ativa=TRUE LIMIT 1;",user_id)
async def ativar_forma(user_id,nome):
    async with get_pool().acquire() as c:
        async with c.transaction():
            await c.execute("UPDATE formas_personagem SET ativa=FALSE WHERE user_id=$1;",user_id)
            return await c.fetchrow("UPDATE formas_personagem SET ativa=TRUE WHERE user_id=$1 AND LOWER(nome)=LOWER($2) AND desbloqueada=TRUE RETURNING *;",user_id,nome)
async def desativar_forma(user_id): return await get_pool().execute("UPDATE formas_personagem SET ativa=FALSE WHERE user_id=$1;",user_id)


# =========================================================
# SISTEMAS FINAIS — SOCIAL / AKUMA / PRISÃO / ORGANIZAÇÕES
# =========================================================
async def criar_tripulacao(nome,capitao):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            if await c.fetchrow("SELECT 1 FROM membros_tripulacao WHERE user_id=$1",capitao): return None
            r=await c.fetchrow("INSERT INTO tripulacoes(nome,capitao_user_id) VALUES($1,$2) ON CONFLICT(nome) DO NOTHING RETURNING *",nome,capitao)
            if not r:return None
            await c.execute("INSERT INTO membros_tripulacao(tripulacao_id,user_id,cargo) VALUES($1,$2,'Capitão')",r['id'],capitao); return r
async def buscar_tripulacao_nome(nome): return await get_pool().fetchrow("SELECT * FROM tripulacoes WHERE LOWER(nome)=LOWER($1)",nome)
async def buscar_tripulacao_user(uid): return await get_pool().fetchrow("SELECT t.*,m.cargo FROM tripulacoes t JOIN membros_tripulacao m ON m.tripulacao_id=t.id WHERE m.user_id=$1",uid)
async def entrar_tripulacao(tid,uid): return await get_pool().execute("INSERT INTO membros_tripulacao(tripulacao_id,user_id) VALUES($1,$2) ON CONFLICT(user_id) DO NOTHING",tid,uid)
async def sair_tripulacao(uid): return await get_pool().execute("DELETE FROM membros_tripulacao WHERE user_id=$1 AND cargo<>'Capitão'",uid)
async def listar_membros_tripulacao(tid): return await get_pool().fetch("SELECT m.*,f.nome FROM membros_tripulacao m JOIN fichas f ON f.user_id=m.user_id WHERE m.tripulacao_id=$1 ORDER BY m.entrou_em",tid)
async def registrar_alcunha(uid,nome,motivo): return await get_pool().execute("INSERT INTO alcunhas(user_id,alcunha,motivo) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",uid,nome,motivo)
async def listar_alcunhas(uid): return await get_pool().fetch("SELECT * FROM alcunhas WHERE user_id=$1 ORDER BY criada_em DESC",uid)
async def prender(uid,local,motivo): return await get_pool().execute("INSERT INTO prisoes(user_id,local,motivo) VALUES($1,$2,$3) ON CONFLICT(user_id) DO UPDATE SET local=$2,motivo=$3,status='preso',preso_em=NOW(),execucao_em=NULL",uid,local,motivo)
async def buscar_prisao(uid): return await get_pool().fetchrow("SELECT * FROM prisoes WHERE user_id=$1 AND status IN ('preso','execucao')",uid)
async def libertar(uid): return await get_pool().execute("UPDATE prisoes SET status='liberto' WHERE user_id=$1",uid)
async def listar_organizacoes(): return await get_pool().fetch("SELECT * FROM organizacoes ORDER BY nome")
async def garantir_organizacoes():
    for n,t in [('Germa 66','Reino/Exército'),('Cipher Pol','Governo Mundial'),('Baroque Works','Organização criminosa'),('Cross Guild','Organização pirata'),('Shichibukai','Título/Organização'),('Yonkou','Poder marítimo'),('Marinha','Governo Mundial'),('Exército Revolucionário','Revolucionária')]:
        await get_pool().execute("INSERT INTO organizacoes(nome,tipo) VALUES($1,$2) ON CONFLICT(nome) DO NOTHING",n,t)
async def entrar_organizacao(oid,uid,cargo='Membro'): return await get_pool().execute("INSERT INTO membros_organizacao(organizacao_id,user_id,cargo) VALUES($1,$2,$3) ON CONFLICT(user_id) DO NOTHING",oid,uid,cargo)
async def organizacao_user(uid): return await get_pool().fetchrow("SELECT o.*,m.cargo FROM organizacoes o JOIN membros_organizacao m ON m.organizacao_id=o.id WHERE m.user_id=$1",uid)
async def execucao_diaria_feita(chave): return bool(await get_pool().fetchrow("SELECT 1 FROM execucoes_diarias WHERE chave=$1",chave))
async def marcar_execucao_diaria(chave): return await get_pool().execute("INSERT INTO execucoes_diarias(chave) VALUES($1) ON CONFLICT DO NOTHING",chave)
async def registrar_akuma_encontrada(uid,item,nome,tipo,expira): return await get_pool().execute("INSERT INTO akumas_encontradas(user_id,item_id,nome,tipo,expira_em) VALUES($1,$2,$3,$4,$5)",uid,item,nome,tipo,expira)
async def akumas_expiradas(): return await get_pool().fetch("SELECT * FROM akumas_encontradas WHERE consumida=FALSE AND expira_em<=NOW()")
async def expirar_akuma(i):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            r=await c.fetchrow("SELECT * FROM akumas_encontradas WHERE id=$1 FOR UPDATE",i)
            if not r or r['consumida']: return False
            await c.execute("UPDATE inventario SET quantidade=GREATEST(0,quantidade-1) WHERE user_id=$1 AND item_id=$2",r['user_id'],r['item_id'])
            await c.execute("UPDATE akumas_encontradas SET consumida=TRUE WHERE id=$1",i); return True
async def transferir_item(origem,destino,item,qtd):
    db=get_pool(); qtd=int(qtd)
    async with db.acquire() as c:
        async with c.transaction():
            r=await c.fetchrow("SELECT quantidade FROM inventario WHERE user_id=$1 AND item_id=$2 FOR UPDATE",origem,item)
            if not r or r['quantidade']<qtd:return False
            await c.execute("UPDATE inventario SET quantidade=quantidade-$3 WHERE user_id=$1 AND item_id=$2",origem,item,qtd)
            await adicionar_item_inventario(destino,item,qtd,c); return True

async def criar_sorteio(premio,valor,encerra): return await get_pool().fetchrow("INSERT INTO sorteios_diarios(premio,valor,encerra_em) VALUES($1,$2,$3) RETURNING *",premio,int(valor),encerra)
async def participar_sorteio(sid,uid): return await get_pool().execute("INSERT INTO participantes_sorteio(sorteio_id,user_id) VALUES($1,$2) ON CONFLICT DO NOTHING",sid,uid)
async def sorteios_encerrar(): return await get_pool().fetch("SELECT * FROM sorteios_diarios WHERE status='aberto' AND encerra_em<=NOW()")
async def sorteios_abertos(): return await get_pool().fetch("SELECT * FROM sorteios_diarios WHERE status='aberto' AND encerra_em>NOW()")
async def participantes_sorteio(sid): return await get_pool().fetch("SELECT user_id FROM participantes_sorteio WHERE sorteio_id=$1",sid)
async def encerrar_sorteio(sid,uid): return await get_pool().execute("UPDATE sorteios_diarios SET status='encerrado',vencedor_user_id=$2 WHERE id=$1",sid,uid)

async def boss_rp_ativo_usuario(user_id):
    return await get_pool().fetchrow("SELECT * FROM bosses_rp_ativos WHERE user_id=$1 AND status='ativo' ORDER BY id DESC LIMIT 1",int(user_id))

async def remover_membro_tripulacao(tid,uid):
    return await get_pool().execute("DELETE FROM membros_tripulacao WHERE tripulacao_id=$1 AND user_id=$2 AND cargo<>'Capitão'",int(tid),int(uid))

async def definir_cargo_tripulacao(tid,uid,cargo):
    return await get_pool().execute("UPDATE membros_tripulacao SET cargo=$3 WHERE tripulacao_id=$1 AND user_id=$2 AND cargo<>'Capitão'",int(tid),int(uid),str(cargo)[:40])

async def transferir_capitania(tid,capitao_atual,novo):
    db=get_pool()
    async with db.acquire() as c:
        async with c.transaction():
            t=await c.fetchrow("SELECT * FROM tripulacoes WHERE id=$1 AND capitao_user_id=$2 FOR UPDATE",int(tid),int(capitao_atual))
            if not t:return False
            if not await c.fetchrow("SELECT 1 FROM membros_tripulacao WHERE tripulacao_id=$1 AND user_id=$2",int(tid),int(novo)):return False
            await c.execute("UPDATE membros_tripulacao SET cargo='Tripulante' WHERE tripulacao_id=$1 AND user_id=$2",int(tid),int(capitao_atual))
            await c.execute("UPDATE membros_tripulacao SET cargo='Capitão' WHERE tripulacao_id=$1 AND user_id=$2",int(tid),int(novo))
            await c.execute("UPDATE tripulacoes SET capitao_user_id=$2 WHERE id=$1",int(tid),int(novo)); return True


# =========================================================
# AKUMA NO MI — DROPS ESPONTÂNEOS EM ILHAS
# =========================================================
async def obter_controle_akuma_spawn():
    return await get_pool().fetchrow("SELECT * FROM akuma_spawn_controle WHERE id=1")

async def agendar_proximo_akuma_spawn(quando):
    return await get_pool().fetchrow("""INSERT INTO akuma_spawn_controle(id,proximo_spawn_em) VALUES(1,$1) ON CONFLICT(id) DO UPDATE SET proximo_spawn_em=EXCLUDED.proximo_spawn_em RETURNING *""",quando)

async def criar_akuma_spawn(guild_id,channel_id,localizacao,nome,tipo,expira_em):
    return await get_pool().fetchrow("""INSERT INTO akuma_spawns_mundo(guild_id,channel_id,localizacao,nome,tipo,expira_em) VALUES($1,$2,$3,$4,$5,$6) RETURNING *""",guild_id,channel_id,localizacao,nome,tipo,expira_em)

async def vincular_mensagem_akuma_spawn(spawn_id,mensagem_id):
    return await get_pool().execute("UPDATE akuma_spawns_mundo SET mensagem_id=$2 WHERE id=$1",spawn_id,mensagem_id)

async def listar_akuma_spawns_ativos():
    return await get_pool().fetch("SELECT * FROM akuma_spawns_mundo WHERE status='ativo' ORDER BY criado_em")

async def expirar_akuma_spawns():
    return await get_pool().fetch("""UPDATE akuma_spawns_mundo SET status='expirado' WHERE status='ativo' AND expira_em<=NOW() RETURNING *""")

async def coletar_akuma_spawn(spawn_id,user_id):
    db=get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            r=await conn.fetchrow("SELECT * FROM akuma_spawns_mundo WHERE id=$1 FOR UPDATE",int(spawn_id))
            if not r or r['status']!='ativo' or r['expira_em']<=__import__('datetime').datetime.now(__import__('datetime').timezone.utc): return None
            loc=await conn.fetchrow("SELECT localizacao FROM localizacoes_jogador WHERE user_id=$1",int(user_id))
            if not loc: return False
            from data.navegacao import normalizar_destino
            if normalizar_destino(loc['localizacao']) != normalizar_destino(r['localizacao']): return False
            item='akuma_'+str(abs(hash(r['nome']))%10**8)
            await adicionar_item_inventario(user_id,item,1,conn)
            await conn.execute("INSERT INTO akumas_encontradas(user_id,item_id,nome,tipo,expira_em) VALUES($1,$2,$3,$4,NOW()+INTERVAL '5 days')",int(user_id),item,r['nome'],r['tipo'])
            return await conn.fetchrow("UPDATE akuma_spawns_mundo SET status='coletado',coletado_por=$2,coletado_em=NOW() WHERE id=$1 RETURNING *",int(spawn_id),int(user_id))

async def sincronizar_noticias_recentes(limite=20):
    """Transforma fatos públicos relevantes ainda sem matéria em notícias. Não duplica evento."""
    db=get_pool()
    rows=await db.fetch("""SELECT e.* FROM eventos_mundo e LEFT JOIN noticias_mundo n ON n.evento_id=e.id WHERE n.id IS NULL AND e.criado_em>=NOW()-INTERVAL '7 days' AND (e.publico_sabe=TRUE OR e.alcance IN ('regional','mundial')) AND e.gravidade>=2 ORDER BY e.criado_em ASC LIMIT $1""",max(1,min(50,int(limite))))
    for e in rows:
        local=e['localizacao'] or 'mares'
        tipo=(e['tipo'] or 'acontecimento').replace('_',' ').strip().title()
        manchete=f"{tipo} movimenta {local}"[:180]
        await db.execute("""INSERT INTO noticias_mundo(evento_id,personagem_nome,manchete,corpo,alcance) SELECT $1,$2,$3,$4,$5 WHERE NOT EXISTS(SELECT 1 FROM noticias_mundo WHERE evento_id=$1)""",e['id'],e['personagem_nome'],manchete,e['resumo'][:1500],e['alcance'])
    return len(rows)
