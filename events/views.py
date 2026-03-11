from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import Event, Profile
from .forms import RegisterForm


def home(request):
    events = Event.objects.order_by('start_datetime')[:3]
    return render(request, 'events/home.html', {'events': events})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()

            role = form.cleaned_data['role']

            Profile.objects.create(
                user=user,
                role=role
            )

            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "events/register.html", {"form": form})
