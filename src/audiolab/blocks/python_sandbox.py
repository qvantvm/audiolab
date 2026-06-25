"""Restricted in-process sandbox for PythonCustom block code."""

from __future__ import annotations

import ast
import math
import textwrap
from typing import Any, Callable

import numpy as np

SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
}

_FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "input",
        "help",
        "breakpoint",
    }
)


class PythonBlockSandboxError(ValueError):
    """Raised when custom block code is invalid or unsafe."""


class _CodeValidator(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        raise PythonBlockSandboxError("import statements are not allowed in PythonCustom code")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise PythonBlockSandboxError("import statements are not allowed in PythonCustom code")

    def visit_Global(self, node: ast.Global) -> None:
        raise PythonBlockSandboxError("global is not allowed in PythonCustom code")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise PythonBlockSandboxError("nonlocal is not allowed in PythonCustom code")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _FORBIDDEN_NAMES:
            raise PythonBlockSandboxError(f"use of {node.id!r} is not allowed in PythonCustom code")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise PythonBlockSandboxError("dunder attribute access is not allowed in PythonCustom code")
        self.generic_visit(node)


def validate_python_block_code(code: str) -> None:
    text = code.strip()
    if not text:
        raise PythonBlockSandboxError("PythonCustom code must not be empty")
    tree = ast.parse(text, mode="exec")
    _CodeValidator().visit(tree)


class BlockProcessContext:
    """Helpers exposed to PythonCustom code as `ctx`."""

    def __init__(
        self,
        *,
        block_id: str,
        sample_rate: int,
        block_size: int,
        duration: float,
    ) -> None:
        self.block_id = block_id
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.duration = duration

    def as_array(self, value: object, n_frames: int, default: float = 0.0) -> np.ndarray:
        if value is None:
            return np.full(n_frames, float(default), dtype=np.float32)
        arr = np.asarray(value, dtype=np.float32)
        if arr.ndim == 0:
            return np.full(n_frames, float(arr), dtype=np.float32)
        if arr.shape[0] != n_frames:
            raise PythonBlockSandboxError(
                f"audio buffer length {arr.shape[0]} does not match n_frames={n_frames}"
            )
        return arr.astype(np.float32)

    def as_scalar(self, value: object, default: float = 0.0) -> float:
        if value is None:
            return float(default)
        arr = np.asarray(value)
        if arr.ndim == 0:
            return float(arr)
        if arr.size == 1:
            return float(arr.reshape(-1)[0])
        raise PythonBlockSandboxError("control input must be a scalar")


ProcessFn = Callable[[dict[str, Any], int, dict[str, Any], BlockProcessContext], dict[str, Any]]


def _has_process_function(code: str) -> bool:
    tree = ast.parse(code)
    return any(isinstance(node, ast.FunctionDef) and node.name == "process" for node in tree.body)


def _execution_env() -> dict[str, Any]:
    return {
        "__builtins__": SAFE_BUILTINS,
        "np": np,
        "numpy": np,
        "math": math,
    }


def compile_python_block_process(code: str) -> ProcessFn:
    text = code.strip()
    if _has_process_function(text):
        validate_python_block_code(text)
        env = _execution_env()
        exec(compile(text, "<PythonCustom>", "exec"), env, env)
        process_fn = env.get("process")
        if not callable(process_fn):
            raise PythonBlockSandboxError("PythonCustom code must define process(inputs, n_frames, params, ctx)")
        return process_fn

    validate_python_block_code(text)
    wrapped = (
        "def __python_custom_process(inputs, n_frames, params, ctx):\n"
        "    outputs = {}\n"
        + textwrap.indent(text, "    ")
        + "\n    return outputs\n"
    )
    validate_python_block_code(wrapped)
    env = _execution_env()
    exec(compile(wrapped, "<PythonCustom>", "exec"), env, env)
    fn = env.get("__python_custom_process")
    if not callable(fn):
        raise PythonBlockSandboxError(
            "PythonCustom code must define process(inputs, n_frames, params, ctx) "
            "or assign keys on outputs"
        )
    return fn
