"""Regras centrais da ficha do Sea's Paradise.
Mantém apresentação/cálculo separados dos pontos-base persistidos.
"""

ESCALAS_ATRIBUTOS = {
    "forca": [(20,"Muito Fraco",20,"kg"),(50,"Fraco",50,"kg"),(100,"Normal",100,"kg"),(200,"Mediano",200,"kg"),(350,"Bom",350,"kg"),(600,"Forte",600,"kg"),(1000,"Muito Forte",1000,"kg"),(2000,"Excepcional",2000,"kg"),(5000,"Monstruoso",5000,"kg"),(10000,"Sobre-Humano",10000,"kg"),(25000,"Titânica",25000,"kg"),(50000,"Lendário",50000,"kg")],
    "resistencia": [(20,"Muito Frágil",20,"kg"),(50,"Frágil",50,"kg"),(100,"Normal",100,"kg"),(200,"Resistente",200,"kg"),(400,"Muito Resistente",400,"kg"),(750,"Robusto",750,"kg"),(1500,"Excepcional",1500,"kg"),(3000,"Monstruoso",3000,"kg"),(7500,"Sobre-Humano",7500,"kg"),(15000,"Titânico",15000,"kg"),(30000,"Lendário",30000,"kg")],
    "velocidade": [(10,"Muito Lento",10,"km/h"),(20,"Lento",20,"km/h"),(35,"Normal",35,"km/h"),(50,"Ágil",50,"km/h"),(75,"Muito Ágil",75,"km/h"),(100,"Veloz",100,"km/h"),(150,"Muito Veloz",150,"km/h"),(250,"Excepcional",250,"km/h"),(1235,"Supersônico",1235,"km/h"),(2500,"Sobre-Humano",2500,"km/h"),(5000,"Relâmpago",5000,"km/h"),(10000,"Lendário",10000,"km/h")],
}

# Rank geral de reputação. O admin pode sobrescrever com rank_manual.
RANKS_REPUTACAO = [(0,"Desconhecido"),(100,"Conhecido"),(300,"Notável"),(750,"Renomado"),(1500,"Temido"),(3000,"Grande Nome"),(6000,"Lenda dos Mares"),(10000,"Ícone Mundial")]

# Somente bônus que o catálogo atual declara explicitamente como atributo passivo.
BONUS_ATRIBUTOS = {
    "raca": {
        "Homem-Peixe": {"forca":30,"resistencia":30,"velocidade":30},
        "Tontatta": {"velocidade":15},
        "Gigante": {"resistencia":35},
        "Bucaneiro": {"forca":25,"resistencia":40},
        "Oni": {"forca":80,"resistencia":120},
        "Long-Leg": {"velocidade":20},
        "Corpo Modificado": {"forca":60,"resistencia":150},
    },
    "familia": {},
}

# Benefícios mecânicos explícitos nos catálogos. Benefícios narrativos continuam no catálogo.
TALENTOS_AUTOMATICOS = {
    "raca": {
        "Homem-Peixe": [("estilo","Fish-Man Karate"),("estilo","Fish-Man Jujutsu")],
        "Sereiano": [("profissao","Músico")],
        "Mink": [("estilo","Electro")],
        "Tontatta": [("estilo","Tontatta Fight")],
        "Kuja": [("estilo","Archery"),("profissao","Caçador"),("haki","Busoshoku Haki")],
    },
    "familia": {
        "Kozuki": [("profissao","Arqueólogo")],
        "Shimotsuki": [("profissao","Ferreiro")],
        "Enel": [("haki","Kenbunshoku Haki")],
        "Smoker": [("classe","Lutador")],
    },
}

FAMILIAS_VONTADE_D = {"Monkey","Rocks","Gol"}

# Conteúdo não sorteável/selecionável na criação.
ESTILOS_NAO_SELECIONAVEIS = {"Diable Jambe","Ifrit Jambe","Pacifista Combat","Rokushiki","Six Powers","Cipher Pol Martial Arts"}
ESTILOS_POR_RACA = {"Fish-Man Karate":{"Homem-Peixe"},"Fish-Man Jujutsu":{"Homem-Peixe"},"Electro":{"Mink"}}


def info_atributo(tipo, pontos):
    escala = ESCALAS_ATRIBUTOS[tipo]
    atual = escala[0]
    for item in escala:
        if pontos >= item[0]: atual = item
        else: break
    return {"nome":atual[1],"valor":atual[2],"unidade":atual[3]}


def bonus_atributo(tipo, raca=None, familia=None):
    return BONUS_ATRIBUTOS["raca"].get(raca,{}).get(tipo,0) + BONUS_ATRIBUTOS["familia"].get(familia,{}).get(tipo,0)


def atributo_efetivo(tipo, pontos, raca=None, familia=None):
    info=info_atributo(tipo,pontos); bonus=bonus_atributo(tipo,raca,familia)
    return info, bonus, round(info["valor"]*(1+bonus/100),2)


def rank_por_reputacao(valor):
    valor=max(0,int(valor or 0)); atual=RANKS_REPUTACAO[0][1]
    for minimo,nome in RANKS_REPUTACAO:
        if valor>=minimo: atual=nome
    return atual


def proximo_rank(valor):
    valor=max(0,int(valor or 0))
    for minimo,nome in RANKS_REPUTACAO:
        if minimo>valor: return nome,minimo
    return None,None


def estilo_disponivel_criacao(nome, raca=None):
    if nome in ESTILOS_NAO_SELECIONAVEIS: return False
    permitidas=ESTILOS_POR_RACA.get(nome)
    return not permitidas or raca in permitidas

PISOS_INICIAIS = {
    "raca": {
        "Kuja": {"forca":50,"resistencia":50,"velocidade":35},
        "Oni": {"forca":100,"resistencia":100,"velocidade":50},
    },
    "familia": {
        "Charlotte": {"forca":50,"resistencia":50,"velocidade":35},
    },
}

def aplicar_pisos_iniciais(dados):
    for origem in ("raca","familia"):
        nome=dados.get(origem)
        for atributo,piso in PISOS_INICIAIS[origem].get(nome,{}).items():
            dados[atributo]=max(int(dados.get(atributo,0)),piso)
    return dados
