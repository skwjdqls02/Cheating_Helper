
from openai import OpenAI
import os
import carry_lange_easyocr


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-...")
)

def generate_chat_response(chat_message, role):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 교수님에게 답장을 보내는 대학생이야."},
                {
                    "role": "user",
                    "content": f"\n\n'{chat_message} 다음 대화 내용을 분석하고 {role}에게 보낼 답장만 만들어줘'"
                },
            ]
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred with the OpenAI API: {e}"

if __name__ == '__main__':
    chat_message = carry_lange_easyocr.start_text()
    print(f"Original Message: {chat_message}")
    
    # Generate the response
    reply = generate_chat_response(chat_message, "교수님")
    
    print(f"\nGenerated Reply: {reply}")
