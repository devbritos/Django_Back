from django.db import models

# Create your models here.
class auditory(models.Model):
    name_event = models.CharField(max_length=100)
    date_auditory = models.DateField()
    affected_table = models.CharField(max_length=50)
    past_value = models.TextField()
    new_value = models.TextField()
    functionary = models.ForeignKey(
        'personal.Functionary',
        on_delete=models.PROTECT
    )