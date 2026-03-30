from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Event, Profile, Booking
from .forms import RegisterForm, EventForm
import stripe
from django.conf import settings

# Stripe secret key is taken from settings so checkout can work.
stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    # Get all events in date order and show only the first 3 as featured events.
    all_events = Event.objects.order_by('start_datetime')
    featured_events = all_events[:3]
    organiser_events = []
    user_role = None
    sold_out_event_ids = []

    # Build a list of sold-out event IDs so badges can be shown in the template.
    for event in all_events:
        confirmed_bookings = event.bookings.filter(status="confirmed").count()
        if confirmed_bookings >= event.capacity:
            sold_out_event_ids.append(event.id)

    # If the user is logged in, check their role.
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        if profile:
            user_role = profile.role

            # If the user is an organiser, show their own created events on the home page.
            if user_role == "organiser":
                organiser_events = Event.objects.filter(
                    organiser=request.user
                ).order_by('start_datetime')

    return render(request, 'events/home.html', {
        'featured_events': featured_events,
        'organiser_events': organiser_events,
        'user_role': user_role,
        'sold_out_event_ids': sold_out_event_ids,
    })


def register_view(request):
    # Handle user registration.
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Save the user but hash the password properly first.
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create the linked profile using the selected role.
            role = form.cleaned_data['role']
            Profile.objects.create(
                user=user,
                role=role
            )

            # Log the user in straight after registering.
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "events/register.html", {"form": form})


def login_view(request):
    error_message = None

    # Handle login form submission.
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
    # Log the user out and return them to the home page.
    logout(request)
    return redirect("home")


def about_page(request):
    return render(request, "events/about.html")


def contact_page(request):
    return render(request, "events/contact.html")


def event_list(request):
    # Get any search/filter values from the URL.
    search_query = request.GET.get("q", "").strip()
    location_query = request.GET.get("location", "").strip()

    # Start with all events ordered by soonest first.
    events = Event.objects.all().order_by("start_datetime")

    # Filter by title if a search value was entered.
    if search_query:
        events = events.filter(title__istartswith=search_query)

    # Filter by location if a location value was entered.
    if location_query:
        events = events.filter(location__icontains=location_query)

    return render(request, 'events/event_list.html', {
        'events': events,
        'search_query': search_query,
        'location_query': location_query,
    })


def event_detail(request, event_id):
    # Get the selected event or show 404 if it does not exist.
    event = get_object_or_404(Event, id=event_id)

    # Count confirmed bookings to work out remaining spaces.
    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    remaining_spots = event.capacity - confirmed_bookings

    user_role = None
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        if profile:
            user_role = profile.role

    return render(request, 'events/event_detail.html', {
        'event': event,
        'remaining_spots': remaining_spots,
        'total_bookings': confirmed_bookings,
        'user_role': user_role,
    })


@login_required
def create_event(request):
    # Only organisers are allowed to create events.
    if request.user.profile.role != "organiser":
        return HttpResponseForbidden("Only organisers can create events.")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            # Attach the logged-in user as the organiser before saving.
            event = form.save(commit=False)
            event.organiser = request.user
            event.save()
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventForm()

    return render(request, "events/create_event.html", {"form": form})


@login_required
def book_ticket(request, event_id):
    # Only attendees can make bookings.
    if request.user.profile.role != "attendee":
        return HttpResponseForbidden("Only attendees can book tickets.")

    # Stop booking if Stripe is not configured.
    if not settings.STRIPE_SECRET_KEY:
        return HttpResponseForbidden("Stripe is not configured.")

    event = get_object_or_404(Event, id=event_id)

    # Prevent booking if the event is already full.
    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    if confirmed_bookings >= event.capacity:
        return HttpResponseForbidden("This event is sold out.")

    # Prevent the same user from booking the same event twice.
    existing_booking = Booking.objects.filter(
        user=request.user,
        event=event
    ).first()
    if existing_booking:
        return HttpResponseForbidden("You have already booked this event.")

    # Use the user's full name if available, otherwise fall back to username.
    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not full_name:
        full_name = request.user.username

    # Create Stripe checkout session for payment.
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
    # Stripe sends the session ID back in the success URL.
    session_id = request.GET.get("session_id")

    if not session_id:
        return HttpResponseForbidden("Missing session ID.")

    session = stripe.checkout.Session.retrieve(session_id)

    # Make sure payment actually completed.
    if session.payment_status != "paid":
        return HttpResponseForbidden("Payment not completed.")

    # Get booking details stored in Stripe metadata.
    event_id = session.metadata.get("event_id")
    user_id = session.metadata.get("user_id")
    full_name = session.metadata.get("full_name")
    email = session.metadata.get("email")

    # Security check so users cannot access someone else's payment success page.
    if str(request.user.id) != str(user_id):
        return HttpResponseForbidden("This payment does not belong to you.")

    event = get_object_or_404(Event, id=event_id)

    # Check again in case the event sold out while payment was processing.
    confirmed_bookings = event.bookings.filter(status="confirmed").count()
    if confirmed_bookings >= event.capacity:
        error_msg = (
            "Sorry, this event sold out before your payment completed."
        )
        return HttpResponseForbidden(error_msg)

    # Create the booking if it does not already exist.
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
    # Simple page shown when Stripe checkout is cancelled.
    return render(request, "events/payment_cancel.html")


@login_required
def my_bookings(request):
    # Only attendees should be able to view personal bookings.
    if request.user.profile.role != "attendee":
        return HttpResponseForbidden("Only attendees can view bookings.")

    bookings = Booking.objects.filter(
        user=request.user
    ).order_by('-created_at')

    user_role = None
    profile = Profile.objects.filter(user=request.user).first()
    if profile:
        user_role = profile.role

    return render(request, "events/my_bookings.html", {
        "bookings": bookings,
        "user_role": user_role,
    })


@login_required
def booking_confirmation(request, booking_id):
    # Get the booking and make sure it belongs to the logged-in user.
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You cannot view this booking.")

    return render(request, "events/booking_confirmation.html", {
        "booking": booking
    })


@login_required
def event_attendees(request, event_id):
    # Organisers can see the confirmed attendees for their own event.
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
    # Only the organiser who created the event can edit it.
    event = get_object_or_404(Event, id=event_id)

    if event.organiser != request.user:
        return HttpResponseForbidden("You cannot edit this event.")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
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
    # Only the organiser who created the event can delete it.
    event = get_object_or_404(Event, id=event_id)

    if event.organiser != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        event.delete()
        return redirect("home")

    return redirect("event_detail", event_id=event.id)


@login_required
def cancel_booking(request, booking_id):
    # Only the person who made the booking can cancel it.
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
