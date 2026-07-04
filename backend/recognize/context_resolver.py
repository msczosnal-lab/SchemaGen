"""Runtime wrapper — resolver kontekstu wierszy (faza 2)."""

from backend.geometry.row_layout import (
    ContextAssignment,
    ContextResolver,
    Row,
    assign_contextual,
    find_anchor_in_row,
    group_into_rows,
)

__all__ = [
    "ContextAssignment",
    "ContextResolver",
    "Row",
    "assign_contextual",
    "find_anchor_in_row",
    "group_into_rows",
]
