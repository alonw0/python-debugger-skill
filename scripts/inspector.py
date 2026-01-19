#!/usr/bin/env python3
"""
Deep Object Inspector for Claude Code Python Debugger

Provides detailed inspection of Python objects including:
- DataFrames (pandas)
- NumPy arrays
- Nested dictionaries/lists
- Custom objects with attributes
- Circular reference detection
"""

from typing import Any, Dict, List, Optional, Set
import sys

# Configuration
MAX_VALUE_LENGTH = 1000
MAX_COLLECTION_ITEMS = 50
MAX_DEPTH = 10
MAX_STRING_LENGTH = 200
MAX_ARRAY_PREVIEW = 10


def truncate(value: str, max_length: int = MAX_VALUE_LENGTH) -> str:
    """Truncate a string if it exceeds max length."""
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value


class ObjectInspector:
    """Deep object inspector with circular reference detection."""

    def __init__(self, max_depth: int = MAX_DEPTH, max_items: int = MAX_COLLECTION_ITEMS):
        self.max_depth = max_depth
        self.max_items = max_items
        self._seen: Set[int] = set()

    def inspect(self, obj: Any, depth: int = 0) -> Dict[str, Any]:
        """
        Inspect an object and return detailed information.

        Returns a dict with:
        - type: The type name
        - value: String representation
        - items: For collections, the contained items
        - attributes: For objects, accessible attributes
        - shape: For arrays/DataFrames, the shape
        - dtype: For typed arrays, the data type
        """
        obj_id = id(obj)
        type_name = type(obj).__name__
        module = type(obj).__module__

        # Check for circular reference
        if obj_id in self._seen:
            return {
                "type": type_name,
                "value": "<circular reference>",
                "circular": True
            }

        # Check depth limit
        if depth > self.max_depth:
            return {
                "type": type_name,
                "value": f"<max depth {self.max_depth} exceeded>",
                "truncated": True
            }

        # Track this object
        self._seen.add(obj_id)

        try:
            # Route to appropriate handler
            if obj is None:
                return {"type": "NoneType", "value": "None"}

            if isinstance(obj, bool):
                return {"type": "bool", "value": str(obj)}

            if isinstance(obj, (int, float, complex)):
                return self._inspect_number(obj)

            if isinstance(obj, str):
                return self._inspect_string(obj)

            if isinstance(obj, bytes):
                return self._inspect_bytes(obj)

            if isinstance(obj, (list, tuple)):
                return self._inspect_sequence(obj, depth)

            if isinstance(obj, dict):
                return self._inspect_dict(obj, depth)

            if isinstance(obj, set):
                return self._inspect_set(obj, depth)

            # Check for pandas DataFrame
            if self._is_dataframe(obj):
                return self._inspect_dataframe(obj)

            # Check for pandas Series
            if self._is_series(obj):
                return self._inspect_series(obj)

            # Check for numpy array
            if self._is_ndarray(obj):
                return self._inspect_ndarray(obj)

            # Check for common special types
            if hasattr(obj, "__dict__") or hasattr(obj, "__slots__"):
                return self._inspect_object(obj, depth)

            # Fallback: try repr
            return self._inspect_generic(obj)

        finally:
            self._seen.discard(obj_id)

    def _inspect_number(self, obj: Any) -> Dict[str, Any]:
        """Inspect numeric types."""
        type_name = type(obj).__name__
        result = {
            "type": type_name,
            "value": str(obj)
        }

        # Add special info for floats
        if isinstance(obj, float):
            import math
            if math.isinf(obj):
                result["special"] = "infinity"
            elif math.isnan(obj):
                result["special"] = "nan"

        return result

    def _inspect_string(self, obj: str) -> Dict[str, Any]:
        """Inspect string."""
        result = {
            "type": "str",
            "length": len(obj),
            "value": truncate(repr(obj), MAX_STRING_LENGTH)
        }

        if len(obj) > MAX_STRING_LENGTH:
            result["truncated"] = True
            result["full_length"] = len(obj)

        return result

    def _inspect_bytes(self, obj: bytes) -> Dict[str, Any]:
        """Inspect bytes."""
        result = {
            "type": "bytes",
            "length": len(obj),
            "value": truncate(repr(obj), MAX_STRING_LENGTH)
        }

        if len(obj) > MAX_STRING_LENGTH:
            result["truncated"] = True

        return result

    def _inspect_sequence(self, obj: Any, depth: int) -> Dict[str, Any]:
        """Inspect list or tuple."""
        type_name = type(obj).__name__
        result = {
            "type": type_name,
            "length": len(obj),
            "value": f"<{type_name} with {len(obj)} items>"
        }

        if len(obj) == 0:
            result["items"] = []
            return result

        # Inspect items up to limit
        items = []
        for i, item in enumerate(obj):
            if i >= self.max_items:
                items.append({
                    "type": "...",
                    "value": f"... ({len(obj) - i} more items)",
                    "truncated": True
                })
                break
            items.append(self.inspect(item, depth + 1))

        result["items"] = items
        if len(obj) > self.max_items:
            result["truncated"] = True

        return result

    def _inspect_dict(self, obj: dict, depth: int) -> Dict[str, Any]:
        """Inspect dictionary."""
        result = {
            "type": "dict",
            "length": len(obj),
            "value": f"<dict with {len(obj)} keys>"
        }

        if len(obj) == 0:
            result["items"] = {}
            return result

        # Inspect items up to limit
        items = {}
        for i, (key, value) in enumerate(obj.items()):
            if i >= self.max_items:
                items["..."] = {
                    "type": "...",
                    "value": f"... ({len(obj) - i} more keys)",
                    "truncated": True
                }
                break

            key_str = truncate(repr(key), 100)
            items[key_str] = self.inspect(value, depth + 1)

        result["items"] = items
        if len(obj) > self.max_items:
            result["truncated"] = True

        return result

    def _inspect_set(self, obj: set, depth: int) -> Dict[str, Any]:
        """Inspect set."""
        result = {
            "type": "set",
            "length": len(obj),
            "value": f"<set with {len(obj)} items>"
        }

        if len(obj) == 0:
            result["items"] = []
            return result

        items = []
        for i, item in enumerate(obj):
            if i >= self.max_items:
                items.append({
                    "type": "...",
                    "value": f"... ({len(obj) - i} more items)",
                    "truncated": True
                })
                break
            items.append(self.inspect(item, depth + 1))

        result["items"] = items
        if len(obj) > self.max_items:
            result["truncated"] = True

        return result

    def _is_dataframe(self, obj: Any) -> bool:
        """Check if object is a pandas DataFrame."""
        return (type(obj).__name__ == "DataFrame" and
                type(obj).__module__.startswith("pandas"))

    def _is_series(self, obj: Any) -> bool:
        """Check if object is a pandas Series."""
        return (type(obj).__name__ == "Series" and
                type(obj).__module__.startswith("pandas"))

    def _is_ndarray(self, obj: Any) -> bool:
        """Check if object is a numpy ndarray."""
        return (type(obj).__name__ == "ndarray" and
                type(obj).__module__ == "numpy")

    def _inspect_dataframe(self, df: Any) -> Dict[str, Any]:
        """Inspect pandas DataFrame."""
        result = {
            "type": "DataFrame",
            "module": "pandas",
            "shape": list(df.shape),
            "rows": df.shape[0],
            "columns": df.shape[1],
            "value": f"<DataFrame {df.shape[0]}x{df.shape[1]}>"
        }

        # Column info
        columns = []
        for col in df.columns[:self.max_items]:
            col_info = {
                "name": str(col),
                "dtype": str(df[col].dtype)
            }

            # Add sample values
            try:
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    samples = non_null.head(3).tolist()
                    col_info["samples"] = [truncate(str(s), 50) for s in samples]
            except Exception:
                pass

            columns.append(col_info)

        result["column_info"] = columns

        if len(df.columns) > self.max_items:
            result["columns_truncated"] = True

        # Index info
        result["index"] = {
            "type": type(df.index).__name__,
            "dtype": str(df.index.dtype)
        }

        # Memory usage
        try:
            result["memory_usage"] = df.memory_usage(deep=True).sum()
        except Exception:
            pass

        # Preview data (head)
        try:
            preview_rows = min(5, len(df))
            preview_cols = min(10, len(df.columns))
            preview = df.iloc[:preview_rows, :preview_cols]
            result["preview"] = preview.to_dict(orient="records")
        except Exception:
            pass

        return result

    def _inspect_series(self, series: Any) -> Dict[str, Any]:
        """Inspect pandas Series."""
        result = {
            "type": "Series",
            "module": "pandas",
            "length": len(series),
            "dtype": str(series.dtype),
            "name": str(series.name) if series.name else None,
            "value": f"<Series length={len(series)} dtype={series.dtype}>"
        }

        # Statistics for numeric series
        if series.dtype.kind in "iufc":  # int, uint, float, complex
            try:
                result["stats"] = {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "std": float(series.std())
                }
            except Exception:
                pass

        # Value counts for categorical-like
        try:
            if len(series.unique()) < 20:
                result["value_counts"] = series.value_counts().head(10).to_dict()
        except Exception:
            pass

        # Sample values
        try:
            result["samples"] = [truncate(str(v), 50) for v in series.head(5).tolist()]
        except Exception:
            pass

        return result

    def _inspect_ndarray(self, arr: Any) -> Dict[str, Any]:
        """Inspect numpy array."""
        result = {
            "type": "ndarray",
            "module": "numpy",
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "ndim": arr.ndim,
            "size": arr.size,
            "value": f"<ndarray shape={arr.shape} dtype={arr.dtype}>"
        }

        # Memory info
        result["nbytes"] = arr.nbytes

        # Statistics for numeric arrays
        if arr.dtype.kind in "iufc" and arr.size > 0:
            try:
                import numpy as np
                result["stats"] = {
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "mean": float(np.mean(arr)),
                    "std": float(np.std(arr))
                }
            except Exception:
                pass

        # Preview values
        try:
            flat = arr.flatten()
            preview_count = min(MAX_ARRAY_PREVIEW, len(flat))
            result["preview"] = [truncate(str(v), 50) for v in flat[:preview_count]]
            if len(flat) > preview_count:
                result["preview_truncated"] = True
        except Exception:
            pass

        return result

    def _inspect_object(self, obj: Any, depth: int) -> Dict[str, Any]:
        """Inspect a general object with attributes."""
        type_name = type(obj).__name__
        module = type(obj).__module__

        result = {
            "type": type_name,
            "module": module,
        }

        # Try to get a good string representation
        try:
            value_str = repr(obj)
            result["value"] = truncate(value_str)
        except Exception:
            result["value"] = f"<{type_name} object>"

        # Get attributes
        attributes = {}
        attr_names = []

        # Try __dict__ first
        if hasattr(obj, "__dict__"):
            attr_names.extend(obj.__dict__.keys())

        # Try __slots__
        if hasattr(obj, "__slots__"):
            attr_names.extend(obj.__slots__)

        # Filter and inspect attributes
        for name in attr_names[:self.max_items]:
            if name.startswith("_"):
                continue
            try:
                val = getattr(obj, name)
                if not callable(val):
                    attributes[name] = self.inspect(val, depth + 1)
            except Exception as e:
                attributes[name] = {"type": "error", "value": str(e)}

        if attributes:
            result["attributes"] = attributes

        if len(attr_names) > self.max_items:
            result["attributes_truncated"] = True

        # Get methods (just names)
        methods = []
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                if callable(getattr(obj, name)):
                    methods.append(name)
            except Exception:
                pass

        if methods:
            result["methods"] = methods[:20]
            if len(methods) > 20:
                result["methods_truncated"] = True

        return result

    def _inspect_generic(self, obj: Any) -> Dict[str, Any]:
        """Fallback inspection for unknown types."""
        type_name = type(obj).__name__
        module = type(obj).__module__

        result = {
            "type": type_name,
            "module": module
        }

        try:
            result["value"] = truncate(repr(obj))
        except Exception:
            result["value"] = f"<{type_name} object>"

        # Add length if available
        if hasattr(obj, "__len__"):
            try:
                result["length"] = len(obj)
            except Exception:
                pass

        return result


