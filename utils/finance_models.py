"""Financial models and calculators for debts and investments.

This module contains pure functions for installment calculations (PRICE/SAC),
investment return metrics, and reserve goal progress.
"""

from typing import Any, Dict, List


def _validate_positive(value: float, field_name: str, allow_zero: bool = False) -> None:
    """Validate positive numeric values.

    Args:
        value: Numeric value to validate.
        field_name: Field name for error messages.
        allow_zero: Whether zero is accepted.

    Raises:
        ValueError: If value is invalid.
    """
    if allow_zero:
        if value < 0:
            raise ValueError(f"{field_name} deve ser maior ou igual a zero.")
    elif value <= 0:
        raise ValueError(f"{field_name} deve ser maior que zero.")


def _validate_parcelas(n_parcelas: int, parcela_atual: int) -> None:
    """Validate installment range.

    Args:
        n_parcelas: Total installments.
        parcela_atual: Current installment (1-indexed).

    Raises:
        ValueError: If range is invalid.
    """
    if n_parcelas <= 0:
        raise ValueError("Quantidade de parcelas deve ser maior que zero.")
    if parcela_atual <= 0:
        raise ValueError("Parcela atual deve ser maior que zero.")
    if parcela_atual > n_parcelas:
        raise ValueError("Parcela atual nao pode ser maior que total de parcelas.")


def _to_decimal_rate(taxa_mensal: float) -> float:
    """Convert percent monthly rate to decimal.

    Args:
        taxa_mensal: Monthly rate in percent (e.g. 2.5 for 2.5%).

    Returns:
        Decimal rate.
    """
    if taxa_mensal < 0:
        raise ValueError("Taxa de juros nao pode ser negativa.")
    return taxa_mensal / 100.0


def calcular_parcela_price(
    valor_principal: float, taxa_mensal: float, n_parcelas: int
) -> float:
    """Calculate constant PRICE installment value.

    Args:
        valor_principal: Principal debt value.
        taxa_mensal: Monthly interest rate in percent.
        n_parcelas: Number of installments.

    Returns:
        Fixed installment amount.
    """
    _validate_positive(valor_principal, "Valor principal")
    _validate_positive(float(n_parcelas), "Quantidade de parcelas")

    i = _to_decimal_rate(taxa_mensal)
    if i == 0:
        return valor_principal / n_parcelas

    fator = (1 + i) ** n_parcelas
    return valor_principal * (i * fator) / (fator - 1)


def calcular_parcela_sac(
    valor_principal: float, taxa_mensal: float, n_parcelas: int, parcela_atual: int
) -> float:
    """Calculate SAC installment value for a specific installment.

    Args:
        valor_principal: Principal debt value.
        taxa_mensal: Monthly interest rate in percent.
        n_parcelas: Number of installments.
        parcela_atual: Current installment number (1-indexed).

    Returns:
        Installment amount for the given installment in SAC system.
    """
    _validate_positive(valor_principal, "Valor principal")
    _validate_parcelas(n_parcelas, parcela_atual)

    i = _to_decimal_rate(taxa_mensal)
    amortizacao = valor_principal / n_parcelas
    saldo_devedor = valor_principal - amortizacao * (parcela_atual - 1)
    juros = saldo_devedor * i
    return amortizacao + juros


def gerar_cronograma_price(
    valor_principal: float, taxa_mensal: float, n_parcelas: int
) -> List[Dict[str, float]]:
    """Generate complete PRICE amortization schedule.

    Args:
        valor_principal: Principal debt value.
        taxa_mensal: Monthly interest rate in percent.
        n_parcelas: Number of installments.

    Returns:
        List of rows with installment, amortization, interest and remaining balance.
    """
    _validate_positive(valor_principal, "Valor principal")
    _validate_positive(float(n_parcelas), "Quantidade de parcelas")

    i = _to_decimal_rate(taxa_mensal)
    valor_parcela = calcular_parcela_price(valor_principal, taxa_mensal, n_parcelas)
    saldo = valor_principal
    rows: List[Dict[str, float]] = []

    for parcela in range(1, n_parcelas + 1):
        juros = saldo * i
        amortizacao = valor_parcela - juros
        saldo = max(saldo - amortizacao, 0.0)
        rows.append(
            {
                "parcela": float(parcela),
                "valor_parcela": valor_parcela,
                "juros": juros,
                "amortizacao": amortizacao,
                "saldo_devedor": saldo,
            }
        )

    return rows


