HAKIS = {
 'Busoshoku Haki': [('Revestimento',0,'Revestir corpo/arma com Haki.'),('Endurecimento',30,'Endurecimento visível e defesa/ataque reforçados.'),('Emissão',100,'Projetar o Haki sem contato direto.'),('Destruição Interna',200,'Aplicação avançada que atinge por dentro.')],
 'Kenbunshoku Haki': [('Presença',0,'Perceber presenças e intenções.'),('Leitura de Intenção',40,'Antecipar ações imediatas.'),('Alcance Expandido',100,'Percepção em área muito maior.'),('Visão do Futuro',200,'Antecipação avançada de instantes futuros.')],
 'Haoshoku Haki': [('Pressão do Rei',0,'Impor a vontade e abalar alvos fracos.'),('Explosão de Haoshoku',50,'Liberar a pressão de forma direcionada.'),('Revestimento do Rei',200,'Revestir golpes com Haoshoku avançado.')],
}

AKUMA_TIPOS = {
 'paramecia': [('Manifestação',0,'Uso básico da propriedade da fruta.'),('Aplicação Criativa',35,'Aplicações mais refinadas do poder.'),('Domínio',70,'Controle amplo da habilidade.'),('Despertar',300,'Possibilidade de despertar; exige conquista/condição narrativa.')],
 'zoan': [('Forma Base',0,'Poder passivo da Zoan.'),('Forma Animal',20,'Transformação completa.'),('Forma Híbrida',50,'Forma híbrida com capacidades ampliadas.'),('Domínio Zoan',100,'Controle avançado das formas.'),('Despertar Zoan',300,'Possibilidade de despertar; exige conquista/condição narrativa.')],
 'logia': [('Corpo Elemental',0,'Efeito Logia automático quando aplicável; corpo assume o elemento.'),('Produção Elemental',20,'Produzir e controlar o elemento.'),('Mobilidade Elemental',50,'Movimentação usando o elemento.'),('Domínio Logia',100,'Controle refinado e amplo.'),('Despertar Logia',300,'Possibilidade de despertar; exige conquista/condição narrativa.')],
}

def inferir_tipo(nome):
 n=(nome or '').casefold()
 # Modelos/animais conhecidos no nome tendem a ser Zoan; logias comuns por termos canônicos.
 if any(x in n for x in ('hito hito','inu inu','neko neko','tori tori','ushi ushi','uma uma','hebi hebi','mogu mogu','zou zou','ryu ryu','kumo kumo')): return 'zoan'
 if any(x in n for x in ('moku moku','mera mera','suna suna','goro goro','hie hie','yami yami','pika pika','magu magu','gasu gasu','yuki yuki','mori mori')): return 'logia'
 return 'paramecia'
