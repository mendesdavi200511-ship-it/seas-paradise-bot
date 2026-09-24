"""Mapa de navegação do Sea's Paradise.
Tempos são balanceamento de RP (tempo real), não distâncias canônicas oficiais.
"""

# Região, perigo (1-5), acesso e se é porto navegável.
LOCAIS = {
    # East Blue
    "Dawn Island": ("East Blue",1), "Goa Kingdom": ("East Blue",1), "Shells Town": ("East Blue",1),
    "Orange Town": ("East Blue",1), "Syrup Village": ("East Blue",1), "Baratie": ("East Blue",1),
    "Conomi Islands": ("East Blue",2), "Loguetown": ("East Blue",2), "Tequila Wolf": ("East Blue",3),
    # Entradas / Paraíso
    "Reverse Mountain": ("Grand Line",3), "Twin Cape": ("Grand Line",2), "Whisky Peak": ("Grand Line",2),
    "Little Garden": ("Grand Line",3), "Drum Island": ("Grand Line",3), "Alabasta": ("Grand Line",3),
    "Jaya": ("Grand Line",3), "Skypiea": ("Sky",4), "Long Ring Long Land": ("Grand Line",2),
    "Water 7": ("Grand Line",2), "Enies Lobby": ("Government",4), "Thriller Bark": ("Grand Line",4),
    "Sabaody Archipelago": ("Grand Line",4), "Amazon Lily": ("Calm Belt",4), "Impel Down": ("Government",5),
    "Marineford": ("Government",5), "Rusukaina": ("Calm Belt",5), "Kuraigana Island": ("Grand Line",4),
    "Momoiro Island": ("Grand Line",3), "Boin Archipelago": ("Grand Line",4), "Weatheria": ("Sky",3),
    "Karakuri Island": ("Grand Line",4), "Torino Kingdom": ("Grand Line",3), "Namakura Island": ("Grand Line",3),
    # Red Line / Novo Mundo
    "Fish-Man Island": ("Red Line",4), "Punk Hazard": ("New World",5), "Dressrosa": ("New World",4),
    "Green Bit": ("New World",3), "Zou": ("New World",5), "Whole Cake Island": ("New World",5),
    "Cacao Island": ("Totto Land",4), "Nuts Island": ("Totto Land",4), "Cheese Island": ("Totto Land",4),
    "Wano Country": ("New World",5), "Onigashima": ("New World",5), "Egghead": ("New World",5),
    "Elbaf": ("New World",5), "Hachinosu": ("New World",5), "Winner Island": ("New World",4),
    "Hachinosu Pirate Island": ("New World",5), "Karai Bari Island": ("New World",4),
    "Sphinx": ("New World",3), "G-14": ("New World",5), "Lulusia Kingdom": ("Paradise",4),
    # Outros mares / locais relevantes
    "Ohara": ("West Blue",2), "Ilusia Kingdom": ("West Blue",2), "Kano Country": ("West Blue",3),
    "Germa Kingdom": ("North Blue",4), "Flevance": ("North Blue",3), "Lvneel Kingdom": ("North Blue",2),
    "Sorbet Kingdom": ("South Blue",3), "Centauria": ("South Blue",3), "Baterilla": ("South Blue",2),
    "Mary Geoise": ("Red Line",5), "God Valley": ("Special",5), "Laugh Tale": ("Final",5),
}

ALIASES_NAVEGACAO = {
    "sabaody":"Sabaody Archipelago", "sabaody park":"Sabaody Archipelago", "shabondy":"Sabaody Archipelago",
    "loguetown":"Loguetown", "orange town":"Orange Town", "syrup":"Syrup Village", "baratie":"Baratie",
    "conomi":"Conomi Islands", "dawn":"Dawn Island", "alabasta":"Alabasta", "arabasta":"Alabasta",
    "ilha dos tritoes":"Fish-Man Island", "fishman island":"Fish-Man Island", "wano":"Wano Country",
    "whole cake":"Whole Cake Island", "hachi":"Hachinosu", "pirate island":"Hachinosu",
}

def normalizar_destino(nome):
    if not nome: return None
    s=str(nome).strip(); k=s.casefold()
    if k in ALIASES_NAVEGACAO: return ALIASES_NAVEGACAO[k]
    for local in LOCAIS:
        if local.casefold()==k: return local
    return s

# Grafo principal. Cada ligação recebe duração-base em minutos de tempo real.
CADEIA = [
    "Dawn Island","Shells Town","Orange Town","Syrup Village","Baratie","Conomi Islands","Loguetown",
    "Reverse Mountain","Twin Cape","Whisky Peak","Little Garden","Drum Island","Alabasta","Jaya",
    "Long Ring Long Land","Water 7","Thriller Bark","Sabaody Archipelago","Fish-Man Island","Punk Hazard",
    "Dressrosa","Zou","Whole Cake Island","Wano Country","Egghead","Elbaf"
]

