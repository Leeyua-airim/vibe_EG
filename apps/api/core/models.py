from django.db import models

# 시간 추적을 위한 모델
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# 사용자 모델
class AppUser(TimeStampedModel):
    
    # auth provider 구분을 위한 Enum
    class AuthProvider(models.TextChoices):
        LOCAL = 'local', 'Local'
        GOOGLE = 'google', 'Google'
        SUPABASE = 'supabase', 'Supabase'

    # 이메일 필드 추가, unique=True로 중복 방지
    email = models.EmailField(blank=True, null=True, unique=True)
    # display name 필드 추가
    display_name = models.CharField(max_length=100, blank=True)
    # auth provider 필드 추가
    auth_provider = models.CharField(max_length=20, 
                                     choices=AuthProvider.choices, 
                                     default=AuthProvider.LOCAL)
    # 외부 인증 ID 필드 추가 (예: Google의 sub, Supabase의 user_id 등)
    external_auth_id = models.CharField(max_length=255, blank=True, null=True)

    # 관리자 페이지에서 이메일과 display name으로 사용자 식별 가능하도록 __str__ 메서드 수정
    def __str__(self):
        return self.display_name or self.email or f"User-{self.pk}"
    


class PromptSession(TimeStampedModel):
    
    # 프롬프트 세션 유형을 위한 Enum (초기는 분석 유형만 존재)
    class PromptType(models.TextChoices):
        ANALYSIS = 'analysis', 'Analysis'
    
    # 프롬프트 세션 상태를 위한 Enum (초기 상태는 RECEIVED, 이후 SPEC_GENERATING, SPEC_GENERATED, FAILED 등으로 변경)
    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received' # 사용자의 프롬프트를 받은 상태
        SPEC_GENERATING = 'spec_generating', 'Spec Generating' # LLM 기반 스팩 생성 중
        SPEC_GENERATED = 'spec_generated', 'Spec Generated' # LLM 기반 스팩 생성 완료
        FAILED = 'failed', 'Failed'

    # 사용자 외래키, 프롬프트 세션과 사용자 간의 관계 설정
    user = models.ForeignKey(AppUser, 
                             on_delete=models.CASCADE, 
                             related_name='prompt_sessions')
    
    # raw 프롬프트 텍스트 필드, 사용자가 입력한 원본 프롬프트를 저장
    raw_prompt = models.TextField()
    
    # 프롬프트 타입 필드. 현재는 분석 유형만 존재하지만, 향후 다른 유형을 추가.
    prompt_type = models.CharField(max_length=20,
                                   choices=PromptType.choices,
                                   default=PromptType.ANALYSIS)
    # 프롬프트 세션 상태 필드. 초기 상태는 RECEIVED, 이후 처리 진행에 따라 변경.
    status = models.CharField(max_length=20,
                              choices=Status.choices,
                              default=Status.RECEIVED)
    
    # 에러 메시지 필드, 프롬프트 처리 중 오류가 발생한 경우 상세한 에러 정보를 저장
    error_message = models.TextField(blank=True)

    # 관리자 페이지에서 프롬프트 세션을 식별하기 쉽도록 __str__ 메서드 추가
    def __str__(self) -> str:
        return f"PromptSession<{self.pk}>:{self.status}"
    