def inspect_object(obj: Any, max_depth: int = MAX_DEPTH,
                   max_items: int = MAX_COLLECTION_ITEMS) -> Dict[str, Any]:
    """
    Convenience function to inspect an object.

    Args:
        obj: Object to inspect
        max_depth: Maximum recursion depth
        max_items: Maximum items to show in collections

    Returns:
        Dict with inspection results
    """
    inspector = ObjectInspector(max_depth=max_depth, max_items=max_items)
    return inspector.inspect(obj)


def format_inspection(inspection: Dict[str, Any], indent: int = 0) -> str:
    """
    Format an inspection result as readable text.

    Args:
        inspection: Inspection result dict
        indent: Current indentation level

    Returns:
        Formatted string representation
    """
    lines = []
    prefix = "  " * indent

    type_name = inspection.get("type", "unknown")
    value = inspection.get("value", "")

    # Header line
    header = f"{prefix}{type_name}"
    if "length" in inspection:
        header += f" (len={inspection['length']})"
    if "shape" in inspection:
        header += f" (shape={inspection['shape']})"
    lines.append(header)

    # Value
    if value and not value.startswith("<"):
        lines.append(f"{prefix}  = {value}")

    # Items for collections
    if "items" in inspection:
        items = inspection["items"]
        if isinstance(items, dict):
            for key, val in items.items():
                if isinstance(val, dict) and "type" in val:
                    lines.append(f"{prefix}  [{key}]: {val.get('type')} = {val.get('value', '')}")
                else:
                    lines.append(f"{prefix}  [{key}]: {val}")
        elif isinstance(items, list):
            for i, item in enumerate(items):
                if isinstance(item, dict) and "type" in item:
                    lines.append(f"{prefix}  [{i}]: {item.get('type')} = {item.get('value', '')}")
                else:
                    lines.append(f"{prefix}  [{i}]: {item}")

    # Attributes for objects
    if "attributes" in inspection:
        lines.append(f"{prefix}  Attributes:")
        for name, attr in inspection["attributes"].items():
            if isinstance(attr, dict):
                lines.append(f"{prefix}    .{name}: {attr.get('type')} = {attr.get('value', '')}")
            else:
                lines.append(f"{prefix}    .{name}: {attr}")

    # Methods
    if "methods" in inspection:
        lines.append(f"{prefix}  Methods: {', '.join(inspection['methods'])}")

    # Column info for DataFrames
    if "column_info" in inspection:
        lines.append(f"{prefix}  Columns:")
        for col in inspection["column_info"]:
            col_line = f"{prefix}    {col['name']}: {col['dtype']}"
            if "samples" in col:
                col_line += f" (e.g., {col['samples'][0]})"
            lines.append(col_line)

    # Stats
    if "stats" in inspection:
        stats = inspection["stats"]
        stats_str = ", ".join(f"{k}={v:.4g}" for k, v in stats.items())
        lines.append(f"{prefix}  Stats: {stats_str}")

    # Preview
    if "preview" in inspection and isinstance(inspection["preview"], list):
        lines.append(f"{prefix}  Preview: [{', '.join(str(v) for v in inspection['preview'][:5])}...]")

    return "\n".join(lines)


# =============================================================================
# CLI for standalone testing
# =============================================================================

if __name__ == "__main__":
    import json

    # Test with various objects
    test_objects = [
        None,
        42,
        3.14159,
        "Hello, World!",
        [1, 2, 3, 4, 5],
        {"name": "test", "values": [1, 2, 3]},
        {"nested": {"deep": {"value": 123}}},
    ]

    # Try to test with pandas/numpy if available
    try:
        import numpy as np
        test_objects.append(np.array([[1, 2, 3], [4, 5, 6]]))
    except ImportError:
        pass

    try:
        import pandas as pd
        test_objects.append(pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}))
    except ImportError:
        pass

    # Create a class for testing
    class TestClass:
        def __init__(self):
            self.name = "test"
            self.value = 42
            self._private = "hidden"

        def method(self):
            pass

    test_objects.append(TestClass())

    # Test circular reference
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    test_objects.append(circular_list)

    print("Object Inspector Tests")
    print("=" * 60)

    for obj in test_objects:
        print(f"\nObject: {type(obj).__name__}")
        print("-" * 40)
        result = inspect_object(obj, max_depth=3)
        print(json.dumps(result, indent=2, default=str))
        print()
        print("Formatted:")
        print(format_inspection(result))
        print()
