import os
from dotenv import load_dotenv
from google.cloud import bigquery


load_dotenv()
project_id = os.getenv("GCP_PROJECT_ID")

client = bigquery.Client(project=project_id)

files = {"data/daily_analytics.csv": "daily_analytics",
        "data/steps_analytics.csv": "steps_analytics",
        "data/leads.csv": "leads",
        "data/replies.csv": "replies",
}

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    allow_quoted_newlines=True,
    write_disposition="WRITE_TRUNCATE",
)

for file_path, table_name in files.items():
    table_id = f"{project_id}.instantly_raw.{table_name}"

    with open(file_path, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)

    job.result()  # wait for the upload to finish

    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows} rows into {table_id}")