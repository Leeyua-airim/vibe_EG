import logging

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response    

from core.models import AppUser, PromptSession, GeneratedApp, PromptEvent
from core.serializers import GenerateSpecRequestSerializer
from core.services.spec_generator import generate_app_spec_from_prompt 
from core.services.workspace_builder import scaffold_generated_app
# 로깅 설정
logger = logging.getLogger(__name__)


SCAFFOLD_ALLOWED_STATUSES = {
    GeneratedApp.Status.SPEC_GENERATED, 
    GeneratedApp.Status.GENERATED, 
    GeneratedApp.Status.FAILED,    
}

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

@api_view(['POST'])
def generated_app_scaffold(request, app_id:int):
    # GeneratedApp 객체를 app_id를 사용하여 데이터베이스에서 가져오기 | get_object_or_404 함수를 사용하여 app_id에 해당하는 GeneratedApp 객체를 가져오고, 존재하지 않을 경우 404 응답 반환
    app = get_object_or_404(GeneratedApp, pk=app_id)

    # 만약 앱의 상태가 SPEC_GENERATED, GENERATED, FAILED 중 하나가 아니라면, 
    # 즉 스펙이 생성되지 않았거나 이미 생성된 앱이거나 실패한 앱이 아니라면 409 Conflict 응답 반환
    if app.status not in SCAFFOLD_ALLOWED_STATUSES:
        return Response(
            {
                'detail' : "현재 상태에서는 Scaffold를 실행할 수 없습니다.",
                'current_status': app.status,
            },
            status=status.HTTP_409_CONFLICT, #409란 현재 리소스의 상태가 요청을 처리하기에 적합하지 않음을 나타내는 HTTP 상태 코드입니다.
        )
    
    try:
        result = scaffold_generated_app(app) # 스캐폴딩 함수 호출
        return Response(
            {
                "id": app.id,
                "status": app.status,
                "project_root": app.project_root,
                "entry_file": app.entry_file,
                "files_created": result['files_created'],
            },
            status=status.HTTP_200_OK,
        )
    # 
    except ValueError as exc:
        app.status = GeneratedApp.Status.FAILED
        app.save(update_fields=['status', 'updated_at'])

        return Response(
            {"detail": "앱 스캐폴딩 중 오류가 발생했습니다.", "error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )



