"""Campanhas universais do mundo.

A campanha NÃO é um segundo sistema de combate. Ela fornece objetivos, ordem de encontros
marcantes e contexto para o mesmo Narrador usado por !iniciar/!acao.
Toda localização cadastrada em data.navegacao.LOCAIS recebe campanha automaticamente;
conteúdo específico só especializa a ilha, nunca cria código exclusivo para ela.
"""
from data.navegacao import LOCAIS
from data.mundo import ILHAS_ESPECIAIS

# rank, alvo. Ordem = progressão narrativa quando a ilha possui arco conhecido.
ARCOS = {
    "Shells Town": [("D","Machado Morgan")],
    "Orange Town": [("D","Mohji"),("D","Cabaji"),("C","Buggy, o Palhaço")],
    "Syrup Village": [("D","Jango"),("C","Kuro dos Mil Planos")],
    "Baratie": [("C","Pearl"),("B","Gin"),("B","Don Krieg")],
    "Conomi Islands": [("C","Chew"),("C","Kuroobi"),("C","Hatchan"),("B","Arlong")],
    "Loguetown": [("B","Caçador de Loguetown")],
    "Whisky Peak": [("C","Agente Baroque")],
    "Little Garden": [("B","Mr. 3")],
    "Drum Island": [("B","Wapol")],
    "Alabasta": [("B","Mr. 1"),("A","Agentes Baroque de Elite"),("S","Crocodile")],
    "Jaya": [("B","Bellamy")],
    "Skypiea": [("A","Sacerdotes de Skypiea"),("S","Enel")],
    "Water 7": [("A","Agentes infiltrados do CP9")],
    "Enies Lobby": [("A","Blueno"),("S","Kaku"),("S","Jabra"),("S","Rob Lucci")],
    "Thriller Bark": [("A","General Zumbi"),("S","Gecko Moria")],
    "Sabaody Archipelago": [("A","Pacifista"),("S","Supernova Hostil")],
    "Impel Down": [("S","Guardião de Impel Down")],
    "Marineford": [("SS","Oficial de Marineford")],
    "Fish-Man Island": [("A","Ameaça submarina")],
    "Punk Hazard": [("S","Novo Pirata do Novo Mundo")],
    "Dressrosa": [("A","Diamante"),("S","Pica"),("S","Trebol"),("SS","Donquixote Doflamingo")],
    "Zou": [("S","Comandante Mink Corrompido")],
    "Whole Cake Island": [("S","Oficial de Totto Land"),("SS","Comandante de Totto Land")],
    "Wano Country": [("S","Samurai Renegado"),("SS","Oficial das Feras"),("LENDARIO","Kaido")],
    "Onigashima": [("SS","All-Star das Feras"),("LENDARIO","Kaido")],
    "Egghead": [("SS","Experimento Seraphim")],
    "Elbaf": [("SS","Guerreiro Gigante")],
    "Hachinosu": [("SS","Capitão de Hachinosu")],
    "Hachinosu Pirate Island": [("SS","Capitão de Hachinosu")],
}

# Conteúdo não-canônico/custom entra aqui ou em ILHAS_ESPECIAIS e automaticamente usa o mesmo motor.
# Nunca criar if ilha == X no Narrador.
def campanha_da_ilha(local):
    regiao, perigo = LOCAIS.get(local, ("Desconhecida", 2))
    info = ILHAS_ESPECIAIS.get(local, {})
    encontros = ARCOS.get(local)
    if encontros is None:
        bosses = info.get("bosses") or []
        rank_padrao = "E" if perigo <= 1 else "D" if perigo == 2 else "C" if perigo == 3 else "A" if perigo == 4 else "S"
        encontros = [(rank_padrao, b) for b in bosses]
    return {
        "id": local.casefold().replace(" ", "-").replace("'", ""),
        "local": local,
        "regiao": regiao,
        "perigo": perigo,
        "inimigos": list(info.get("inimigos") or ["Ameaças e conflitos próprios da região"]),
        "segredos": list(info.get("segredos") or ["Eventos, relações e descobertas emergentes do mundo"]),
        "encontros": [{"ordem":i+1,"rank":rank,"nome":nome} for i,(rank,nome) in enumerate(encontros)],
    }

def todas_campanhas():
    return {local: campanha_da_ilha(local) for local in LOCAIS}

def contexto_campanha(local, derrotados=()):
    c=campanha_da_ilha(local)
    feitos={str(x).casefold() for x in derrotados}
    linhas=[]
    proximo=None
    for e in c["encontros"]:
        ok=e["nome"].casefold() in feitos
        if not ok and proximo is None: proximo=e
        linhas.append(f"- {'CONCLUÍDO' if ok else 'PENDENTE'}: {e['nome']} (Rank {e['rank']})")
    return c, proximo, "\n".join(linhas) if linhas else "- Nenhum chefe obrigatório fixo: a campanha é emergente nesta localização."
