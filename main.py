# main.py
import json
import time
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
from llm_client import chat_completion
from prompts import EXTRACT_METADATA, GENERATE_ANALYSIS_CODE, FIX_CODE_PROMPT
from utils import preview_file
from executor import run_python_script
import base64

app = FastAPI()

MAX_TOTAL_SECONDS = 180  # 3 minutes total end-to-end

@app.post("/api/")
async def analyze(files: List[UploadFile] = File(...)):
    """
    Accept one or more uploaded files. questions.txt MUST be included.
    We expect clients to POST multipart/form-data with files.
    """
    start_time = time.time()

    # Read uploads
    uploaded = {}
    for f in files:
        content = await f.read()
        uploaded[f.filename] = content

    # Must have questions.txt
    if "questions.txt" not in uploaded:
        return JSONResponse({"error": "questions.txt is required"}, status_code=400)

    question_text = uploaded["questions.txt"].decode("utf-8", errors="ignore")

    # Build file previews for metadata extraction
    files_list_lines = []
    for fname, content in list(uploaded.items()):
        if fname == "questions.txt":
            continue
        pr = preview_file(fname, content)
        files_list_lines.append(f"- {fname}: {pr}")

    files_list_text = "\n".join(files_list_lines) if files_list_lines else "No extra files uploaded."

    # 1) Use LLM to extract metadata
    msg = [{"role":"system", "content":"You are a metadata-extraction assistant."},
           {"role":"user", "content": EXTRACT_METADATA.format(question_text=question_text, files_list=files_list_text)}]
    meta_out = chat_completion(msg, model="gpt-4o-mini", max_tokens=800, temperature=0.0)
    # Expect valid JSON. Try to parse; if not parseable, wrap it.
    try:
        metadata_json = json.loads(meta_out)
    except Exception:
        # attempt to recover with the LLM: ask it to emit JSON only
        msg2 = [{"role":"system","content":"You must return valid JSON only."},
                {"role":"user","content":"Previous output could not be parsed as JSON. Here was the output:\n\n" + meta_out + "\n\nPlease return a JSON object with file metadata only."}]
        metadata_out2 = chat_completion(msg2, model="gpt-4o-mini", max_tokens=800)
        metadata_json = json.loads(metadata_out2)

    # 2) Ask LLM to produce analysis code
    msg = [
        {"role":"system","content":"You are a python data analysis assistant. Produce a single python script."},
        {"role":"user","content": GENERATE_ANALYSIS_CODE.format(question_text=question_text, metadata_json=json.dumps(metadata_json))}
    ]
    script = chat_completion(msg, model="gpt-4o-mini", max_tokens=2000, temperature=0.0)

    # 3) Run the code in executor, loop on errors until success or time exhausted
    total_elapsed = lambda: time.time() - start_time
    attempt = 0
    while total_elapsed() < MAX_TOTAL_SECONDS and attempt < 5:
        attempt += 1
        returncode, stdout, stderr = run_python_script(script, uploaded, timeout_seconds=120)
        if returncode == 0:
            # Expect stdout is pure JSON
            try:
                result = json.loads(stdout.strip())
                return JSONResponse(result)
            except Exception as e:
                # Not JSON — send stderr + stdout back to LLM to fix
                stderr_text = stderr + "\nSTDOUT:\n" + stdout
                fix_msg = [
                    {"role":"system","content":"You will get an execution error. Fix the python script so it prints only final JSON to stdout."},
                    {"role":"user","content": FIX_CODE_PROMPT.format(error_text=stderr_text, script=script)}
                ]
                script = chat_completion(fix_msg, model="gpt-4o-mini", max_tokens=2000, temperature=0.0)
                continue
        else:
            # send error text back to LLM to fix the script
            stderr_text = stderr if stderr else "Non-zero return code: " + str(returncode)
            fix_msg = [
                {"role":"system","content":"You will get an execution error. Fix the python script so it prints only final JSON to stdout."},
                {"role":"user","content": FIX_CODE_PROMPT.format(error_text=stderr_text, script=script)}
            ]
            script = chat_completion(fix_msg, model="gpt-4o-mini", max_tokens=2000, temperature=0.0)
            continue

    return JSONResponse({"error":"Failed to produce a valid JSON result within time/attempts", "last_stderr": stderr}, status_code=500)
