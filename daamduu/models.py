from django.db import models

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    calorie = models.IntegerField()
    image = models.TextField()  # Store the image as a base64 string
    date = models.DateField()

    def __str__(self):
        return self.name 