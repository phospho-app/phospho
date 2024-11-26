"""
Example script to push historical data to Phospho
"""
import pandas as pd
import phospho
from dotenv import load_dotenv

load_dotenv()

phospho.init()

# The exact conversion script depends on the file format
# We assume that the data is stored in a .csv file
# with the following columns:
# - created_at: timestamp in seconds
# - raw_input: string of a json with the input to an OpenAI completion
# - raw_output: string of a json with the output of an OpenAI completion
# - (optional) metadata: string of a json with metadata about the task
# - (optional) session_id: string with the session id

# Load the data
df = pd.read_csv(
    "/Users/nicolasoulianov/phospho/phospho/examples/push_data/example.csv", sep=";"
)

# Convert the created_at column to int
df["created_at"] = df["created_at"].astype(int)

# Convert the raw_input and raw_output columns to dicts
df["raw_input"] = df["raw_input"].apply(lambda x: eval(x))
df["raw_output"] = df["raw_output"].apply(lambda x: eval(x))

# Convert the metadata column to dicts
df["metadata"] = df["metadata"].apply(lambda x: eval(x) if not pd.isna(x) else {})

# Where session_id is NA, replace with a random uuid
# (or any other unique string)
df["session_id"] = df["session_id"].apply(
    lambda x: phospho.generate_uuid() if pd.isna(x) else x
)

# Iterate over the lines and do phospho.log
# This will create the sessions and tasks in the database
# and trigger the event detection pipeline
for _, row in df.iterrows():
    phospho.log(
        row["raw_input"],
        row["raw_output"],
        created_at=row["created_at"],
        metadata=row["metadata"],
        session_id=row["session_id"],
        # This is how to customize the input/output to string conversion
        # The input and output will be logged in raw_input and raw_output
        input_to_str_function=lambda x: x["prompt"],
        output_to_str_function=lambda x: x["choices"][0]["text"],
    )
