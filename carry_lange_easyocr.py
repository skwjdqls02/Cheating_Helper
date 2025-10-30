import os
import easyocr
import cv2

reader = easyocr.Reader(['ko', 'en'])

img_path = './test_img'
re_img_path = './make_img'

def img_resize(img_path, num):
    size_up = 2.0
    
    process_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    img_width = int(process_img.shape[1] * size_up)
    img_height = int(process_img.shape[0] * size_up)
    img_info = (img_width, img_height)
    
    return cv2.imwrite(re_img_path + f'/re_img_{num}.png', cv2.resize(process_img, img_info, interpolation=cv2.INTER_CUBIC))

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

def groupping_func(result):
    result_length = len(result)
    chat_content = []
    is_continue_chat = False
    
    for i in range(0, result_length):
            
            if is_continue_chat :
                chat_content[-1] += result[i][1]
                
                if is_sender(result[i + 1]) or is_user(result[i + 1]):
                    is_continue_chat = False
            
            if is_sender(result[i]) and not(is_continue_chat):
                if i + 1 < result_length and is_message(result[i + 1]):
                    chat_content.append(result[i][1] + " : ")
                    is_continue_chat = True
            
            elif is_user(result[i]) and not(is_continue_chat):
                if i + 1 < result_length:
                    chat_content.append("me : " + result[i][1])
                    if is_user(result[i + 1]):
                        is_continue_chat = True
    
    return chat_content
                    

def character_extraction(img_path):
    full_text = ""
    if os.path.exists(img_path):
        
        result = groupping_func(reader.readtext(img_path))
        for text in result:
            full_text += text + '\n'
    else:
        print(f"Error : file{img_path} not Find!")
    return full_text

def start_text():
    for i in range(1, 2):
        img_resize(img_path + f'/kakao_img_{i}.png', i)
        result = character_extraction(re_img_path + f'/re_img_{i}.png')
        return result

start_text()