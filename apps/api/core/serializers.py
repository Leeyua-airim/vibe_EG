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


