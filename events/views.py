from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Event, Profile, Booking
from .forms import RegisterForm, EventForm
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    featured_events = Event.objects.order_by('start_datetime')[:3]
    organiser_events = []
    user_role = None

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        if profile:
            user_role = profile.role
            if user_role == "organiser":
                organiser_events = Event.objects.filter(
                    organiser=request.user
                ).order_by('start_datetime')

    return render(request, 'events/home.html', {
        'featured_events': featured_events,
        'organiser_events': organiser_events,
        'user_role': user_role,
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

    return render(request, "events/login.html", {
        "error_message": error_message
    })


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

    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    if confirmed_bookings >= event.capacity:
        return HttpResponseForbidden("This event is sold out.")

    existing_booking = Booking.objects.filter(
        user=request.user,
        event=event
        ).first()
    if existing_booking:
        return HttpResponseForbidden("You have already booked this event.")

    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not full_name:
        full_name = request.user.username

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": event.title,
                        "description": event.description[:200],
                    },
                    "unit_amount": int(event.price * 100),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "event_id": str(event.id),
            "user_id": str(request.user.id),
            "full_name": full_name,
            "email": request.user.email,
        },
        success_url=(
            request.build_absolute_uri("/payment/success/")
            + "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=request.build_absolute_uri("/payment/cancel/"),
    )

    return redirect(session.url, code=303)


@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return HttpResponseForbidden("Missing session ID.")

    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status != "paid":
        return HttpResponseForbidden("Payment not completed.")

    event_id = session.metadata.get("event_id")
    user_id = session.metadata.get("user_id")
    full_name = session.metadata.get("full_name")
    email = session.metadata.get("email")

    if str(request.user.id) != str(user_id):
        return HttpResponseForbidden("This payment does not belong to you.")

    event = get_object_or_404(Event, id=event_id)

    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    if confirmed_bookings >= event.capacity:
        error_msg = (
            "Sorry, this event sold out before your payment completed."
        )
        return HttpResponseForbidden(error_msg)

    booking = Booking.objects.filter(
        user=request.user,
        event=event
        ).first()
    if not booking:
        booking = Booking.objects.create(
            user=request.user,
            event=event,
            full_name=full_name,
            email=email,
            payment_status="paid",
            status="confirmed",
            )

    return redirect("booking_confirmation", booking_id=booking.id)


@login_required
def payment_cancel(request):
    return render(request, "events/payment_cancel.html")


@login_required
def my_bookings(request):
    if request.user.profile.role != "attendee":
        return HttpResponseForbidden("Only attendees can view bookings.")

    bookings = Booking.objects.filter(
        user=request.user
    ).order_by('-created_at')

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

    bookings = Booking.objects.filter(
        event=event,
        status="confirmed",
    ).order_by('-created_at')

    return render(request, "events/event_attendees.html", {
        "event": event,
        "bookings": bookings
    })


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.organiser != request.user:
        return HttpResponseForbidden("You cannot edit this event.")

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, "events/edit_event.html", {
        "form": form,
        "event": event
    })


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.organiser != request.user:
        return HttpResponseForbidden("You cannot delete this event.")

    if request.method == "POST":
        event.delete()
        return redirect("home")

    return render(request, "events/delete_event.html", {
        "event": event
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        booking.delete()
        messages.success(request, "Booking cancelled successfully.")
        return redirect("my_bookings")

    return render(request, "events/cancel_booking.html", {
        "booking": booking
    })
