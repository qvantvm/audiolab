from __future__ import annotations

import audiolab.blocks  # noqa: F401
from audiolab.blocks.help import build_block_help, build_connection_help
from audiolab.graph.schema import BlockSpec, ConnectionSpec, GraphSpec


def test_soundboard_modal_bank_help_explains_modal_approximation():
    help_info = build_block_help("SoundboardModalBank")

    assert help_info is not None
    assert "vibrating wooden plate" in help_info.explanation_markdown
    assert "resonant filters" in help_info.explanation_markdown
    assert "not a solved plate model" in help_info.explanation_markdown


def test_connection_help_resolves_audio_port_kinds():
    graph = GraphSpec(
        name="help_test",
        blocks=[
            BlockSpec(id="osc", type="SineOscillator", params={}),
            BlockSpec(id="out", type="Output", params={}),
        ],
        connections=[
            ConnectionSpec.model_validate({"from": "osc.audio", "to": "out.audio"}),
        ],
    )

    help_text = build_connection_help(graph.connections[0], graph)

    assert "`osc.audio` -> `out.audio`" in help_text
    assert "audio" in help_text
    assert "Audio-rate buffer data" in help_text
