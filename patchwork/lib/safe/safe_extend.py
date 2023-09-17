from patchwork.lib.values import show_index
from patchwork.lib.values import show_value
from patchwork.exceptions import PatchworkInputError


def safe_extend(container, index, value):
    if not isinstance(container, list):
        raise PatchworkInputError(
            f"Cannot perform operation at {show_index(index, container)}: "
            f"value {show_value(container)} is not a list."
        )
    if not isinstance(value, list):
        raise PatchworkInputError(
            f"Cannot perform operation at {show_index(index, container)}: "
            f"value {show_value(value)} is not a list."
        )
    if index is None:
        container.extend(value)
    else:
        if not isinstance(index, int):
            raise PatchworkInputError(
                f"Cannot perform operation at {show_index(index, container)}: "
                "index must be an integer."
            )
        length = len(container)
        lower_boundary, upper_boundary = -length, max(length, 1)
        if not (lower_boundary <= index < upper_boundary):
            raise PatchworkInputError(
                f"List index {show_value(index)} out of range [{lower_boundary}, {upper_boundary - 1}]."
            )
        container[index:index] = value
