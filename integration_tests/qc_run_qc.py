# integration_tests/qc_run_qc.py


from shinto.qc import run_qc

async def run_qc_integration_test(conn):
    project_list = [
        {
            "id": "123",
            "name": "Test Project",
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
                "id": "123",
                "expression": "name == 'Test Project'",
                "onFail": {
                    "message": "Name must be 'Test Project'",
                }
            }
        ]
    }
    result = await run_qc(project_list, taxonomy, pack)
    assert result["issues"] == 0
    assert result["majorIssues"] == 0
    assert result["failedCheckIds"] == []
    assert result["detailIssues"] == []
    assert result["project_qc"]["issues"] == 0
    assert result["project_qc"]["majorIssues"] == 0
    assert result["project_qc"]["failedCheckIds"] == []
    assert result["project_qc"]["detailIssues"] == []
