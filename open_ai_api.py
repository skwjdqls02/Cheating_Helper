
from openai import OpenAI
import os
import carry_lange_easyocr

KEY = "sk-..."

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", KEY)
)

def generate_chat_response(chat_message, role):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 교수님에게 답장을 보내는 대학생이야."},
                {
                    "role": "user",
                    "content": f"\n\n'{chat_message} 다음은 [이름] : 대화로 구성 되어 있고 me : 는 내가 말한 내용이야. 다음 카톡 대화 내용을 분석하고 {role}에게 보낼 카톡 답장만 만들어줘'"
                },
            ]
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred with the OpenAI API: {e}"

def start_open_ai_api(img_paths):
    chat_message = carry_lange_easyocr.start_easyocr(img_paths)
    print(f"Original Message: {chat_message}")
    
    # Generate the response
    reply = generate_chat_response(chat_message, "교수님")
    
    print(f"\nGenerated Reply: {reply}")
    return reply
