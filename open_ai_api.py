from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

KEY = "sk-..." 
client = AsyncOpenAI(
    api_key=KEY
)

async def generate_chat_response(chat_message, summary, role):
    """
    대화 상대방(role)에 맞춰 변경하여 답장을 생성.
    """
    
    # role 역할별 맞춤(후에 더 자연스럽게 수정)
    prompts = {
        "교수님": (
            "너는 예의 바르고 성실한 대학생이야. "
            "교수님께 보내는 카톡이므로 정중한 존댓말(해요체/하십시오체 혼용)을 사용해. "
            "이모티콘은 자제하고, 되도록 깔끔하고 명확하게 의사를 전달해. "
            "문장은 완결된 형태(~했습니다, ~겠습니다, ~요)로 끝맺음해."
        ),
        "선배": (
            "너는 센스 있고 싹싹한 후배야. "
            "친한 선배에게 보내는 카톡이므로 예의를 지키되 너무 딱딱하지 않은 부드러운 존댓말(~요, ~는데요)을 사용해. "
            "적절한 느낌표(!)나 물결(~)을 사용해서 밝은 분위기를 줘도 좋아."
        ),
        "친구": (
            "너는 정말 친한 친구야. "
            "완전한 반말(해체)을 사용해. (~했어, ~야, ~냐? 등) "
            "너무 길게 쓰지 말고 진짜 친구랑 카톡하듯이 자연스럽게 줄임말이나 'ㅋㅋ', 'ㅠㅠ' 같은 표현을 적절히 섞어서 작성해."
        ),
        "후배": (
            "너는 챙겨주는 따뜻한 선배야. "
            "편하게 반말을 하되, 권위적이지 않고 친근하게 말해. "
            "상대방을 배려하는 말투(~했니?, ~하자)를 사용해."
        )
    }

    # role이 비어있거나, 딕셔너리에 없으면 기본값으로 교수님 설정(일단 기본값으로 존댓말을 쓰도록 설정해놓음)
    selected_persona = prompts.get(role, prompts["교수님"])

    #  공통 제약 사항 (형식 고정할 수 있도록)
    common_constraints = (
        "\n[절대 금지 사항]\n"
        "- '제목:', '내용:', 'Subject:' 같은 이메일 서식 절대 금지.\n"
        "- 답변 앞뒤에 괄호 ( ) 나 따옴표 \" \" 절대 넣지 말 것.\n"
        "- 불필요한 인사말(예: 안녕하십니까, 000입니다)을 매번 반복하지 말고, 자연스러운 대화 흐름을 따를 것.\n"
        "- 오직 상대방에게 전송할 '답장 텍스트'만 출력할 것."
    )

    system_instruction = selected_persona + common_constraints

    user_content = (
        f"상황 요약: {summary}\n"
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