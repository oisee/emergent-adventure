"""
Emergent Adventure - Streamlit Visualizer

Interactive visualization of generated worlds.
Run with: streamlit run visualizer.py
"""

import streamlit as st
import random
from wfc import WorldGenerator, TileType, TILE_CHARS, ProppFunction
from wfc.plot import PROPP_NAMES
from wfc.plot_advanced import (
    ProppFunc, Genre, TwistType, MultiPlot,
    PROPP_NAMES as ADV_PROPP_NAMES, GENRES, mix_genres
)
from wfc.integration import PlotType
from wfc.plot_fractal import (
    FractalPlotGenerator, FractalPlot, FractalPlotNode,
    NarrativeLevel, LEVEL_NAMES, LEVEL_COMPLEXITY,
    EndingMode, ENDING_MODES
)
from wfc.npc.archetypes.fractal_roles import ActantRole, NarrativeLevel as RoleLevel
from wfc.npc.integration.plot_roles import PROPP_ROLE_INVOLVEMENT, PLOT_TRIGGERED_TRANSITIONS
from wfc.weather import (
    WeatherState, WeatherType, Season, ClimateZone, TimeOfDay,
    AtmosphericPhenomenon, WEATHER_INFO, SEASON_INFO, TIME_OF_DAY_INFO, CLIMATE_INFO
)

# Tile colors for visualization
TILE_COLORS = {
    TileType.FOREST: '#228B22',     # Forest green
    TileType.CLEARING: '#90EE90',   # Light green
    TileType.RIVER: '#4169E1',      # Royal blue
    TileType.ROAD: '#D2691E',       # Chocolate
    TileType.MOUNTAIN: '#808080',   # Gray
    TileType.CAVE: '#2F4F4F',       # Dark slate
    TileType.VILLAGE: '#FFD700',    # Gold
    TileType.CASTLE: '#8B0000',     # Dark red
    TileType.SWAMP: '#556B2F',      # Dark olive
    TileType.RUINS: '#A0522D',      # Sienna
    TileType.TOWER: '#4B0082',      # Indigo
    TileType.LAKE: '#1E90FF',       # Dodger blue
    TileType.BRIDGE: '#8B4513',     # Saddle brown
    TileType.TAVERN: '#FF8C00',     # Dark orange
    TileType.TEMPLE: '#9932CC',     # Dark orchid
    TileType.DUNGEON: '#191970',    # Midnight blue
}


def generate_html_map(gen: WorldGenerator, highlight_path: list = None) -> str:
    """Generate HTML table visualization of the map"""
    grid = gen.geo_gen.wfc.to_tile_grid()
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Get plot locations
    plot_positions = set(gen.world.node_locations.values())

    # Path positions
    path_positions = set(highlight_path) if highlight_path else set()

    html = '<table style="border-collapse: collapse; font-family: monospace;">'

    for y in range(height):
        html += '<tr>'
        for x in range(width):
            tile_id = grid[y][x]
            tile_type = TileType(tile_id)
            color = TILE_COLORS.get(tile_type, '#FFFFFF')
            char = TILE_CHARS.get(tile_type, '?')

            # Check if this is a plot location
            is_plot = (x, y) in plot_positions
            is_path = (x, y) in path_positions

            # Style
            border = '2px solid red' if is_plot else '1px solid #333'
            bg = '#FFFF00' if is_path and not is_plot else color
            font_weight = 'bold' if is_plot else 'normal'
            font_size = '16px' if is_plot else '14px'

            html += f'''<td style="
                width: 20px; height: 20px;
                background-color: {bg};
                border: {border};
                text-align: center;
                color: white;
                text-shadow: 1px 1px 1px black;
                font-weight: {font_weight};
                font-size: {font_size};
            ">{char if not is_plot else "@"}</td>'''
        html += '</tr>'

    html += '</table>'
    return html


def generate_plot_graph_html(gen: WorldGenerator) -> str:
    """Generate HTML visualization of plot structure"""
    # Check for advanced plot first, then simple plot
    is_advanced = gen.world.advanced_plot is not None
    plot = gen.world.advanced_plot if is_advanced else gen.world.plot

    if not plot:
        return "<p>No plot generated</p>"

    order = plot.topological_sort()
    node_map = {n.id: n for n in plot.nodes}

    # Choose correct propp names
    propp_names = ADV_PROPP_NAMES if is_advanced else PROPP_NAMES

    html = '<div style="font-family: sans-serif;">'

    # Plot metadata
    if is_advanced:
        html += f'<h4>Plot: {gen.world.plot_type.name}</h4>'
        if gen.world.genre:
            html += f'<p style="color: #666; margin: 0;">Genre: {gen.world.genre.name}</p>'
        if gen.world.has_twist:
            twist_name = gen.world.twist_type.name if gen.world.twist_type else "Unknown"
            html += f'<p style="color: #9932CC; margin: 0;">Twist: {twist_name}</p>'
        if gen.world.has_false_ending:
            html += '<p style="color: #FF6347; margin: 0;">Has False Ending</p>'
        html += '<hr style="margin: 10px 0;">'
    else:
        html += '<h4>Plot Sequence (Simple)</h4>'

    # Color by function type (expanded for 16 functions)
    colors = {
        # Simple plot functions
        ProppFunction.LACK: '#FF6B6B',
        ProppFunction.DEPARTURE: '#4ECDC4',
        ProppFunction.DONOR_TEST: '#45B7D1',
        ProppFunction.ACQUISITION: '#96CEB4',
        ProppFunction.GUIDANCE: '#FFEAA7',
        ProppFunction.STRUGGLE: '#DDA0DD',
        ProppFunction.VICTORY: '#98D8C8',
        ProppFunction.RETURN: '#F7DC6F',
    }

    # Advanced plot colors (16 functions)
    adv_colors = {
        ProppFunc.EQUILIBRIUM: '#87CEEB',
        ProppFunc.LACK: '#FF6B6B',
        ProppFunc.INTERDICTION: '#FFB347',
        ProppFunc.VIOLATION: '#FF7F7F',
        ProppFunc.DEPARTURE: '#4ECDC4',
        ProppFunc.DONOR_TEST: '#45B7D1',
        ProppFunc.ACQUISITION: '#96CEB4',
        ProppFunc.GUIDANCE: '#FFEAA7',
        ProppFunc.STRUGGLE: '#DDA0DD',
        ProppFunc.BRANDING: '#9370DB',
        ProppFunc.VICTORY: '#98D8C8',
        ProppFunc.PURSUIT: '#FF8C00',
        ProppFunc.RESCUE: '#98FB98',
        ProppFunc.RECOGNITION: '#DEB887',
        ProppFunc.PUNISHMENT: '#CD5C5C',
        ProppFunc.RETURN: '#F7DC6F',
    }

    for i, node_id in enumerate(order):
        node = node_map.get(node_id)
        if not node:
            continue
        pos = gen.world.node_locations.get(node_id, "?")

        # Choose color based on plot type
        if is_advanced:
            color = adv_colors.get(node.function, '#CCCCCC')
        else:
            color = colors.get(node.function, '#CCCCCC')

        # Special styling for twists and false endings
        border_color = '#333'
        extra_markers = []

        if is_advanced:
            if hasattr(node, 'is_twist') and node.is_twist:
                border_color = '#9932CC'
                extra_markers.append('TWIST')
            if hasattr(node, 'twist_type') and node.twist_type and node.twist_type != TwistType.NONE:
                border_color = '#9932CC'
                extra_markers.append(f'TWIST: {node.twist_type.name}')
            if hasattr(node, 'is_false_ending') and node.is_false_ending:
                border_color = '#FF6347'
                extra_markers.append('FALSE ENDING')
            if hasattr(node, 'is_ending') and node.is_ending:
                extra_markers.append('ENDING')

        func_name = propp_names.get(node.function, str(node.function))

        html += f'''
        <div style="
            background: {color};
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid {border_color};
        ">
            <strong>{i+1}. {func_name}</strong>
            <span style="float: right; font-size: 12px;">@ {pos}</span>
            <br>
            <span style="font-size: 13px;">{node.description}</span>
            <br>
            <span style="font-size: 11px; color: #555;">Location: {getattr(node, "location_hint", "") or getattr(node, "location", "")}</span>
        '''

        # Show extra markers
        if extra_markers:
            markers_html = ' '.join([f'<span style="background: {border_color}; color: white; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-left: 5px;">{m}</span>' for m in extra_markers])
            html += f'<br>{markers_html}'

        # Show twist reveal
        if is_advanced and hasattr(node, 'twist_reveals') and node.twist_reveals:
            html += f'<br><span style="font-size: 11px; color: #9932CC;">Reveals: {node.twist_reveals}</span>'

        # Show false ending reveal
        if is_advanced and hasattr(node, 'false_ending_reveal') and node.false_ending_reveal:
            html += f'<br><span style="font-size: 11px; color: #FF6347;">But then: {node.false_ending_reveal}</span>'

        html += '</div>'

        if i < len(order) - 1:
            html += '<div style="text-align: center; color: #666;">↓</div>'

    html += '</div>'
    return html


