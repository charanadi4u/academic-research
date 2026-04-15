# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test deployment of Academic Research Agent to Agent Engine."""

import os

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")
flags.DEFINE_string(
    "resource_id",
    None,
    "ReasoningEngine resource ID (returned after deploying the agent)",
)
flags.DEFINE_string("user_id", None, "User ID (can be any string).")
flags.mark_flag_as_required("resource_id")
flags.mark_flag_as_required("user_id")


def main(argv: list[str]) -> None:  # pylint: disable=unused-argument
    load_dotenv()

    # Priority: Flag > Environment Variable
    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    if not all([project_id, location, bucket]):
        print(
            "Missing required configuration: GOOGLE_CLOUD_PROJECT, LOCATION, or BUCKET."
        )
        print("Please set them as flags or environment variables.")
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    try:
        agent = agent_engines.get(FLAGS.resource_id)
        print(f"Found agent with resource ID: {FLAGS.resource_id}")

        session = agent.create_session(user_id=FLAGS.user_id)
        print(f"Created session for user ID: {FLAGS.user_id}")
        print("Type 'quit' to exit.")

        while True:
            user_input = input("Input: ")
            if user_input.lower() == "quit":
                break

            for event in agent.stream_query(
                user_id=FLAGS.user_id, session_id=session["id"], message=user_input
            ):
                if "content" in event and "parts" in event["content"]:
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            print(f"Response: {part['text']}")

        agent.delete_session(user_id=FLAGS.user_id, session_id=session["id"])
        print(f"Deleted session for user ID: {FLAGS.user_id}")

    except Exception as e:
        print(f"Error during deployment test: {e}")


if __name__ == "__main__":
    app.run(main)
