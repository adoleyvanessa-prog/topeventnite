from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid


class Profile(models.Model):
    # These are the two roles available on the platform.
    ROLE_CHOICES = [
        ('organiser', 'Organiser'),
        ('attendee', 'Attendee'),
    ]

    # Each user gets one profile linked to their account.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Event(models.Model):
    # This links each event to the organiser who created it.
    organiser = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events_created'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    location = models.CharField(max_length=150)
    venue = models.CharField(max_length=150)

    # Capacity must be at least 1.
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Price can be free, so the minimum allowed value is 0.
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Organisers can optionally upload an event image.
    event_image = models.ImageField(
        upload_to='event_images/',
        blank=True,
        null=True
    )

    # Saves the date and time the event was created.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def confirmed_bookings_count(self):
        # Counts how many paid and confirmed bookings belong to this event.
        return self.bookings.filter(
            payment_status="paid",
            status="confirmed"
        ).count()

    @property
    def remaining_spots(self):
        # Works out how many spaces are left, but never lets it go below 0.
        return max(self.capacity - self.confirmed_bookings_count, 0)

    @property
    def is_sold_out(self):
        # Returns True when there are no spaces left.
        return self.remaining_spots <= 0


class Booking(models.Model):
    # Payment can be waiting, completed, or unsuccessful.
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    # Booking itself can either stay confirmed or be cancelled.
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    # This links the booking to the user who made it.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # This links the booking to the event being booked.
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    # Booking reference is generated automatically if one does not exist yet.
    booking_reference = models.CharField(
        max_length=20, unique=True, blank=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents the same user from booking the same event more than once.
        unique_together = ('user', 'event')

    def save(self, *args, **kwargs):
        # Generates a short unique booking reference the first time the
        # booking is saved.
        if not self.booking_reference:
            self.booking_reference = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
