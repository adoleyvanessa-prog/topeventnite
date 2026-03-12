from django import forms
from django.contrib.auth.models import User
from .models import Event
from django.forms import DateTimeInput


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    ROLE_CHOICES = [
        ('organiser', 'Organiser'),
        ('attendee', 'Attendee'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password'
        ]
      
        
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'start_datetime',
            'location',
            'venue',
            'capacity',
            'price',
        ]
        widgets = {
            'start_datetime': DateTimeInput(attrs={'type': 'datetime-local'}),
        }