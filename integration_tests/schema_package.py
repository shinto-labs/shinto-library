# integration_tests/schema_package.py

import logging

from shinto.mimir.base import get_default_user_id
from shinto.mimir.data import (
    create_schema_package,
    delete_schema_package,
    get_schema_package_by_id,
    get_schema_package_list,
    update_schema_package,
)
from shinto.mimir.exception import MimirEntityNotFoundException

BULK_COUNT = 1000
BULK_DELETE_RATIO = 0.4
BULK_NAME_PREFIX = "schema_package_bulk_"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run_crud_lifecycle(conn, action_by) -> None:
    logging.info("Schema package CRUD: create")
    created = create_schema_package(
        conn,
        action_by=action_by,
        name="schema_package_crud_test",
        data={"version": "1.0.0", "tables": ["projects"]},
    )
    schema_package_id = created["id"]
    _assert(
        created["name"] == "schema_package_crud_test",
        f"unexpected name after create: {created}",
    )
    _assert(
        created["data"]["version"] == "1.0.0",
        f"unexpected data after create: {created}",
    )

    logging.info("Schema package CRUD: get after create")
    fetched = get_schema_package_by_id(
        conn, action_by=action_by, schema_package_id=schema_package_id
    )
    _assert(fetched["id"] == schema_package_id, "get by id did not return created schema_package")
    _assert(fetched["name"] == "schema_package_crud_test", "get by id returned wrong name")

    logging.info("Schema package CRUD: list after create")
    packages = get_schema_package_list(conn, action_by=action_by)
    _assert(
        any(item["id"] == schema_package_id for item in packages),
        "created schema_package missing from list",
    )

    logging.info("Schema package CRUD: update")
    updated = update_schema_package(
        conn,
        action_by=action_by,
        schema_package_id=schema_package_id,
        name="schema_package_crud_updated",
        data={"version": "1.1.0", "tables": ["projects", "files"]},
    )
    _assert(
        updated["name"] == "schema_package_crud_updated",
        f"unexpected name after update: {updated}",
    )
    _assert(
        updated["data"]["version"] == "1.1.0",
        f"unexpected data after update: {updated}",
    )

    logging.info("Schema package CRUD: get after update")
    fetched = get_schema_package_by_id(
        conn, action_by=action_by, schema_package_id=schema_package_id
    )
    _assert(fetched["name"] == "schema_package_crud_updated", "get after update returned wrong name")
    _assert(fetched["data"]["version"] == "1.1.0", "get after update returned wrong data")

    logging.info("Schema package CRUD: list after update")
    packages = get_schema_package_list(conn, action_by=action_by)
    listed = next(item for item in packages if item["id"] == schema_package_id)
    _assert(listed["name"] == "schema_package_crud_updated", "list after update returned wrong name")

    logging.info("Schema package CRUD: delete")
    deleted = delete_schema_package(
        conn, action_by=action_by, schema_package_id=schema_package_id
    )
    _assert(deleted["action"] == "deleted", f"unexpected action after delete: {deleted}")

    logging.info("Schema package CRUD: get after delete (expect not found)")
    try:
        get_schema_package_by_id(
            conn, action_by=action_by, schema_package_id=schema_package_id
        )
    except MimirEntityNotFoundException:
        logging.info("Schema package correctly not found after delete")
    else:
        raise AssertionError("expected MimirEntityNotFoundException after delete")

    packages = get_schema_package_list(conn, action_by=action_by)
    _assert(
        all(item["id"] != schema_package_id for item in packages),
        "deleted schema_package still present in list",
    )


def _run_bulk_lifecycle(conn, action_by) -> None:
    delete_count = int(BULK_COUNT * BULK_DELETE_RATIO)
    keep_count = BULK_COUNT - delete_count

    logging.info("Schema package bulk: creating %s records", BULK_COUNT)
    created_ids = []
    for index in range(BULK_COUNT):
        record = create_schema_package(
            conn,
            action_by=action_by,
            name=f"{BULK_NAME_PREFIX}{index:04d}",
            data={"index": index},
        )
        created_ids.append(record["id"])

    listed = [
        item
        for item in get_schema_package_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(
        len(listed) == BULK_COUNT,
        f"expected {BULK_COUNT} bulk schema_packages, got {len(listed)}",
    )

    ids_to_delete = created_ids[:delete_count]
    ids_to_keep = created_ids[delete_count:]

    logging.info(
        "Schema package bulk: deleting %s records (%.0f%%)",
        delete_count,
        BULK_DELETE_RATIO * 100,
    )
    for schema_package_id in ids_to_delete:
        delete_schema_package(
            conn, action_by=action_by, schema_package_id=schema_package_id
        )

    listed = [
        item
        for item in get_schema_package_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(
        len(listed) == keep_count,
        f"expected {keep_count} remaining bulk schema_packages, got {len(listed)}",
    )

    remaining_ids = {item["id"] for item in listed}
    _assert(
        remaining_ids == set(ids_to_keep),
        "remaining bulk schema_package ids do not match expected set",
    )

    for schema_package_id in ids_to_delete:
        try:
            get_schema_package_by_id(
                conn, action_by=action_by, schema_package_id=schema_package_id
            )
        except MimirEntityNotFoundException:
            continue
        raise AssertionError(
            f"deleted bulk schema_package still retrievable: {schema_package_id}"
        )

    for schema_package_id in ids_to_keep:
        fetched = get_schema_package_by_id(
            conn, action_by=action_by, schema_package_id=schema_package_id
        )
        _assert(
            fetched["id"] == schema_package_id,
            f"kept bulk schema_package not found: {schema_package_id}",
        )

    logging.info(
        "Schema package bulk: verified %s kept and %s deleted", keep_count, delete_count
    )


def run_integration_test(conn) -> None:
    logging.info("Clearing schema package table")
    conn.execute_command("TRUNCATE TABLE data.schema_package CASCADE")

    logging.info("Starting schema_package integration test")
    action_by = get_default_user_id(conn)

    _run_crud_lifecycle(conn, action_by)
    _run_bulk_lifecycle(conn, action_by)

    logging.info("schema_package integration test completed")