def gerar_cronograma_sac(
    valor_principal: float, taxa_mensal: float, n_parcelas: int
) -> List[Dict[str, float]]:
    """Generate complete SAC amortization schedule.

    Args:
        valor_principal: Principal debt value.
        taxa_mensal: Monthly interest rate in percent.
        n_parcelas: Number of installments.

    Returns:
        List of rows with installment, amortization, interest and remaining balance.
    """
    _validate_positive(valor_principal, "Valor principal")
    _validate_positive(float(n_parcelas), "Quantidade de parcelas")

    i = _to_decimal_rate(taxa_mensal)
    amortizacao = valor_principal / n_parcelas
    saldo = valor_principal
    rows: List[Dict[str, float]] = []

    for parcela in range(1, n_parcelas + 1):
        juros = saldo * i
        valor_parcela = amortizacao + juros
        saldo = max(saldo - amortizacao, 0.0)
        rows.append(
            {
                "parcela": float(parcela),
                "valor_parcela": valor_parcela,
                "juros": juros,
                "amortizacao": amortizacao,
                "saldo_devedor": saldo,
            }
        )

    return rows


def calcular_total_pago_restante(
    valor_total: float, parcela_atual: int, n_parcelas: int, valor_parcela: float
) -> Dict[str, float]:
    """Calculate paid and remaining totals based on current installment.

    Args:
        valor_total: Total debt value (estimated final amount).
        parcela_atual: Current installment number (1-indexed).
        n_parcelas: Number of installments.
        valor_parcela: Current/constant installment amount.

    Returns:
        Dictionary with paid/remaining totals and installment counters.
    """
    _validate_positive(valor_total, "Valor total")
    _validate_parcelas(n_parcelas, parcela_atual)
    _validate_positive(valor_parcela, "Valor da parcela")

    parcelas_pagas = parcela_atual - 1
    parcelas_restantes = n_parcelas - parcelas_pagas
    total_pago = parcelas_pagas * valor_parcela
    total_restante = max(valor_total - total_pago, 0.0)

    return {
        "parcelas_pagas": float(parcelas_pagas),
        "parcelas_restantes": float(parcelas_restantes),
        "total_pago": total_pago,
        "total_restante": total_restante,
    }


def calcular_resumo_divida(
    valor_principal: float,
    taxa_mensal: float,
    n_parcelas: int,
    parcela_atual: int,
    sistema: str = "PRICE",
    status: str = "Ativa",
) -> Dict[str, float]:
    """Calculate debt summary values for dashboard metrics.

    Args:
        valor_principal: Principal debt value.
        taxa_mensal: Monthly interest rate in percent.
        n_parcelas: Number of installments.
        parcela_atual: Current installment number (1-indexed).
        sistema: Amortization system (PRICE or SAC).
        status: Debt status (Ativa or Quitada).

    Returns:
        Dictionary with paid, remaining, monthly installment and final debt value.
    """
    sistema_norm = sistema.upper().strip()
    _validate_positive(valor_principal, "Valor principal")
    _validate_parcelas(n_parcelas, parcela_atual)

    if sistema_norm == "SAC":
        cronograma = gerar_cronograma_sac(valor_principal, taxa_mensal, n_parcelas)
    else:
        cronograma = gerar_cronograma_price(valor_principal, taxa_mensal, n_parcelas)

    total_final = sum(item["valor_parcela"] for item in cronograma)

    if status.lower() == "quitada":
        total_pago = total_final
        total_restante = 0.0
        parcela_mensal_atual = 0.0
    else:
        parcelas_pagas = max(parcela_atual - 1, 0)
        total_pago = sum(item["valor_parcela"] for item in cronograma[:parcelas_pagas])
        total_restante = max(total_final - total_pago, 0.0)
        indice_parcela = min(parcela_atual - 1, n_parcelas - 1)
        parcela_mensal_atual = cronograma[indice_parcela]["valor_parcela"]

    return {
        "total_final": total_final,
        "total_pago": total_pago,
        "total_restante": total_restante,
        "parcela_mensal_atual": parcela_mensal_atual,
    }


