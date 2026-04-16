import os
import json
import time

from openai import OpenAI

APP_SPEC_JSON_SCHEMA = {
    "name": "app_spec",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 80
            },
            "summary": {
                "type": "string",
                "minLength": 40,
                "maxLength": 220
            },
            "features": {
                "type": "array",
                "minItems": 3,
                "maxItems": 6,
                "items": {
                    "type": "string",
                    "minLength": 5,
                    "maxLength": 40
                }
            },
            "inputs": {
                "type": "array",
                "minItems": 0,
                "maxItems": 4,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 40
                }
            },
            "outputs": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 40
                }
            },
            "ui_pattern": {
                "type": "string",
                "enum": [
                    "landing-page",
                    "dashboard",
                    "form-result",
                    "list-detail",
                    "chat",
                    "map-dashboard",
                    "editor",
                    "general"
                ]
            }
        },
        "required": [
            "title",
            "summary",
            "features",
            "inputs",
            "outputs",
            "ui_pattern"
        ]
    },
    "strict": True
}


SYSTEM_PROMPT = """
너는 사용자의 자연어 요청을 구조화된 AppSpec으로 변환하는 기획자의 역할.

업무 수행 필수규칙:
1. 사용자의 요청을 앱 관점에서 해석한다.
2. features는 핵심 기능만 고른다.
3. inputs는 사용자가 직접 제공하거나 선택하는 값만 포함한다.
4. outputs는 사용자에게 보여줄 핵심 결과만 포함한다.
5. 내부 구현 단계, 알고리즘 세부 단계, 중복 항목은 제외한다.
6. title과 summary는 간결하고 이해하기 쉽게 작성한다.
7. ui_pattern은 가장 적절한 패턴 1개를 선택한다.
8. 모든 문자열은 자연스러운 한국어로 작성한다.
9. features, inputs, outputs 각 항목에는 줄바꿈을 넣지 않는다.
10. features는 짧은 기능 문구로만 작성하고, 설명형 문단으로 쓰지 않는다.
11. 같은 의미의 항목을 반복하지 않는다.
12. JSON 외의 메타 텍스트, 설명, 사과문, 코드블록을 절대 포함하지 않는다.
13. summary는 1~2문장으로만 작성한다.
14. features의 각 항목은 명사형 또는 짧은 기능구로 작성한다.
"""

# 텍스트에서 JSON 객체를 추출하는 함수 | 텍스트에서 JSON 객체를 추출하여 딕셔너리로 반환
def _extract_json_object(text: str) -> dict:
    # 기초 전처리
    # 양쪽 공백 제거 | 변수로 받은 text에서 strip() 사용
    text = text.strip()

    # 1차 파싱 시도. 
    try:
        return json.loads(text) 
    except json.JSONDecodeError: # JSONDecodeError 예외 처리 | JSONDecodeError 예외가 발생하면 None 반환
        pass

    # 2차 파싱 시도 - 텍스트에서 가장 처음과 마지막 중괄호 위치 찾기 | text.find("{")와 text.rfind("}") 사용하여 JSON 객체의 시작과 끝 위치 찾기
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start: 
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # 유효한 JSON 객체를 찾을 수 없는 경우 예외 발생 |
    raise ValueError("유효한 JSON 객체를 찾을 수 없습니다.")

# 프롬프트에서 앱 스펙을 생성하는 함수 | 사용자 프롬프트를 받아 OpenAI API를 호출하여 앱 스펙을 생성하는 함수
def generate_app_spec_from_prompt(prompt: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    client = OpenAI(api_key=api_key)

    t0 = time.perf_counter()

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"다음 사용자 요청을 AppSpec으로 변환해줘:\n\n{prompt}",
            },
        ],
        text={
            'format': {
                'type': 'json_schema',
                'name' :  APP_SPEC_JSON_SCHEMA['name'],
                'schema': APP_SPEC_JSON_SCHEMA['schema'],
                'strict': APP_SPEC_JSON_SCHEMA['strict'],
            }
        }
    )

    t1 = time.perf_counter()

    output_text = response.output_text
    spec = _extract_json_object(output_text)

    t2 = time.perf_counter()

    spec.setdefault("title", "생성 앱") # setdefault() 메서드를 사용하여 빈 값이 들어오는 경우 방지. 
    spec.setdefault("summary", "사용자 요청을 기반으로 생성된 앱입니다.")
    spec.setdefault("features", [])
    spec.setdefault("inputs", [])
    spec.setdefault("outputs", [])
    spec.setdefault("ui_pattern", "general")

    t3 = time.perf_counter()

    print(f"OpenAI 호출 시간: {t1 - t0:.4f}초")
    print(f"JSON 추출 시간: {t2 - t1:.6f}초")
    print(f"후처리 시간: {t3 - t2:.6f}초")
    print(f"전체 시간: {t3 - t0:.4f}초")

    return spec