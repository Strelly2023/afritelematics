from django.db import models


class Fleet(models.Model):
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, related_name="vehicles")
    plate_number = models.CharField(max_length=50)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("fleet", "plate_number")
        ordering = ("plate_number",)

    def __str__(self):
        return self.plate_number


class FleetDriverAssignment(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("fleet", "vehicle", "driver", "active")
        ordering = ("-assigned_at",)

    def __str__(self):
        return f"{self.fleet_id}:{self.vehicle_id}:{self.driver_id}"
