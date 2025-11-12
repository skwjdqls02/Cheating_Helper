import os
import uuid
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from werkzeug.utils import secure_filename
import traceback

from open_ai_api import start_open_ai_api, regenerate_replies

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
            
            # 사진 파일 저장 -> /uploads
            with open(filepath, "wb") as buffer:
                buffer.write(await file.read())
            
            saved_filepaths.append(filepath)

        # 요청
        reply, new_summary, found_title = await start_open_ai_api(saved_filepaths, summary, role)
        
        # 응답 json
        return {
            'results': reply,
            'summary': new_summary,
            'title': found_title
        }

    except Exception as e:
        # 에러 표시
        return JSONResponse(
            status_code=500,
            content={'error': str(e), 'traceback': traceback.format_exc()}
        )

    finally:
        # uploads에 임시 저장 사진 파일 지우기
        for filepath in saved_filepaths:
            if os.path.exists(filepath):
                os.remove(filepath)

@app.post("/regenerate")
async def regenerate_response(
    original_reply: str = Form(...),
    modification_request: str = Form(...),
    role: str = Form(...)
):
    try:
        new_replies = await regenerate_replies(original_reply, modification_request, role)
        return {
            'results': new_replies
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e), 'traceback': traceback.format_exc()}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
