# integration_tests/transformation.py

import logging

from shinto.juno.data import projects_to_stage_data
from shinto.mimir.base import get_default_user_id
from shinto.mimir.data import (
    create_transformation,
    delete_transformation,
    get_transformation_by_id,
    get_transformation_by_name,
    get_transformation_list,
    update_transformation,
)
from shinto.mimir.exception import MimirEntityNotFoundException
from shinto.transform import transform_data

PROCESFASE_EXPR = "'Gereed' if str(planfase).strip().lower() == 'gereed' else 'In aanbouw' if str(planfase).strip().lower().replace(' ', '_') in ['realisatie'] else 'In voorbereiding' if str(planfase).strip().lower() == 'vergunningfase' else 'In studie' if str(planologische_status).strip().upper().replace(' ', '') in ['5B', '5A', '4B', '4A'] else 'In voorbereiding' if str(planologische_status).strip().upper().replace(' ', '') in ['3', '2', '1B', '1A'] else 'Onbekend'"

PROCESFASE_TRANSFORMATION = [
    {
        "name": "Set procesfase",
        "init": "copy",
        "transformations": [
            {
                "action": "set_field",
                "key": "procesfase",
                "type": "text",
                "source": {"expr": PROCESFASE_EXPR},
            }
        ],
    }
]

DALSTRAAT_PROJECT = {
    "id": "f550b2b0-4f1b-4676-9c8a-9e40899db1a5",
    "data": {
        "naam": "Dalstraat 2, Kerkstraat 68 en 70, Lambert Goofersstraat 1 en 3",
        "stages": [
            {
                "planfase": "gereed",
                "planstatus": "gereed",
                "project_id": "f550b2b0-4f1b-4676-9c8a-9e40899db1a5",
                "stage_uuid": "f70285ae-8adf-4135-bb1d-d85441f7640c",
                "planologische_status": "1A",
                "bruto_aantalwoningen": 5,
            }
        ],
        "project_id": "f550b2b0-4f1b-4676-9c8a-9e40899db1a5",
    },
}

BULK_COUNT = 1000
BULK_DELETE_RATIO = 0.4
BULK_NAME_PREFIX = "transformation_bulk_"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run_crud_lifecycle(conn, action_by) -> None:
    logging.info("Transformation CRUD: create")
    created = create_transformation(
        conn,
        action_by=action_by,
        name="transformation_crud_test",
        data={
            "steps": [
                {
                    "name": "Copy name",
                    "init": "copy",
                    "transformations": [
                        {
                            "action": "add_field",
                            "key": "contact_name",
                            "type": "string",
                            "source": {"coalesce": ["preferred_name", "full_name"]},
                        }
                    ],
                }
            ]
        },
    )
    transformation_id = created["id"]
    _assert(
        created["name"] == "transformation_crud_test",
        f"unexpected name after create: {created}",
    )
    _assert(
        created["data"]["steps"][0]["name"] == "Copy name",
        f"unexpected data after create: {created}",
    )

    logging.info("Transformation CRUD: get after create")
    fetched = get_transformation_by_id(
        conn, action_by=action_by, transformation_id=transformation_id
    )
    _assert(fetched["id"] == transformation_id, "get by id did not return created transformation")
    _assert(fetched["name"] == "transformation_crud_test", "get by id returned wrong name")

    logging.info("Transformation CRUD: get by name after create")
    fetched = get_transformation_by_name(
        conn, action_by=action_by, transformation_name="transformation_crud_test"
    )
    _assert(fetched["id"] == transformation_id, "get by name did not return created transformation")
    _assert(
        fetched["data"]["steps"][0]["transformations"][0]["key"] == "contact_name",
        "get by name returned wrong data",
    )

    logging.info("Transformation CRUD: list after create")
    transformations = get_transformation_list(conn, action_by=action_by)
    _assert(
        any(item["id"] == transformation_id for item in transformations),
        "created transformation missing from list",
    )

    logging.info("Transformation CRUD: update")
    updated = update_transformation(
        conn,
        action_by=action_by,
        transformation_id=transformation_id,
        name="transformation_crud_updated",
        data={
            "steps": [
                {
                    "name": "Set display name",
                    "init": "copy",
                    "transformations": [
                        {
                            "action": "set_field",
                            "key": "display_name",
                            "type": "string",
                            "source": "full_name",
                        }
                    ],
                }
            ]
        },
    )
    _assert(
        updated["name"] == "transformation_crud_updated",
        f"unexpected name after update: {updated}",
    )
    _assert(
        updated["data"]["steps"][0]["name"] == "Set display name",
        f"unexpected data after update: {updated}",
    )

    logging.info("Transformation CRUD: get after update")
    fetched = get_transformation_by_id(
        conn, action_by=action_by, transformation_id=transformation_id
    )
    _assert(fetched["name"] == "transformation_crud_updated", "get after update returned wrong name")
    _assert(
        fetched["data"]["steps"][0]["transformations"][0]["key"] == "display_name",
        "get after update returned wrong data",
    )

    logging.info("Transformation CRUD: get by name after update")
    fetched = get_transformation_by_name(
        conn, action_by=action_by, transformation_name="transformation_crud_updated"
    )
    _assert(fetched["id"] == transformation_id, "get by name after update returned wrong id")

    logging.info("Transformation CRUD: list after update")
    transformations = get_transformation_list(conn, action_by=action_by)
    listed = next(item for item in transformations if item["id"] == transformation_id)
    _assert(listed["name"] == "transformation_crud_updated", "list after update returned wrong name")

    logging.info("Transformation CRUD: delete")
    deleted = delete_transformation(
        conn, action_by=action_by, transformation_id=transformation_id
    )
    _assert(deleted["action"] == "deleted", f"unexpected action after delete: {deleted}")

    logging.info("Transformation CRUD: get after delete (expect not found)")
    try:
        get_transformation_by_id(
            conn, action_by=action_by, transformation_id=transformation_id
        )
    except MimirEntityNotFoundException:
        logging.info("Transformation correctly not found after delete")
    else:
        raise AssertionError("expected MimirEntityNotFoundException after delete")

    try:
        get_transformation_by_name(
            conn, action_by=action_by, transformation_name="transformation_crud_updated"
        )
    except MimirEntityNotFoundException:
        logging.info("Transformation correctly not found by name after delete")
    else:
        raise AssertionError("expected MimirEntityNotFoundException for get by name after delete")

    transformations = get_transformation_list(conn, action_by=action_by)
    _assert(
        all(item["id"] != transformation_id for item in transformations),
        "deleted transformation still present in list",
    )


