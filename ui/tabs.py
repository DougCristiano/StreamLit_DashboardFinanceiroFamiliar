"""Backward-compatibility shim — tabs.py was refactored into individual modules.

Each tab now lives in its own file:
  ui/tab_dashboard.py
  ui/tab_lancamentos.py
  ui/tab_familia.py
  ui/tab_extrato.py
  ui/tab_dividas.py
  ui/tab_investimentos.py
  ui/tab_planejamento.py
  ui/tab_configuracoes.py

This file re-exports all public render functions so existing imports keep working.
"""

from ui.tab_dashboard import render_dashboard
from ui.tab_lancamentos import render_lancamentos
from ui.tab_familia import render_familia
from ui.tab_extrato import render_extrato
from ui.tab_dividas import render_dividas
from ui.tab_investimentos import render_investimentos
from ui.tab_planejamento import render_planejamento
from ui.tab_configuracoes import render_configuracoes

__all__ = [
    "render_dashboard",
    "render_lancamentos",
    "render_familia",
    "render_extrato",
    "render_dividas",
    "render_investimentos",
    "render_planejamento",
    "render_configuracoes",
]
