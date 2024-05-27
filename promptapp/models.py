from django.db import models

# class InstructionsSet(models.Model):
#     name = models.CharField(max_length=50)
#     instructionA = models.CharField(max_length=250, default="")
#     instructionB = models.CharField(max_length=250, default="")
#     instructionC = models.CharField(max_length=250, default="")    
#     def __str__(self):
#         return self.name
    
class SettingPage(models.Model):
    Claude_API = models.CharField(max_length=250, default="")
    Claude_API_status = models.BooleanField(default=False)
    OpenAI_API = models.CharField(max_length=250, default="") 
    OpenAI_API_status = models.BooleanField(default=False)
    

class InstructionsSet(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Instruction(models.Model):
    instruction_set = models.ForeignKey(InstructionsSet, related_name='instructions', on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    text = models.CharField(max_length=250)

    def __str__(self):
        return self.name
