"""Confirm the Grok tool registry exposes the new options + crypto tools."""

from __future__ import annotations

from app.services.grok.tools import TOOLS, to_grok_tool_specs


NEW_TOOL_NAMES = ("get_option_chain", "get_crypto_bars", "get_crypto_quote")


def test_new_tools_registered_in_tools_dict():
    for name in NEW_TOOL_NAMES:
        assert name in TOOLS, f"{name} missing from TOOLS registry"


def test_to_grok_tool_specs_includes_new_tools():
    specs = to_grok_tool_specs()
    names = {spec["function"]["name"] for spec in specs}
    for name in NEW_TOOL_NAMES:
        assert name in names, f"{name} not exposed via to_grok_tool_specs()"


def test_new_tools_have_pydantic_arg_schemas():
    """Each new tool must have a Pydantic argument model with required fields."""
    schemas = {name: TOOLS[name].args_schema for name in NEW_TOOL_NAMES}
    chain_props = schemas["get_option_chain"].model_json_schema()["properties"]
    assert "underlying" in chain_props
    assert "expiration_date" in chain_props

    bars_props = schemas["get_crypto_bars"].model_json_schema()["properties"]
    for key in ("symbol", "timeframe", "lookback"):
        assert key in bars_props

    quote_props = schemas["get_crypto_quote"].model_json_schema()["properties"]
    assert "symbol" in quote_props