# =============================================================================
# Fractal Plot Visualization
# =============================================================================

# Colors for narrative levels
LEVEL_COLORS = {
    NarrativeLevel.MEGA: '#8B0000',    # Dark red - epic saga
    NarrativeLevel.MACRO: '#4B0082',   # Indigo - main arc
    NarrativeLevel.MESO: '#2F4F4F',    # Dark slate - chapter
    NarrativeLevel.MICRO: '#228B22',   # Forest green - scene
    NarrativeLevel.NANO: '#4682B4',    # Steel blue - beat
}


def generate_fractal_node_html(node: FractalPlotNode, depth: int = 0, index: int = 0, cast_system=None) -> str:
    """Generate HTML for a single fractal node with its sub-plot"""
    level_name = LEVEL_NAMES.get(node.level, str(node.level))
    level_color = LEVEL_COLORS.get(node.level, '#666')
    func_name = ADV_PROPP_NAMES.get(node.function, str(node.function))

    # Indentation based on depth
    margin = depth * 20

    # Node styling
    has_children = node.has_sub_plot()
    expand_icon = "▼" if has_children else "●"

    # Get roles involved in this Propp function
    role_involvement = PROPP_ROLE_INVOLVEMENT.get(node.function, {})
    role_icons_html = ''
    if role_involvement:
        role_icons_html = '<span style="float: right; margin-left: 8px;">'
        for role, desc in role_involvement.items():
            icon = ROLE_ICONS.get(role, '❓')
            color = ROLE_COLORS.get(role, '#666')
            role_icons_html += f'<span title="{role.name}: {desc}" style="cursor: help; margin-left: 2px; filter: drop-shadow(0 0 1px {color});">{icon}</span>'
        role_icons_html += '</span>'

    html = f'''
    <div style="margin-left: {margin}px; margin-bottom: 8px;">
        <div style="
            background: linear-gradient(135deg, {level_color}22, {level_color}44);
            border-left: 4px solid {level_color};
            padding: 10px;
            border-radius: 5px;
            cursor: {'pointer' if has_children else 'default'};
        " class="fractal-node">
            <span style="color: {level_color}; font-weight: bold;">{expand_icon} [{level_name}]</span>
            <strong style="margin-left: 8px;">{func_name}</strong>
            {role_icons_html}
            <br>
            <span style="font-size: 13px; color: #333;">{node.description[:60]}{"..." if len(node.description) > 60 else ""}</span>
    '''

    # Show twist/ending markers
    markers = []
    if node.is_ending:
        markers.append(('ENDING', '#98D8C8'))
    if node.is_false_ending:
        markers.append(('FALSE ENDING', '#FF6347'))
    if node.twist_type and node.twist_type != TwistType.NONE:
        markers.append((f'TWIST: {node.twist_type.name}', '#9932CC'))

    if markers:
        html += '<br>'
        for marker_text, marker_color in markers:
            html += f'<span style="background: {marker_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-right: 5px;">{marker_text}</span>'

    html += '</div>'

    # Recursively add sub-plot nodes using edges for branching
    if has_children:
        html += '<div class="sub-plot" style="border-left: 2px dashed #ccc; margin-left: 10px; padding-left: 5px;">'
        html += render_subplot_with_branches(node.sub_plot, depth + 1)
        html += '</div>'

    html += '</div>'
    return html


def render_subplot_with_branches(subplot: FractalPlot, depth: int = 0) -> str:
    """Render a sub-plot with proper branching visualization"""
    if not subplot or not subplot.nodes:
        return ""

    rendered = set()

    def render_from_node(node_id: int) -> str:
        if node_id in rendered or node_id >= len(subplot.nodes):
            return ""
        rendered.add(node_id)

        node = subplot.nodes[node_id]
        result = generate_fractal_node_html(node, depth, node_id)

        successors = subplot.edges.get(node_id, [])

        if len(successors) == 0:
            # Ending node
            pass
        elif len(successors) == 1:
            # Linear
            result += f'<div style="margin-left: {depth * 20}px; color: #999; font-size: 12px;">↓</div>'
            result += render_from_node(successors[0])
        else:
            # BRANCHING
            result += f'''
            <div style="margin-left: {depth * 20}px; text-align: center; color: #9932CC; font-size: 11px; margin: 8px 0; font-weight: bold;">
                ↓ BRANCHES ({len(successors)} paths) ↓
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; margin-left: {depth * 20}px;">
            '''
            for i, succ_id in enumerate(successors):
                branch_color = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'][i % 4]
                result += f'''
                <div style="flex: 1; min-width: 180px; border: 2px solid {branch_color}; border-radius: 6px; padding: 8px; background: {branch_color}11;">
                    <div style="color: {branch_color}; font-weight: bold; font-size: 11px; margin-bottom: 4px;">Path {i + 1}</div>
                '''
                result += render_from_node(succ_id)
                result += '</div>'
            result += '</div>'

        return result

    # Find root nodes (no incoming edges)
    incoming = {i: 0 for i in range(len(subplot.nodes))}
    for from_id, to_list in subplot.edges.items():
        for to_id in to_list:
            incoming[to_id] = incoming.get(to_id, 0) + 1

    roots = [i for i in range(len(subplot.nodes)) if incoming.get(i, 0) == 0]
    if not roots:
        roots = [0] if subplot.nodes else []

    html = ""
    for root_id in roots:
        html += render_from_node(root_id)

    return html


