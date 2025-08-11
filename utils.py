# utils.py
import pandas as pd
import io
import base64
from PIL import Image
import os

def preview_file(filename: str, content: bytes):
    lower = filename.lower()
    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), nrows=5)
            return {"type": "csv", "preview_columns": list(df.columns)}
        if lower.endswith(".parquet"):
            import pyarrow.parquet as pq
            import pyarrow as pa
            # quick: read metadata with pandas
            df = pd.read_parquet(io.BytesIO(content))
            return {"type": "parquet", "preview_columns": list(df.columns)}
        if lower.endswith(".json"):
            import json
            obj = json.loads(content.decode("utf8", errors="ignore"))
            if isinstance(obj, dict):
                return {"type": "json", "keys": list(obj.keys())}
            return {"type": "json", "len": len(obj)}
        if any(lower.endswith(ext) for ext in [".png",".jpg",".jpeg",".webp"]):
            im = Image.open(io.BytesIO(content))
            return {"type": "image", "size": im.size, "format": im.format}
        if lower.endswith(".txt"):
            txt = content.decode("utf8", errors="ignore")
            return {"type": "text", "head": txt[:200]}
    except Exception as e:
        return {"type": "unknown", "error": str(e)}
    return {"type": "unknown"}
