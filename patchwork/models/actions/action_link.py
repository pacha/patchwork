from patchwork.models import Path
from patchwork.lib.copy_on_write import safe_traverse
from patchwork.lib.copy_on_write import safe_set
from . import action


@action
def action_link(output_dict, key, indices, change_value, input_dict, patch, path):
    """Set the value pointed by a path in input_dict as new value."""

    # get container to modify
    container, index = safe_traverse(output_dict, key, indices)

    # get value
    input_path = Path(change_value)
    linked_value = input_path.get_value(input_dict)

    # perform action
    safe_set(container, index, linked_value)
