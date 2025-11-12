from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

KEY = "sk-..." 
client = AsyncOpenAI(
    api_key=KEY
)

async def generate_chat_response(chat_message, summary, role):
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"너는 {role}에게 카카오톡 답장을 보내는 사람이야."},
                {
                    "role": "user",
                    "content": f"이전 대화 요약: '{summary}'\n"
                            f"분석할 카톡 대화 내용: '{chat_message}'\n"
                            f"위 내용을 바탕으로 {role}에게 보낼 카톡 답장만 만들어줘."
                },
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in generate_chat_response: {e}"

# 새로운 답변 요청 이전 답변 + 사용자 희망 사항
async def refine_chat_response(role, original_reply, modification_request):
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{role}에게 카카오톡 답장을 보내는 사람이야."},
                {
                    "role": "user",
                    "content": f"아래는 이전에 생성된 답장이야:\n'{original_reply}'"
                    f"이 답장을 다음 요청에 맞게 수정해줘: '{modification_request}'\n"
                    f"수정된 최종 답장만 보내줘."
                },
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in refine_chat_response: {e}"

#요약 요청하는 함수
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

async def regenerate_replies(original_reply, modification_request, role):

    # 세 개의 재생성 작업을 병렬로 실행합니다.
    response_tasks = [
        refine_chat_response(role, original_reply, modification_request)
        for _ in range(3)
    ]
    
    # asyncio.gather를 사용하여 모든 작업을 동시에 실행합니다.
    new_replies = await asyncio.gather(*response_tasks)
    
    print(f"\nRegenerated Replies: {new_replies}")
    
    return new_replies