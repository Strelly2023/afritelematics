from rest_framework import serializers


class GPSUpdateSerializer(serializers.Serializer):
    ride_id = serializers.IntegerField(min_value=1)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    speed = serializers.FloatField(required=False, default=0)
    heading = serializers.FloatField(required=False, default=0)
    recorded_at = serializers.DateTimeField(required=False)

    def validate_latitude(self, value):
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def validate_speed(self, value):
        if value is None:
            return 0
        if value < 0:
            raise serializers.ValidationError("Speed cannot be negative.")
        return value

    def validate_heading(self, value):
        if value is None:
            return 0
        if value < 0 or value > 360:
            raise serializers.ValidationError("Heading must be between 0 and 360.")
        return value
