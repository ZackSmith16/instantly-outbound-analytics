"""Start the Dataform daily_refresh workflow and wait for it to finish.

Runs right after the load step, so Dataform always transforms fresh data.
"""
import os
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession

PROJECT = os.environ["GCP_PROJECT_ID"]
LOCATION = "us-east1"
REPO = "instantly-outbound-analytics"
WORKFLOW_CONFIG = "daily_refresh"

repo_path = f"projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO}"
api = "https://dataform.googleapis.com/v1beta1"

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
session = AuthorizedSession(credentials)

# Start the run, using the latest production compilation and the workflow config's settings
response = session.post(
    f"{api}/{repo_path}/workflowInvocations",
    json={"workflowConfig": f"{repo_path}/workflowConfigs/{WORKFLOW_CONFIG}"},
)
response.raise_for_status()
invocation = response.json()["name"]
print("Started Dataform run: " + invocation)

# Check every 10 seconds until it finishes (give up after 10 minutes)
state = "RUNNING"
for _ in range(60):
    time.sleep(10)
    state = session.get(f"{api}/{invocation}").json()["state"]
    print("State: " + state)
    if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
        break

if state != "SUCCEEDED":
    raise SystemExit("Dataform run did not succeed (state: " + state + ")")

print("Dataform run succeeded.")
