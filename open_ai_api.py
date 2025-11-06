from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

# It's recommended to use environment variables for API keys for better security.
KEY = "sk-..."

client = AsyncOpenAI(
    api_key=KEY
)

async def generate_chat_response(chat_message, summary, role):
    """Generates a chat response based on the conversation history."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 교수님에게 답장을 보내는 대학생이야."},
                {
                    "role": "user",
                    "content": f"\n\n'{summary}이건 이전 대화 내용이야. me는 나야. 저 내용과 다음 카톡 대화 내용을 분석해서 {chat_message} {role}에게 보낼 카톡 답장만 만들어줘."
                },
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in generate_chat_response: {e}"


async def summarize_chat_message(chat_message):
    """Summarizes the chat conversation."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at summarizing conversations concisely."},
                {
                    "role": "user",
                    "content": f"Please summarize the following conversation in Korean: \n\n{chat_message}"
                },
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in summarize_chat_message: {e}"

async def start_open_ai_api(img_paths, previous_chat_summary, role):
    """
    Processes images to text, then concurrently generates a chat response and a summary.
    """
    # 1. easyocr을 호출하여 chat_message와 title을 받습니다. (반환값이 2개)
    chat_message, found_title = carry_lange_easyocr.start_easyocr(img_paths)
    print(f"Original Message: {chat_message}")
    print(f"Found Title: {found_title}")
    
    # 2. 두 개의 API 호출을 병렬로 실행합니다.
    response_task = generate_chat_response(chat_message, previous_chat_summary, role)
    summary_task = summarize_chat_message(chat_message)
    
    reply, new_summary = await asyncio.gather(
        response_task,
        summary_task
    )
    
    print(f"\nGenerated Reply: {reply}")
    print(f"\nNew Summary: {new_summary}")
    
    # 3. 최종적으로 3개의 값을 반환합니다.
    return reply, new_summary, found_title
