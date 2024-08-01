from loguru import logger
import json
import tempfile

from app.db.mongo import get_mongo_db
from app.db.models import FineTuningJob
from app.core import config
import pandas as pd

import openai

anyscale_client = openai.OpenAI(
    base_url=config.ANYSCALE_BASE_URL, api_key=config.ANYSCALE_API_KEY
)

system_prompt = "You are a helpful assistant that assert if an event is present in a given text. Your respond Yes if the event is present in the text, and Yes otherwise. You only respond with the word 'Yes' or 'No'."


def convert_to_msg(row):
    """
    Takes as input a row from the pandas dataframe and returns a message object
    """
    row["detection_scope"]
    if row["label"]:
        llm_response = "Yes"
    else:
        llm_response = "No"

    # TODO: improve the prompts based on the scope
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"The event to detect is: {row['event_description']}. The following is a conversation between a user and an assistant. The user says: {row['task_input']}. The assistant responds: {row['task_output']}. Is the event present in the text?",
            },
            {"role": "assistant", "content": llm_response},
        ]
    }


async def start_fine_tuning_job(fine_tuning_job: FineTuningJob):
    mongo_db = await get_mongo_db()

    # Store the document in the database
    await mongo_db["fine_tuning_jobs"].insert_one(fine_tuning_job.model_dump())

    # Load all the documents with the matching file_id and org_id
    documents = (
        await mongo_db["datasets"]
        .find({"file_id": fine_tuning_job.file_id, "org_id": fine_tuning_job.org_id})
        .to_list(length=None)
    )

    # Check we have enough documents to start the fine-tuning job

    # Trim the documents if there are too many

    # Get the required parameters for the fine-tuning job
    detection_scope = fine_tuning_job.parameters.get("detection_scope", None)
    event_description = fine_tuning_job.parameters.get("event_description", None)

    if not detection_scope or not event_description:
        logger.error(
            f"Missing parameters for the fine-tuning job: detection_scope: {detection_scope}, event_description: {event_description}. Aborting job."
        )
        # Update the fine-tuning job status to cancelled
        await mongo_db["fine_tuning_jobs"].update_one(
            {"id": fine_tuning_job.id}, {"$set": {"status": "cancelled"}}
        )
        return

    # Load the list of documents in a pandas dataframe
    df = pd.DataFrame(documents)

    # For each database row, delete it if it is not of the type detection_scope
    if detection_scope == "task_input_only":
        df = df[df["detection_scope"] == "task_input_only"]
    elif detection_scope == "task_output_only":
        df = df[df["detection_scope"] == "task_output_only"]
    else:
        logger.error(
            f"Detection scope {detection_scope} is not supported. Aborting job."
        )
        # Update the fine-tuning job status to cancelled
        await mongo_db["fine_tuning_jobs"].update_one(
            {"id": fine_tuning_job.id}, {"$set": {"status": "cancelled"}}
        )
        return

    logger.debug(
        f"Found {len(df)} documents for the fine-tuning job with type {detection_scope}"
    )

    # Check we have enough documents to start the fine-tuning job
    if len(df) < config.FINE_TUNING_MINIMUM_DOCUMENTS:
        logger.warning(
            f"Found {len(df)} documents for the fine-tuning job. We need at least {config.FINE_TUNING_MINIMUM_DOCUMENTS}. Aborting job."
        )
        # Update the fine-tuning job status to cancelled
        await mongo_db["fine_tuning_jobs"].update_one(
            {"id": fine_tuning_job.id}, {"$set": {"status": "cancelled"}}
        )
        return

    # TODO: Check we only have a single event description

    # Split the df in 80% train and 20% validation
    train_dataset = df.sample(frac=0.8, random_state=42)
    validation_dataset = df.drop(train_dataset.index)

    # Save this to a temporary file:
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=True, mode="w+") as temp:
        for index, row in train_dataset.iterrows():
            json.dump(convert_to_msg(row), temp)
            temp.write("\n")
        temp.seek(0)  # Reset file pointer to the beginning

        logger.debug(f"Temporary file created: {temp.name}")

        # Read the contents of the file into a bytes object
        file_content = temp.read().encode()

        anyscale_training_file_id = anyscale_client.files.create(
            file=file_content,
            purpose="fine-tune",
        ).id

        logger.debug(f"Anyscale training file created: {anyscale_training_file_id}")

    # Save the file id to the fine-tuning job document in the database
    await mongo_db["fine_tuning_jobs"].update_one(
        {"id": fine_tuning_job.id},
        {"$set": {"anyscale_training_file_id": anyscale_training_file_id}},
    )

    # Do the same for the validation dataset
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=True, mode="w+") as temp:
        for index, row in validation_dataset.iterrows():
            json.dump(convert_to_msg(row), temp)
            temp.write("\n")
        temp.seek(0)  # Reset file pointer to the beginning

        logger.debug(f"Temporary file created: {temp.name}")

        # Read the contents of the file into a bytes object
        file_content = temp.read().encode()

        anyscale_validation_file_id = anyscale_client.files.create(
            file=file_content,
            purpose="fine-tune",
        ).id

        logger.debug(f"Anyscale validation file created: {anyscale_validation_file_id}")

    # Save the file id to the fine-tuning job document in the database
    await mongo_db["fine_tuning_jobs"].update_one(
        {"id": fine_tuning_job.id},
        {"$set": {"anyscale_validation_file_id": anyscale_training_file_id}},
    )

    # Start the fine-tuning job on Anyscale
    anyscale_finetuning_job_id = anyscale_client.fine_tuning.jobs.create(
        training_file=anyscale_training_file_id,
        validation_file=anyscale_validation_file_id,
        model=fine_tuning_job.model,
    ).id

    logger.info(
        f"Anyscale fine-tuning job created: {anyscale_finetuning_job_id} for fine-tuning job {fine_tuning_job.id}"
    )

    # Save the file id to the fine-tuning job document in the database
    await mongo_db["fine_tuning_jobs"].update_one(
        {"id": fine_tuning_job.id},
        {"$set": {"anyscale_finetuning_job_id": anyscale_finetuning_job_id}},
    )


