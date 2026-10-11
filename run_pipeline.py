import subprocess

scripts = ["daily_analytics.py",
"replies.py",
"steps_analytics.py",
"leads.py",
"load_to_bigquery.py"]

for s in scripts:
    print("Running " + s)
    subprocess.run(["python", s], check=True)
print("Pipeline complete.")