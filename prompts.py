# prompts.py

EXTRACT_METADATA = """
You are a data analysis assistant. The user sent the following question content between triple backticks:

{question_text}

They also uploaded the following files (names + short preview): 
{files_list}

For each uploaded file, produce a JSON dictionary describing:
- name: filename
- type: one of ["csv","parquet","json","image","text","unknown"]
- suggested_read_code: Python snippet (pandas / duckdb / open) showing how to read it and the first few columns
- expected_rows_estimate: a short estimate if you can (e.g., 'small (<1k)', 'medium (1k-100k)', 'large (>100k)').

Return just valid JSON (no explanation).
"""

GENERATE_ANALYSIS_CODE = """
You are a helpful python programmer for data analysis. The user question:
{question_text}

Available files and their metadata:
{metadata_json}

Write a single Python script that:
- reads the necessary files (use only the filenames as provided, relative paths),
- performs the analysis requested,
- constructs the final JSON response object (either an array or object) and prints it to stdout as JSON,
- if a plot is required, create it and save as PNG into /tmp/plot.png and include a base64 data URI under the appropriate JSON field,
- ensure the final printed JSON is the only stdout (no extra logging),
- keep the plot PNG under 100000 bytes: use fig.tight_layout(), small dpi, compress if needed.

Use only imports from: pandas, numpy, matplotlib, base64, io, duckdb, json, requests, bs4 (BeautifulSoup). If web scraping required, use requests + BeautifulSoup.

Write robust code that handles missing columns gracefully and raises readable exceptions.

Return only the python script (no explanation).
"""

FIX_CODE_PROMPT = """
The execution of your last script raised this error:

{error_text}

Here is the last script you produced:
