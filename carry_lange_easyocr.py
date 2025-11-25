import os
import easyocr
import cv2
from PIL import Image
import numpy as np

reader = easyocr.Reader(['ko', 'en'])


# 경로를 상위 폴더로 수정
re_img_path = 'make_img'

# 모듈 수준의 전역 변수
has_title = False
title = ""

def img_resize(img_path, num):
    # --- Image Preprocessing ---
    # 1. Use Pillow to open the image and convert RGBA to RGB
    pil_img = Image.open(img_path).convert('RGB')
    
    # 2. Convert Pillow's RGB image to OpenCV's BGR format
    process_img = np.array(pil_img)
    process_img = cv2.cvtColor(process_img, cv2.COLOR_RGB2BGR)

    # 3. Smartly resize the image if it's too large
    MAX_WIDTH = 1200
    height, width, _ = process_img.shape
    
    if width > MAX_WIDTH:
        # Calculate new height to maintain aspect ratio
        new_height = int(MAX_WIDTH * height / width)
        # Use INTER_AREA for shrinking, it's generally better
        process_img = cv2.resize(process_img, (MAX_WIDTH, new_height), interpolation=cv2.INTER_AREA)

    # 4. Convert the final image to Grayscale for OCR
    gray_img = cv2.cvtColor(process_img, cv2.COLOR_BGR2GRAY)

    # Create the output directory if it doesn't exist
    if not os.path.exists(re_img_path):
        os.makedirs(re_img_path)
        
    # 5. Save the processed image, overwriting if it exists
    output_path = os.path.join(re_img_path, f're_img_{num}.png')
    cv2.imwrite(output_path, gray_img)

def is_sender(info):
    # Adjusted range for sender names based on debug output
    top_left_x = info[0][0][0]
    if top_left_x >= 130 and top_left_x <= 150:
        return True
    else:
        return False

def is_user(info):
    # Adjusted range for user messages (right-aligned) based on debug output and image width
    top_left_x = info[0][1][0]
    if top_left_x > 1030 and top_left_x < 1040:
        return True
    else:
        return False

def is_message(info):
    # Adjusted range for sender messages based on debug output
    top_left_x = info[0][0][0]
    if top_left_x >= 160 and top_left_x <= 190:
        return True
    else:
        return False

def is_title(info):
    if info[0][0][0] > 150 and info[0][1][0] < 840 and info[0][0][1] > 125 and info[0][2][1] < 205:
        return True
    else:
        return False
        
def groupping_func(result):
    global has_title, title
    
    result_length = len(result)
    chat_content = []
    is_continue_chat = False
    
    for i in range(0, result_length):
            if not(has_title):
                if is_title(result[i]):
                    has_title = True
                    title += result[i][1]
            
            # A potential IndexError is guarded here.
            if is_continue_chat:
                chat_content[-1] += " " + result[i][1]
                if i + 1 >= result_length or is_sender(result[i + 1]) or is_user(result[i + 1]):
                    is_continue_chat = False
                continue

            if is_sender(result[i]):
                if i + 1 < result_length and is_message(result[i + 1]):
                    chat_content.append(result[i][1] + " :")
                    is_continue_chat = True
            
            elif is_user(result[i]):
                chat_content.append("me : " + result[i][1])
                if i + 1 < result_length and is_user(result[i + 1]):
                    is_continue_chat = True
    
    return chat_content
                    
def character_extraction(img_path):
    full_text = ""
    if os.path.exists(img_path):
        result = groupping_func(reader.readtext(img_path))
        full_text = '\n'.join(result)
    else:
        print(f"Error : file {img_path} not Found!")
    return full_text

def start_easyocr(img_paths):

    global title, has_title
    
    # 함수 호출 시마다 title 상태 초기화
    title = ""
    has_title = False
    
    result_text = ""
    
    for i, path in enumerate(img_paths):
        resized_img_path = os.path.join(re_img_path, f're_img_{i}.png')
        img_resize(path, i)
        result_text += character_extraction(resized_img_path) + '\n'
        
    # 추출된 텍스트와 제목을 함께 반환
    return result_text, title
