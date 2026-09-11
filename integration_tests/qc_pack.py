# integration_tests/qc_pack.py

import logging

from shinto.mimir.base import get_default_user_id
from shinto.mimir.data import (
    create_qc_pack,
    delete_qc_pack,
    get_qc_pack_by_id,
    get_qc_pack_list,
    update_qc_pack,
)
from shinto.mimir.exception import MimirEntityNotFoundException

BULK_COUNT = 1000
BULK_DELETE_RATIO = 0.4
BULK_NAME_PREFIX = "qc_pack_bulk_"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run_crud_lifecycle(conn, action_by) -> None:
    logging.info("QC pack CRUD: create")
    created = create_qc_pack(
        conn,
        action_by=action_by,
        name="qc_pack_crud_test",
        data={"rules": [{"id": 1, "severity": "x > 0"}]},
    )
    qc_pack_id = created["id"]
    _assert(created["name"] == "qc_pack_crud_test", f"unexpected name after create: {created}")
    _assert(created["data"]["rules"][0]["id"] == 1, f"unexpected data after create: {created}")

    logging.info("QC pack CRUD: get after create")
    fetched = get_qc_pack_by_id(conn, action_by=action_by, qc_pack_id=qc_pack_id)
    _assert(fetched["id"] == qc_pack_id, "get by id did not return created qc_pack")
    _assert(fetched["name"] == "qc_pack_crud_test", "get by id returned wrong name")

    logging.info("QC pack CRUD: list after create")
    qc_packs = get_qc_pack_list(conn, action_by=action_by)
    _assert(any(item["id"] == qc_pack_id for item in qc_packs), "created qc_pack missing from list")

    logging.info("QC pack CRUD: update")
    updated = update_qc_pack(
        conn,
        action_by=action_by,
        qc_pack_id=qc_pack_id,
        name="qc_pack_crud_updated",
        data={"rules": [{"id": 2, "severity": "x >= 0"}]},
    )
    _assert(updated["name"] == "qc_pack_crud_updated", f"unexpected name after update: {updated}")
    _assert(updated["data"]["rules"][0]["id"] == 2, f"unexpected data after update: {updated}")

    logging.info("QC pack CRUD: get after update")
    fetched = get_qc_pack_by_id(conn, action_by=action_by, qc_pack_id=qc_pack_id)
    _assert(fetched["name"] == "qc_pack_crud_updated", "get after update returned wrong name")
    _assert(fetched["data"]["rules"][0]["id"] == 2, "get after update returned wrong data")

    logging.info("QC pack CRUD: list after update")
    qc_packs = get_qc_pack_list(conn, action_by=action_by)
    listed = next(item for item in qc_packs if item["id"] == qc_pack_id)
    _assert(listed["name"] == "qc_pack_crud_updated", "list after update returned wrong name")

    logging.info("QC pack CRUD: delete")
    deleted = delete_qc_pack(conn, action_by=action_by, qc_pack_id=qc_pack_id)
    _assert(deleted["action"] == "deleted", f"unexpected action after delete: {deleted}")

    logging.info("QC pack CRUD: get after delete (expect not found)")
    try:
        print(get_qc_pack_by_id(conn, action_by=action_by, qc_pack_id=qc_pack_id))
    except MimirEntityNotFoundException:
        logging.info("QC pack correctly not found after delete")
    else:
        raise AssertionError("expected MimirEntityNotFoundException after delete")

    qc_packs = get_qc_pack_list(conn, action_by=action_by)
    _assert(
        all(item["id"] != qc_pack_id for item in qc_packs),
        "deleted qc_pack still present in list",
    )


def _run_bulk_lifecycle(conn, action_by) -> None:
    delete_count = int(BULK_COUNT * BULK_DELETE_RATIO)
    keep_count = BULK_COUNT - delete_count

    logging.info("QC pack bulk: creating %s records", BULK_COUNT)
    created_ids = []
    for index in range(BULK_COUNT):
        record = create_qc_pack(
            conn,
            action_by=action_by,
            name=f"{BULK_NAME_PREFIX}{index:04d}",
            data={"index": index},
        )
        created_ids.append(record["id"])

    listed = [
        item
        for item in get_qc_pack_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(len(listed) == BULK_COUNT, f"expected {BULK_COUNT} bulk qc_packs, got {len(listed)}")

    ids_to_delete = created_ids[:delete_count]
    ids_to_keep = created_ids[delete_count:]

    logging.info("QC pack bulk: deleting %s records (%.0f%%)", delete_count, BULK_DELETE_RATIO * 100)
    for qc_pack_id in ids_to_delete:
        delete_qc_pack(conn, action_by=action_by, qc_pack_id=qc_pack_id)

    listed = [
        item
        for item in get_qc_pack_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(len(listed) == keep_count, f"expected {keep_count} remaining bulk qc_packs, got {len(listed)}")

    remaining_ids = {item["id"] for item in listed}
    _assert(remaining_ids == set(ids_to_keep), "remaining bulk qc_pack ids do not match expected set")

    for qc_pack_id in ids_to_delete:
        try:
            get_qc_pack_by_id(conn, action_by=action_by, qc_pack_id=qc_pack_id)
        except MimirEntityNotFoundException:
            continue
        raise AssertionError(f"deleted bulk qc_pack still retrievable: {qc_pack_id}")

    for qc_pack_id in ids_to_keep:
        fetched = get_qc_pack_by_id(conn, action_by=action_by, qc_pack_id=qc_pack_id)
        _assert(fetched["id"] == qc_pack_id, f"kept bulk qc_pack not found: {qc_pack_id}")

    logging.info("QC pack bulk: verified %s kept and %s deleted", keep_count, delete_count)


def run_integration_test(conn) -> None:
    logging.info("Clearing qc_pack table")
    conn.execute_command("TRUNCATE TABLE data.qc_pack CASCADE")

    logging.info("Starting qc_pack integration test")
    action_by = get_default_user_id(conn)

    _run_crud_lifecycle(conn, action_by)
    _run_bulk_lifecycle(conn, action_by)

    logging.info("qc_pack integration test completed")
