"""
Plot-Roles Integration

Connects fractal plot structure to NPC fractal roles:
- Maps Propp functions to actant roles
- Assigns NPC roles based on plot participation
- Updates roles when narrative level changes
- Triggers role transitions on plot events
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import IntEnum
import random

from ..archetypes.fractal_roles import (
    FractalRoleSystem, FractalRole, ActantRole, NarrativeLevel as RoleLevel,
    RoleTransition, ROLE_BEHAVIORS
)
from ...plot_fractal import (
    FractalPlot, FractalPlotNode, NarrativeLevel as PlotLevel,
    ProppFunc, EndingMode, LEVEL_NAMES
)


# =============================================================================
# Propp Function -> Actant Role Mapping
# =============================================================================

# Which actant roles are typically involved in each Propp function
# Based on the 16-function ProppFunc enum from plot_advanced.py
PROPP_ROLE_INVOLVEMENT = {
    # ACT I - Setup
    ProppFunc.EQUILIBRIUM: {
        ActantRole.SENDER: "establishes status quo",
    },
    ProppFunc.LACK: {
        ActantRole.SENDER: "reveals the need",
        ActantRole.OPPONENT: "creates the lack",
    },
    ProppFunc.INTERDICTION: {
        ActantRole.SENDER: "gives warning",
        ActantRole.MENTOR: "provides guidance",
    },
    ProppFunc.VIOLATION: {
        ActantRole.SUBJECT: "breaks rule",
        ActantRole.TRICKSTER: "tempts violation",
    },

    # ACT II - Adventure
    ProppFunc.DEPARTURE: {
        ActantRole.SUBJECT: "begins journey",
        ActantRole.HELPER: "accompanies",
    },
    ProppFunc.DONOR_TEST: {
        ActantRole.MENTOR: "tests hero",
        ActantRole.THRESHOLD_GUARDIAN: "challenges worthiness",
    },
    ProppFunc.ACQUISITION: {
        ActantRole.MENTOR: "bestows gift",
        ActantRole.HELPER: "provides aid",
    },
    ProppFunc.GUIDANCE: {
        ActantRole.MENTOR: "shows the way",
        ActantRole.HELPER: "guides hero",
    },

    # ACT III - Confrontation
    ProppFunc.STRUGGLE: {
        ActantRole.SUBJECT: "fights villain",
        ActantRole.OPPONENT: "confronts hero",
        ActantRole.HELPER: "assists in battle",
    },
    ProppFunc.BRANDING: {
        ActantRole.SUBJECT: "receives mark",
        ActantRole.MENTOR: "bestows mark",
    },
    ProppFunc.VICTORY: {
        ActantRole.SUBJECT: "defeats villain",
        ActantRole.OPPONENT: "is defeated",
    },
    ProppFunc.PURSUIT: {
        ActantRole.OPPONENT: "chases hero",
        ActantRole.SHADOW: "pursues",
    },

    # ACT IV - Resolution
    ProppFunc.RESCUE: {
        ActantRole.SUBJECT: "saves victim",
        ActantRole.HELPER: "assists rescue",
        ActantRole.RECEIVER: "is rescued",
    },
    ProppFunc.RECOGNITION: {
        ActantRole.SUBJECT: "is recognized",
        ActantRole.RECEIVER: "acknowledges hero",
        ActantRole.TRICKSTER: "reveals truth",
    },
    ProppFunc.PUNISHMENT: {
        ActantRole.OPPONENT: "is punished",
        ActantRole.SHADOW: "faces justice",
    },
    ProppFunc.RETURN: {
        ActantRole.SUBJECT: "returns home",
        ActantRole.RECEIVER: "welcomes hero",
    },
}


# Role transitions triggered by plot events
PLOT_TRIGGERED_TRANSITIONS = {
    # Recognition - unknown becomes known, potential betrayals revealed
    ProppFunc.RECOGNITION: [
        ("true_identity", ActantRole.TRICKSTER, ActantRole.MENTOR),
        ("heroic_deed", ActantRole.HELPER, ActantRole.SUBJECT),
        ("revealed_traitor", ActantRole.HELPER, ActantRole.SHADOW),
        ("revealed_ally", ActantRole.OPPONENT, ActantRole.HELPER),
    ],

    # Branding - transformation and change
    ProppFunc.BRANDING: [
        ("redemption", ActantRole.OPPONENT, ActantRole.HELPER),
        ("corruption", ActantRole.HELPER, ActantRole.SHADOW),
    ],

    # Victory can shift dynamics
    ProppFunc.VICTORY: [
        ("power_vacuum", ActantRole.MENTOR, ActantRole.SENDER),
    ],

    # Punishment - consequences
    ProppFunc.PUNISHMENT: [
        ("villain_defeated", ActantRole.OPPONENT, ActantRole.NONE),
    ],
}


@dataclass
class NPCPlotParticipation:
    """Tracks an NPC's involvement in plot nodes"""
    npc_name: str
    role_in_node: ActantRole
    node_id: int
    level: PlotLevel
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_name": self.npc_name,
            "role": self.role_in_node.name,
            "node_id": self.node_id,
            "level": LEVEL_NAMES.get(self.level, str(self.level)),
            "description": self.description,
        }


