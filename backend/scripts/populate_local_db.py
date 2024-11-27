"""
This script is meant to be run in local environment to populate the local test database with test data.
"""

import datetime
import random

import phospho
from dotenv import load_dotenv
from tqdm import tqdm

# Load env variables form the .env
load_dotenv()

# Get the project id from the user inpout in the terminal
project_id = input("Enter the project id: ")
phospho_api_key = input("Enter the phospho api key: ")

# Override the default values with the test values
phospho.config.BASE_URL = "http://127.0.0.1:8000/v2"

phospho.init(api_key=phospho_api_key, project_id=project_id)

print("Populating the test database with test data...")
# Populate with some test data
# This is how you log a task to phospho
phospho.log(
    input="Some input",
    output="Some output",
    # Optional: for chats, group tasks together in sessions
    # session_id = "session_1",
)

# Some more
phospho.log(
    input="What is the weather like today?",
    output="It's suny and warm.",
)

# Create a session
phospho.log(
    input="Some input for a session",
    output="Some output for a session",
    session_id="session_1",
)

# Some more
phospho.log(
    input="Some more input for a session",
    output="Some more output for a session",
    session_id="session_1",
)

print("Logged some test data to the test database.")

# Boost it up.
if True:
    print("Logging 1000 tasks to the test database...")
    for i in tqdm(range(4)):
        # Create a random date in the last week
        random_date = datetime.datetime.now() - datetime.timedelta(days=7)
        random_date = random_date + datetime.timedelta(days=random.randint(0, 7))
        random_date = random_date + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24)
        )
        phospho.log(
            input="Some input",
            output="Some output",
            session_id=phospho.new_session(),
            created_at=int(random_date.timestamp()),
            user_id=random.sample(
                ["Roger", "Frederic Jacob", "nicolas@gmail.com", "+33292566776"], 1
            )[0],
        )
