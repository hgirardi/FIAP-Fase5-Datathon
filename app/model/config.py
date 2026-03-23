from utils.caminhos import CAMINHO_MODELO_RISCO, CAMINHO_PERCENTIS_2024

MODELO_PATH = CAMINHO_MODELO_RISCO
PERCENTIS_PATH = CAMINHO_PERCENTIS_2024

# Mapeamentos de entrada
NIVEIS = {
    'ALFA': 0, '1': 1, '2': 2, '3': 3,
    '4': 4, '5': 5, '6': 6, '7': 7, '8': 8
}

TIPOS_ESCOLA = {
    'Pública': 0,
    'Privada': 1,
}

# Faixas de risco
FAIXAS_RISCO = {
    'Muito baixo': {'min': 0.0, 'max': 0.2, 'cor': '#2ecc71', 'emoji': '🟢'},
    'Baixo': {'min': 0.2, 'max': 0.4, 'cor': '#82e0aa', 'emoji': '🟢'},
    'Moderado': {'min': 0.4, 'max': 0.6, 'cor': '#f9e79f', 'emoji': '🟡'},
    'Alto': {'min': 0.6, 'max': 0.8, 'cor': '#f0b27a', 'emoji': '🟠'},
    'Muito alto': {'min': 0.8, 'max': 1.0, 'cor': '#e74c3c', 'emoji': '🔴'},
}