def generate_fractal_plot_html(plot: FractalPlot, include_export: bool = True) -> str:
    """Generate HTML visualization of fractal plot structure with branching support"""
    if not plot or not plot.nodes:
        return "<p>No fractal plot generated</p>"

    # Embed JSON data for export
    import json
    json_data = json.dumps(plot.to_dict(), indent=2, ensure_ascii=False)
    # Escape for embedding in HTML
    json_escaped = json_data.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

    html = '<div style="font-family: sans-serif;">'

    # Add export button if requested
    if include_export:
        html += f'''
        <div style="margin-bottom: 15px;">
            <button onclick="exportToJSON()" style="
                background: #4CAF50; color: white; border: none;
                padding: 10px 20px; cursor: pointer; border-radius: 5px;
                font-size: 14px; margin-right: 10px;
            ">📥 Export JSON</button>
            <button onclick="copyToClipboard()" style="
                background: #2196F3; color: white; border: none;
                padding: 10px 20px; cursor: pointer; border-radius: 5px;
                font-size: 14px;
            ">📋 Copy JSON</button>
        </div>
        <script>
            const plotJSON = `{json_escaped}`;

            function exportToJSON() {{
                const blob = new Blob([plotJSON], {{type: 'application/json'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'fractal_plot.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}

            function copyToClipboard() {{
                navigator.clipboard.writeText(plotJSON).then(() => {{
                    alert('JSON copied to clipboard!');
                }}).catch(err => {{
                    console.error('Failed to copy:', err);
                    // Fallback
                    const textarea = document.createElement('textarea');
                    textarea.value = plotJSON;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    alert('JSON copied to clipboard!');
                }});
            }}
        </script>
        '''

    # Plot metadata
    level_name = LEVEL_NAMES.get(plot.level, str(plot.level))
    html += f'<h4>Fractal Plot: {level_name} Level</h4>'
    if plot.genre:
        html += f'<p style="color: #666; margin: 0;">Genre: {plot.genre.name}</p>'
    if plot.title:
        html += f'<p style="color: #333; margin: 0;"><em>{plot.title}</em></p>'

    # Ending Mode display
    ending_info = ENDING_MODES.get(plot.ending_mode, {})
    ending_color = ending_info.get("color", "#666")
    html += f'''
    <div style="background: {ending_color}22; border-left: 4px solid {ending_color};
                padding: 8px 12px; margin: 10px 0; border-radius: 0 5px 5px 0;">
        <strong style="color: {ending_color};">🎭 {ending_info.get("name", "?")} ({ending_info.get("greek", "")})</strong>
        <br><span style="font-size: 12px; color: #555;">{ending_info.get("emotion", "")}</span>
    </div>
    '''

    # Stats
    total_edges = sum(len(targets) for targets in plot.edges.values())
    has_branching = any(len(targets) > 1 for targets in plot.edges.values())

    html += f'''
    <div style="background: #f5f5f5; padding: 8px; border-radius: 5px; margin: 10px 0; font-size: 12px;">
        <span style="margin-right: 15px;">📊 Total Nodes: {plot.get_total_node_count()}</span>
        <span style="margin-right: 15px;">📐 Max Depth: {plot.get_max_depth()}</span>
        <span style="margin-right: 15px;">🔗 Edges: {total_edges}</span>
        {'<span style="color: #9932CC;">🌿 Branching</span>' if has_branching else '<span style="color: #666;">📏 Linear</span>'}
    </div>
    '''

    # Level legend
    html += '<div style="margin-bottom: 15px;">'
    for level in reversed(NarrativeLevel):
        color = LEVEL_COLORS.get(level, '#666')
        name = LEVEL_NAMES.get(level, str(level))
        html += f'<span style="background: {color}22; border-left: 3px solid {color}; padding: 2px 8px; margin-right: 8px; font-size: 11px;">{name}</span>'
    html += '</div>'

    html += '<hr style="margin: 10px 0;">'

    # Render using topological order with branching visualization
    order = plot.topological_sort()
    if not order:
        order = list(range(len(plot.nodes)))

    rendered = set()

    def render_with_branches(node_id: int, depth: int = 0) -> str:
        if node_id in rendered or node_id >= len(plot.nodes):
            return ""
        rendered.add(node_id)

        node = plot.nodes[node_id]
        result = generate_fractal_node_html(node, depth, node_id)

        # Get successors
        successors = plot.edges.get(node_id, [])

        if len(successors) == 0:
            # No successors - this is an ending
            pass
        elif len(successors) == 1:
            # Linear continuation
            result += '<div style="text-align: center; color: #666; font-size: 14px; margin: 5px 0;">↓</div>'
            result += render_with_branches(successors[0], depth)
        else:
            # BRANCHING! Show multiple paths
            result += f'''
            <div style="text-align: center; color: #9932CC; font-size: 12px; margin: 10px 0; font-weight: bold;">
                ↓ BRANCHES ({len(successors)} paths) ↓
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0;">
            '''
            for i, succ_id in enumerate(successors):
                branch_color = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'][i % 4]
                result += f'''
                <div style="flex: 1; min-width: 200px; border: 2px solid {branch_color}; border-radius: 8px; padding: 10px; background: {branch_color}11;">
                    <div style="color: {branch_color}; font-weight: bold; margin-bottom: 5px;">Branch {i + 1}</div>
                '''
                result += render_with_branches(succ_id, depth)
                result += '</div>'
            result += '</div>'

        return result

    # Find root nodes (nodes with no incoming edges)
    incoming = {i: 0 for i in range(len(plot.nodes))}
    for from_id, to_list in plot.edges.items():
        for to_id in to_list:
            incoming[to_id] = incoming.get(to_id, 0) + 1

    roots = [i for i in range(len(plot.nodes)) if incoming.get(i, 0) == 0]
    if not roots:
        roots = [0] if plot.nodes else []

    for root_id in roots:
        html += render_with_branches(root_id, 0)

    html += '</div>'
    return html


# =============================================================================
# Cast Panel - Character Roles Visualization
# =============================================================================

# Colors for different actant roles
ROLE_COLORS = {
    ActantRole.SUBJECT: '#FFD700',      # Gold - hero
    ActantRole.MENTOR: '#9370DB',       # Purple - wise
    ActantRole.HELPER: '#32CD32',       # Green - ally
    ActantRole.OPPONENT: '#DC143C',     # Crimson - enemy
    ActantRole.SHADOW: '#2F2F2F',       # Dark - dark side
    ActantRole.SENDER: '#4169E1',       # Royal blue - quest giver
    ActantRole.RECEIVER: '#20B2AA',     # Light sea green - beneficiary
    ActantRole.TRICKSTER: '#FF8C00',    # Orange - unpredictable
    ActantRole.THRESHOLD_GUARDIAN: '#8B4513',  # Brown - guardian
}

