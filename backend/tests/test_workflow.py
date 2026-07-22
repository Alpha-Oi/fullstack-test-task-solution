from src.workers.tasks import build_file_processing_workflow


def test_scan_and_metadata_tasks_are_grouped_for_parallel_execution() -> None:
    workflow = build_file_processing_workflow("file-id")
    assert len(workflow.tasks) == 2
    parallel_step = workflow.tasks[1]
    assert parallel_step.task == "celery.chord"
    assert {task.task for task in parallel_step.tasks} == {
        "files.scan",
        "files.extract_metadata",
    }
    assert parallel_step.body.task == "files.finalize"
