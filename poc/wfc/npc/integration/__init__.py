"""
NPC Integration Module

Connects NPC systems with other game components:
- plot_roles: Links fractal plots to NPC fractal roles
"""

from .plot_roles import (
    PlotRoleIntegrator,
    PlotRoleAssignment,
    NPCPlotParticipation,
    PROPP_ROLE_INVOLVEMENT,
    PLOT_TRIGGERED_TRANSITIONS,
)

__all__ = [
    'PlotRoleIntegrator',
    'PlotRoleAssignment',
    'NPCPlotParticipation',
    'PROPP_ROLE_INVOLVEMENT',
    'PLOT_TRIGGERED_TRANSITIONS',
]
