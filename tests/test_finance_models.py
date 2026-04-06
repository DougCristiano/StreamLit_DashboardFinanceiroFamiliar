"""Tests for financial models (PRICE/SAC, returns, goals)."""

import pytest

from utils.finance_models import (
    calcular_parcela_price,
    calcular_parcela_sac,
    gerar_cronograma_price,
    gerar_cronograma_sac,
    calcular_total_pago_restante,
    calcular_resumo_divida,
    calcular_rentabilidade,
    calcular_progresso_meta,
)


class TestParcelasPrice:
    """PRICE system tests."""

    def test_parcela_price_sem_juros(self):
        """Should divide principal equally when rate is zero."""
        parcela = calcular_parcela_price(1200.0, 0.0, 12)
        assert parcela == pytest.approx(100.0)

    def test_parcela_price_com_juros(self):
        """Should calculate fixed installment with interest."""
        parcela = calcular_parcela_price(1000.0, 2.0, 10)
        assert parcela > 100.0

    def test_parcela_price_valor_invalido(self):
        """Should reject non-positive principal."""
        with pytest.raises(ValueError):
            calcular_parcela_price(0.0, 2.0, 12)


class TestParcelasSac:
    """SAC system tests."""

    def test_parcela_sac_reduz_ao_longo_tempo(self):
        """SAC installments should decrease over time."""
        p1 = calcular_parcela_sac(1200.0, 2.0, 12, 1)
        p12 = calcular_parcela_sac(1200.0, 2.0, 12, 12)
        assert p1 > p12

    def test_parcela_sac_sem_juros(self):
        """SAC without interest should be constant amortization."""
        p1 = calcular_parcela_sac(1200.0, 0.0, 12, 1)
        p10 = calcular_parcela_sac(1200.0, 0.0, 12, 10)
        assert p1 == pytest.approx(100.0)
        assert p10 == pytest.approx(100.0)

    def test_parcela_sac_parcela_invalida(self):
        """Should reject parcela_atual greater than total."""
        with pytest.raises(ValueError):
            calcular_parcela_sac(1000.0, 1.0, 10, 11)


class TestCronogramas:
    """Amortization schedule tests."""

    def test_cronograma_price_tamanho(self):
        """Schedule length must match number of installments."""
        cronograma = gerar_cronograma_price(1000.0, 2.0, 10)
        assert len(cronograma) == 10

    def test_cronograma_sac_tamanho(self):
        """Schedule length must match number of installments."""
        cronograma = gerar_cronograma_sac(1000.0, 2.0, 8)
        assert len(cronograma) == 8

    def test_cronograma_saldo_final_quase_zero(self):
        """Final balance should be near zero due to floating-point operations."""
        cronograma = gerar_cronograma_price(1000.0, 2.0, 12)
        saldo_final = cronograma[-1]["saldo_devedor"]
        assert saldo_final == pytest.approx(0.0, abs=1e-6)


class TestResumoDivida:
    """Debt summary tests."""

    def test_resumo_divida_ativa(self):
        """Active debt should have positive remaining amount."""
        resumo = calcular_resumo_divida(1000.0, 2.0, 10, 3, "PRICE", "Ativa")
        assert resumo["total_restante"] > 0
        assert resumo["parcela_mensal_atual"] > 0

    def test_resumo_divida_quitada(self):
        """Paid debt should have zero remaining amount."""
        resumo = calcular_resumo_divida(1000.0, 2.0, 10, 10, "SAC", "Quitada")
        assert resumo["total_restante"] == pytest.approx(0.0)
        assert resumo["parcela_mensal_atual"] == pytest.approx(0.0)

    def test_total_pago_restante(self):
        """Should split paid and remaining totals based on current installment."""
        data = calcular_total_pago_restante(1200.0, 4, 12, 100.0)
        assert data["parcelas_pagas"] == pytest.approx(3.0)
        assert data["total_pago"] == pytest.approx(300.0)
        assert data["total_restante"] == pytest.approx(900.0)


class TestInvestimentosEMetas:
    """Investment return and reserve goal tests."""

    def test_rentabilidade_positiva(self):
        """Should compute positive return correctly."""
        rent = calcular_rentabilidade(1000.0, 1200.0)
        assert rent["lucro"] == pytest.approx(200.0)
        assert rent["rentabilidade_percentual"] == pytest.approx(20.0)

    def test_rentabilidade_negativa(self):
        """Should compute negative return correctly."""
        rent = calcular_rentabilidade(1000.0, 900.0)
        assert rent["lucro"] == pytest.approx(-100.0)
        assert rent["rentabilidade_percentual"] == pytest.approx(-10.0)

    def test_rentabilidade_valor_aplicado_invalido(self):
        """Should reject zero applied value."""
        with pytest.raises(ValueError):
            calcular_rentabilidade(0.0, 1000.0)

    def test_progresso_meta(self):
        """Should compute percentage progress for reserve goals."""
        progresso = calcular_progresso_meta(2500.0, 5000.0)
        assert progresso == pytest.approx(50.0)

    def test_progresso_meta_superado(self):
        """Should allow values above 100% when goal is exceeded."""
        progresso = calcular_progresso_meta(6000.0, 5000.0)
        assert progresso == pytest.approx(120.0)

    def test_progresso_meta_invalida(self):
        """Should reject invalid goal target value."""
        with pytest.raises(ValueError):
            calcular_progresso_meta(1000.0, 0.0)
