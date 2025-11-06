import os
import easyocr
import cv2

reader = easyocr.Reader(['ko', 'en'])


# 경로를 상위 폴더로 수정
re_img_path = 'make_img'

# 모듈 수준의 전역 변수
has_title = False
title = ""

def img_resize(img_path, num):
    size_up = 2.0
    
    process_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    img_width = int(process_img.shape[1] * size_up)
    img_height = int(process_img.shape[0] * size_up)
    img_info = (img_width, img_height)
    
    # re_img_path 디렉토리가 없으면 생성
    if not os.path.exists(re_img_path):
        os.makedirs(re_img_path)
        
    return cv2.imwrite(os.path.join(re_img_path, f're_img_{num}.png'), cv2.resize(process_img, img_info, interpolation=cv2.INTER_CUBIC))

def is_sender(info):
    if info[0][0][0] > 250 and info[0][0][0] < 350:
        return True
    else:
        return False

def is_user(info):
    if info[0][1][0] > 2150 and info[0][1][0] <= 2250:
        return True
    else:
        return False

def is_message(info):
    if info[0][0][0] >= 350 and info[0][0][0] < 400:
        return True
    else:
        return False

def is_title(info):
    if info[0][0][0] > 430 and info[0][2][0] < 1500 and info[0][0][1] > 350 and info[0][2][1] < 500:
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
