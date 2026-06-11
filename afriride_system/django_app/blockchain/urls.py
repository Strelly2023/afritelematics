# afriride_system/django_app/blockchain/urls.py

from django.urls import path

from .views import anchor_proof

app_name = "blockchain"

urlpatterns = [
    path("anchor/", anchor_proof, name="anchor_proof"),
]