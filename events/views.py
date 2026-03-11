from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Event, Profile
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def home(request):
    events = Event.objects.order_by('start_datetime')[:3]
    return render(request, 'events/home.html', {'events': events})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
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


def login_view(request):
    error_message = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            error_message = "Invalid username or password."

    return render(request, "events/login.html", {"error_message": error_message})


def logout_view(request):
    logout(request)
    return redirect("home")
