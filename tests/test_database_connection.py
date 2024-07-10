"""Tests for DataBaseWriter class."""

# TODO: Fix the tests with psycopg

# import unittest
# from unittest.mock import MagicMock, patch

# from shinto.database_connection import DatabaseConnection


# class TestDataBaseWriter(unittest.TestCase):
#     """Tests for DataBaseWriter class."""

#     @patch("psycopg2.connect")
#     def test_create(self, mock_connect):
#         """Testing Creation of instance of DataBaseWriter class."""
#         db_conn = DatabaseConnection("", "", "", "", "")
#         self.assertIsNotNone(db_conn)

#     @patch("psycopg2.connect")
#     @patch("psycopg2.extras.execute_batch")
#     def test_write_datarecords_success(self, mock_execute_batch, mock_connect):
#         """Testing successful write_datarecords method."""
#         mock_connection = mock_connect.return_value
#         mock_cursor = mock_connection.cursor.return_value

#         db_conn = DatabaseConnection("", "", "", "", "")

#         update_query = "INSERT INTO table_name (created, updated, id) VALUES (now(), now(), 1)"
#         datachunk.get_query.return_value = update_query
#         datachunk.get_records.return_value = []
#         datachunk.check.return_value = True

#         result = db_conn.write_records(datachunk)

#         mock_execute_batch.assert_called_once_with(
#             mock_cursor, datachunk.get_query.return_value, datachunk.get_records.return_value
#         )

#         self.assertTrue(result)

#     @patch("psycopg2.connect")
#     def test_write_datarecords_invalid_datachunk(self, mock_connect):
#         """Testing bad datachunk check in write_datarecords method."""
#         db_conn = DatabaseConnection("", "", "", "", "")

#         datachunk = MagicMock(spec=DataChunk)
#         datachunk.check.return_value = False

#         result = db_conn.write_datarecords(datachunk)

#         self.assertFalse(result)

#     @patch("psycopg2.connect")
#     @patch("psycopg2.extras.execute_batch")
#     def test_write_datarecords_failure(self, mock_execute_batch, mock_connect):
#         """Testing bad datachunk check in write_datarecords method."""
#         mock_connection = mock_connect.return_value
#         mock_cursor = mock_connection.cursor.return_value
#         mock_execute_batch.side_effect = psycopg2.Error()

#         db_conn = DatabaseConnection("", "", "", "", "")

#         datachunk = MagicMock(spec=DataChunk)
#         update_query = "bad query"
#         datachunk.get_query.return_value = update_query
#         datachunk.get_records.return_value = []
#         datachunk.check.return_value = True

#         result = db_conn.write_datarecords(datachunk)

#         mock_execute_batch.assert_called_once_with(
#             mock_cursor, datachunk.get_query.return_value, datachunk.get_records.return_value
#         )

#         self.assertFalse(result)
