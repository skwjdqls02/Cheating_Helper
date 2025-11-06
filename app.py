import os
import uuid
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from werkzeug.utils import secure_filename
import traceback

from open_ai_api import start_open_ai_api

app = FastAPI()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    summary: str = Form(None),
    role: str = Form(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No selected files")

    saved_filepaths = []
    try:
        for file in files:
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = str(uuid.uuid4()) + file_extension
            
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Save the uploaded file
            with open(filepath, "wb") as buffer:
                buffer.write(await file.read())
            
            saved_filepaths.append(filepath)

        # Call the existing async function
        reply, new_summary, found_title = await start_open_ai_api(saved_filepaths, summary, role)
        
        # Return the results as a dictionary
        return {
            'results': reply,
            'summary': new_summary,
            'title': found_title
        }

    except Exception as e:
        # Provide a more detailed error response
        return JSONResponse(
            status_code=500,
            content={'error': str(e), 'traceback': traceback.format_exc()}
        )

    finally:
        # Clean up the saved files
        for filepath in saved_filepaths:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
