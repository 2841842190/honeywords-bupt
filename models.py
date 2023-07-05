from django.db import models


class User(models.Model):
    identity = models.AutoField(primary_key=True)
    username = models.CharField(max_length=3200)
    s = models.TextField()


class Loginlog(models.Model):
    identity = models.IntegerField()
    ip = models.CharField(max_length=3200)
    is_honeyword = models.BooleanField()
    time = models.DateTimeField(auto_now_add=True)
