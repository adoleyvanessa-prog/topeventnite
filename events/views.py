from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Event, Profile, Booking
from .forms import RegisterForm, EventForm


def home(request):
    featured_events = Event.objects.order_by('start_datetime')[:3]
    organiser_events = None

    if request.user.is_authenticated and request.user.profile.role == "organiser":
        organiser_events = Event.objects.filter(
            organiser=request.user
        ).order_by('start_datetime')

    return render(request, 'events/home.html', {
        'featured_events': featured_events,
        'organiser_events': organiser_events,
    })


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


def event_list(request):
    events = Event.objects.order_by('start_datetime')
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    remaining_spots = event.capacity - confirmed_bookings

    return render(request, 'events/event_detail.html', {
        'event': event,
        'remaining_spots': remaining_spots,
        'total_bookings': confirmed_bookings,
    })


@login_required
def create_event(request):
    if request.user.profile.role != "organiser":
        return HttpResponseForbidden("Only organisers can create events.")

    if request.method == "POST":
        form = EventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)
            event.organiser = request.user
            event.save()
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventForm()

    return render(request, "events/create_event.html", {"form": form})


@login_required
def book_ticket(request, event_id):
    if request.user.profile.role != "attendee":
        return HttpResponseForbidden("Only attendees can book tickets.")

    event = get_object_or_404(Event, id=event_id)

    if Booking.objects.filter(user=request.user, event=event).exists():
        return HttpResponseForbidden("You have already booked this event.")

    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    if confirmed_bookings >= event.capacity:
        return HttpResponseForbidden("This event is sold out.")

    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not full_name:
        full_name = request.user.username

    booking = Booking.objects.create(
        user=request.user,
        event=event,
        full_name=full_name,
        email=request.user.email,
        payment_status="pending",
        status="cancelled",
    )

    return redirect("payment_page", booking_id=booking.id)


@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You cannot access this payment page.")

    return render(request, "events/payment.html", {
        "booking": booking
    })


@login_required
def complete_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You cannot complete this payment.")

    booking.payment_status = "paid"
    booking.status = "confirmed"
    booking.save()

    return redirect("booking_confirmation", booking_id=booking.id)


@login_required
def my_bookings(request):
    if request.user.profile.role != "attendee":
        return HttpResponseForbidden("Only attendees can view bookings.")

    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    return render(request, "events/my_bookings.html", {
        "bookings": bookings
    })


@login_required
def booking_confirmation(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You cannot view this booking.")

    return render(request, "events/booking_confirmation.html", {
        "booking": booking
    })


@login_required
def event_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.organiser != request.user:
        return HttpResponseForbidden("You cannot view this event's bookings.")

    bookings = Booking.objects.filter(event=event).order_by('-created_at')

    return render(request, "events/event_attendees.html", {
        "event": event,
        "bookings": bookings
    })
