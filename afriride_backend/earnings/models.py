from django.db import models


class DriverEarning(models.Model):
    ride = models.OneToOneField("rides.Ride", on_delete=models.CASCADE)
    driver = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    gross_fare = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    net_earning = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"DriverEarning(ride={self.ride_id}, driver={self.driver_id})"
