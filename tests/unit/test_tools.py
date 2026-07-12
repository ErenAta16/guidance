import pytest

from guidance._tools import FunctionTool, Tool


def _make_tool(callable) -> Tool:
    def add(a: int, b: int) -> int:
        return a + b

    return Tool(
        name="add",
        description="add two numbers",
        tool=FunctionTool.from_callable(add),
        callable=callable,
    )


class TestToolCall:
    def test_normal_exception_is_formatted(self):
        def raises(*args, **kwargs):
            raise ValueError("bad input")

        tool = _make_tool(raises)
        result = tool.call(1, 2)
        assert "ValueError" in result
        assert "bad input" in result

    def test_keyboard_interrupt_propagates(self):
        # BaseException subclasses like KeyboardInterrupt/SystemExit must not
        # be caught and silently turned into tool-output strings.
        def raises_kb(*args, **kwargs):
            raise KeyboardInterrupt()

        tool = _make_tool(raises_kb)
        with pytest.raises(KeyboardInterrupt):
            tool.call()

    def test_system_exit_propagates(self):
        def raises_exit(*args, **kwargs):
            raise SystemExit()

        tool = _make_tool(raises_exit)
        with pytest.raises(SystemExit):
            tool.call()

    def test_call_signature_mismatch_does_not_crash(self):
        # An arity mismatch is detected by the interpreter's argument-binding
        # check before the callable's own frame is ever entered, so
        # e.__traceback__.tb_next is None. This must not raise AssertionError.
        class Callback:
            def __call__(self, x):
                return x

        tool = _make_tool(Callback())
        result = tool.call(1, 2)  # Callback.__call__ only takes one positional arg
        assert "TypeError" in result
