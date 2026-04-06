"""Development data generator for Dashboard Financeiro Familiar.

Generates realistic sample transactions, debts, investments, and goals
so the dashboard works out-of-the-box without real bank data.
Activate via the sidebar toggle in development mode.
"""

import random
from datetime import date, timedelta
from typing import Any, Dict, List


def _random_date(start: date, end: date) -> str:
    delta = (end - start).days
    return str(start + timedelta(days=random.randint(0, delta)))


def gerar_transacoes_exemplo(
    membros: List[str] | None = None,
    meses: int = 3,
) -> List[Dict[str, Any]]:
    """Generate a list of realistic sample transactions.

    Args:
        membros: Family member names to distribute transactions across.
        meses: How many past months to generate data for.

    Returns:
        List of transaction dicts compatible with processar_dados().
    """
    if not membros:
        membros = ["Douglas", "Família Conjunta"]

    hoje = date.today()
    inicio = date(hoje.year, hoje.month, 1) - timedelta(days=30 * meses)

    receitas = [
        ("Salário Douglas", 5800.0, "Douglas"),
        ("Salário Esposa", 4200.0, "Família Conjunta"),
        ("Freelance Design", 800.0, "Douglas"),
        ("Aluguel recebido", 1200.0, "Família Conjunta"),
        ("Dividendos FII", 150.0, "Douglas"),
    ]

    despesas_fixas = [
        ("Financiamento Imóvel", -1850.0, "Moradia", "Família Conjunta"),
        ("Internet Vivo Fibra", -119.90, "Moradia", "Família Conjunta"),
        ("Energia Elétrica", -210.0, "Moradia", "Família Conjunta"),
        ("Água SABESP", -95.0, "Moradia", "Família Conjunta"),
        ("Condomínio", -450.0, "Moradia", "Família Conjunta"),
        ("Plano de Saúde Unimed", -780.0, "Saúde", "Família Conjunta"),
        ("Netflix", -55.90, "Lazer", "Douglas"),
        ("Spotify", -21.90, "Lazer", "Douglas"),
        ("Academia Smart Fit", -89.90, "Saúde", "Douglas"),
        ("Seguro Auto", -180.0, "Transporte", "Família Conjunta"),
    ]

    despesas_variaveis = [
        ("Mercado Extra", -380.0, "Alimentação", "Família Conjunta"),
        ("Supermercado Carrefour", -520.0, "Alimentação", "Família Conjunta"),
        ("iFood Pedido", -65.0, "Alimentação", "Douglas"),
        ("iFood Almoço", -38.0, "Alimentação", "Douglas"),
        ("Posto Gasolina", -200.0, "Transporte", "Douglas"),
        ("Uber Corrida", -35.0, "Transporte", "Douglas"),
        ("Farmácia Drogasil", -120.0, "Saúde", "Família Conjunta"),
        ("Cityfarma Remédios", -85.0, "Saúde", "Família Conjunta"),
        ("Cinema Kinoplex", -80.0, "Lazer", "Douglas"),
        ("Bar Boteco", -120.0, "Lazer", "Douglas"),
        ("Amazon Compras", -250.0, "Compras", "Douglas"),
        ("Mercado Livre", -180.0, "Compras", "Família Conjunta"),
        ("Curso Udemy", -50.0, "Educação", "Douglas"),
        ("Livros Amazon", -90.0, "Educação", "Douglas"),
        ("Pet Shop Ração", -145.0, "Outros", "Família Conjunta"),
        ("Veterinário", -220.0, "Saúde", "Família Conjunta"),
        ("Restaurante Almoço", -95.0, "Alimentação", "Família Conjunta"),
        ("Padaria Café", -45.0, "Alimentação", "Douglas"),
        ("Estacionamento", -30.0, "Transporte", "Douglas"),
        ("Manutenção Carro", -350.0, "Transporte", "Família Conjunta"),
    ]

    transacoes = []

    for mes_offset in range(meses):
        ref = hoje.replace(day=1) - timedelta(days=30 * mes_offset)
        mes_inicio = ref.replace(day=1)
        mes_fim = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Receitas mensais (todo mês)
        for desc, valor, membro in receitas:
            # Não gerar todas receitas todos os meses — freelance é eventual
            if "Freelance" in desc and random.random() < 0.5:
                continue
            if "Dividendos" in desc and random.random() < 0.3:
                continue
            # Salário cai entre os dias 5 e 10
            dia = random.randint(5, 10)
            dia = min(dia, mes_fim.day)
            d = mes_inicio.replace(day=dia)
            membro_real = membro if membro in membros else (membros[0] if membros else "Família Conjunta")
            transacoes.append({
                "Data": str(d),
                "Descrição": desc,
                "Valor": valor,
                "Categoria_Manual": "Receita",
                "Pessoa": membro_real,
            })

        # Despesas fixas (todo mês, dia entre 1 e 15)
        for desc, valor, cat, membro in despesas_fixas:
            dia = random.randint(1, 15)
            dia = min(dia, mes_fim.day)
            d = mes_inicio.replace(day=dia)
            membro_real = membro if membro in membros else (membros[0] if membros else "Família Conjunta")
            transacoes.append({
                "Data": str(d),
                "Descrição": desc,
                "Valor": valor,
                "Categoria_Manual": cat,
                "Pessoa": membro_real,
            })

        # Despesas variáveis (aleatórias — nem todas aparecem todo mês)
        n_var = random.randint(10, len(despesas_variaveis))
        selecionadas = random.sample(despesas_variaveis, n_var)
        for desc, valor, cat, membro in selecionadas:
            # Variação de ±20% no valor
            fator = 1.0 + random.uniform(-0.2, 0.2)
            valor_var = round(valor * fator, 2)
            d = _random_date(mes_inicio, mes_fim)
            membro_real = membro if membro in membros else (membros[0] if membros else "Família Conjunta")
            transacoes.append({
                "Data": d,
                "Descrição": desc,
                "Valor": valor_var,
                "Categoria_Manual": cat,
                "Pessoa": membro_real,
            })

    return transacoes


