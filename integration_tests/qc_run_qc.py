# integration_tests/qc_run_qc.py

import asyncio

from shinto.qc import run_qc


def run_qc_integration_test(conn):
    """conn is unused; kept for parity with other integration tests."""
    del conn
    project_list = [
        {
            "id": "123",
            "data": {
                "name": "Test Project",
            },
        }
    ]
    taxonomy = {
        "fields": [
            {
                "name": "name",
                "type": "string",
            }
        ]
    }
    pack = {
        "rules": [
            {
                "id": "name_ok",
                "kind": "assert",
                "scope": "project",
                "expression": "name == 'Test Project'",
                "onFail": {
                    "message": "Name must be 'Test Project'",
                },
            }
        ]
    }
    result = asyncio.run(run_qc(project_list, taxonomy, pack))

    assert result["issues"] == 0
    assert result["majorIssues"] == []
    assert result["label"] == "goed"
    assert result["taxonomyIssues"] == []
    assert result["projectQcById"] == {}
    assert result["summary"]["data"]["projectsWithIssues"] == 0
    assert result["checkOverview"][0]["pass"] is True
    assert result["checkOverview"][0]["failCount"] == 0

    project_qc = project_list[0]["data"]["qc"]
    assert project_qc["issues"] == 0
    assert project_qc["majorIssues"] == []
    assert project_qc["failedCheckIds"] == []
    assert project_qc["detailIssues"] == []
    assert project_qc["project_qc"]["issues"] == 0
