from rest_framework import serializers
from .models import Artisan, Client, TradeCategory

# Artisan Registration Serializer
class ArtisanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artisan
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


# Client Registration Serializer
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


class TradeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeCategory
        fields = ['id', 'name']