def gerar_dividas_exemplo() -> List[Dict[str, Any]]:
    """Generate sample debts list.

    Returns:
        List of debt dicts compatible with session_state.dividas.
    """
    from datetime import datetime
    base_ts = int(datetime(2024, 1, 1).timestamp() * 1_000_000)

    return [
        {
            "id": base_ts + 1,
            "nome": "Financiamento Imóvel",
            "credor": "Caixa Econômica",
            "sistema": "SAC",
            "status": "Ativa",
            "valor_principal": 280000.0,
            "taxa_mensal": 0.7,
            "n_parcelas": 360,
            "parcela_atual": 48,
            "vencimento_dia": 10,
        },
        {
            "id": base_ts + 2,
            "nome": "Carro Financiado",
            "credor": "Banco Itaú",
            "sistema": "PRICE",
            "status": "Ativa",
            "valor_principal": 45000.0,
            "taxa_mensal": 1.2,
            "n_parcelas": 60,
            "parcela_atual": 18,
            "vencimento_dia": 20,
        },
        {
            "id": base_ts + 3,
            "nome": "Cartão de Crédito",
            "credor": "Nubank",
            "sistema": "PRICE",
            "status": "Ativa",
            "valor_principal": 8000.0,
            "taxa_mensal": 2.99,
            "n_parcelas": 12,
            "parcela_atual": 3,
            "vencimento_dia": 15,
        },
    ]


def gerar_investimentos_exemplo() -> List[Dict[str, Any]]:
    """Generate sample investments list.

    Returns:
        List of investment dicts compatible with session_state.investimentos.
    """
    from datetime import datetime
    base_ts = int(datetime(2024, 1, 1).timestamp() * 1_000_000)

    return [
        {
            "id": base_ts + 10,
            "tipo": "Tesouro",
            "instituicao": "Tesouro Direto",
            "valor_aplicado": 15000.0,
            "valor_atual": 16850.0,
            "aporte_mensal": 500.0,
            "data_aplicacao": "2023-01-15",
            "objetivo": "Reserva de emergência",
            "liquidez": "D+1",
        },
        {
            "id": base_ts + 11,
            "tipo": "FII",
            "instituicao": "XP Investimentos",
            "valor_aplicado": 8000.0,
            "valor_atual": 8640.0,
            "aporte_mensal": 200.0,
            "data_aplicacao": "2023-06-01",
            "objetivo": "Renda passiva",
            "liquidez": "D+2",
        },
        {
            "id": base_ts + 12,
            "tipo": "CDB",
            "instituicao": "Nubank",
            "valor_aplicado": 5000.0,
            "valor_atual": 5380.0,
            "aporte_mensal": 0.0,
            "data_aplicacao": "2024-01-10",
            "objetivo": "Viagem Europa",
            "liquidez": "No vencimento",
        },
    ]


def gerar_metas_exemplo() -> List[Dict[str, Any]]:
    """Generate sample reserve goals.

    Returns:
        List of goal dicts compatible with session_state.metas_reserva.
    """
    from datetime import datetime
    base_ts = int(datetime(2024, 1, 1).timestamp() * 1_000_000)

    return [
        {
            "id": base_ts + 20,
            "objetivo": "Reserva de emergência (6 meses)",
            "valor_meta": 60000.0,
            "valor_atual": 16850.0,
        },
        {
            "id": base_ts + 21,
            "objetivo": "Viagem Europa",
            "valor_meta": 25000.0,
            "valor_atual": 5380.0,
        },
        {
            "id": base_ts + 22,
            "objetivo": "Troca do carro",
            "valor_meta": 50000.0,
            "valor_atual": 8640.0,
        },
    ]
