from bisect import bisect_left

def pollock_3_dobras(dobras: dict, idade: int, sexo: str) -> float:
    """
    Calcula % gordura corporal pelo protocolo de Pollock 3 Dobras.
    dobros: dict com as dobras necessárias (em mm)
    sexo: "masculino" ou "feminino"
    """
    soma = sum(dobras.values())
    
    if sexo.lower() == "masculino":
        dc = 1.10938 - 0.0008267 * soma + 0.0000016 * soma**2 - 0.0002574 * idade
    else:
        dc = 1.0994921 - 0.0009929 * soma + 0.0000023 * soma**2 - 0.0001392 * idade
    
    gc = (495 / dc) - 450
    return round(gc, 2)


def pollock_7_dobras(dobras: dict, idade: int, sexo: str) -> float:
    """
    Calcula % gordura corporal pelo protocolo de Pollock 7 Dobras.
    dobros: dict com as 7 dobras necessárias (em mm)
    """
    soma = sum(dobras.values())

    if sexo.lower() == "masculino":
        dc = 1.112 - 0.00043499 * soma + 0.00000055 * soma**2 - 0.00028826 * idade
    else:
        dc = 1.097 - 0.000468 * soma + 0.00000056 * soma**2 - 0.00012828 * idade
    
    gc = (495 / dc) - 450
    return round(gc, 2)


def faulkner(dobras: dict) -> float:
    """
    Calcula % gordura corporal pelo protocolo de Faulkner.
    dobros: dict com 4 dobras (tricipital, subescapular, supra-ilíaca, abdominal)
    """
    soma = sum(dobras.values())
    gc = soma * 0.153 + 5.783
    return round(gc, 2)


def durnin_womersley(dobras: dict, idade: int, sexo: str) -> float:
    """
    Estima % gordura corporal usando fórmula genérica baseada na soma das dobras.
    Essa versão usa uma equação linear aproximada para densidade corporal.
    """
    soma = sum(dobras.values())

    if sexo.lower() == "masculino":
        dc = 1.1765 - 0.0744 * (soma ** 0.5)
    else:
        dc = 1.1567 - 0.0717 * (soma ** 0.5)

    gc = (495 / dc) - 450
    return round(gc, 2)

# Tabela densidade Durnin & Womersley (simplificada)
DENSIDADE_TABELA = {
    (17, 19): {
        10: (1.1665, 1.1590),
        20: (1.1620, 1.1582),
        30: (1.1547, 1.1503),
        40: (1.1495, 1.1442),
        50: (1.1453, 1.1394),
        60: (1.1419, 1.1353),
        70: (1.1390, 1.1319),
        80: (1.1365, 1.1289),
    },
    (20, 29): {
        10: (1.1631, 1.1541),
        20: (1.1572, 1.1503),
        30: (1.1506, 1.1443),
        40: (1.1461, 1.1395),
        50: (1.1419, 1.1353),
        60: (1.1387, 1.1319),
        70: (1.1358, 1.1289),
        80: (1.1331, 1.1261),
    },
    (30, 39): {
        10: (1.1593, 1.1521),
        20: (1.1534, 1.1443),
        30: (1.1477, 1.1394),
        40: (1.1432, 1.1353),
        50: (1.1389, 1.1319),
        60: (1.1357, 1.1289),
        70: (1.1327, 1.1261),
        80: (1.1300, 1.1235),
    },
    (40, 49): {
        10: (1.1557, 1.1483),
        20: (1.1500, 1.1443),
        30: (1.1444, 1.1394),
        40: (1.1401, 1.1353),
        50: (1.1359, 1.1319),
        60: (1.1327, 1.1289),
        70: (1.1298, 1.1261),
        80: (1.1270, 1.1235),
    },
    (50, 59): {
        10: (1.1524, 1.1450),
        20: (1.1467, 1.1407),
        30: (1.1411, 1.1364),
        40: (1.1367, 1.1330),
        50: (1.1325, 1.1296),
        60: (1.1293, 1.1267),
        70: (1.1264, 1.1240),
        80: (1.1236, 1.1213),
    },
    (60, 120): {
        10: (1.1494, 1.1419),
        20: (1.1437, 1.1373),
        30: (1.1381, 1.1328),
        40: (1.1338, 1.1292),
        50: (1.1295, 1.1257),
        60: (1.1264, 1.1231),
        70: (1.1234, 1.1206),
        80: (1.1206, 1.1182),
    }
}

def get_faixa_etaria(idade: int):
    for faixa in DENSIDADE_TABELA.keys():
        if faixa[0] <= idade <= faixa[1]:
            return faixa
    return (60, 120)

def interpola(x, x0, y0, x1, y1):
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def densidade_durnin_womersley(soma: float, idade: int, sexo: str) -> float:
    faixa = get_faixa_etaria(idade)
    tabela = DENSIDADE_TABELA[faixa]
    sex_idx = 0 if sexo.lower() == 'masculino' else 1
    somas_ordenadas = sorted(tabela.keys())
    
    if soma <= somas_ordenadas[0]:
        dens = tabela[somas_ordenadas[0]][sex_idx]
    elif soma >= somas_ordenadas[-1]:
        dens = tabela[somas_ordenadas[-1]][sex_idx]
    else:
        idx = bisect_left(somas_ordenadas, soma)
        x0, x1 = somas_ordenadas[idx-1], somas_ordenadas[idx]
        y0, y1 = tabela[x0][sex_idx], tabela[x1][sex_idx]
        dens = interpola(soma, x0, y0, x1, y1)
    return dens

def percentual_gordura_siri(densidade: float) -> float:
    return round((495 / densidade) - 450, 2)

def percentual_gordura_durnin_womersley(biceps: float, triceps: float, subescapular: float, suprailíaca: float, idade: int, sexo: str) -> float:
    soma = biceps + triceps + subescapular + suprailíaca
    densidade = densidade_durnin_womersley(soma, idade, sexo)
    return percentual_gordura_siri(densidade)