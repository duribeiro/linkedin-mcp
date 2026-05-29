"""Basic smoke tests for linkedin-mcp server and tools."""


def test_imports():
    """All core modules should be importable."""
    import server  # noqa: F401
    import auth  # noqa: F401
    from tools import articles, insights, posts  # noqa: F401


def test_server_has_tools():
    """Server should expose all expected MCP tools."""
    from server import TOOLS

    expected = {
        "get_my_profile",
        "create_post",
        "create_article",
        "get_my_articles",
        "get_share_stats",
        "get_my_feed",
    }
    assert set(TOOLS.keys()) == expected


def test_tool_handlers_match():
    """Every tool should have a matching handler."""
    from server import TOOLS, HANDLERS

    assert TOOLS.keys() == HANDLERS.keys()
