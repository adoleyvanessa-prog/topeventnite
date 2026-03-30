from django import forms
from django.contrib.auth.models import User
from .models import Event
from django.forms import DateTimeInput


class RegisterForm(forms.ModelForm):
    # Password is shown as dots instead of plain text in the form.
    password = forms.CharField(widget=forms.PasswordInput)

    # These are the user roles available when someone registers.
    ROLE_CHOICES = [
        ('organiser', 'Organiser'),
        ('attendee', 'Attendee'),
    ]

    # Extra field added to the form so a user can choose their role.
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        # This form is based on Django's built-in User model.
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
        # This form is used for both creating and editing events.
        model = Event
        fields = [
            'title',
            'description',
            'start_datetime',
            'location',
            'venue',
            'capacity',
            'price',
            'event_image',
        ]
        widgets = {
            # This changes the input type so the browser shows a date/time
            # picker.
            'start_datetime': DateTimeInput(attrs={'type': 'datetime-local'}),
        }
