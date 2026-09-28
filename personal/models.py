from django.db import models
from core.models import BaseModel



class Functionary(BaseModel):
    delegation = models.ForeignKey(
        'Delegation',
        on_delete=models.PROTECT)
    position = models.ForeignKey(
        'Position',
        on_delete= models.PROTECT,

    )
    names = models.CharField(max_length=50)
    lastnames = models.CharField(max_length=50)


class Delegation(BaseModel):
    #The first shows in a row on a DB and the second(value) its the frontend label
    STATES_CHOICES = [
        ('ACTIVO','Activo'),
        ('INACTIVO','Inactivo')
    ]

    FIELD_CHOICES = [
        ('RURAL', 'Rural'),
        ('URBANO', 'Urbano')
    ]   
    name = models.CharField(max_length=50)
    state = models.CharField(max_length=15, choices= STATES_CHOICES, 
                            default = 'ACTIVO')
    
    field = models.CharField(max_length=50, choices = FIELD_CHOICES)



class Position(BaseModel):
    name = models.CharField(max_length=50)
    validity = models.BooleanField(default=True)

class Role(BaseModel):
    role_name = models.CharField(max_length=30)
    
class FunctionaryRole(BaseModel):
    functionary = models.ForeignKey(
        'Functionary',
        on_delete=models.CASCADE)
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE)

    #Class that will do that,The same role can't be
    # Assigned twice to the same functionary  
    class Meta:
        constraints= [
            models.UniqueConstraint(
                fields= ["functionary", "role"],
                name = "unique_functionary_role",
            )
        ]
    