ROLE_ICONS = {
    ActantRole.SUBJECT: '⚔️',
    ActantRole.MENTOR: '🧙',
    ActantRole.HELPER: '🤝',
    ActantRole.OPPONENT: '👹',
    ActantRole.SHADOW: '🌑',
    ActantRole.SENDER: '👑',
    ActantRole.RECEIVER: '🙏',
    ActantRole.TRICKSTER: '🎭',
    ActantRole.THRESHOLD_GUARDIAN: '🚪',
    ActantRole.NONE: '❓',
}


def generate_cast_panel_html(cast_system) -> str:
    """Generate HTML for the cast panel showing character roles"""
    if not cast_system:
        return "<p>No cast generated</p>"

    html = '<div style="font-family: sans-serif;">'
    html += '<h4>🎭 Cast of Characters</h4>'

    # Get all NPCs and their roles
    role_system = cast_system.role_system

    # Group by primary role
    role_groups = {}
    for npc_name, fractal_role in role_system.npc_roles.items():
        # Get the highest-level role
        primary_role = (fractal_role.macro_role or
                       fractal_role.meso_role or
                       fractal_role.micro_role or
                       ActantRole.NONE)
        if primary_role not in role_groups:
            role_groups[primary_role] = []
        role_groups[primary_role].append((npc_name, fractal_role))

    # Display by role category
    role_order = [
        ActantRole.MENTOR, ActantRole.HELPER, ActantRole.SENDER,
        ActantRole.THRESHOLD_GUARDIAN, ActantRole.TRICKSTER,
        ActantRole.OPPONENT, ActantRole.SHADOW, ActantRole.RECEIVER,
    ]

    for role in role_order:
        if role not in role_groups:
            continue

        color = ROLE_COLORS.get(role, '#666')
        icon = ROLE_ICONS.get(role, '❓')

        html += f'''
        <div style="margin-bottom: 15px;">
            <div style="background: {color}22; border-left: 4px solid {color};
                        padding: 8px 12px; font-weight: bold; color: {color};">
                {icon} {role.name}
            </div>
        '''

        for npc_name, fractal_role in role_groups[role]:
            # Show all levels for this character
            levels_html = ''
            for level_name, level_attr in [
                ('MEGA', 'mega_role'),
                ('MACRO', 'macro_role'),
                ('MESO', 'meso_role'),
                ('MICRO', 'micro_role'),
            ]:
                level_role = getattr(fractal_role, level_attr)
                if level_role:
                    level_color = ROLE_COLORS.get(level_role, '#666')
                    level_icon = ROLE_ICONS.get(level_role, '❓')
                    # Highlight if different from primary (dual role!)
                    is_conflict = level_role != role
                    border = f'2px solid {level_color}' if is_conflict else 'none'
                    levels_html += f'''
                    <span style="background: {level_color}22; color: {level_color};
                                 padding: 2px 6px; margin: 2px; border-radius: 3px;
                                 font-size: 11px; border: {border};"
                          title="{level_name}: {level_role.name}">
                        {level_icon} {level_name}
                    </span>
                    '''

            # Check for transitions
            transitions_html = ''
            if fractal_role.transitions:
                for t in fractal_role.transitions:
                    t_from_icon = ROLE_ICONS.get(t.from_role, '?')
                    t_to_icon = ROLE_ICONS.get(t.to_role, '?')
                    transitions_html += f'''
                    <span style="font-size: 10px; color: #9932CC; margin-left: 10px;"
                          title="Transition: {t.trigger}">
                        ⚡ {t_from_icon}→{t_to_icon} on "{t.trigger}"
                    </span>
                    '''

            html += f'''
            <div style="padding: 8px 12px; border-bottom: 1px solid #eee;">
                <strong>{npc_name}</strong>
                {transitions_html}
                <div style="margin-top: 5px;">
                    {levels_html}
                </div>
            </div>
            '''

        html += '</div>'

    # Plot-triggered transitions section
    html += '''
    <div style="margin-top: 20px; border-top: 2px solid #eee; padding-top: 15px;">
        <h5 style="color: #9932CC; margin-bottom: 10px;">⚡ Plot-Triggered Transitions</h5>
        <p style="font-size: 11px; color: #666; margin-bottom: 10px;">
            When these Propp functions occur, roles may shift:
        </p>
    '''

    for propp_func, transitions in PLOT_TRIGGERED_TRANSITIONS.items():
        func_name = ADV_PROPP_NAMES.get(propp_func, str(propp_func))
        html += f'''
        <div style="background: #f8f4ff; padding: 8px; margin: 5px 0; border-radius: 4px;">
            <strong style="color: #9932CC;">{func_name}</strong>
            <div style="margin-top: 5px;">
        '''
        for trigger_name, from_role, to_role in transitions:
            from_icon = ROLE_ICONS.get(from_role, '❓')
            to_icon = ROLE_ICONS.get(to_role, '❓')
            from_color = ROLE_COLORS.get(from_role, '#666')
            to_color = ROLE_COLORS.get(to_role, '#666')
            html += f'''
            <span style="display: inline-block; margin: 2px 8px 2px 0; font-size: 12px;">
                <span style="color: {from_color};">{from_icon} {from_role.name}</span>
                <span style="color: #999;">→</span>
                <span style="color: {to_color};">{to_icon} {to_role.name}</span>
                <span style="font-size: 10px; color: #666;">({trigger_name})</span>
            </span>
            '''
        html += '</div></div>'

    html += '</div>'

    # Show legend for dual roles
    html += '''
    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;
                margin-top: 15px; font-size: 11px;">
        <strong>Legend:</strong><br>
        📍 Roles shown at each narrative level (MEGA → MICRO)<br>
        🔲 Bordered = <em>Dual Role</em> (different from primary)<br>
        ⚡ = Role transition trigger
    </div>
    '''

    html += '</div>'
    return html


