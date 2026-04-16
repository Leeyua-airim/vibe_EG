from rest_framework import serializers

# 프롬프트를 받고 변수화 하는 클래스 (prompt)
class GenerateSpecRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField()

# 변수화된 프롬프트를 반환하는 클래스
class GenerateSpecResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField() # id
    status = serializers.CharField() # 
    name = serializers.CharField() # 
    spec = serializers.JSONField() # 


# 스캐폴드 요청 시, 프론트에서 보내주는 스펙의 형태를 검증하기 위한 시리얼라이저
class ScaffoldSpecSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    summary = serializers.CharField()
    features = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    inputs = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    outputs = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    ui_pattern = serializers.CharField(max_length=100)

# scaffold 요청 body 전체 검증
class ScaffoldRequestSerializer(serializers.Serializer):
    spec = ScaffoldSpecSerializer()


