from django.contrib import admin
from .models import Profile, Event, Booking


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Show user and role in the admin profile list.
    list_display = ('user', 'role')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Controls how events appear in the Django admin.
    list_display = ('title', 'organiser', 'start_datetime', 'location',
                    'price', 'capacity')
    search_fields = ('title', 'location', 'venue')
    list_filter = ('location', 'start_datetime')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Controls how bookings appear in the Django admin.
    list_display = ('booking_reference', 'user', 'event', 'payment_status',
                    'status', 'created_at')
    search_fields = ('booking_reference', 'full_name', 'email')
    list_filter = ('payment_status', 'status', 'created_at')