async def fetch_fine_tuning_job(fine_tuning_job_id: str) -> FineTuningJob:
    mongo_db = await get_mongo_db()
    fine_tuning_job = await mongo_db["fine_tuning_jobs"].find_one(
        {"id": fine_tuning_job_id}
    )

    if not fine_tuning_job:
        raise ValueError(f"Fine-tuning job with id {fine_tuning_job_id} not found.")

    # Remove the _id key, which is not serializable
    if "_id" in fine_tuning_job:
        del fine_tuning_job["_id"]

    # Valdiate the fine_tuning_job object
    fine_tuning_job = FineTuningJob(**fine_tuning_job)

    # Convert the model to a dictionary
    fine_tuning_job_dict = fine_tuning_job.model_dump()

    # Check if there is a field for the Anyscale job id
    # Check if the key anyscale_finetuning_job_id exists
    if (
        fine_tuning_job_dict.get("anyscale_finetuning_job_id")
        and fine_tuning_job.status == "started"
    ):
        logger.debug(
            f"Fine-tuning job {fine_tuning_job_id} has a anyscale_finetuning_job_id."
        )
        # Fetch the status of the anyscale job
        anyscale_job_obj = anyscale_client.fine_tuning.jobs.retrieve(
            fine_tuning_job_dict["anyscale_finetuning_job_id"]
        )
        logger.debug(f"Anyscale job: {anyscale_job_obj}")

        # Check the status
        if anyscale_job_obj.status == "succeeded":
            # Update the phospho fine tuning job object in the db
            await mongo_db["fine_tuning_jobs"].update_one(
                {"id": fine_tuning_job_id},
                {
                    "$set": {
                        "status": "finished",
                        "fine_tuned_model": anyscale_job_obj.fine_tuned_model,
                    }
                },
            )

            # Update the object in memory
            fine_tuning_job.status = "finished"
            fine_tuning_job.fine_tuned_model = anyscale_job_obj.fine_tuned_model
            # TODO: finished at time

        elif anyscale_job_obj.status == "failed":
            logger.warning(
                f"Anyscale job {fine_tuning_job_dict['anyscale_finetuning_job_id']} with phospho id {fine_tuning_job.id} failed."
            )
            # Update the phospho fine tuning job object in the db
            await mongo_db["fine_tuning_jobs"].update_one(
                {"id": fine_tuning_job_id},
                {
                    "$set": {
                        "status": "failed",
                    }
                },
            )

            # Update the object in memory
            fine_tuning_job.status = "failed"

        elif anyscale_job_obj.status == "cancelled":
            # Update the phospho fine tuning job object in the db
            await mongo_db["fine_tuning_jobs"].update_one(
                {"id": fine_tuning_job_id},
                {
                    "$set": {
                        "status": "cancelled",
                    }
                },
            )

            # Update the object in memory
            fine_tuning_job.status = "cancelled"

        else:
            logger.debug(
                f"Anyscale job {fine_tuning_job_dict['anyscale_finetuning_job_id']} with phospho id {fine_tuning_job.id} has status: {anyscale_job_obj.status}."
            )

    return fine_tuning_job