@dataclass
class PlotRoleAssignment:
    """Assignment of NPCs to roles for a specific plot"""
    plot_id: str  # Unique identifier for the plot
    assignments: Dict[str, List[NPCPlotParticipation]] = field(default_factory=dict)
    # npc_name -> list of participations at different levels

    def get_npc_role_at_level(self, npc_name: str, level: PlotLevel) -> Optional[ActantRole]:
        """Get an NPC's role at a specific narrative level"""
        if npc_name not in self.assignments:
            return None
        for part in self.assignments[npc_name]:
            if part.level == level:
                return part.role_in_node
        return None

    def get_npcs_with_role(self, role: ActantRole, level: PlotLevel = None) -> List[str]:
        """Get all NPCs with a specific role (optionally at a level)"""
        result = []
        for npc_name, parts in self.assignments.items():
            for part in parts:
                if part.role_in_node == role:
                    if level is None or part.level == level:
                        result.append(npc_name)
                        break
        return result


class PlotRoleIntegrator:
    """
    Integrates fractal plots with NPC fractal roles.

    Responsibilities:
    - Assign NPCs to plot roles based on their participation
    - Synchronize narrative levels between plot and role systems
    - Trigger role transitions based on plot events
    - Generate NPCs for plot nodes that need participants
    """

    def __init__(self, role_system: FractalRoleSystem = None):
        self.role_system = role_system or FractalRoleSystem()
        self.plot_assignments: Dict[str, PlotRoleAssignment] = {}
        self.active_plot_id: Optional[str] = None
        self.npc_names: Set[str] = set()  # Known NPCs

    def register_npc(self, npc_name: str,
                     default_role: ActantRole = ActantRole.NONE):
        """Register an NPC that can participate in plots"""
        self.npc_names.add(npc_name)
        if npc_name not in self.role_system.npc_roles:
            self.role_system.assign_role(npc_name, macro_role=default_role)

    def assign_plot_roles(self, plot: FractalPlot,
                          plot_id: str = None,
                          npc_roster: Dict[str, ActantRole] = None) -> PlotRoleAssignment:
        """
        Assign NPCs to roles in a fractal plot.

        Args:
            plot: The fractal plot to assign roles for
            plot_id: Unique ID for this plot (generated if not provided)
            npc_roster: Optional mapping of NPC names to preferred roles

        Returns:
            PlotRoleAssignment with all NPC participations
        """
        if plot_id is None:
            plot_id = f"plot_{id(plot)}"

        assignment = PlotRoleAssignment(plot_id=plot_id)
        npc_roster = npc_roster or {}

        # Register any NPCs from roster
        for npc_name, role in npc_roster.items():
            self.register_npc(npc_name, role)

        # Assign roles recursively through the plot structure
        self._assign_node_roles(plot, assignment, npc_roster, plot.level)

        self.plot_assignments[plot_id] = assignment
        self.active_plot_id = plot_id

        # Update role system with assignments
        self._sync_roles_from_assignment(assignment)

        return assignment

    def _assign_node_roles(self, plot: FractalPlot,
                           assignment: PlotRoleAssignment,
                           npc_roster: Dict[str, ActantRole],
                           current_level: PlotLevel,
                           used_npcs: Set[str] = None):
        """Recursively assign NPC roles for plot nodes"""
        if used_npcs is None:
            used_npcs = set()

        for node in plot.nodes:
            # Get roles involved in this Propp function
            role_involvement = PROPP_ROLE_INVOLVEMENT.get(node.function, {})

            for role, role_desc in role_involvement.items():
                # Find an NPC for this role
                npc_name = self._find_npc_for_role(
                    role, npc_roster, used_npcs, current_level
                )

                if npc_name:
                    participation = NPCPlotParticipation(
                        npc_name=npc_name,
                        role_in_node=role,
                        node_id=node.id,
                        level=current_level,
                        description=role_desc,
                    )

                    if npc_name not in assignment.assignments:
                        assignment.assignments[npc_name] = []
                    assignment.assignments[npc_name].append(participation)

                    # Track usage to avoid over-assigning
                    used_npcs.add(npc_name)

            # Recurse into sub-plot
            if node.has_sub_plot():
                sub_level = PlotLevel(current_level - 1) if current_level > PlotLevel.NANO else current_level
                self._assign_node_roles(
                    node.sub_plot, assignment, npc_roster,
                    sub_level, used_npcs.copy()  # Fresh set for sub-plot
                )

    def _find_npc_for_role(self, role: ActantRole,
                           npc_roster: Dict[str, ActantRole],
                           used_npcs: Set[str],
                           level: PlotLevel) -> Optional[str]:
        """Find an NPC to fill a role"""
        # First, check roster for NPCs assigned to this role
        for npc_name, preferred_role in npc_roster.items():
            if preferred_role == role and npc_name not in used_npcs:
                return npc_name

        # Then check existing NPCs with compatible roles
        for npc_name in self.npc_names:
            if npc_name in used_npcs:
                continue
            existing_role = self.role_system.get_role(npc_name)
            if existing_role and existing_role.get_role() == role:
                return npc_name

        # Finally, pick any unused NPC or generate name
        available = self.npc_names - used_npcs
        if available:
            return random.choice(list(available))

        # Generate a placeholder name
        return self._generate_npc_name(role)

    def _generate_npc_name(self, role: ActantRole) -> str:
        """Generate a placeholder NPC name for a role"""
        role_name_templates = {
            ActantRole.MENTOR: ["Elder {}", "Sage {}", "Master {}"],
            ActantRole.HELPER: ["Companion {}", "Ally {}", "Friend {}"],
            ActantRole.OPPONENT: ["Rival {}", "Enemy {}", "Foe {}"],
            ActantRole.SHADOW: ["Dark {}", "Shadow {}"],
            ActantRole.SENDER: ["King {}", "Elder {}", "Chief {}"],
            ActantRole.TRICKSTER: ["Stranger {}", "Wanderer {}"],
            ActantRole.THRESHOLD_GUARDIAN: ["Guardian {}", "Keeper {}"],
        }

        templates = role_name_templates.get(role, ["Character {}"])
        template = random.choice(templates)
        suffix = random.choice(["Aldric", "Theron", "Vera", "Lyra", "Zara", "Kira"])

        name = template.format(suffix)
        self.register_npc(name, role)
        return name

    def _sync_roles_from_assignment(self, assignment: PlotRoleAssignment):
        """Update role system based on plot assignments"""
        for npc_name, participations in assignment.assignments.items():
            fractal_role = FractalRole()

            for part in participations:
                # Map plot level to role level
                role_level = self._plot_to_role_level(part.level)
                fractal_role.set_role(role_level, part.role_in_node)

            self.role_system.npc_roles[npc_name] = fractal_role

    def _plot_to_role_level(self, plot_level: PlotLevel) -> RoleLevel:
        """Convert plot narrative level to role narrative level"""
        # They use the same enum values
        return RoleLevel(int(plot_level))

    def on_plot_event(self, plot_func: ProppFunc,
                      node_id: int = None,
                      custom_triggers: List[str] = None):
        """
        Handle a plot event that may trigger role transitions.

        Args:
            plot_func: The Propp function that was completed
            node_id: Optional specific node ID
            custom_triggers: Additional trigger names to fire
        """
        # Get predefined transitions for this function
        transitions = PLOT_TRIGGERED_TRANSITIONS.get(plot_func, [])

        # Fire each transition type
        for trigger_name, from_role, to_role in transitions:
            self._process_transition(trigger_name, from_role, to_role)

        # Fire custom triggers
        if custom_triggers:
            for trigger in custom_triggers:
                self.role_system.trigger_event(trigger)

    def _process_transition(self, trigger: str,
                            from_role: ActantRole,
                            to_role: ActantRole):
        """Process a role transition for all applicable NPCs"""
        for npc_name, fractal_role in self.role_system.npc_roles.items():
            current_role = fractal_role.get_role()
            if current_role == from_role:
                # Check if this NPC should transition (50% chance by default)
                if random.random() < 0.5:
                    # Add and apply transition
                    transition = RoleTransition(
                        from_role=from_role,
                        to_role=to_role,
                        trigger=trigger,
                        at_level=fractal_role.active_level,
                    )
                    fractal_role.apply_transition(transition)

    def set_narrative_level(self, level: PlotLevel):
        """Update the active narrative level for all NPCs"""
        role_level = self._plot_to_role_level(level)
        self.role_system.set_narrative_level(role_level)

    def get_npc_role_in_current_context(self, npc_name: str) -> Optional[ActantRole]:
        """Get an NPC's current role based on active narrative level"""
        fractal_role = self.role_system.get_role(npc_name)
        if fractal_role:
            return fractal_role.get_role()
        return None

    def get_scene_participants(self, node: FractalPlotNode) -> Dict[ActantRole, List[str]]:
        """Get NPCs participating in a specific plot node, grouped by role"""
        result: Dict[ActantRole, List[str]] = {}

        if self.active_plot_id not in self.plot_assignments:
            return result

        assignment = self.plot_assignments[self.active_plot_id]

        for npc_name, participations in assignment.assignments.items():
            for part in participations:
                if part.node_id == node.id:
                    if part.role_in_node not in result:
                        result[part.role_in_node] = []
                    result[part.role_in_node].append(npc_name)

        return result

    def generate_cast_list(self, plot: FractalPlot = None) -> str:
        """Generate a human-readable cast list for the plot"""
        if plot:
            assignment = self.assign_plot_roles(plot)
        elif self.active_plot_id and self.active_plot_id in self.plot_assignments:
            assignment = self.plot_assignments[self.active_plot_id]
        else:
            return "No plot assigned."

        lines = ["=== Cast List ===", ""]

        # Group by role
        role_groups: Dict[ActantRole, List[str]] = {}
        for npc_name, participations in assignment.assignments.items():
            for part in participations:
                if part.role_in_node not in role_groups:
                    role_groups[part.role_in_node] = []
                if npc_name not in role_groups[part.role_in_node]:
                    role_groups[part.role_in_node].append(npc_name)

        # Print by role importance
        role_order = [
            ActantRole.SUBJECT, ActantRole.OPPONENT, ActantRole.SHADOW,
            ActantRole.MENTOR, ActantRole.HELPER, ActantRole.SENDER,
            ActantRole.RECEIVER, ActantRole.TRICKSTER, ActantRole.THRESHOLD_GUARDIAN,
        ]

        for role in role_order:
            if role in role_groups:
                npcs = role_groups[role]
                lines.append(f"{role.name}:")
                for npc in npcs:
                    lines.append(f"  - {npc}")
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary"""
        return {
            "role_system": self.role_system.to_dict(),
            "npc_names": list(self.npc_names),
            "active_plot_id": self.active_plot_id,
            "plot_assignments": {
                pid: {
                    "plot_id": pa.plot_id,
                    "assignments": {
                        name: [p.to_dict() for p in parts]
                        for name, parts in pa.assignments.items()
                    }
                }
                for pid, pa in self.plot_assignments.items()
            }
        }


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo plot-role integration"""
    print("=" * 60)
    print("PLOT-ROLE INTEGRATION DEMO")
    print("=" * 60)

    from ...plot_fractal import FractalPlotGenerator, GENRES

    # Create systems
    integrator = PlotRoleIntegrator()

    # Register some NPCs
    integrator.register_npc("Elder Sage", ActantRole.MENTOR)
    integrator.register_npc("Dark Knight", ActantRole.OPPONENT)
    integrator.register_npc("Loyal Squire", ActantRole.HELPER)
    integrator.register_npc("Mysterious Stranger", ActantRole.TRICKSTER)
    integrator.register_npc("Village Elder", ActantRole.SENDER)

    # Generate a plot
    gen = FractalPlotGenerator(GENRES["fantasy"], seed=42)
    gen.generate(PlotLevel.MACRO, depth=2, finale=ProppFunc.VICTORY)
    plot = gen.plot

    print("\nPlot Summary:")
    print(gen.get_summary())

    # Assign roles
    npc_roster = {
        "Elder Sage": ActantRole.MENTOR,
        "Dark Knight": ActantRole.OPPONENT,
        "Loyal Squire": ActantRole.HELPER,
    }
    assignment = integrator.assign_plot_roles(plot, npc_roster=npc_roster)

    print("\n" + integrator.generate_cast_list())

    # Show fractal roles
    print("\n=== Fractal Roles ===")
    for npc_name in ["Elder Sage", "Dark Knight", "Loyal Squire"]:
        role = integrator.role_system.get_role(npc_name)
        if role:
            print(f"\n{npc_name}:")
            print(f"  Macro: {role.macro_role.name if role.macro_role else 'None'}")
            print(f"  Meso: {role.meso_role.name if role.meso_role else 'None'}")
            print(f"  Micro: {role.micro_role.name if role.micro_role else 'None'}")

    # Simulate plot event
    print("\n=== After EXPOSURE event ===")
    integrator.on_plot_event(ProppFunc.EXPOSURE)

    for npc_name in ["Elder Sage", "Dark Knight", "Loyal Squire"]:
        role = integrator.role_system.get_role(npc_name)
        if role:
            current = role.get_role()
            print(f"{npc_name}: {current.name if current else 'None'}")


if __name__ == "__main__":
    demo()
