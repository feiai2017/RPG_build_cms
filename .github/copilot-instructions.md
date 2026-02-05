# Copilot instructions for this repo

## Big picture architecture
- Streamlit UI entry is unified_main_app.py; it initializes all core modules, applies performance optimization, and calls `render_unified_interface()`.
- `UnifiedStateManager` is the central data hub. It owns character data, bagua config, combat settings, and loot inventory, and pushes data into module views via `sync_modules()`.
- Core domain engines live as standalone modules and are orchestrated by the state manager:
  - wuxing_engine.py for 五行/八卦 calculations used by `_calculate_bagua_bonuses()`.
  - enhanced_combat_engine.py for combat simulation.
  - cultivation_school_system.py for schools/skills.
  - loot_generator.py for drop generation and BD optimization.
- Data flow is: UI → `UnifiedStateManager` → module states → UI renders; state consistency checks and status live in `get_system_status()`.

## Key files and patterns
- UI routing and page composition: unified_interface_modules.py (many `render_*` functions).
- Sidebar navigation and system tools: `render_unified_navigation()` in unified_main_app.py.
- Global singleton access pattern: `get_state_manager()` in unified_state_manager.py; do not instantiate new managers in UI code.
- Persistence: state is saved/loaded in .kiro/rpg_config/unified_state.json with backups in .kiro/rpg_config/backups.
- Config/data inputs live under configs/, presets/, and data.yaml; bagua/board assets under board/ and board_configs/.

## Developer workflows
- Run the unified UI (recommended): streamlit run unified_main_app.py
- Legacy entry points exist (app.py, app_five_elements.py) but the unified app is the integration target.
- Tests are pytest-based; property tests use Hypothesis (see test_*.py files).

## Project-specific conventions
- UI code uses Streamlit containers with `border=True` and emoji-labeled sections for consistent layout.
- New modules should add a `render_*` function in unified_interface_modules.py, then register in the sidebar radio options and the unified interface router.
- When computing combat stats, always route through `UnifiedStateManager` to apply bagua + school bonuses (see `_sync_to_combat()` and `_calculate_bagua_bonuses()`).

## Integration points
- `performance_optimizer.get_performance_optimizer().optimize_streamlit_performance()` is called during app init.
- `help_system`, `balance_system`, and `loot_generator` are globally initialized during startup and expected to be accessed via their factory functions.
