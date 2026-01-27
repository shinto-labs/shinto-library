"""Tests for the taxonomy module."""

import json
import unittest
from pathlib import Path

from shinto.taxonomy import Taxonomy, TaxonomyField

TEST_TAXONOMY_FILE = Path(__file__).parent / "fixtures/taxonomy_tilburg_test.json"
TEST_PROJECT_DATA_LIST_FILE = Path(__file__).parent / "fixtures/project_data_list_tilburg_test.json"


class TestTaxonomy(unittest.TestCase):
    """Test the taxonomy module."""

    def test_taxonomy_creation(self):
        """Test the creation of a Taxonomy object."""
        taxonomy_dict = json.loads(TEST_TAXONOMY_FILE.read_text())

        taxonomy = Taxonomy(taxonomy_dict)
        self.assertIsInstance(taxonomy, Taxonomy)
        self.assertIsInstance(taxonomy.fields, list)
        for field in taxonomy.fields:
            self.assertIsInstance(field, TaxonomyField)

    def test_check_taxonomy_compliance(self):
        """Test the check_taxonomy_compliance function."""
        taxonomy_dict = json.loads(TEST_TAXONOMY_FILE.read_text())
        data = json.loads(TEST_PROJECT_DATA_LIST_FILE.read_text())

        taxonomy = Taxonomy(taxonomy_dict)

        for item in data:
            taxonomy.validate_data(item)


if __name__ == "__main__":
    unittest.main()
