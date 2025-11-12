from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

# It's recommended to use environment variables for API keys for better security.
KEY = "sk-..."

client = AsyncOpenAI(
    api_key=KEY
)

async def generate_chat_response(chat_message, summary, role, original_reply=None, modification_request=None):
    """Generates or refines a chat response based on the conversation history and user requests."""
    
    user_content = ""
    # 답장 수정 요청이 있을 경우
    if original_reply and modification_request:
        user_content = (
            f"이전 대화 요약: '{summary}'\n"
            f"분석할 카톡 대화 내용: '{chat_message}'\n"
            f"아래는 이전에 생성된 답장이야:\n'{original_reply}'\n\n"
            f"이 답장을 다음 요청에 맞게 수정해줘: '{modification_request}'\n"
            f"수정된 최종 답장만 보내줘."
        )
    # 처음 답장을 생성할 경우
    else:
        user_content = (
            f"이전 대화 요약: '{summary}'\n"
            f"분석할 카톡 대화 내용: '{chat_message}'\n"
            f"위 내용을 바탕으로 {role}에게 보낼 카톡 답장만 만들어줘."
        )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 교수님에게 답장을 보내는 대학생이야."},
                {
                    "role": "user",
                    "content": user_content
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
    
    # 2. 세 개의 API 호출을 병렬로 실행합니다.
    response_tasks = [generate_chat_response(chat_message, previous_chat_summary, role) for _ in range(3)]
    summary_task = summarize_chat_message(chat_message)
    
    # asyncio.gather를 사용하여 모든 작업을 동시에 실행합니다.
    results = await asyncio.gather(
        *response_tasks,
        summary_task
    )
    
    # gather의 결과에서 응답과 요약을 분리합니다.
    replies = results[:-1]
    new_summary = results[-1]
    
    print(f"\nGenerated Replies: {replies}")
    print(f"\nNew Summary: {new_summary}")
    
    # 3. 최종적으로 3개의 값(응답 목록, 새 요약, 찾은 제목)을 반환합니다.
    return replies, new_summary, found_title
