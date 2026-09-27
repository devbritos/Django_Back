from django.db import models
from core.models import BaseModel



class Functionary(BaseModel):
    delegation = models.ForeignKey(
        'Delegation',
        on_delete=models.CASCADE)

    names = models.CharField(max_length=50)
    lastnames = models.CharField(max_length=50)


class Delegation(BaseModel):    
    name = models.CharField(max_length=50)
    state = models.CharField(max_length=15)
    field = models.CharField(max_length=50)