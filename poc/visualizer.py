"""
Emergent Adventure - Streamlit Visualizer

Interactive visualization of generated worlds.
Run with: streamlit run visualizer.py
"""

import streamlit as st
import random
from wfc import WorldGenerator, TileType, TILE_CHARS, ProppFunction
from wfc.plot import PROPP_NAMES

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
    if not gen.world.plot:
        return "<p>No plot generated</p>"

    order = gen.world.plot.topological_sort()

    html = '<div style="font-family: sans-serif;">'
    html += '<h4>Plot Sequence</h4>'

    for i, node_id in enumerate(order):
        node = gen.world.plot.nodes[node_id]
        pos = gen.world.node_locations.get(node_id, "?")

        # Color by function type
        colors = {
            ProppFunction.LACK: '#FF6B6B',
            ProppFunction.DEPARTURE: '#4ECDC4',
            ProppFunction.DONOR_TEST: '#45B7D1',
            ProppFunction.ACQUISITION: '#96CEB4',
            ProppFunction.GUIDANCE: '#FFEAA7',
            ProppFunction.STRUGGLE: '#DDA0DD',
            ProppFunction.VICTORY: '#98D8C8',
            ProppFunction.RETURN: '#F7DC6F',
        }
        color = colors.get(node.function, '#CCCCCC')

        html += f'''
        <div style="
            background: {color};
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid #333;
        ">
            <strong>{i+1}. {PROPP_NAMES[node.function]}</strong>
            <span style="float: right; font-size: 12px;">@ {pos}</span>
            <br>
            <span style="font-size: 13px;">{node.description}</span>
            <br>
            <span style="font-size: 11px; color: #555;">Location: {node.location_hint}</span>
        </div>
        '''

        if i < len(order) - 1:
            html += '<div style="text-align: center; color: #666;">↓</div>'

    html += '</div>'
    return html


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
            if gen.generate():
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
                order = gen.world.plot.topological_sort()
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
            plot_html = generate_plot_graph_html(gen)
            st.markdown(plot_html, unsafe_allow_html=True)

            # Stats
            st.subheader("Statistics")
            valid, msg = gen.verify_completability()
            st.metric("Status", "✅ Completable" if valid else "❌ " + msg)
            st.metric("Plot Nodes", len(gen.world.plot.nodes))
            st.metric("Generation Attempts", gen.world.attempts)

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

    # Tabs
    tab1, tab2 = st.tabs(["🗺️ World Visualizer", "🎮 Play Game"])

    with tab1:
        run_visualizer_tab()

    with tab2:
        run_game_tab()


if __name__ == "__main__":
    main()
