from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

KEY = "sk-..." 
client = AsyncOpenAI(
    api_key=KEY
)

async def generate_chat_response(chat_message, lost_reply, role):
    """
    대화 상대방(role)에 맞춰 변경하여 답장을 생성.
    """
    
    base_system_instruction = (
        "너는 사용자가 지정한 상대방(role)에게 보낼 자연스러운 카카오톡 답장을 생성하는 AI야. "
        "주어진 상황 요약, 상대방 메시지, 그리고 상대방 역할(role)을 바탕으로 "
        "한국어 카카오톡 대화 스타일에 가장 적합한 말투(존댓말, 반말 등)와 분위기를 스스로 판단하여 답장을 작성해. "
    )

    #  공통 제약 사항 (형식 고정할 수 있도록)
    common_constraints = (
        "\n[절대 금지 사항]\n"
        "- '제목:', '내용:', 'Subject:' 같은 이메일 서식 절대 금지.\n"
        "- 답변 앞뒤에 괄호 ( ) 나 따옴표 \" \" 절대 넣지 말 것.\n"
        "- 불필요한 인사말(예: 안녕하십니까, 000입니다)을 매번 반복하지 말고, 자연스러운 대화 흐름을 따를 것.\n"
        "- 오직 상대방에게 전송할 '답장 텍스트'만 출력할 것."
    )

    system_instruction = base_system_instruction + common_constraints

    user_content = (
        f"이전에 맘에 든 스타일 답: {lost_reply}\n"
        f"상대방({role})이 보낸 메시지: {chat_message}\n\n"
        f"위 내용을 바탕으로 '{role}'에게 보낼 자연스러운 카톡 답장을 작성해줘."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in generate_chat_response: {e}"

# 새로운 답변 요청 이전 답변 + 사용자 희망 사항
async def refine_chat_response(original_reply, modification_request, role):
    """
    재생성 요청 반영하여 답장을 생성.
    """
    base_system_instruction = (
        "너는 사용자가 지정한 상대방(role)에게 보낼 자연스러운 카카오톡 답장을 생성하는 AI야. "
        "주어진 상황 요약, 상대방 메시지, 그리고 상대방 역할(role)을 바탕으로 "
        "한국어 카카오톡 대화 스타일에 가장 적합한 말투(존댓말, 반말 등)와 분위기를 스스로 판단하여 답장을 작성해. "
    )
    common_constraints = (
        "\n[절대 금지 사항]\n"
        "- '제목:', '내용:', 'Subject:' 같은 이메일 서식 절대 금지.\n"
        "- 답변 앞뒤에 괄호 ( ) 나 따옴표 \" \" 절대 넣지 말 것.\n"
        "- 불필요한 인사말(예: 안녕하십니까, 000입니다)을 매번 반복하지 말고, 자연스러운 대화 흐름을 따를 것.\n"
        "- 오직 상대방에게 전송할 '답장 텍스트'만 출력할 것."
    )

    system_instruction = base_system_instruction + common_constraints
    
    # 사용자 요청을 추가한 user_content 생성
    user_content = (
        f"상대방({role})이 보낸 메시지: {original_reply}\n"
        f"**답장 작성 시, 다음 지시사항을 반드시 반영해줘: {modification_request}**\n\n" 
        f"위 내용을 바탕으로 '{role}'에게 보낼 자연스러운 카톡 답장을 다시 작성해줘."
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7 
        )
        return response.choices[0].message.content.strip().strip('"').strip("'")
    except Exception as e:
        return f"An error occurred in regenerate function: {e}"

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

async def start_open_ai_api(img_paths, previous_reply, role):
    # 1. easyocr을 호출하여 chat_message와 title을 받습니다. (반환값이 2개)
    chat_message, found_title = carry_lange_easyocr.start_easyocr(img_paths)
    print(f"Original Message: {chat_message}")
    print(f"Found Title: {found_title}")
    
    # 2. 세 개의 API 호출을 병렬로 실행합니다.
    response_tasks = [generate_chat_response(chat_message, previous_reply, role) for _ in range(3)]
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