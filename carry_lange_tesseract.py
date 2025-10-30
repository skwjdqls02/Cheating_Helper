import pytesseract
from PIL import Image
import os
import cv2

  # -------------------------------------------------------------------------
  # 중요: 1단계에서 설치한 Tesseract-OCR의 경로를 여기에 입력하세요.
  # 보통 C:\Program Files\Tesseract-OCR\tesseract.exe 입니다.
tesseract_cmd_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  # -------------------------------------------------------------------------
size_up = 12.0
  # 텍스트를 추출할 이미지 파일 경로
image_path = '.\\test_img' # 실제 이미지 경로로 변경
def character_extraction(image_path):
  try:
      # Tesseract 실행 파일 경로 설정
      pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
      rev_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
      img_width = int(rev_img.shape[1] * size_up)
      img_height = int(rev_img.shape[0] * size_up)
      
      img_size = (img_width, img_height)
      resized_img = cv2.resize(rev_img, img_size, interpolation=cv2.INTER_CUBIC)

      # 이미지에서 한국어 텍스트 추출 ('kor')
      if os.path.exists(image_path):
          text = pytesseract.image_to_string(resized_img, lang='kor')

          print(f"--- 이미지 '{os.path.basename(image_path)}' 에서 Tesseract 추출 결과 ---")
          print(text)
          print("----------------------------------------------------")
      else:
          print(f"오류: 파일 '{image_path}'을(를) 찾을 수 없습니다.")

  except pytesseract.TesseractNotFoundError:
      print("오류: Tesseract를 찾을 수 없습니다.")
      print(f"'{tesseract_cmd_path}' 경로에 Tesseract가 올바르게 설치되었는지 확인하세요.")
  except Exception as e:
      print(f"오류 발생: {e}")
      
for i in range(1,5):
    character_extraction(image_path + f'\\kakao_img_{i}.png')