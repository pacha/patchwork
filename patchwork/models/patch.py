from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Generator
from dataclasses import dataclass

from .change import Change
from .operation import Operation
from .key_location import KeyLocation
from .annotated_key import AnnotatedKey
from .annotation_config import AnnotationConfig
from patchwork.exceptions import PatchworkInputError
from patchwork.lib.value_type import value_type


@dataclass
class Patch:
    """Normalized form of a raw dictionary patch."""

    vars: Dict[str, Any]
    data: Dict[Any, List[Change]]
    annotation_config: AnnotationConfig
    parent_patch: "Union[Patch, None]"

    def __getitem__(self, key: Any) -> List[Change]:
        return self.data[key]

    def __init__(
        self,
        raw_patch: dict,
        annotation_config: AnnotationConfig = AnnotationConfig(),
        parent_patch: "Union[Patch, None]" = None,
    ):
        self.parent_patch = parent_patch
        self.annotation_config = annotation_config
        self.vars = {}
        self.data = {}
        for key, value in raw_patch.items():
            # extract annotation
            annotated_key = AnnotatedKey(key, annotation_config)

            # extract changes and vars
            try:
                changes = self.extract_changes(annotated_key.annotation, value)
            except ValueError as err:
                raise PatchworkInputError(
                    f"Error found in patch file while processing key '{key}': {err}"
                )
            self.data[annotated_key.key] = []
            for change in changes:
                if change.operation == "var":
                    self.vars[annotated_key.key] = change.value
                else:
                    self.data[annotated_key.key].append(change)

    def __repr__(self):
        return f"[{', '.join([str(key) for key in self.data.keys()])}]"

    @staticmethod
    def extract_changes(annotation, value):
        """Get list of changes for a given value."""

        # when not annotated, the operation for a key is determined by the value type
        if not annotation:
            change = Change(
                operation=None,
                value=value,
                indices=[],
            )
            return [change]

        # 'change' operation allows to specify the changes explicitly
        if annotation.operation == "change":
            if not isinstance(value, list):
                raise ValueError(
                    "A change operation takes a list of dictionaries as parameter. "
                    f"Found value of type '{value_type(value)}' instead."
                )
            changes = []
            for raw_change in value:
                change = Change.from_dict(raw_change)
                changes.append(change)
            return changes

        # in any other case use the annotation data to determine the change
        change = Change(
            operation=annotation.operation,
            value=value,
            indices=annotation.indices,
        )
        return [change]

    def get_keys(self, input_dict: dict) -> Generator[Tuple[Any, KeyLocation], None, None]:
        """Return all keys with their corresponding locations."""

        # classify input keys
        for key in input_dict:
            if key not in self.data:
                yield key, KeyLocation.only_input
            else:
                yield key, KeyLocation.in_both

        # classify new keys
        for key in self.data:
            if key not in input_dict:
                yield key, KeyLocation.only_patch

    def get_all_vars(self):
        """Recursively return vars from all patch levels."""
        all_vars = {}
        if self.parent_patch:
            all_vars.update(self.parent_patch.get_all_vars())
        all_vars.update(self.vars)
        return all_vars

    def get_var(self, name):
        """Recursively search and return a variable value."""
        try:
            value = self.vars[name]
        except KeyError:
            if self.parent_patch:
                return self.parent_patch.get_var(name)
            else:
                raise
        return value
