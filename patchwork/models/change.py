from typing import Any
from typing import List
from typing import Union
from dataclasses import field
from dataclasses import dataclass

from dacite import from_dict
from dacite import DaciteError
from typeguard import check_type
from typeguard import TypeCheckError

from .actions import actions
from .operation import Operation
from patchwork.lib.values import show_value
from patchwork.lib.values import value_type
from patchwork.exceptions import PatchworkInputError


@dataclass
class Change:
    operation: Union[Operation, None]
    value: Any
    indices: List[Union[int, None]] = field(default_factory=list)

    def __init__(
        self,
        operation: Union[Operation, None],
        value: Any = None,
        indices: List[Union[int, None]] = [],
    ):
        if operation:
            # chech that the value type matches the allowed types
            try:
                check_type(value, operation.value_type)
            except TypeCheckError:
                raise PatchworkInputError(
                    f"Cannot execute operation {show_value(operation)} with value {show_value(value)}. "
                    f"This operation requires a value of type {value_type(operation.value_type)}"
                )
            # check that the operation takes indices
            if not operation.takes_indices and indices:
                raise PatchworkInputError(
                    f"Operation {show_value(operation)} cannot take indices (provided {show_value(indices)})"
                )

        # set fields
        self.operation = operation
        self.value = value
        self.indices = indices

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        # get operation
        try:
            operation_name = data["operation"]
        except KeyError:
            raise PatchworkInputError(f"Missing 'operation' key in {show_value(data)}")
        try:
            operation = Operation.get(operation_name)
        except KeyError:
            raise PatchworkInputError(
                f"Wrong operation: {show_value(operation_name)} in change list"
            )

        # for some operations, it is fine to not to specify value
        value_missing = "value" not in data
        if value_missing:
            if operation.requires_value:
                raise PatchworkInputError(f"Missing 'value' key in {show_value(data)}")
            else:
                data["value"] = None

        # indices must me a list of integers
        indices = data.get("indices", [])
        if not isinstance(indices, list):
            raise PatchworkInputError(
                f"'indices' field must be of type list instead of {value_type(indices)}"
            )
        for index in indices:
            if not isinstance(index, int) or index == "_":
                raise PatchworkInputError("'indices' field must be a list of integers")

        # check no extra fields
        extra_fields = set(data.keys()) - {"operation", "value", "indices"}
        if extra_fields:
            raise PatchworkInputError(
                f"Found invalid keys in change dictionary: {show_value(extra_fields)}"
            )

        # create change object
        try:
            data["operation"] = operation
            obj = from_dict(cls, data)
        except DaciteError as err:
            raise PatchworkInputError(err)
        return obj

    def __str__(self):
        if not self.operation:
            return ""
        index_str = (
            ("@" + ",".join([str(index) for index in self.indices]))
            if self.indices
            else ""
        )
        return f"{{{self.operation.name}{index_str}}}"

    def apply(self, output_dict, key, patch, path, root_input_dict):
        """Apply operation at key."""

        # find operation
        if self.operation:
            operation_name = self.operation.name
        else:
            patch_value_is_dict = isinstance(self.value, dict)
            operation_name = "patch" if patch_value_is_dict else "set"

        # find action
        action = actions[operation_name]

        # apply action
        action(
            container=output_dict,
            key=key,
            indices=self.indices,
            change_value=self.value,
            patch=patch,
            path=path,
            root_input_dict=root_input_dict,
        )
