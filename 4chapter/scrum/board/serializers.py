from rest_framework import serializers
from .models import Spint

class SprintSerializer(serializers.ModelSerializer):

    class Meta:
        model = Spint
        fields = ('id', 'name', 'description','end')

