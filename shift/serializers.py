from django.utils import timezone
from rest_framework import serializers

from shift.models import Shift


class ShiftSerializer(serializers.ModelSerializer):
    start_hour = serializers.IntegerField(write_only=True)
    date = serializers.DateField()

    class Meta:
        model = Shift
        fields = ('id', 'date', 'created_at', 'shift_period', 'worker', 'start_hour', 'date')
        extra_kwargs = {
            'worker': {'read_only': True},
            'shift_period': {'read_only': True}
        }

    def validate(self, attrs):
        user = self.context.get('user')
        date = attrs['date']
        current_date = timezone.now().date()
        if current_date < date:
            raise serializers.ValidationError({'date': 'you cannot create shift for previous days'})
        if attrs['start_hour'] not in [0, 8, 16]:
            raise serializers.ValidationError({'start_hour': 'start hour must be 0, 8, or 16'})
        if Shift.objects.filter(worker=user, date=date).exists():
            raise serializers.ValidationError({'shift': 'user already has an existing shift for this day'})

        match attrs['start_hour']:
            case 0:
                attrs['shift_period'] = '0 - 8'
            case 8:
                attrs['shift_period'] = '8 - 16'
            case 16:
                attrs['shift_period'] = '16 - 24'
            case _:
                raise serializers.ValidationError({'start_hour': 'invalid start hour'})
        return attrs

    def create(self, validated_data):
        return Shift.objects.create(
            worker=self.context.get('user'),
            shift_period=validated_data.get('shift_period'),
            date=validated_data.get('date')
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['worker'] = instance.worker.username if instance.worker else None
        return data



