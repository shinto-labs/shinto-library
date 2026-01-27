"""Module for handling taxonomies."""

from __future__ import annotations

import datetime
from typing import Any

from typing_extensions import Literal

TAXONOMY_LEVEL = Literal["stage_plus"]

FIELD_TYPE = Literal[
    "number",
    "categorical",
    "text",
    "string",
    "multi_categorical",
    "date-time",
    "polygon",
]

type_mapping = {
    "number": int,
    "text": str,
    "string": str,
    "date-time": str,
    "categorical": str,
    "multi_categorical": list[str],
    "polygon": list[dict],
}


class TaxonomyComplianceError(Exception):
    """Exception raised for data that does not comply with the taxonomy."""


class TaxonomyFieldValue:
    """Class representing a value in a taxonomy field."""

    value: str
    label: str | None
    description: str | None

    def __init__(self, value_dict: dict):
        """Initialize the FieldValue from a dictionary."""
        if not isinstance(value_dict, dict):
            raise TypeError("value_dict must be a dictionary.")
        if "value" not in value_dict:
            raise TypeError("value_dict must contain a 'value' key.")
        self.value = value_dict["value"]
        self.label = value_dict.get("label")
        self.description = value_dict.get("description")


class TaxonomyField:
    """Class representing a field in a taxonomy."""

    field_id: str
    type: FIELD_TYPE
    label: str
    values: list[TaxonomyFieldValue] | None
    description: str | None
    level: str | None
    tags: list[str] | None

    def __init__(self, field_dict: dict):
        """Initialize the Field from a dictionary."""
        if not isinstance(field_dict, dict):
            raise TypeError("field_dict must be a dictionary.")
        if "field" not in field_dict or "type" not in field_dict or "label" not in field_dict:
            raise TypeError("field_dict must contain 'field', 'type', and 'label' keys.")
        if field_dict["type"] not in FIELD_TYPE.__args__:
            raise TypeError(
                f"Unrecognized field type: {field_dict['type']}."
                f"Must be one of {FIELD_TYPE.__args__}."
            )
        self.field_id = field_dict["field"]
        self.type = field_dict["type"]
        self.label = field_dict["label"]
        self.description = field_dict.get("description")
        self.level = field_dict.get("level")
        self.tags = field_dict.get("tag")
        self.values = None
        if "values" in field_dict:
            if not isinstance(field_dict["values"], list):
                raise TypeError("field_dict['values'] must be a list.")
            self.values = [TaxonomyFieldValue(v) for v in field_dict["values"]]
        if self.type in ["categorical", "multi_categorical"] and not self.values:
            raise ValueError(
                f"Field of type '{self.type}' must have 'values' defined '{self.field_id}'."
            )

    def validate(self, value: Any):  # noqa: ANN401
        """
        Validate a single field value against its type and constraints.

        Args:
            value: The value to validate

        Raises:
            TaxonomyComplianceError: If value doesn't comply

        """
        # Skip None values (field is optional)
        # TODO: Should we enforce required fields?
        if value is None:
            raise TaxonomyComplianceError(f"Field '{self.field_id}' is required but missing.")

        if not isinstance(value, type_mapping[self.type]):
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' expects type {type_mapping[self.type].__name__}, "
                f"got {type(value).__name__}: {value}"
            )

        if self.type == "multi_categorical":
            if not isinstance(value, list):
                raise TaxonomyComplianceError(
                    f"Field '{self.field_id}' expects a list of values, "
                    f"got {type(value).__name__}: {value}"
                )
            for v in value:
                if v not in [val.value for val in self.values]:
                    raise TaxonomyComplianceError(
                        f"Field '{self.field_id}' has invalid value '{v}'. "
                        f"Allowed values are {[val.value for val in self.values]}"
                    )

        if self.type == "categorical" and value not in [val.value for val in self.values]:
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' has invalid value '{value}'. "
                f"Allowed values are {[val.value for val in self.values]}"
            )

        if self.type == "date-time":
            try:
                datetime.datetime.fromisoformat(value)
            except ValueError as e:
                raise TaxonomyComplianceError(
                    f"Field '{self.field_id}' expects a date-time in ISO 8601 format, got: {value}"
                ) from e

        # TODO: how do we validate polygon?


class Taxonomy:
    """Class representing a taxonomy."""

    level: str | None
    fields: list[TaxonomyField]

    def __init__(self, taxonomy_dict: dict):
        """Initialize the Taxonomy from a dictionary."""
        if not isinstance(taxonomy_dict, dict):
            raise TypeError("taxonomy_dict must be a dictionary.")
        if "fields" not in taxonomy_dict:
            raise TypeError("taxonomy_dict must contain a 'fields' key.")
        if not isinstance(taxonomy_dict["fields"], list):
            raise TypeError("taxonomy_dict['fields'] must be a list.")
        if len(taxonomy_dict["fields"]) == 0:
            raise ValueError("taxonomy_dict['fields'] must contain at least one field.")
        if "level" in taxonomy_dict and taxonomy_dict["level"] not in TAXONOMY_LEVEL.__args__:
            raise TypeError(
                f"Unrecognized taxonomy level: {taxonomy_dict['level']}."
                f"Must be one of {TAXONOMY_LEVEL.__args__}."
            )
        self.level = taxonomy_dict.get("level")
        self.fields = [TaxonomyField(field_dict) for field_dict in taxonomy_dict["fields"]]

    def validate_data(self, data: dict):
        """
        Validate data against the taxonomy.

        Args:
            data: Project data dictionary (with potential 'stages' array)

        Raises:
            TaxonomyComplianceError: If value doesn't comply

        """
        for field in self.fields:
            # Check if field is present in data
            # TODO: Or are fields always required?
            if field.field_id in data:
                field.validate(data[field.field_id])

            if field.level and "stage" in field.level and "stages" in data:
                stages = data["stages"]
                for idx, stage in enumerate(stages):
                    if field.field_id in stage:
                        try:
                            field.validate(stage[field.field_id])
                        except TaxonomyComplianceError as e:
                            raise TaxonomyComplianceError(
                                f"Failed to validate field '{field.field_id}' in stage {idx} "
                            ) from e

    def __to_json_schema__(self) -> dict:
        """Convert a taxonomy to a JSON schema."""
        raise NotImplementedError("Not implemented yet.")
