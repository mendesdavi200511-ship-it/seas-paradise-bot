# Sea's Paradise — Sistemas 13 a 15

## 13 — Inventário
- Inventário persistente por personagem no PostgreSQL.
- `!inventario` / `!inv` / `!mochila`.
- Seleção visual de itens, quantidade, consumo e venda.
- Venda padrão por 50% do valor-base.
- Kit de Reparo Naval consome 1 unidade e recupera integridade da embarcação ativa.
- A ficha exibe quantidade total de itens e embarcação ativa.

## 14 — Loja & Economia
- `!loja` usa a localização persistente do jogador.
- Catálogos próprios para Dawn Island, Orange Town, Syrup Village, Baratie, Conomi Islands e Loguetown.
- Compras são transacionais: Berries e item são alterados juntos ou nada é alterado.
- Histórico persistente em `transacoes_economia`.
- `!estaleiro` compra embarcações disponíveis na localização.

## 15 — Navegação & Embarcações
- Embarcações possuem registro próprio, não ocupam inventário pessoal.
- `!navio` / `!barco` / `!embarcacao` mostra patrimônio naval.
- `!nomearnavio <nome>` nomeia a embarcação ativa.
- `!rotas` lista rotas diretas da localização atual.
- `!viajar <destino>` valida estado do jogador, rota, embarcação ativa e localização do navio antes de atualizar a localização persistente.
- Log Pose e Eternal Poses são itens persistentes; Eternal Pose é individualizado por destino.

## Segurança de dados
As tabelas são criadas com `CREATE TABLE IF NOT EXISTS`; fichas existentes e progresso anterior não são apagados.

## Compatibilidade
`cogs/narrador.py` não foi alterado nesta atualização. O sistema econômico reutiliza `localizacoes_jogador` como fonte de localização, evitando um segundo estado paralelo.
