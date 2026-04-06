"""Tests for utils.processing module."""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import sys


class MockSessionState(dict):
    """Mock streamlit SessionState that behaves like both dict and object."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"No attribute {key}")

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        return dict.get(self, key, default)


# Mock streamlit before importing processing
sys.modules['streamlit'] = MagicMock()


class TestProcessarDados:
    """Test data processing function."""

    @patch('utils.processing.st')
    def test_processar_dados_empty_state(self, mock_st):
        """Should set df_transacoes to None when no data."""
        from utils.processing import processar_dados

        # Setup mock session state
        session_state = MockSessionState({
            'df_from_upload': None,
            'transacoes': [],
            'categories': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        # Should set df_transacoes to None
        assert session_state.get('df_transacoes') is None

    @patch('utils.processing.st')
    def test_processar_dados_with_upload(self, mock_st, sample_transactions):
        """Should process uploaded data correctly."""
        from utils.processing import processar_dados

        # Create upload dataframe
        df_upload = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-03'],
            'title': ['iFood Delivery', 'Aluguel Apartamento'],
            'amount': [-50.00, -1200.00]
        })

        # Setup mock session state
        mock_categories = {
            "Alimentação": ["ifood"],
            "Moradia": ["aluguel"],
            "Outros": []
        }

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': mock_categories,
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        # Check result
        result_df = session_state['df_transacoes']
        assert result_df is not None
        assert len(result_df) == 2
        assert 'Data' in result_df.columns
        assert 'Tipo' in result_df.columns
        assert 'Categoria' in result_df.columns

    @patch('utils.processing.st')
    def test_processar_dados_tipo_conversion(self, mock_st):
        """Should correctly identify Receita vs Despesa."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'title': ['Salário', 'Gasto'],
            'amount': [3000.00, -100.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        tipos = result_df['Tipo'].tolist()

        assert 'Receita' in tipos
        assert 'Despesa' in tipos

    @patch('utils.processing.st')
    def test_processar_dados_valor_abs(self, mock_st):
        """Should calculate absolute values correctly."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01'],
            'title': ['Gasto'],
            'amount': [-100.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        assert result_df['ValorAbs'].iloc[0] == 100.00

    @patch('utils.processing.st')
    def test_processar_dados_anomes(self, mock_st):
        """Should calculate AnoMes period correctly."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-15', '2024-02-10'],
            'title': ['Transação 1', 'Transação 2'],
            'amount': [-50.00, -60.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        anomeses = result_df['AnoMes'].unique()

        assert '2024-01' in anomeses
        assert '2024-02' in anomeses

    @patch('utils.processing.st')
    def test_processar_dados_invalid_dates(self, mock_st):
        """Should skip rows with invalid dates."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01', 'invalid-date', '2024-01-03'],
            'title': ['Transação 1', 'Transação 2', 'Transação 3'],
            'amount': [-50.00, -60.00, -70.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        # Should only have 2 rows (invalid date removed)
        assert len(result_df) == 2

    @patch('utils.processing.st')
    def test_processar_dados_zero_values_filtered(self, mock_st):
        """Should filter out zero values."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'title': ['Transação 1', 'Transação 2'],
            'amount': [-50.00, 0.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        # Should only have 1 row (zero value removed)
        assert len(result_df) == 1

    @patch('utils.processing.st')
    def test_processar_dados_with_manual_transactions(self, mock_st):
        """Should combine upload and manual transactions."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01'],
            'title': ['Gasto de Arquivo'],
            'amount': [-50.00]
        })

        manual = [{
            'Data': '2024-01-02',
            'Descrição': 'Gasto Manual',
            'Valor': -100.00,
            'Categoria_Manual': 'Outros',
            'Pessoa': 'João'
        }]

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': manual,
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        # Should have both transactions
        assert len(result_df) == 2

    @patch('utils.processing.st')
    def test_processar_dados_sorting_by_data(self, mock_st):
        """Should sort by date descending."""
        from utils.processing import processar_dados

        df_upload = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-03', '2024-01-02'],
            'title': ['A', 'C', 'B'],
            'amount': [-50.00, -70.00, -60.00]
        })

        session_state = MockSessionState({
            'df_from_upload': df_upload,
            'transacoes': [],
            'categories': {"Outros": []},
            'orcamento_mensal': {}
        })
        mock_st.session_state = session_state

        processar_dados()

        result_df = session_state['df_transacoes']
        # First row should be the latest date
        assert result_df['Descrição'].iloc[0] == 'C'  # 2024-01-03
