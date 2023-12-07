from django.db import models
from django.utils.text import slugify


# This function generates the directory path
def ai_directory_path(instance, filename):
    # Replace 'name' with the actual field name of the 'AI' model that contains the AI's name
    ai_name = slugify(instance.ai.name)
    return f'ai_files/{ai_name}/{filename}'

class AI(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class AIFile(models.Model):
    ai = models.ForeignKey(AI, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to=ai_directory_path)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.file.name
    
class Customer(models.Model):
    name = models.CharField(max_length=255)
    chat_id = models.IntegerField(null=True)

    def __str__(self):
        return self.name
    
class ChatHistory(models.Model):
    user_id = models.IntegerField(null=True)
    chat_id = models.IntegerField(null=True)
    ai = models.ForeignKey(AI, on_delete=models.CASCADE, null=True)  # Allowing null for user messages
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    from_ai = models.BooleanField(default=False)  # True if the message is from the AI
    
    def __str__(self):
        participant = self.ai.name if self.from_ai else f"User {self.user_id}"
        return f"Message from {participant} at {self.timestamp}"
    class Meta:
        ordering = ['timestamp']