def calcular_rentabilidade(
    valor_aplicado: float, valor_atual: float
) -> Dict[str, float]:
    """Calculate investment return in currency and percentage.

    Args:
        valor_aplicado: Invested principal amount.
        valor_atual: Current market/current value.

    Returns:
        Dictionary with absolute and percentual return.
    """
    _validate_positive(valor_aplicado, "Valor aplicado")
    _validate_positive(valor_atual, "Valor atual", allow_zero=True)

    lucro = valor_atual - valor_aplicado
    percentual = (lucro / valor_aplicado) * 100 if valor_aplicado > 0 else 0.0
    return {
        "lucro": lucro,
        "rentabilidade_percentual": percentual,
    }


def calcular_progresso_meta(valor_atual: float, valor_meta: float) -> float:
    """Calculate progress percentage for reserve goals.

    Args:
        valor_atual: Current accumulated value for the goal.
        valor_meta: Target amount.

    Returns:
        Progress percentage (can exceed 100 when goal is surpassed).
    """
    _validate_positive(valor_meta, "Valor da meta")
    _validate_positive(valor_atual, "Valor atual da meta", allow_zero=True)

    return (valor_atual / valor_meta) * 100.0


def simular_meta_sonhos(
    fv: float,
    p: float,
    taxa_mensal: float,
    saldo_inicial: float = 0.0,
    max_meses: int = 600,
) -> Dict[str, Any]:
    """Simulate months needed to reach a dream goal using compound interest.

    Uses the future value of annuity formula:
        FV = P × ((1 + r)^n - 1) / r

    When saldo_inicial > 0, it grows alongside contributions:
        FV_total = saldo_inicial × (1 + r)^n + P × ((1 + r)^n - 1) / r

    Iterates month-by-month to find n and build the growth curve.

    Args:
        fv: Target future value (goal amount in R$).
        p: Monthly contribution (aporte mensal in R$).
        taxa_mensal: Expected monthly return rate in percent (e.g. 0.8 for 0.8%).
        saldo_inicial: Already-accumulated balance today (default 0).
        max_meses: Safety ceiling to prevent infinite loops (default 600 = 50 years).

    Returns:
        Dictionary with:
            - meses (int): Months to reach the goal (-1 if unreachable).
            - anos (float): Years to reach the goal.
            - curva (List[Dict]): Month-by-month growth curve for plotting.
            - atingido (bool): Whether goal is reachable within max_meses.
            - total_aportado (float): Total contributed (excluding initial balance).
            - juros_gerados (float): Total interest earned.
    """
    _validate_positive(fv, "Valor da meta")
    if p < 0:
        raise ValueError("Aporte mensal não pode ser negativo.")
    if taxa_mensal < 0:
        raise ValueError("Taxa de juros não pode ser negativa.")
    if saldo_inicial < 0:
        raise ValueError("Saldo inicial não pode ser negativo.")

    r = taxa_mensal / 100.0
    saldo = saldo_inicial
    curva: List[Dict[str, float]] = [{"mes": 0, "saldo": round(saldo, 2)}]

    for mes in range(1, max_meses + 1):
        if r > 0:
            saldo = saldo * (1 + r) + p
        else:
            saldo = saldo + p

        curva.append({"mes": mes, "saldo": round(saldo, 2)})

        if saldo >= fv:
            total_aportado = p * mes
            juros_gerados = saldo - saldo_inicial - total_aportado
            return {
                "meses": mes,
                "anos": round(mes / 12, 1),
                "curva": curva,
                "atingido": True,
                "total_aportado": round(total_aportado, 2),
                "juros_gerados": round(juros_gerados, 2),
            }

    # Goal not reachable within max_meses
    return {
        "meses": -1,
        "anos": -1,
        "curva": curva,
        "atingido": False,
        "total_aportado": round(p * max_meses, 2),
        "juros_gerados": round(curva[-1]["saldo"] - saldo_inicial - p * max_meses, 2),
    }
