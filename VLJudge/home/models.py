from django.db import models
from django.contrib.auth.models import User
import os 

# Create your models here.

def hidden_testcases_upload_path(instance, filename):
    return f'hidden_testcases/hidden_testcases_{instance.id}.txt'
class Problem(models.Model):
    title = models.CharField(max_length=200)
    statement = models.TextField()
    tags = models.CharField(max_length=200)
    rating = models.IntegerField()
    input = models.TextField()
    output = models.TextField()
    image = models.ImageField(upload_to='problem_images/', null=True, blank=True, verbose_name="Image", help_text="Optional image for the problem")
    sample_testcases = models.TextField()
    hidden_testcases = models.FileField(upload_to=hidden_testcases_upload_path, blank=True, null=True, verbose_name="Hidden Testcases", help_text="Hidden test cases file")

    time_limit = models.FloatField(default=1)   
    memory_limit = models.IntegerField(default=256)
    solved_count = models.IntegerField(default=0)       
    def __str__(self):
        return self.title      
    def save(self, *args, **kwargs):
        # Xóa tệp cũ nếu có
        if self.pk:
            old_instance = Problem.objects.get(pk=self.pk)
            if old_instance.hidden_testcases and old_instance.hidden_testcases != self.hidden_testcases:
                old_instance.hidden_testcases.delete(save=False)
        super().save(*args, **kwargs)                                
  
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    github = models.URLField(null=True, blank=True)
    rank = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    solved_count = models.IntegerField(default=0)
    achievements = models.TextField(null=True, blank=True)
    easy_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    hard_count = models.IntegerField(default=0)
    public_results = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
 
class RatingChange(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    rating = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.rating}"

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    problem_title = models.CharField(max_length=255)
    source_code = models.TextField()
    language = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    result = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    memory_used = models.IntegerField()
    time_limit = models.FloatField()
    outputs = models.TextField(default='')  # Thêm cột outputs
    
    def __str__(self):
        return f"Submission by {self.user.username} for {self.problem.title}"

User.add_to_class('accepted_problems', models.JSONField(default=list, blank=True))
User.add_to_class('tried_problems', models.JSONField(default=list, blank=True))


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}"

        