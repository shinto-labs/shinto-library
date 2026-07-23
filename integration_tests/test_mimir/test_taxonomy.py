from shinto.mimir.data import create_taxonomy, delete_taxonomy


def test_taxonomy():
    taxonomy = create_taxonomy("test_taxonomy", "Test Taxonomy")
    assert taxonomy is not None
    taxonomy = delete_taxonomy("test_taxonomy")
    assert taxonomy is None


if __name__ == "__main__":
    test_taxonomy()
