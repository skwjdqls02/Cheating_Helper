from openai import AsyncOpenAI
import os
import asyncio
import carry_lange_easyocr

KEY = "sk-..." 
client = AsyncOpenAI(
    api_key=KEY
)

# 공통 페르소나 (사람 같은 말투)
HUMAN_PERSONA_PROMPT = (
    "너는 AI가 아니라, 지금 스마트폰으로 카카오톡 답장을 보내려는 '현실적인 한국 사람'이야. "
    "교과서적인 문어체나 딱딱한 번역투는 절대 쓰지 마. "
    "상황과 상대방과의 관계(친밀도)에 따라 말투를 유연하게 바꿔야 해.\n"
    "- 친구/연인/썸: 'ㅋㅋㅋ', 'ㅠㅠ', '아 진짜?', 'ㅇㅇ' 같은 추임새나 줄임말을 적절히 섞어. 맞춤법에 너무 집착하지 마.\n"
    "- 직장상사/어른/선배: 예의를 갖추되, 너무 로봇 같지 않은 '사회생활 만렙' 부하직원처럼 자연스럽게 존댓말을 써.\n"
    "- 문장은 너무 길게 쓰지 말고, 카톡 특성상 짧게 끊어치는 느낌을 살려."
)

COMMON_CONSTRAINTS = (
    "\n[형식 절대 금지 사항]\n"
    "- '제목:', '내용:', 'Subject:' 같은 이메일 서식 금지.\n"
    "- 답변 앞뒤에 쌍따옴표(\")나 괄호()를 넣지 말고, 오직 보낼 메시지 텍스트만 출력할 것.\n"
    "- '안녕하세요 000입니다' 같은 불필요한 자기소개나 인사 반복 금지."
)

async def generate_chat_response(chat_message, lost_reply, role):
    """
    대화 상대방(role)에 맞춰 변경하여 답장을 생성.
    """
    system_instruction = HUMAN_PERSONA_PROMPT + COMMON_CONSTRAINTS

    # 사용자 입력 프롬프트 구체화
    user_content = (
        f"상황 정보:\n"
        f"1. 내 대화 상대방의 역할: {role}\n"
        f"2. 상대방이 보낸 최근 메시지들:\n{chat_message}\n"
        f"3. (참고) 내가 평소 선호하는 스타일/이전 답변: {lost_reply}\n\n"
        f"지시: 위 대화의 흐름을 읽고, '{role}'에게 보낼 가장 센스 있고 적절한 답장을 하나만 딱 작성해줘. "
        f"상대방이 {role}이라는 점을 고려해서 반말/존댓말 여부를 스스로 판단해."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            temperature=0.8 # 창의성과 자연스러움을 위해 약간 높임 
        )
        return response.choices[0].message.content.strip().strip('"').strip("'")
    except Exception as e:
        return f"An error occurred in generate_chat_response: {e}"

# 새로운 답변 요청 이전 답변 + 사용자 희망 사항
async def refine_chat_response(original_reply, modification_request, role):
    """
    재생성 요청 반영하여 답장을 생성.
    """
    system_instruction = HUMAN_PERSONA_PROMPT + COMMON_CONSTRAINTS
    
    # 재생성 전용 추가 구체화
    refine_instruction = (
        "\n[수정 지침]\n"
        "사용자가 기존 답변이 마음에 들지 않아 수정을 요청했다. "
        "단순히 문장을 다듬는 수준을 넘어, 사용자의 요청(modification_request)에 담긴 '의도'와 '감정'을 정확히 캐치해서 반영해.\n"
        "예시) '더 차갑게' -> 단답형, 마침표 사용, 이모티콘 삭제.\n"
        "예시) '더 친근하게' -> 'ㅋㅋㅋ' 추가, 물결표(~) 사용, 공감하는 말 추가."
    )

    full_system_prompt = system_instruction + refine_instruction

    user_content = (
        f"상대방({role})에게 보내려던 원래 답장: \"{original_reply}\"\n"
        f"**사용자의 수정 요청사항: \"{modification_request}\"**\n\n" 
        f"위 요청사항을 완벽하게 반영해서, '{role}'에게 보낼 새로운 답장을 작성해줘. "
        "요청사항이 말투 변경이면 확실하게 말투를 바꾸고, 내용 추가면 자연스럽게 녹여내."
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": full_system_prompt},
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
                {"role": "system", "content": "너는 대화 내용을 핵심만 간결하게 3줄 이내로 요약하는 전문가야."},
                {
                    "role": "user",
                    "content": f"다음 카카오톡 대화 내용을 한국어로 누가 어떤 상황인지 알 수 있게 요약해줘: \n\n{chat_message}"
                },
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred in summarize_chat_message: {e}"

async def start_open_ai_api(img_paths, previous_reply, role):
    # 1. easyocr을 호출하여 chat_message을 받습니다.
    chat_message = carry_lange_easyocr.start_easyocr(img_paths)
    print(f"Original Message: {chat_message}")
    
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
    return replies, new_summary

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