def _run_bulk_lifecycle(conn, action_by) -> None:
    delete_count = int(BULK_COUNT * BULK_DELETE_RATIO)
    keep_count = BULK_COUNT - delete_count

    logging.info("Transformation bulk: creating %s records", BULK_COUNT)
    created_ids = []
    for index in range(BULK_COUNT):
        record = create_transformation(
            conn,
            action_by=action_by,
            name=f"{BULK_NAME_PREFIX}{index:04d}",
            data={"index": index},
        )
        created_ids.append(record["id"])

    listed = [
        item
        for item in get_transformation_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(
        len(listed) == BULK_COUNT,
        f"expected {BULK_COUNT} bulk transformations, got {len(listed)}",
    )

    ids_to_delete = created_ids[:delete_count]
    ids_to_keep = created_ids[delete_count:]

    logging.info(
        "Transformation bulk: deleting %s records (%.0f%%)",
        delete_count,
        BULK_DELETE_RATIO * 100,
    )
    for transformation_id in ids_to_delete:
        delete_transformation(
            conn, action_by=action_by, transformation_id=transformation_id
        )

    listed = [
        item
        for item in get_transformation_list(conn, action_by=action_by)
        if item["name"].startswith(BULK_NAME_PREFIX)
    ]
    _assert(
        len(listed) == keep_count,
        f"expected {keep_count} remaining bulk transformations, got {len(listed)}",
    )

    remaining_ids = {item["id"] for item in listed}
    _assert(
        remaining_ids == set(ids_to_keep),
        "remaining bulk transformation ids do not match expected set",
    )

    for transformation_id in ids_to_delete:
        try:
            get_transformation_by_id(
                conn, action_by=action_by, transformation_id=transformation_id
            )
        except MimirEntityNotFoundException:
            continue
        raise AssertionError(
            f"deleted bulk transformation still retrievable: {transformation_id}"
        )

    for transformation_id in ids_to_keep:
        fetched = get_transformation_by_id(
            conn, action_by=action_by, transformation_id=transformation_id
        )
        _assert(
            fetched["id"] == transformation_id,
            f"kept bulk transformation not found: {transformation_id}",
        )

    logging.info(
        "Transformation bulk: verified %s kept and %s deleted", keep_count, delete_count
    )


def _run_procesfase_pipeline(conn, action_by) -> None:
    """Store the procesfase transformation, then apply it to the Dalstraat project."""
    logging.info("Transformation pipeline: create procesfase transformation")
    created = create_transformation(
        conn,
        action_by=action_by,
        name="procesfase_dalstraat",
        data=PROCESFASE_TRANSFORMATION,
    )

    logging.info("Transformation pipeline: load procesfase transformation and apply it")
    loaded = get_transformation_by_name(
        conn, action_by=action_by, transformation_name="procesfase_dalstraat"
    )
    result = transform_data(projects_to_stage_data([DALSTRAAT_PROJECT]), loaded)
    _assert(len(result) == 1, f"expected one stage row, got {len(result)}")
    _assert(result[0]["planfase"] == "gereed", f"planfase was {result[0].get('planfase')!r}")
    _assert(
        result[0]["planologische_status"] == "1A",
        f"planologische_status was {result[0].get('planologische_status')!r}",
    )
    _assert(
        result[0]["procesfase"] == "Gereed",
        f"procesfase was {result[0].get('procesfase')!r}",
    )

    delete_transformation(conn, action_by=action_by, transformation_id=created["id"])


def run_integration_test(conn) -> None:
    logging.info("Clearing transformation table")
    conn.execute_command("TRUNCATE TABLE data.transformation CASCADE")

    logging.info("Starting transformation integration test")
    action_by = get_default_user_id(conn)

    _run_procesfase_pipeline(conn, action_by)
    _run_crud_lifecycle(conn, action_by)
    _run_bulk_lifecycle(conn, action_by)

    logging.info("transformation integration test completed")
