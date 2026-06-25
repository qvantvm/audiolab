# Block registry

The central registry lives in `src/audiolab/blocks/registry.py`. Blocks self-register via `@register_block` when their modules are imported (`audiolab.blocks`).

## API

```python
from audiolab.blocks.registry import (
    list_blocks,
    get_block_spec,
    validate_node,
    list_block_types,
    inspect_block,
    get_block_class,
)
```

| Function | Returns |
|----------|---------|
| `list_block_types()` | `list[str]` — sorted block type names |
| `list_blocks()` | `list[BlockTypeSpec]` — full metadata for all blocks |
| `get_block_spec(block_type)` | `BlockTypeSpec` for one type |
| `validate_node(node_dict)` | `list[NodeValidationError]` |
| `inspect_block(block_type)` | JSON-serializable dict (same as `BlockTypeSpec.to_dict()`) |
| `get_block_class(block_type)` | Python block class |

## BlockTypeSpec fields

- `block_type`, `category`, `legacy_category`, `description`
- `input_ports`, `output_ports` — `PortSpec` with kind, domain, variables, rate
- `parameters` — `ParameterSpec` with type, default, min, max, unit
- `deterministic`, `execution_mode` (`graph`, `analysis`, `task`, `event`)
- `pasp_classification` — `pasp_core`, `piano_specific`, `generic_dsp`, `legacy`, `experimental`, `analysis`, `calibration`
- `physical_role`, `interpretability_level`
- `reuse_as_is`, `needs_metadata`, `needs_refactor`

Metadata is built in `src/audiolab/blocks/metadata.py` from block class attributes plus PASP overrides.

## CLI

```bash
audiolab list-blocks
audiolab inspect-block PASPStringLine
```

## Graph validation integration

`validate_graph()` calls `validate_node()` for each block and uses `PortSpec` for physical compatibility checks.

## Block count

The generated current count is in [audiolab/blocks.md](audiolab/blocks.md), which is rebuilt from `BLOCK_REGISTRY`.

Categories used in migration metadata include: `signal`, `control`, `filter`, `delay/waveguide`, `piano-specific`, `physical mechanical`, `physical acoustic`, `modal/body`, `analysis`, `utility`, `output/rendering`.
