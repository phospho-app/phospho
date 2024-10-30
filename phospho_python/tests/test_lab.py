import pytest
from phospho import lab


@pytest.mark.asyncio
async def test_event_detection():
    workload = lab.Workload()

    class EventConfig(lab.JobConfig):
        event_name: str
        event_description: str

    workload.add_job(
        lab.Job(
            name="event_detection",
            id="talking_about_product",
            config=EventConfig(
                event_name="User talks about a product",
                event_description="User mentions a product in a message",
            ),
        )
    )

    messages = [
        lab.Message(
            id="current",
            # content="I don't know what you are talking about.",
            role="Assistant",
            content="You just need to click on the checkout button.",
            previous_messages=[
                lab.Message(
                    id="previous",
                    role="User",
                    content="How to buy the tires on the website?",
                ),
            ],
        ),
    ]

    await workload.async_run(messages=messages, executor_type="parallel")
    assert len(workload.results) == 1


@pytest.mark.asyncio
async def test_evaluation():
    workload = lab.Workload()

    class EvalConfig(lab.JobConfig):
        few_shot_min_number_of_examples: int

    # Create a workload
    workload = lab.Workload()
    workload.add_job(
        lab.Job(id="talking_about_product", job_function=lab.job_library.evaluate_task)
    )

    messages = [
        lab.Message(
            id="current",
            # content="I don't know what you are talking about.",
            role="Assistant",
            content="You just need to click on the checkout button.",
            previous_messages=[
                lab.Message(
                    id="previous",
                    role="User",
                    content="How to buy the tires on the website?",
                ),
            ],
        ),
    ]

    await workload.async_run(messages=messages, executor_type="parallel")
    assert len(workload.results) == 1

    messages = [
        lab.Message(
            id="current",
            # content="I don't know what you are talking about.",
            role="Assistant",
            content="You just need to click on the checkout button.",
            previous_messages=[
                lab.Message(
                    id="previous",
                    role="User",
                    content="How to buy the tires on the website?",
                ),
            ],
            metadata={
                "successful_examples": [
                    {
                        "input": "How to buy the tires on the website?",
                        "output": "You just need to click on the checkout button.",
                        "flag": "success",
                    },
                    {
                        "input": "How to buy the tires on the website?",
                        "output": "You just need to click on the checkout button.",
                        "flag": "success",
                    },
                ],
                "unsuccessful_examples": [
                    {
                        "input": "How to buy the tires on the website?",
                        "output": "I don't know what you are talking about.",
                        "flag": "failure",
                    },
                    {
                        "input": "How to buy the tires on the website?",
                        "output": "I don't know what you are talking about.",
                        "flag": "failure",
                    },
                ],
            },
        ),
    ]

    await workload.async_run(messages=messages, executor_type="parallel")
    assert len(workload.results) == 1
