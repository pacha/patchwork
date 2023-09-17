from .safe_get import safe_get
from .make_safe import make_safe
from patchwork.lib.values import show_value
from patchwork.exceptions import PatchworkInputError


def safe_traverse(container, key, indices):
    """Traverse a chain of nested lists making them safe to modify."""
    if not indices:
        return container, key
    index, indices_left = indices[0], indices[1:]
    next_container = safe_get(container, key)
    if not isinstance(next_container, list):
        index_str = show_value(index) if index else "_"
        raise PatchworkInputError(f"Cannot use index {index_str} on a non-list value")
    safe_container = make_safe(next_container)
    container[key] = safe_container
    return safe_traverse(safe_container, index, indices_left)
