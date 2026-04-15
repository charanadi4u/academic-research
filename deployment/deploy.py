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

"""Deployment script for Academic Research Agent."""

import logging
import os
import sys

# Add the project root to sys.path to ensure academic_research is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import vertexai  # noqa: E402
from dotenv import load_dotenv, set_key  # noqa: E402
from vertexai import agent_engines  # noqa: E402
from vertexai.preview.reasoning_engines import AdkApp  # noqa: E402

from academic_research.agent import root_agent  # noqa: E402

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants and Environment
load_dotenv()
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
ENV_FILE_PATH = os.path.join(project_root, ".env")

def update_env_file(agent_engine_id: str, env_file_path: str) -> None:
    """Updates the .env file with the agent engine ID for future use."""
    try:
        if os.path.exists(env_file_path):
            set_key(env_file_path, "AGENT_ENGINE_ID", agent_engine_id)
            logger.info(f"Updated AGENT_ENGINE_ID in {env_file_path} to {agent_engine_id}")
        else:
            logger.warning(f".env file not found at {env_file_path}. Skipping ID update.")
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")

def deploy() -> None:
    """Deploys the Academic Research agent to Vertex AI Agent Engine."""
    if not all([GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, STAGING_BUCKET]):
        logger.error("Missing required environment variables (Project, Location, or Bucket).")
        return

    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=f"gs://{STAGING_BUCKET}",
    )

    logger.info("Preparing deployment for Academic Research...")

    app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    # Note: version constraints should align with pyproject.toml
    remote_app = agent_engines.create(
        app,
        display_name="academic_research",
        requirements=[
            "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",
            "google-genai>=1.9.0",
            "pydantic>=2.10.6",
            "python-dotenv>=1.0.1",
            "google-adk>=1.0.0",
        ],
        extra_packages=[
            "./academic_research",
        ],
    )

    logger.info(f"Deployed successfully. Resource Name: {remote_app.resource_name}")

    # Update local .env for convenience
    update_env_file(remote_app.resource_name, ENV_FILE_PATH)

if __name__ == "__main__":
    deploy()
