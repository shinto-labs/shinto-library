"""Tests for the taxonomy module."""

import json
import logging
import unittest
from pathlib import Path

import jsonschema

from shinto.taxonomy import Taxonomy, TaxonomyComplianceError, TaxonomyField

FIXTURES_DIR = Path(__file__).parent / "fixtures"
(FIXTURES_DIR / "generated").mkdir(exist_ok=True)

TEST_TAXONOMY = json.loads((FIXTURES_DIR / "taxonomy_tilburg_test.json").read_text())
TEST_PROJECT_DATA_LIST = json.loads(
    (FIXTURES_DIR / "project_data_list_tilburg_test.json").read_text()
)


class TestTaxonomy(unittest.TestCase):
    """Test the taxonomy module."""

    def test_valid_number_field(self):
        """Test validation of valid number fields."""
        taxonomy = Taxonomy(
            {"fields": [{"field": "count", "type": "number", "label": "Count", "level": "project"}]}
        )

        # Valid number
        taxonomy.validate({"count": 42})
        taxonomy.validate({"count": 0})
        taxonomy.validate({"count": -10})

    def test_valid_text_field(self):
        """Test validation of valid text fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "name", "type": "text", "label": "Name", "level": "project"},
                    {
                        "field": "description",
                        "type": "string",
                        "label": "Description",
                        "level": "project",
                    },
                ]
            }
        )

        taxonomy.validate({"name": "Project A", "description": "A test project"})
        taxonomy.validate({"name": "", "description": ""})

    def test_valid_categorical_field(self):
        """Test validation of valid categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "active", "label": "Active"},
                            {"value": "inactive", "label": "Inactive"},
                        ],
                        "level": "project",
                    }
                ]
            }
        )

        taxonomy.validate({"status": "active"})
        taxonomy.validate({"status": "inactive"})

    def test_valid_multi_categorical_field(self):
        """Test validation of valid multi-categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "tags",
                        "type": "multi_categorical",
                        "label": "Tags",
                        "values": [
                            {"value": "urgent", "label": "Urgent"},
                            {"value": "important", "label": "Important"},
                            {"value": "review", "label": "Review"},
                        ],
                        "level": "project",
                    }
                ]
            }
        )

        taxonomy.validate({"tags": ["urgent"]})
        taxonomy.validate({"tags": ["urgent", "important"]})
        taxonomy.validate({"tags": []})

    def test_valid_datetime_field(self):
        """Test validation of valid date-time fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "created_at",
                        "type": "date-time",
                        "label": "Created At",
                        "level": "project",
                    }
                ]
            }
        )

        taxonomy.validate({"created_at": "2025-08-07T00:00:00"})
        taxonomy.validate({"created_at": "2025-08-07T00:00:00.000"})
        taxonomy.validate({"created_at": "2025-08-07T14:30:45"})
        taxonomy.validate({"created_at": "2025-08-07T14:30:45.123456"})

    def test_valid_polygon_field(self):
        """Test validation of valid polygon fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "geo", "type": "polygon", "label": "Geometry", "level": "project"}
                ]
            }
        )

        valid_geojson = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
                "properties": {},
            }
        ]
        taxonomy.validate({"geo": valid_geojson})

    def test_valid_boolean_field(self):
        """Test validation of valid boolean fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "is_active",
                        "type": "boolean",
                        "label": "Is Active",
                        "level": "project",
                    }
                ]
            }
        )

        taxonomy.validate({"is_active": True})
        taxonomy.validate({"is_active": False})

    def test_invalid_number_field(self):
        """Test validation of invalid number fields."""
        taxonomy = Taxonomy(
            {"fields": [{"field": "count", "type": "number", "label": "Count", "level": "project"}]}
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"count": "42"})

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"count": 3.14})

    def test_invalid_categorical_field(self):
        """Test validation of invalid categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "active", "label": "Active"},
                            {"value": "inactive", "label": "Inactive"},
                        ],
                        "level": "project",
                    }
                ]
            }
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"status": "pending"})

    def test_invalid_multi_categorical_field(self):
        """Test validation of invalid multi-categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "tags",
                        "type": "multi_categorical",
                        "label": "Tags",
                        "values": [
                            {"value": "urgent", "label": "Urgent"},
                            {"value": "important", "label": "Important"},
                        ],
                        "level": "project",
                    }
                ]
            }
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"tags": ["urgent", "invalid"]})

    def test_invalid_datetime_field(self):
        """Test validation of invalid date-time fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "created_at",
                        "type": "date-time",
                        "label": "Created At",
                        "level": "project",
                    }
                ]
            }
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"created_at": "not-a-date"})

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate({"created_at": "2025-13-45"})

    def test_unknown_field_type_skipped(self):
        """Test that fields with unknown types are skipped with a warning."""
        with self.assertLogs(level=logging.WARNING) as log_context:
            taxonomy = Taxonomy(
                {
                    "fields": [
                        {"field": "name", "type": "text", "label": "Name", "level": "project"},
                        {
                            "field": "unknown_field",
                            "type": "unknown_type",
                            "label": "Unknown",
                            "level": "project",
                        },
                        {"field": "count", "type": "number", "label": "Count", "level": "project"},
                    ]
                },
                skip_unknown_types=True,
            )

            # Should have 2 valid fields (name and count), unknown_field should be skipped
            self.assertEqual(len(taxonomy.fields), 2)
            self.assertEqual(taxonomy.fields[0].field_id, "name")
            self.assertEqual(taxonomy.fields[1].field_id, "count")

            # Check that a warning was logged
            self.assertTrue(
                any(
                    "unknown_field" in message and "unknown_type" in message
                    for message in log_context.output
                )
            )

        # Validation should work with remaining valid fields
        taxonomy.validate({"name": "Test", "count": 5})

    def test_missing_optional_fields(self):
        """Test that missing fields are handled correctly."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "name", "type": "text", "label": "Name", "level": "project"},
                    {"field": "count", "type": "number", "label": "Count", "level": "project"},
                ]
            }
        )

        # Fields not in data should not raise errors (they're optional)
        taxonomy.validate({"name": "Test"})
        taxonomy.validate({"count": 5})
        taxonomy.validate({})

    def test_complex_valid_data(self):
        """Test validation of complex valid data structures."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "project_name",
                        "type": "text",
                        "label": "Project Name",
                        "level": "project",
                    },
                    {"field": "budget", "type": "number", "label": "Budget", "level": "project"},
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "planning", "label": "Planning"},
                            {"value": "active", "label": "Active"},
                            {"value": "completed", "label": "Completed"},
                        ],
                        "level": "project",
                    },
                    {
                        "field": "features",
                        "type": "multi_categorical",
                        "label": "Features",
                        "values": [
                            {"value": "solar", "label": "Solar Panels"},
                            {"value": "parking", "label": "Parking"},
                            {"value": "garden", "label": "Garden"},
                        ],
                        "level": "project",
                    },
                    {
                        "field": "start_date",
                        "type": "date-time",
                        "label": "Start Date",
                        "level": "project",
                    },
                ]
            }
        )

        valid_data = {
            "project_name": "Green Building Project",
            "budget": 1500000,
            "status": "active",
            "features": ["solar", "garden"],
            "start_date": "2025-01-15T09:00:00",
        }

        taxonomy.validate(valid_data)

    def test_taxonomy_creation_real_schema(self):
        """Test the creation of a Taxonomy object."""
        taxonomy = Taxonomy(TEST_TAXONOMY)
        self.assertIsInstance(taxonomy, Taxonomy)
        self.assertIsInstance(taxonomy.fields, list)
        for field in taxonomy.fields:
            self.assertIsInstance(field, TaxonomyField)

    def test_taxonomy_validation_real_data(self):
        """Test the check_taxonomy_compliance function."""
        taxonomy = Taxonomy(TEST_TAXONOMY)

        for item in TEST_PROJECT_DATA_LIST:
            taxonomy.validate(item)

    def test_taxonomy_json_schema_real_schema(self):
        """Test the JSON schema generation of a Taxonomy object."""
        taxonomy = Taxonomy(TEST_TAXONOMY)
        json_schema = taxonomy.__json_schema__
        self.assertIsInstance(json_schema, dict)
        (FIXTURES_DIR / "generated/taxonomy_schema.json").write_text(
            json.dumps(json_schema, indent=2)
        )

        jsonschema.validate(
            instance=TEST_PROJECT_DATA_LIST,
            schema={
                "type": "array",
                "items": json_schema,
                "definitions": json_schema.get("definitions", {}),
            },
        )


if __name__ == "__main__":
    unittest.main()
