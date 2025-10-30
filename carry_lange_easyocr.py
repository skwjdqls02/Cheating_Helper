import os
import easyocr
import cv2

reader = easyocr.Reader(['ko'])

img_path = './test_img'
re_img_path = './make_img'

def img_resize(img_path, num):
    size_up = 2.0
    
    process_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    img_width = int(process_img.shape[1] * size_up)
    img_height = int(process_img.shape[0] * size_up)
    img_info = (img_width, img_height)
    
    return cv2.imwrite(re_img_path + f'\\re_img_{num}.png', cv2.resize(process_img, img_info, interpolation=cv2.INTER_CUBIC))
    
def character_extraction(img_path):
    full_text = ""
    if os.path.exists(img_path):
        result = reader.readtext(img_path)

        print(f"IMG ----'{os.path.basename(img_path)}'")
        for i in result:
            text = i[1]
            full_text += text + '\n'
    else:
        print(f"Error : file{img_path} not Find!")
    return full_text

def start_text():
    for i in range(1, 2):
        img_resize(img_path + f'\\kakao_img_{i}.png', i)
        result = character_extraction(re_img_path + f'\\re_img_{i}.png')
        return result
