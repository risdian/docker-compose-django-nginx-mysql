from django.contrib import admin
from .models import ChatHistory, AI, AIFile, Customer

admin.site.register(ChatHistory)
admin.site.register(AI)
admin.site.register(AIFile)
admin.site.register(Customer)