def generate_weather_panel_html(weather: WeatherState) -> str:
    """Generate HTML for the weather panel"""
    if not weather:
        return "<p>No weather generated</p>"

    weather_info = WEATHER_INFO.get(weather.weather, {})
    time_info = TIME_OF_DAY_INFO.get(weather.time_of_day, {})
    season_info = SEASON_INFO.get(weather.season, {})
    climate_info = CLIMATE_INFO.get(weather.climate, {})

    # Temperature color gradient (cold blue to hot red)
    temp = weather.get_effective_temperature()
    if temp < -0.3:
        temp_color = "#00BFFF"  # Cold
        temp_name = "Freezing"
    elif temp < 0.0:
        temp_color = "#87CEEB"  # Cool
        temp_name = "Cold"
    elif temp < 0.3:
        temp_color = "#98FB98"  # Mild
        temp_name = "Mild"
    elif temp < 0.6:
        temp_color = "#FFD700"  # Warm
        temp_name = "Warm"
    else:
        temp_color = "#FF6347"  # Hot
        temp_name = "Hot"

    html = f'''
    <div style="font-family: sans-serif; background: linear-gradient(180deg,
               {time_info.get("color", "#87CEEB")}22,
               {weather_info.get("color", "#87CEEB")}44);
               padding: 15px; border-radius: 10px;">

        <h4 style="margin: 0 0 10px 0;">
            {weather_info.get("icon", "☀️")} {weather_info.get("name", "?")}
            <span style="float: right; font-size: 0.8em;">
                {time_info.get("icon", "")} {time_info.get("name", "?")}
            </span>
        </h4>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="background: white; padding: 8px; border-radius: 5px; text-align: center;">
                <div style="font-size: 24px;">{season_info.get("icon", "")}</div>
                <div style="font-size: 12px; color: #666;">{season_info.get("name", "?")}</div>
            </div>
            <div style="background: white; padding: 8px; border-radius: 5px; text-align: center;">
                <div style="font-size: 24px;">{climate_info.get("icon", "")}</div>
                <div style="font-size: 12px; color: #666;">{climate_info.get("name", "?")}</div>
            </div>
        </div>

        <div style="background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>🌡️ Temperature</span>
                <span style="background: {temp_color}; color: white; padding: 2px 8px;
                             border-radius: 10px; font-size: 12px;">{temp_name}</span>
            </div>
            <div style="height: 6px; background: linear-gradient(90deg, #00BFFF, #98FB98, #FFD700, #FF6347);
                        border-radius: 3px; margin-top: 5px;">
                <div style="width: 8px; height: 8px; background: #333; border-radius: 50%;
                            margin-top: -1px; margin-left: {(temp + 1) / 2 * 100}%;"></div>
            </div>
        </div>

        <div style="background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span>👁️ Visibility</span>
                <span>{weather.get_effective_visibility():.0%}</span>
            </div>
            <div style="height: 4px; background: #eee; border-radius: 2px; margin-top: 5px;">
                <div style="width: {weather.get_effective_visibility() * 100}%; height: 100%;
                            background: #4CAF50; border-radius: 2px;"></div>
            </div>
        </div>

        <div style="background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span>💨 Wind</span>
                <span>{weather.wind_direction} @ {weather.wind_speed:.0%}</span>
            </div>
        </div>

        <div style="background: {weather_info.get("color", "#87CEEB")}33; padding: 10px;
                    border-radius: 5px; font-style: italic; font-size: 13px;">
            {weather.get_description()}
        </div>

        <div style="margin-top: 10px; text-align: center;">
            <span style="background: #9932CC22; color: #9932CC; padding: 4px 10px;
                        border-radius: 15px; font-size: 12px;">
                Mood: {weather.get_mood()}
            </span>
        </div>
    '''

    # Phenomenon
    if weather.phenomenon and weather.phenomenon != AtmosphericPhenomenon.NONE:
        from wfc.weather import PHENOMENON_INFO
        phenom_info = PHENOMENON_INFO.get(weather.phenomenon, {})
        html += f'''
        <div style="margin-top: 10px; background: linear-gradient(90deg, #9932CC44, #FF69B444);
                    padding: 10px; border-radius: 5px; text-align: center;">
            <span style="font-size: 20px;">{phenom_info.get("icon", "✨")}</span>
            <strong>{phenom_info.get("name", "?")}</strong>
            <div style="font-size: 12px; margin-top: 5px;">{phenom_info.get("description", "")}</div>
        </div>
        '''

    html += '</div>'
    return html