ROTAS_INFO={}
def rota(a,b,minutos=60,requisito="barco",suprimentos=1,desgaste=5,perigo=None,bidirecional=True):
    if perigo is None: perigo=max(LOCAIS.get(a,(None,2))[1],LOCAIS.get(b,(None,2))[1])
    ROTAS_INFO[(a,b)]={"minutos":minutos,"requisito":requisito,"suprimentos":suprimentos,"desgaste":desgaste,"perigo":perigo}
    if bidirecional: ROTAS_INFO[(b,a)]={"minutos":minutos,"requisito":requisito,"suprimentos":suprimentos,"desgaste":desgaste,"perigo":perigo}

for i in range(len(CADEIA)-1):
    a,b=CADEIA[i],CADEIA[i+1]
    reg=LOCAIS[b][0]
    req="log_pose" if reg in {"Grand Line","New World","Red Line","Totto Land"} and a not in {"Dawn Island","Shells Town","Orange Town","Syrup Village","Baratie","Conomi Islands","Loguetown"} else "barco"
    rota(a,b,45 if i<7 else 90,req,1 if i<7 else 2,4 if i<7 else 8)

# Ligações especiais/importantes.
rota("Jaya","Skypiea",120,"knock_up_or_special",2,12,4)
rota("Water 7","Enies Lobby",45,"barco",1,6,4)
rota("Sabaody Archipelago","Amazon Lily",150,"calm_belt",3,10,4)
rota("Sabaody Archipelago","Marineford",120,"barco",3,10,5)
rota("Sabaody Archipelago","Impel Down",150,"government_or_special",3,12,5)
rota("Sabaody Archipelago","Fish-Man Island",120,"revestimento",3,12,4)
rota("Dressrosa","Green Bit",30,"barco",1,3,3)
rota("Whole Cake Island","Cacao Island",30,"log_pose",1,3,4)
rota("Whole Cake Island","Nuts Island",30,"log_pose",1,3,4)
rota("Whole Cake Island","Cheese Island",30,"log_pose",1,3,4)
rota("Wano Country","Onigashima",30,"barco",1,4,5)
rota("Egghead","G-14",45,"log_pose",1,5,5)
rota("Egghead","Winner Island",75,"log_pose",2,7,4)
rota("Winner Island","Hachinosu",120,"log_pose",2,10,5)
rota("Elbaf","Hachinosu",150,"log_pose",3,12,5)
rota("Elbaf","Sphinx",120,"log_pose",2,8,4)
rota("Sphinx","Karai Bari Island",90,"log_pose",2,7,4)
rota("Mary Geoise","Fish-Man Island",120,"special",3,12,5)
rota("Elbaf","Laugh Tale",480,"road_poneglyphs",8,30,5)

# Conexões laterais de Paradise e ilhas de timeskip.
for x in ["Kuraigana Island","Momoiro Island","Boin Archipelago","Karakuri Island","Torino Kingdom","Namakura Island"]:
    rota("Sabaody Archipelago",x,180,"eternal_or_route",3,10,LOCAIS[x][1])
rota("Jaya","Weatheria",180,"special",2,8,3)

OBSTACULOS = {
  1:[("🌫️","Neblina fechada","A visibilidade caiu. Decidam como manter o rumo sem perder tempo."),
     ("🌊","Corrente lateral","Uma corrente começa a empurrar o navio para fora da rota.")],
  2:[("⛈️","Tempestade repentina","Vento e ondas atingem o casco. É preciso escolher entre reduzir velas, contornar ou atravessar."),
     ("🪨","Recifes","Recifes aparecem à frente e exigem manobra cuidadosa."),
     ("🏴‍☠️","Vela desconhecida","Uma embarcação não identificada muda o curso na direção de vocês.")],
  3:[("🌪️","Mar revolto","Uma mudança violenta do clima ameaça mastros e carga."),
     ("🐋","Criatura marinha","Uma criatura de grande porte cruza a rota do navio."),
     ("⚓","Destroços à deriva","Destroços extensos bloqueiam o caminho e podem esconder perigo ou recursos.")],
  4:[("🐙","Sea Beast","Um Sea Beast intercepta a rota e força uma decisão imediata."),
     ("🌩️","Clima anômalo","O clima muda de forma impossível para mares comuns; a rota deixa de ser previsvisível."),
     ("🚢","Navio hostil","Uma embarcação armada surge em posição de interceptação.")],
  5:[("🐉","Ameaça extrema","Algo grande demais para ignorar domina a rota marítima. Fugir, enfrentar ou improvisar terá consequências."),
     ("🌊","Fenômeno da Grand Line","Mar, vento e corrente entram em conflito e ameaçam seriamente a embarcação."),
     ("⚔️","Interceptação perigosa","Uma força hostil tenta impedir a continuação da viagem.")]
}

def destinos_de(origem):
    origem=normalizar_destino(origem)
    return sorted([b for (a,b) in ROTAS_INFO if a==origem])
