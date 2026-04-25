from django.db import models

# Create your models here.

class User(models.Model):

    bale_id = models.CharField(max_length=100, unique=True)

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    level = models.CharField(max_length=20, blank=True, null=True)

    score = models.IntegerField(default=0)

    last_exam_level = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
    


    