def run_fractal_plot_tab():
    """Fractal plot generation and visualization tab"""
    st.header("🌳 Fractal Plot Generator")
    st.caption("Generate nested narrative structures with sub-plots at different levels")

    # Sidebar controls
    st.sidebar.header("Fractal Plot Settings")

    # Genre
    genre_names = list(GENRES.keys())
    selected_genre = st.sidebar.selectbox(
        "Genre",
        genre_names,
        index=0,
        key="fractal_genre"
    )

    # Starting level
    level_options = {
        "Saga (MEGA)": NarrativeLevel.MEGA,
        "Arc (MACRO)": NarrativeLevel.MACRO,
        "Chapter (MESO)": NarrativeLevel.MESO,
    }
    selected_level = st.sidebar.selectbox(
        "Starting Level",
        list(level_options.keys()),
        index=1,  # Default to MACRO
        key="fractal_level"
    )
    target_level = level_options[selected_level]

    # Depth
    depth = st.sidebar.slider("Decomposition Depth", 1, 4, 2, key="fractal_depth")

    # Branching
    enable_branching = st.sidebar.checkbox(
        "Enable Branching",
        value=True,
        key="fractal_branching",
        help="Allow branching paths in the narrative"
    )
    branching_chance = st.sidebar.slider(
        "Branching Chance",
        0.0, 1.0, 0.4,
        key="fractal_branch_chance",
        disabled=not enable_branching,
        help="Probability of creating branches at decision points"
    )

    # Finale type
    finale_options = {
        "Victory": ProppFunc.VICTORY,
        "Rescue": ProppFunc.RESCUE,
        "Recognition": ProppFunc.RECOGNITION,
        "Acquisition": ProppFunc.ACQUISITION,
    }
    selected_finale = st.sidebar.selectbox(
        "Finale Type",
        list(finale_options.keys()),
        index=0,
        key="fractal_finale"
    )
    finale = finale_options[selected_finale]

    # Ending Mode selector
    st.sidebar.subheader("Ending Mode")
    ending_mode_options = {
        f"{data['name']} ({data['greek']})": mode
        for mode, data in ENDING_MODES.items()
    }
    ending_mode_options = {"(auto - based on finale)": None, **ending_mode_options}
    selected_ending = st.sidebar.selectbox(
        "Emotional Resolution",
        list(ending_mode_options.keys()),
        index=0,
        key="fractal_ending_mode",
        help="The emotional state at the story's conclusion"
    )
    ending_mode = ending_mode_options[selected_ending]

    # Show ending mode info
    if ending_mode is not None:
        info = ENDING_MODES[ending_mode]
        st.sidebar.markdown(
            f'<div style="background: {info["color"]}22; border-left: 3px solid {info["color"]}; '
            f'padding: 5px 10px; font-size: 12px;">{info["emotion"]}</div>',
            unsafe_allow_html=True
        )

    # Seed
    seed = st.sidebar.number_input("Seed", 0, 999999, 42, key="fractal_seed")

    if st.sidebar.button("🎲 Random Seed", key="fractal_random"):
        seed = random.randint(0, 999999)
        st.sidebar.write(f"New seed: {seed}")

    generate_btn = st.sidebar.button("🌳 Generate Fractal Plot", type="primary", key="fractal_generate_btn")

    # State (use different names than widget keys!)
    if 'fplot_data' not in st.session_state:
        st.session_state.fplot_data = None
        st.session_state.fplot_generator = None

    if generate_btn:
        with st.spinner("Generating fractal plot..."):
            genre = GENRES[selected_genre]
            gen = FractalPlotGenerator(
                genre=genre,
                seed=seed,
                branching_chance=branching_chance if enable_branching else 0.0
            )
            if gen.generate(
                target_level=target_level,
                depth=depth,
                finale=finale,
                branching=enable_branching,
                ending_mode=ending_mode
            ):
                st.session_state.fplot_generator = gen
                st.session_state.fplot_data = gen.plot
            else:
                st.error("Failed to generate fractal plot!")

    # Display
    if st.session_state.fplot_data:
        plot = st.session_state.fplot_data
        gen = st.session_state.fplot_generator

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Plot Structure")
            plot_html = generate_fractal_plot_html(plot)
            st.markdown(plot_html, unsafe_allow_html=True)

        with col2:
            st.subheader("Statistics")
            st.metric("Total Nodes", plot.get_total_node_count())
            st.metric("Max Depth", plot.get_max_depth())
            st.metric("Top Level", LEVEL_NAMES.get(plot.level, "?"))

            if gen and gen.genre:
                st.metric("Genre", gen.genre.name)

            # Level breakdown
            st.subheader("Level Breakdown")

            def count_by_level(p: FractalPlot) -> dict:
                counts = {level: 0 for level in NarrativeLevel}
                for node in p.nodes:
                    for flat_node in node.get_all_nodes_flat():
                        counts[flat_node.level] += 1
                return counts

            level_counts = count_by_level(plot)
            for level in reversed(NarrativeLevel):
                count = level_counts[level]
                if count > 0:
                    color = LEVEL_COLORS.get(level, '#666')
                    name = LEVEL_NAMES.get(level, str(level))
                    st.markdown(
                        f'<div style="background: {color}22; border-left: 3px solid {color}; '
                        f'padding: 5px 10px; margin: 3px 0;">{name}: {count}</div>',
                        unsafe_allow_html=True
                    )

        # Text summary
        with st.expander("📋 Text Summary"):
            if gen:
                st.text(gen.get_summary())
    else:
        # Show example
        st.info("Click 'Generate Fractal Plot' to create a nested narrative structure.")

        st.markdown("""
        ### About Fractal Plots

        Fractal plots implement nested narrative structures where each plot point can contain sub-plots:

        - **MEGA** (Saga): World-spanning epic events (rare)
        - **MACRO** (Arc): Main story quest (e.g., "Defeat the Dark Lord")
        - **MESO** (Chapter): Subplot/chapter (e.g., "Acquire the Magic Sword")
        - **MICRO** (Scene): Single encounter (e.g., "Convince the Blacksmith")
        - **NANO** (Beat): Single action/dialogue beat

        **Example Structure:**
        ```
        [Arc] VICTORY: Defeat the Dark Lord
          ├── [Chapter] ACQUISITION: Get the Magic Sword
          │     ├── [Scene] GUIDANCE: Find the Blacksmith
          │     ├── [Scene] DONOR_TEST: Prove Worthiness
          │     └── [Scene] ACQUISITION: Receive the Blade
          └── [Chapter] STRUGGLE: Confront Evil
                ├── [Scene] GUIDANCE: Journey to Dark Castle
                └── [Scene] STRUGGLE: Final Battle
        ```
        """)


def run_game_tab():
    """Interactive text adventure in Streamlit"""
    st.header("🎮 Play Adventure")

    from wfc.engine import GameEngine, TILE_DESCRIPTIONS

    # Initialize game state
    if 'game_engine' not in st.session_state:
        st.session_state.game_engine = None
        st.session_state.game_log = []

    # Game controls
    col1, col2 = st.columns([1, 3])

    with col1:
        game_seed = st.number_input("Game Seed", 0, 999999, 42, key="game_seed")
        if st.button("🎮 New Game"):
            engine = GameEngine()
            if engine.initialize(seed=game_seed, width=16, height=12):
                st.session_state.game_engine = engine
                st.session_state.game_log = []
                engine.describe_location()
                st.session_state.game_log.append(engine.get_output())
            else:
                st.error("Failed to generate world!")

    engine = st.session_state.game_engine

    if engine:
        with col2:
            # Direction buttons
            st.write("**Movement:**")
            bcol1, bcol2, bcol3, bcol4 = st.columns(4)
            with bcol1:
                if st.button("⬆️ North"):
                    engine.move('north')
                    st.session_state.game_log.append(engine.get_output())
            with bcol2:
                if st.button("⬇️ South"):
                    engine.move('south')
                    st.session_state.game_log.append(engine.get_output())
            with bcol3:
                if st.button("⬅️ West"):
                    engine.move('west')
                    st.session_state.game_log.append(engine.get_output())
            with bcol4:
                if st.button("➡️ East"):
                    engine.move('east')
                    st.session_state.game_log.append(engine.get_output())

        # Action buttons
        acol1, acol2, acol3, acol4 = st.columns(4)
        with acol1:
            if st.button("👁️ Look"):
                engine.describe_location()
                st.session_state.game_log.append(engine.get_output())
        with acol2:
            if st.button("⚔️ Interact"):
                engine.do_event()
                st.session_state.game_log.append(engine.get_output())
        with acol3:
            if st.button("🎒 Inventory"):
                engine.show_inventory()
                st.session_state.game_log.append(engine.get_output())
        with acol4:
            if st.button("📜 Quest"):
                engine.show_quest()
                st.session_state.game_log.append(engine.get_output())

        # Display area
        st.divider()

        gcol1, gcol2 = st.columns([2, 1])

        with gcol1:
            # Game log
            st.write("**Adventure Log:**")
            log_text = "\n\n---\n\n".join(st.session_state.game_log[-10:])
            st.markdown(f"```\n{log_text}\n```")

        with gcol2:
            # Mini map
            st.write("**Map:**")
            grid = engine.world_gen.geo_gen.wfc.to_tile_grid()
            map_lines = []
            for y in range(len(grid)):
                line = ""
                for x in range(len(grid[0])):
                    if (x, y) == (engine.player_x, engine.player_y):
                        line += "🔵"
                    elif (x, y) in engine.world_gen.world.node_locations.values():
                        event = engine._get_event_at_position(x, y)
                        if event and event.id in engine.completed_events:
                            line += "✅"
                        else:
                            line += "⭐"
                    elif (x, y) in engine.visited:
                        line += TILE_CHARS.get(TileType(grid[y][x]), '?')
                    else:
                        line += "·"
                map_lines.append(line)
            st.text("\n".join(map_lines))

            # Status
            st.write("**Status:**")
            st.write(f"Turns: {engine.turn_count}")
            st.write(f"Visited: {len(engine.visited)} locations")
            st.write(f"Quest: {len(engine.completed_events)}/{len(engine.world_gen.world.plot.nodes)}")

            if engine.inventory:
                st.write("**Inventory:**")
                for item in engine.inventory:
                    st.write(f"  • {item}")
    else:
        st.info("Click 'New Game' to start playing!")