# 생성된 스펙 모델, 사용자가 입력한 프롬프트를 기반으로 생성된 앱의 스펙과 상태를 저장
class GeneratedApp(TimeStampedModel):

    # 앱 유형을 위한 Enum, 현재는 분석 유형만 존재하지만 향후 다른 유형 추가 가능
    class AppType(models.TextChoices):
        ANALYSIS = 'analysis', 'Analysis'
    
    # 생성된 스펙의 상태를 위한 Enum (모델의 앱 생성 및 실행 상태표 / 생명주기)
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft' # 초기상태
        
        SPEC_GENERATED = 'spec_generated', 'Spec Generated' # 앱 구조 명세가 만들어진 상태 
        
        SCAFFOLDING = 'scaffolding', 'Scaffolding' # 실제 프로젝트 파일을 만드는 중
        GENERATED = 'generated', 'Generated' # 완료 상태
        
        PREVIEW_STARTING = 'preview_starting', 'Preview Starting' # 프리뷰 서버 띄우는 용
        PREVIEW_RUNNING = 'preview_running', 'Preview Running' # 프리뷰 서버 띄운 상태
        PREVIEW_FAILED = 'preview_failed', 'Preview Failed' # 프리뷰 실패
        
        DEPLOY_PENDING = 'deploy_pending', 'Deploy Pending' # 배포 대기 중
        DEPLOYED = 'deployed', 'Deployed' # 실 배포 완료 상태
        
        FAILED = 'failed', 'Failed'

    # 사용자 외래키, 생성된 스펙과 사용자 간의 관계 설정
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='generated_apps')
    
    # 프롬프트 세션 외래키, 생성된 스펙과 프롬프트 세션 간의 관계 설정
    prompt_session = models.ForeignKey(
        PromptSession,
        on_delete=models.CASCADE,
        related_name='generated_specs'
        )
    
    # 생성된 스펙의 이름 필드, 사용자가 지정한 앱 이름을 저장
    name = models.CharField(max_length=100)
    # App 유형 필드. 현재는 분석 유형만 존재하지만, 향후 다른 유형을 추가할 수 있도록 Enum으로 정의.
    app_type = models.CharField(
        max_length=40,
        choices=AppType.choices,
        default=AppType.ANALYSIS)
    
    # 생성된 스펙의 상태 필드. 초기 상태는 DRAFT, 이후 처리 진행에 따라 변경.
    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.DRAFT)
    
    # 오리지널 프롬프트 텍스트 필드, 생성된 스펙의 원본 프롬프트를 저장
    original_prompt = models.TextField()
    # 생성된 스펙의 JSON 필드, 실제로 생성된 스펙의 상세 내용을 JSON 형태로 저장
    spec_json = models.JSONField(default=dict, blank=True)

    # 생성된 앱의 프로젝트 루트 경로 필드, 실제로 생성된 앱의 프로젝트 루트 경로를 저장
    project_root = models.CharField(max_length=500, blank=True)
    # 생성된 앱의 엔트리 파일 경로 필드, 실제로 생성된 앱의 엔트리 파일 경로를 저장
    entry_file = models.CharField(max_length=255, blank=True)

    # 미리보기 관련 필드들
    preview_port = models.PositiveIntegerField(blank=True, null=True) # PositiveIntegerField는 포트 번호가 음수가 될 수 없으므로 
    preview_url  = models.URLField(blank=True) 
    preview_pid  = models.IntegerField(blank=True, null=True) 

    # 배포 관련 필드들
    production_url = models.URLField(blank=True)
    # 배포 시간 필드, 앱이 실제로 배포된 시간을 저장
    deployed_at = models.DateTimeField(blank=True, null=True) 

    # 에러 메시지 필드, 앱 생성/미리보기/배포 과정에서 오류가 발생한 경우 상세한 에러 정보를 저장
    last_error_message = models.TextField(blank=True)

    def __str__(self):
        return f"GeneratedApp<{self.pk}>:{self.name}:{self.status}"


class PromptEvent(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        SYSTEM = "system", "System"
        ASSISTANT = "assistant", "Assistant"

    class EventType(models.TextChoices):
        INITIAL_PROMPT = "initial_prompt", "Initial Prompt" # 사용자가 처음 프롬프트를 입력했을 때
        REFINE_PROMPT = "refine_prompt", "Refine Prompt" # 사용자가 추가 프롬프트를 입력하였을 때
        STATUS_CHANGE = "status_change", "Status Change" # 프롬프트 세션이나 생성된 앱의 상태가 변경되었을 때
        ERROR = "error", "Error"
        SYSTEM_MESSAGE = "system_message", "System Message"

    generated_app = models.ForeignKey(
        GeneratedApp,
        on_delete=models.CASCADE,
        related_name="prompt_events",
    )
    user = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prompt_events",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.INITIAL_PROMPT,
    )
    content = models.TextField()

    def __str__(self) -> str:
        return f"PromptEvent<{self.pk}>:{self.event_type}"