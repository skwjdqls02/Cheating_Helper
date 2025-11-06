import os
import uuid
import sys
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# 이제 repair 폴더의 모듈을 import 할 수 있습니다.
from open_ai_api import start_open_ai_api

app = Flask(__name__)

# 업로드된 파일을 저장할 디렉토리 설정 (프로젝트 루트 기준)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False # 한글 깨짐 방지

@app.route('/upload', methods=['POST'])
async def upload_images():
    files = request.files.getlist('files')
    previous_chat_summary = request.form.get('summary')
    chat_role = request.form.get('role')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400

    saved_filepaths = []

    try:
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = str(uuid.uuid4()) + file_extension
                
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                saved_filepaths.append(filepath)

        # 1. 수정된 start_open_ai_api를 호출합니다. (인자 3개)
        # 2. 반환되는 3개의 값을 모두 받습니다.
        reply, new_summary, found_title = await start_open_ai_api(saved_filepaths, previous_chat_summary, chat_role)
        
        # 3. 받은 값들을 JSON으로 반환합니다.
        return jsonify({'results' : reply,
                        'summary' : new_summary,
                        'title' : found_title})

    except Exception as e:
        # 오류 발생 시 traceback을 포함하여 더 자세한 정보 제공
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    
    finally:
        # 성공 여부와 관계없이 모든 임시 파일 삭제
        for filepath in saved_filepaths:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)