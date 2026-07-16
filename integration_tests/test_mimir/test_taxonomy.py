import shinto.mimir.taxonomy

def test_taxonomy():
    taxonomy = shinto.mimir.taxonomy.Taxonomy()
    taxonomy.create_taxonomy("test_taxonomy", "Test Taxonomy")
    assert taxonomy.get_taxonomy("test_taxonomy") is not None
    taxonomy.delete_taxonomy("test_taxonomy")
    assert taxonomy.get_taxonomy("test_taxonomy") is None

if __name__ == "__main__":
    test_taxonomy()