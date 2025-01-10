from django.contrib import admin
from .models import Problem
from django import forms
# Register your models here.

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = '__all__'
        widgets = {
            'sample_testcases': forms.Textarea(attrs={
                'placeholder': 'Testcase 1:\nInput:\n3\n1 1\n2 2\n3 3\nOutput:\n2\n4\n6\n\nTestcase 2:\nInput:\n2\n2 3\n1 2\nOutput:\n5\n3'
            }),
        } 

class ProblemAdmin(admin.ModelAdmin):
    form = ProblemForm

admin.site.register(Problem, ProblemAdmin)