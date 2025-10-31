

import os
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
# easyocr 이미지 처리를 위한 함수를 import 합니다.
# 실제 함수 이름으로 변경해야 할 수 있습니다.
from open_ai_api import start_open_ai_api

app = Flask(__name__)

# 업로드된 파일을 저장할 디렉토리 설정
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False # 한글 깨짐 방지

@app.route('/upload', methods=['POST'])
def upload_images(): # 함수 이름을 복수형으로 변경
    # 'files' 키로 여러 파일들을 리스트로 받음
    files = request.files.getlist('files')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400

    saved_filepaths = []

    try:
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                # 고유한 파일 이름 생성 (UUID + 원래 확장자)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = str(uuid.uuid4()) + file_extension
                
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                saved_filepaths.append(filepath)

                # 이미지 처리 함수 호출
                
        extracted_text = start_open_ai_api(saved_filepaths)
        
        return jsonify({'results': extracted_text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # 성공 여부와 관계없이 모든 임시 파일 삭제
        for filepath in saved_filepaths:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == '__main__':
    # 외부에서 접근 가능하도록 host를 '0.0.0.0'으로 설정
    app.run(host='0.0.0.0', port=5000, debug=True)

