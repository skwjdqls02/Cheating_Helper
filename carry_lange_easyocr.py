import os
import easyocr
import cv2
from PIL import Image
import numpy as np
import re

reader = easyocr.Reader(['ko', 'en'])


# 경로를 상위 폴더로 수정
re_img_path = 'make_img'



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
    return process_img.shape[1], process_img.shape[0] # Return height


def is_ui_element(text, y_pos, image_height):
    text = text.strip()
    # Regex for "오전/오후/ HH:MM" or "오전/오후/ H.MM" or "오전/오후/ H*MM"
    if re.fullmatch(r'(오전|오후|)\s*\d{1,2}[:.*]\d{1,2}', text):
        return True
        
    # Check for message input field (usually at the very bottom)
    if y_pos > image_height * 0.93 or "메시지 입력" in text:
        return True
    
    elif y_pos <= image_height * 0.09:
        return True
    
    return False

def groupping_func(result, image_height, image_width):
    start = 0
    end = 0
    for i in range(0, len(result)):
        if result[i][0][0][1] <= image_height * 0.09:
            start = i
        elif result[i][0][0][1] <= image_height * 0.9:
            end = i
    partial = result[start:end]
    
    # 왼쪽 위 x좌표 기준 정렬
    partial_sorted = sorted(partial, key=lambda item: item[0][0][0])
    min_x = partial_sorted[0][0][0][0]
    chat_content = [""]
    tmp = 5
    in_name = False
    
    for i in range(0, len(result)):
        if is_ui_element(result[i][1], result[i][0][0][1], image_height):
            continue
        
        # me : 
        elif (result[i][0][0][0] + result[i][0][1][0]) / 2 > ((image_width * 0.5) + tmp):
            if image_width * 0.8 < result[i][0][1][0]:
                if chat_content[-1][:2] == "me":
                    chat_content[-1] += result[i][1]
                else:
                    chat_content.append(f'me:{result[i][1]}')
        
        # x축 기준 왼쪽 이름 or 전송 내용
        elif (result[i][0][0][0] + result[i][0][1][0]) / 2 < ((image_width * 0.5) - tmp):
            if result[i][0][0][0] - tmp <= min_x <= result[i][0][0][0] + tmp:
                chat_content.append(f'{result[i][1]}:')
                in_name = True
            else:
                if not(in_name) and chat_content[-1][:2] == "me" and result[i][0][0][0] < image_width * 0.2:
                    chat_content.append(f"sender:{result[i][1]}")
                else:
                    chat_content[-1] += result[i][1]
    
    return chat_content
        
    
def character_extraction(img_path, image_height, image_width):
    full_text = ""
    if os.path.exists(img_path):
        test = reader.readtext(img_path)
        result = groupping_func(test, image_height, image_width)
        full_text = '\n'.join(result)
    else:
        print(f"Error : file {img_path} not Found!")
    return full_text

def start_easyocr(img_paths):
    
    result_text = ""
    
    for i, path in enumerate(img_paths):
        resized_img_path = os.path.join(re_img_path, f're_img_{i}.png')
        width, height = img_resize(path, i)
        result_text += character_extraction(resized_img_path, height, width) + '\n'
    return result_text
