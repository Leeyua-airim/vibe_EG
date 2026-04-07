# vibe_EG

## 프로젝트 목적
사용자가 배포된 서비스에 접속해 프롬프트 기반으로 웹사이트 생성을 요청하고,
생성된 결과를 확인하고 수정하며, 최종적으로 배포까지 이어질 수 있도록 지원하는 바이브 코딩 플랫폼을 구축한다.

## 현재 목표
초기 MVP로 아래 흐름을 구현한다.

1. 사용자가 프롬프트를 입력한다.
2. 시스템이 요청을 해석해 웹 앱 구조를 생성한다.
3. 생성된 결과를 미리보기 형태로 확인할 수 있다.
4. 이후 수정 요청을 반영할 수 있다.
5. 최종적으로 배포 가능한 형태로 연결한다.

## 현재 기술 스택
- Frontend: Vite + React + TypeScript
- Backend: Django + Django REST Framework
- Python package/runtime management: uv

## 현재까지 완료한 작업
- Git 저장소 초기화 및 클론
- `apps/api` 생성
- `uv init` 완료
- Django / DRF / CORS / dotenv / OpenAI 패키지 설치 완료
- Django 프로젝트 생성 완료 (`config`, `manage.py`)

## 설치된 Python 라이브러리
- django
- djangorestframework
- django-cors-headers
- python-dotenv
- openai