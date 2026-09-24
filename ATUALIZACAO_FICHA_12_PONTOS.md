# Sea's Paradise — Reforma da Ficha/Criação (12 pontos)

Base: repositório completo enviado em 24/09/2026.

## Implementado
1. Escalas oficiais separadas de Força, Resistência e Velocidade/Agilidade, com unidade física.
2. Bônus passivos estruturados e valor efetivo separado dos pontos-base (sem multiplicar o banco repetidamente).
3. Talentos automáticos explícitos de raça/família viram domínios quando aplicável.
4. Botões de revelação de Haoshoku e Prodígio; garantias familiares continuam prevalecendo.
5. Reputação com Rank automático e aba própria.
6. Admin pode definir Rank manual ou devolver ao automático.
7. Remoção de especialização por Select com os domínios reais do jogador.
8. Domínios exibem progressão/benefícios: profissões usam os estágios já existentes; classes e estilos exibem marcos.
9. Estilos possuem estrutura de skills; Black Leg contém Diable Jambe e Ifrit Jambe como evolução.
10. Catálogos oficiais são usados pela criação em vez das listas antigas duplicadas.
11. Ficha/domínios/atributos/reputação receberam apresentação mais organizada.
12. Requisitos: Corpo Modificado só nasce via Vinsmoke; Fish-Man Karate/Jujutsu só Homem-Peixe; Electro só Mink; Governo e Pacifista não são escolha inicial; Vontade do D. não é sorte aleatório; JoyBoy começa bloqueado.

## Catálogo de estilos
Foi adicionado Free Style. Também foi adicionado Tontatta Fight porque o catálogo oficial de raças já concedia esse estilo ao Tontatta, mas ele não existia em data/skills.py.

## Compatibilidade
- `cogs/narrador.py` não foi alterado.
- PostgreSQL não deve ser apagado. As novas colunas usam migração `ADD COLUMN IF NOT EXISTS`.
- Fichas antigas continuam válidas; Rank é calculado pela reputação existente quando não há override manual.
- Relações persistentes por facção (`reputacoes_mundo`) continuam existindo. Eventos confirmados também alimentam a reputação geral da ficha para progressão de Rank.

## Observação de conteúdo
Os catálogos antigos não traziam técnicas individualizadas para a maioria dos estilos. Para não inventar golpes canônicos, esses estilos receberam marcos genéricos Fundamentos/Intermediário/Avançado/Maestria. Black Leg recebeu explicitamente Diable Jambe e Ifrit Jambe conforme a regra definida. Esses marcos podem ser substituídos depois por listas oficiais de técnicas sem mudar a arquitetura.
