from django.contrib import admin

# Register your models here.
from .models import AppUser, PromptSession, GeneratedApp, PromptEvent

@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin): # 관리자 페이지에서 AppUser 모델을 관리하기 위한 설정
    list_display = ('id', 
                    'email', 
                    'display_name', 
                    'auth_system', 
                    'external_auth_id', 
                    'identity_provider',
                    'external_auth_id',
                    'created_at', 
                    'updated_at')
    list_filter = ('auth_system','created_at', 'updated_at') # 리스트 필터링 옵션 
    search_fields = ('email', 'display_name', 'external_auth_id') # 검색 필드 옵션

    ordering = ('-created_at',) 

@admin.register(PromptSession)
class PromptSessionAdmin(admin.ModelAdmin): # 관리자 페이지에서 PromptSession 모델을 관리하기 위한 설정
    list_display = ('id', 
                    'user', 
                    'raw_prompt', 
                    'prompt_type', 
                    'status', 
                    'created_at', 
                    'updated_at')
    list_filter = ('prompt_type','status','created_at', 'updated_at') # 리스트 필터링 옵션 
    search_fields = ('raw_prompt','user__email','user__display_name') # 검색 필드 옵션
    ordering = ('-created_at',)
    readonly_fields = ('raw_prompt', 'prompt_type') # 관리자 페이지에서 raw_prompt, prompt_type 필드를 읽기 전용으로 설정하여 실수로 변경되는 것을 방지


@admin.register(GeneratedApp)
class GeneratedAppAdmin(admin.ModelAdmin): # 관리자 페이지에서 GeneratedApp 모델을 관리하기 위한 설정
    list_display = ('id', 
                    'user', 
                    'name',
                    'app_type', 
                    'status', 
                    'preview_port',
                    'preview_url',
                    'production_url',
                    'created_at'
                    )
    search_fields = (
        "name",
        "original_prompt",
        "project_root",
        "entry_file",
        "user__email",
        "user__display_name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "deployed_at")

@admin.register(PromptEvent)
class PromptEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "generated_app",
        "user",
        "role",
        "event_type",
        "created_at",
    )
    list_filter = ("role", "event_type", "created_at")
    search_fields = (
        "content",
        "generated_app__name",
        "user__email",
        "user__display_name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")