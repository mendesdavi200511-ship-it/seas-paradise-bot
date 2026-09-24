# SEA'S PARADISE — catálogo mecânico de Haki e Akuma no Mi.
# Cada fruta cadastrada possui progressão própria; não usar texto genérico por tipo.
HAKIS = {
 'Busoshoku Haki': [('Revestimento',0,'Reveste corpo ou arma com Haki; pode ser ativado como buff de combate.'),('Endurecimento',30,'Endurecimento visível, ampliando ataque e resistência.'),('Emissão',100,'Projeta o Haki para atingir/defender sem contato direto.'),('Destruição Interna',200,'Haki penetra a defesa e causa impacto internamente.')],
 'Kenbunshoku Haki': [('Presença',0,'Percebe presenças e intenções ao redor.'),('Leitura de Intenção',40,'Lê movimentos imediatos e melhora reação/esquiva.'),('Alcance Expandido',100,'Amplia drasticamente a área de percepção.'),('Visão do Futuro',200,'Permite antecipar breves instantes do futuro.')],
 'Haoshoku Haki': [('Pressão do Rei',0,'Impõe a vontade e pode derrubar alvos de vontade muito inferior.'),('Explosão de Haoshoku',50,'Libera a pressão de forma direcionada.'),('Revestimento do Rei',200,'Reveste ataques com Haoshoku avançado, elevando brutalmente o poder ofensivo.')],
}

