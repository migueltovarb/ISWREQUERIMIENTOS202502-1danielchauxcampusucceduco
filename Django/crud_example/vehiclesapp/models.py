# vehiclesapp/models.py

from django.db import models

class Vehicle(models.Model):
    name = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    year = models.IntegerField()
    
    def __str__(self):
        return self.name