def run_visualizer_tab():
    """World visualizer tab"""
    # Sidebar controls
    st.sidebar.header("Generation Settings")

    seed = st.sidebar.number_input("Seed", min_value=0, max_value=999999, value=42)
    width = st.sidebar.slider("Map Width", 10, 30, 20)
    height = st.sidebar.slider("Map Height", 8, 20, 12)

    # Plot Type selector
    st.sidebar.subheader("Plot Settings")
    plot_type_names = [pt.name for pt in PlotType]
    selected_plot_type = st.sidebar.selectbox(
        "Plot Type",
        plot_type_names,
        index=0,
        help="SIMPLE: Basic linear\nBRANCHING: Multiple branches\nWITH_TWIST: Plot twist\nFRACTAL: Nested sub-plots\nEPIC: Full 3-act"
    )
    plot_type = PlotType[selected_plot_type]

    # Genre selector with mixing support
    st.sidebar.subheader("🎨 Genre")

    # Categorize genres by mood for easier selection
    GENRE_CATEGORIES = {
        "☀️ Solar/Hopeful": ["solarpunk", "hopepunk", "fairytale", "cozy", "pastoral",
                            "iyashikei", "whimsical", "heartwarming", "luminous"],
        "🌱 Coming of Age": ["coming_of_age", "slice_of_life"],
        "⚔️ Epic/Adventure": ["fantasy", "mythic"],
        "🌑 Dark": ["dark_fantasy"],
        "🔍 Other": ["mystery"],
    }

    # Show mood categories with colored indicators
    mood_colors = {"hopeful": "🌞", "epic": "⚔️", "dark": "🌑", "mysterious": "🔮", "neutral": "⚪"}

    genre_mix_mode = st.sidebar.radio(
        "Genre Mode",
        ["Single Genre", "Mix Genres"],
        index=0,
        key="genre_mode",
        horizontal=True
    )

    genre = None
    mixed_genre = None

    if genre_mix_mode == "Single Genre":
        # Flat list with mood indicator
        genre_display = ["(default)"]
        for g_name, g_obj in GENRES.items():
            mood_icon = mood_colors.get(g_obj.mood, "⚪")
            genre_display.append(f"{mood_icon} {g_obj.name}")

        selected_idx = st.sidebar.selectbox(
            "Select Genre",
            range(len(genre_display)),
            format_func=lambda i: genre_display[i],
            index=0,
            key="single_genre"
        )

        if selected_idx > 0:
            genre = list(GENRES.keys())[selected_idx - 1]

        # Show genre info
        if genre and genre in GENRES:
            g = GENRES[genre]
            st.sidebar.markdown(
                f'<div style="background: {g.palette.get("primary", "#666")}22; '
                f'border-left: 3px solid {g.palette.get("primary", "#666")}; '
                f'padding: 5px 10px; font-size: 12px;">'
                f'<em>{g.description}</em></div>',
                unsafe_allow_html=True
            )
    else:
        # Multi-select for mixing
        st.sidebar.caption("Select 2-4 genres to blend together")

        available_genres = list(GENRES.keys())
        selected_genres = st.sidebar.multiselect(
            "Genres to Mix",
            available_genres,
            default=["fantasy", "solarpunk"],
            max_selections=4,
            format_func=lambda g: f"{mood_colors.get(GENRES[g].mood, '⚪')} {GENRES[g].name}",
            key="mix_genres"
        )

        if len(selected_genres) >= 2:
            # Weight sliders
            st.sidebar.caption("Adjust blend weights:")
            weights = []
            for g_name in selected_genres:
                w = st.sidebar.slider(
                    f"{GENRES[g_name].name}",
                    0.0, 1.0, 1.0 / len(selected_genres),
                    key=f"weight_{g_name}"
                )
                weights.append(w)

            # Normalize weights
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]

            # Create mixed genre
            mixed_genre = mix_genres(*selected_genres, weights=weights)

            # Show mixed result
            st.sidebar.markdown(
                f'<div style="background: {mixed_genre.palette.get("primary", "#666")}22; '
                f'border-left: 3px solid {mixed_genre.palette.get("primary", "#666")}; '
                f'padding: 5px 10px; font-size: 12px;">'
                f'<strong>{mixed_genre.name}</strong><br>'
                f'Mood: {mixed_genre.mood}</div>',
                unsafe_allow_html=True
            )
        elif len(selected_genres) == 1:
            genre = selected_genres[0]
            st.sidebar.warning("Select at least 2 genres to mix")

    # Fractal options (only show when FRACTAL selected)
    fractal_level = NarrativeLevel.MACRO
    fractal_depth = 2
    fractal_ending = None
    fractal_branching = True
    fractal_add_twist = False
    fractal_add_false_ending = False

    # Level complexity settings (used for fractal)
    level_complexity_override = None

    if plot_type == PlotType.FRACTAL:
        st.sidebar.subheader("🌳 Fractal Settings")

        level_options = {
            "Saga (MEGA)": NarrativeLevel.MEGA,
            "Arc (MACRO)": NarrativeLevel.MACRO,
            "Chapter (MESO)": NarrativeLevel.MESO,
        }
        fractal_level = level_options[st.sidebar.selectbox(
            "Narrative Level",
            list(level_options.keys()),
            index=1,
            key="world_fractal_level"
        )]

        fractal_depth = st.sidebar.slider("Depth", 1, 8, 2, key="world_fractal_depth")
        fractal_branching = st.sidebar.checkbox("Branching", value=True, key="world_fractal_branch")

        # Twist and False Ending options
        st.sidebar.markdown("**Plot Features:**")
        fractal_add_twist = st.sidebar.checkbox("Add Plot Twist", value=False, key="world_fractal_twist")
        fractal_add_false_ending = st.sidebar.checkbox("Add False Ending", value=False, key="world_fractal_false_ending")

        # Level complexity customization
        with st.sidebar.expander("📊 Complexity per Level"):
            st.caption("Set min-max nodes at each narrative level")

            # Get defaults from LEVEL_COMPLEXITY
            default_complexity = dict(LEVEL_COMPLEXITY)

            custom_mega = st.slider(
                "MEGA (Saga) → MACRO arcs",
                min_value=1, max_value=8,
                value=default_complexity[NarrativeLevel.MEGA],
                key="complexity_mega",
                help="How many major arcs in an epic saga"
            )
            custom_macro = st.slider(
                "MACRO (Arc) → MESO chapters",
                min_value=1, max_value=12,
                value=default_complexity[NarrativeLevel.MACRO],
                key="complexity_macro",
                help="How many chapters per story arc"
            )
            custom_meso = st.slider(
                "MESO (Chapter) → MICRO scenes",
                min_value=1, max_value=10,
                value=default_complexity[NarrativeLevel.MESO],
                key="complexity_meso",
                help="How many scenes per chapter"
            )
            custom_micro = st.slider(
                "MICRO (Scene) → NANO beats",
                min_value=0, max_value=6,
                value=default_complexity[NarrativeLevel.MICRO],
                key="complexity_micro",
                help="How many beats per scene"
            )

            # Build override dict
            level_complexity_override = {
                NarrativeLevel.MEGA: custom_mega,
                NarrativeLevel.MACRO: custom_macro,
                NarrativeLevel.MESO: custom_meso,
                NarrativeLevel.MICRO: custom_micro,
            }

        # Ending mode
        ending_options = {"(auto)": None}
        ending_options.update({
            f"{data['name']} ({data['greek']})": mode
            for mode, data in ENDING_MODES.items()
        })
        fractal_ending = ending_options[st.sidebar.selectbox(
            "Ending Mode",
            list(ending_options.keys()),
            index=0,
            key="world_fractal_ending"
        )]

    if st.sidebar.button("🎲 Random Seed"):
        seed = random.randint(0, 999999)
        st.sidebar.write(f"New seed: {seed}")

    generate_btn = st.sidebar.button("🌍 Generate World", type="primary")

    # Store state
    if 'world_gen' not in st.session_state:
        st.session_state.world_gen = None

    if generate_btn or st.session_state.world_gen is None:
        with st.spinner("Generating world..."):
            gen = WorldGenerator(width=width, height=height, seed=seed)

            # Use mixed genre if available, otherwise single genre
            effective_genre = mixed_genre if mixed_genre else genre

            success = gen.generate(
                plot_type=plot_type,
                genre=effective_genre,
                narrative_level=fractal_level,
                fractal_depth=fractal_depth,
                ending_mode=fractal_ending,
                branching=fractal_branching,
                level_complexity=level_complexity_override,
                add_twist=fractal_add_twist,
                add_false_ending=fractal_add_false_ending
            )
            if success:
                st.session_state.world_gen = gen
                st.session_state.seed = seed
            else:
                st.error("Generation failed! Try a different seed.")
                st.session_state.world_gen = None

    gen = st.session_state.world_gen

    if gen:
        # Main layout
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Geography Map")
            st.caption("@ = Plot locations, colored tiles = terrain")

            # Path visualization option
            show_path = st.checkbox("Show path between plot points")

            path = None
            if show_path and len(gen.world.node_locations) >= 2:
                # Get path through all plot points
                plot = gen.world.advanced_plot if gen.world.advanced_plot else gen.world.plot
                order = plot.topological_sort() if plot else []
                path = []
                for i in range(len(order) - 1):
                    from_id = order[i]
                    to_id = order[i + 1]
                    segment = gen.geo_gen.find_path_between(
                        f"plot_{from_id}", f"plot_{to_id}"
                    )
                    if segment:
                        path.extend(segment)

            map_html = generate_html_map(gen, path)
            st.markdown(map_html, unsafe_allow_html=True)

            # Legend
            st.subheader("Legend")
            legend_cols = st.columns(4)
            tiles_per_col = 4
            for i, tile in enumerate(TileType):
                col_idx = i // tiles_per_col
                if col_idx < 4:
                    with legend_cols[col_idx]:
                        color = TILE_COLORS.get(tile, '#CCC')
                        st.markdown(
                            f'<span style="background:{color}; color:white; '
                            f'padding:2px 6px; border-radius:3px;">'
                            f'{TILE_CHARS[tile]}</span> {tile.name}',
                            unsafe_allow_html=True
                        )

        with col2:
            st.subheader("Plot Structure")

            # Show fractal plot if available, else regular plot
            if gen.world.fractal_plot:
                plot_html = generate_fractal_plot_html(gen.world.fractal_plot)
                # Use components.html for complex HTML that st.markdown can't handle
                import streamlit.components.v1 as components
                # Calculate height based on node count
                node_count = gen.world.fractal_plot.get_total_node_count()
                height = min(800, max(400, node_count * 80))
                components.html(plot_html, height=height, scrolling=True)
            else:
                plot_html = generate_plot_graph_html(gen)
                st.markdown(plot_html, unsafe_allow_html=True)

            # Stats
            st.subheader("Statistics")
            valid, msg = gen.verify_completability()
            st.metric("Status", "✅ Completable" if valid else "❌ " + msg)
            st.metric("Plot Nodes", len(gen.world.get_plot_nodes()))
            st.metric("Generation Attempts", gen.world.attempts)

            # Fractal plot info
            if gen.world.fractal_plot:
                st.metric("Narrative Level", LEVEL_NAMES.get(gen.world.narrative_level, "?"))
                st.metric("Depth", gen.world.fractal_depth)
                if gen.world.ending_mode:
                    info = ENDING_MODES.get(gen.world.ending_mode, {})
                    st.metric("Ending Mode", info.get("name", "?"))

                # Export to JSON button (full world with cast + weather)
                st.subheader("Export")
                json_data = gen.world.to_json()
                st.download_button(
                    label="📥 Download World JSON",
                    data=json_data,
                    file_name=f"world_seed{seed}.json",
                    mime="application/json",
                    help="Includes plot, cast, and weather"
                )

                # Weather Panel
                if gen.world.weather:
                    st.subheader("🌤️ Weather")
                    weather_html = generate_weather_panel_html(gen.world.weather)
                    import streamlit.components.v1 as components
                    components.html(weather_html, height=380, scrolling=True)

                # Cast Panel - show character roles
                if gen.world.cast_system:
                    st.subheader("🎭 Cast")
                    cast_html = generate_cast_panel_html(gen.world.cast_system)
                    import streamlit.components.v1 as components
                    components.html(cast_html, height=400, scrolling=True)

            # Advanced plot info
            elif gen.world.advanced_plot:
                if gen.world.has_twist:
                    twist_name = gen.world.twist_type.name if gen.world.twist_type else "Unknown"
                    st.metric("Twist", twist_name)
                if gen.world.has_false_ending:
                    st.metric("False Endings", "Yes")
                endings = [n for n in gen.world.advanced_plot.nodes if hasattr(n, 'is_ending') and n.is_ending]
                if len(endings) > 1:
                    st.metric("Multiple Endings", len(endings))

            # Tile distribution
            st.subheader("Tile Distribution")
            stats = gen.geo_gen.get_tile_stats()
            for tile, count in sorted(stats.items(), key=lambda x: -x[1])[:8]:
                if count > 0:
                    st.progress(count / (width * height), text=f"{tile.name}: {count}")

        # Raw data expander
        with st.expander("📋 Raw Data"):
            st.text(gen.get_summary())


def main():
    st.set_page_config(
        page_title="Emergent Adventure",
        page_icon="🗺️",
        layout="wide"
    )

    st.title("🗺️ Emergent Adventure")

    # Tabs (Fractal Plot merged into World Visualizer)
    tab1, tab2 = st.tabs(["🗺️ World Visualizer", "🎮 Play Game"])

    with tab1:
        run_visualizer_tab()

    with tab2:
        run_game_tab()


if __name__ == "__main__":
    main()
