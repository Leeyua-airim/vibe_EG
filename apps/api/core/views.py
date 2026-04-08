import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response    

from core.models import AppUser, PromptSession, GeneratedApp, PromptEvent
from core.serializers import GenerateSpecRequestSerializer
from core.services.spec_generator import generate_app_spec_from_prompt 

# 로깅 설정
logger = logging.getLogger(__name__)



@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "API 헬스체크 성공"
        })


@api_view(['POST'])
def app_generator_generate_spec(request):
    # 요청 데이터에서 프롬프트를 추출하기 위한 시리얼라이저 사용
    serializer = GenerateSpecRequestSerializer(data=request.data)
    # 데이타 유효성 검사 
    if serializer.is_valid():
        # 프롬프트 추출 | serializer.validated_data에서 'prompt' 키를 사용하여 프롬프트 추출
        prompt = serializer.validated_data['prompt']
        
        user = AppUser.objects.first()
        if not user:
            return Response(
                {"detail" : "사용자가 존재하지 않습니다. 관리자 페이지에서 사용자를 생성해주세요."},
                status = status.HTTP_400_BAD_REQUEST,)
        
        prompt_session = PromptSession.objects.create(
            user=user,
            raw_prompt=prompt,
            prompt_type=PromptSession.PromptType.ANALYSIS,
            status = PromptSession.Status.RECEIVED)
        
        try:
            # 스팩 생성 함수 호출
            spec = generate_app_spec_from_prompt(prompt)

            with transaction.atomic(): # 
                app = GeneratedApp.objects.create(
                    user=user,
                    prompt_session=prompt_session,
                    name=spec.get("title", "생성 앱"),
                    app_type=GeneratedApp.AppType.ANALYSIS,
                    status=GeneratedApp.Status.SPEC_GENERATED,
                    spec_json=spec,
                )

                PromptEvent.objects.create(
                    generated_app=app,
                    user=user,
                    role=PromptEvent.Role.USER,
                    event_type=PromptEvent.EventType.INITIAL_PROMPT,
                    content=prompt,
                )

                PromptEvent.objects.create(
                    generated_app=app,
                    user=None,
                    role=PromptEvent.Role.SYSTEM,
                    event_type=PromptEvent.EventType.STATUS_CHANGE,
                    content="App spec generated successfully.",
                )

                prompt_session.status = PromptSession.Status.COMPLETED
                prompt_session.error_message = ""
                prompt_session.save(update_fields=["status", "error_message", "updated_at"])

            return Response(
                {
                    "id": app.id,
                    "status": app.status,
                    "name": app.name,
                    "spec": app.spec_json,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.exception("app_generator_generate_spec failed: %s", exc)

            prompt_session.status = PromptSession.Status.FAILED
            prompt_session.error_message = str(exc)
            prompt_session.save(update_fields=["status", "error_message", "updated_at"])

            return Response(
                {"detail": "앱 스펙 생성 중 오류가 발생했습니다.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