def _s(*rows): return list(rows)
# pct, nome, descrição. 300% é somente condição de despertar; 0–100% cobre o kit normal.
AKUMA_SKILLS = {
 'Ope Ope no Mi': ('paramecia', _s((0,'ROOM','Cria uma área de operação onde o usuário pode aplicar as técnicas da fruta.'),(20,'Shambles','Troca a posição de alvos/objetos dentro do ROOM.'),(40,'Takt','Manipula e movimenta objetos dentro do ROOM.'),(60,'Scan','Localiza/seleciona alvos e objetos dentro da área.'),(80,'Counter Shock','Descarga elétrica aplicada diretamente ao alvo.'),(100,'Gamma Knife','Ataque avançado que danifica internamente o alvo.'),(300,'Despertar — KROOM/R-ROOM','Possibilidade de despertar; exige conquista narrativa e então permite técnicas despertadas.'))),
 'Bara Bara no Mi': ('paramecia', _s((0,'Corpo Fragmentável','O corpo pode se separar em partes e é naturalmente resistente a cortes comuns.'),(25,'Bara Bara Ho','Dispara partes do corpo para atacar à distância.'),(50,'Bara Bara Car','Usa as partes separadas para mobilidade e perseguição.'),(75,'Controle Fragmentado','Controla várias partes simultaneamente com precisão.'),(100,'Separação Avançada','Domínio completo do corpo fragmentado em combate.'),(300,'Despertar','Possibilidade de despertar mediante condição narrativa.'))),
 'Bomu Bomu no Mi': ('paramecia', _s((0,'Corpo Explosivo','Partes e secreções do corpo podem explodir sem ferir o usuário.'),(25,'Explosão Corporal','Converte golpes físicos em explosões.'),(50,'Munição Explosiva','Usa secreções/recursos corporais como munição explosiva.'),(75,'Explosão Concentrada','Concentra detonações mais fortes e precisas.'),(100,'Bombardeio Corporal','Domínio amplo das explosões do próprio corpo.'),(300,'Despertar','Possibilidade de despertar mediante condição narrativa.'))),
 'Doru Doru no Mi': ('paramecia', _s((0,'Produção de Cera','Produz e molda cera pelo corpo.'),(25,'Wax Wall','Ergue barreiras resistentes de cera.'),(50,'Wax Armor','Cria armaduras/estruturas de cera para combate.'),(75,'Modelagem Complexa','Cria armas, chaves e construções detalhadas.'),(100,'Domínio da Cera','Produção e modelagem em grande escala.'),(300,'Despertar','Possibilidade de despertar mediante condição narrativa.'))),
 'Hana Hana no Mi': ('paramecia', _s((0,'Floração','Faz partes do corpo brotarem em superfícies dentro do alcance.'),(25,'Múltiplos Membros','Cria vários braços/pernas simultaneamente.'),(50,'Clutch','Imobiliza e aplica força articulada com membros brotados.'),(75,'Estruturas Corporais','Combina muitos membros para formar estruturas maiores.'),(100,'Gigantesco Florescimento','Cria manifestações corporais de grande escala.'),(300,'Despertar','Possibilidade de despertar mediante condição narrativa.'))),
 'Mane Mane no Mi': ('paramecia', _s((0,'Memória Facial','Registra rostos tocados com a mão.'),(25,'Transformação Facial','Assume a aparência de um rosto memorizado.'),(50,'Imitação Corporal','Replica também características físicas externas do alvo.'),(75,'Troca Instantânea','Alterna identidades memorizadas rapidamente.'),(100,'Mestre da Imitação','Usa o acervo de identidades com total fluidez.'),(300,'Despertar','Possibilidade de despertar mediante condição narrativa.'))),
 'Moku Moku no Mi': ('logia', _s((0,'Corpo de Fumaça','Efeito Logia: transforma o corpo em fumaça e permite recomposição quando aplicável.'),(20,'Produção de Fumaça','Gera e controla fumaça.'),(45,'White Blow','Projeta fumaça para alcançar/prender alvos.'),(70,'Propulsão de Fumaça','Usa fumaça para mobilidade aérea e aceleração.'),(100,'Domínio da Fumaça','Controle amplo do volume e forma da fumaça.'),(300,'Despertar Logia','Possibilidade de despertar mediante condição narrativa.'))),
 'Suna Suna no Mi': ('logia', _s((0,'Corpo de Areia','Efeito Logia: corpo elemental de areia e recomposição quando aplicável.'),(20,'Controle de Areia','Produz e manipula areia.'),(45,'Desidratação','Extrai umidade por contato.'),(70,'Tempestade de Areia','Cria e controla grandes massas/tempestades de areia.'),(100,'Erosão/Dessecação','Uso avançado para secar e desintegrar materiais suscetíveis.'),(300,'Despertar Logia','Possibilidade de despertar mediante condição narrativa.'))),
 'Mera Mera no Mi': ('logia', _s((0,'Corpo de Fogo','Efeito Logia: corpo elemental de fogo e recomposição quando aplicável.'),(20,'Produção de Chamas','Gera e controla fogo.'),(45,'Hiken','Dispara uma grande coluna/punho de fogo.'),(70,'Propulsão Ígnea','Usa chamas para mobilidade e aceleração.'),(100,'Entei','Concentra enorme massa de fogo em ataque de grande escala.'),(300,'Despertar Logia','Possibilidade de despertar mediante condição narrativa.'))),
 'Inu Inu no Mi, Modelo: Chacal': ('zoan', _s((0,'Fisiologia Zoan','Recebe características passivas do chacal.'),(20,'Forma Animal','Transformação completa em chacal.'),(50,'Forma Híbrida','Forma humano-chacal com força, resistência e sentidos ampliados.'),(100,'Domínio Zoan','Controle pleno das formas e transições.'),(300,'Despertar Zoan','Possibilidade de despertar mediante condição narrativa.'))),
 'Tori Tori no Mi, Modelo: Falcão': ('zoan', _s((0,'Fisiologia Zoan','Recebe características passivas de falcão.'),(20,'Forma Animal','Transformação completa em falcão e voo.'),(50,'Forma Híbrida','Forma híbrida com asas, garras e mobilidade aérea.'),(100,'Domínio Zoan','Controle pleno das formas, voo e transições.'),(300,'Despertar Zoan','Possibilidade de despertar mediante condição narrativa.'))),
 'Ushi Ushi no Mi, Modelo: Bisão': ('zoan', _s((0,'Fisiologia Zoan','Recebe características passivas de bisão.'),(20,'Forma Animal','Transformação completa em bisão.'),(50,'Forma Híbrida','Forma híbrida com grande força e resistência.'),(100,'Domínio Zoan','Controle pleno das formas e investidas.'),(300,'Despertar Zoan','Possibilidade de despertar mediante condição narrativa.'))),
}

def inferir_tipo(nome):
    if nome in AKUMA_SKILLS: return AKUMA_SKILLS[nome][0]
    n=(nome or '').casefold()
    if any(x in n for x in ('hito hito','inu inu','neko neko','tori tori','ushi ushi','uma uma','hebi hebi','mogu mogu','zou zou','ryu ryu','kumo kumo')): return 'zoan'
    if any(x in n for x in ('moku moku','mera mera','suna suna','goro goro','hie hie','yami yami','pika pika','magu magu','gasu gasu','yuki yuki','mori mori')): return 'logia'
    return 'paramecia'

def skills_akuma(nome):
    dado=AKUMA_SKILLS.get(nome)
    if dado: return dado[0], dado[1]
    tipo=inferir_tipo(nome)
    # Fruta criada manualmente sem catálogo: não inventa poderes falsos; deixa explícito para cadastro.
    return tipo, [(0,'Poder não catalogado',f'**{nome}** ainda não possui técnicas específicas cadastradas. O poder não será substituído por skills genéricas.'),(300,'Despertar','Possibilidade de despertar após cadastro das técnicas e condição narrativa.')]

# compatibilidade com imports antigos
AKUMA_TIPOS={t:[] for t in ('paramecia','zoan','logia')}
