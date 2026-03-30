from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),

    path('create-event/', views.create_event, name='create_event'),
    path('book/<int:event_id>/', views.book_ticket, name='book_ticket'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    path(
        'booking-confirmation/<int:booking_id>/',
        views.booking_confirmation,
        name='booking_confirmation',
    ),

    path(
        'events/<int:event_id>/attendees/',
        views.event_attendees,
        name='event_attendees',
    ),

    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),

    path("events/<int:event_id>/edit/", views.edit_event, name="edit_event"),
    path(
        "events/<int:event_id>/delete/",
        views.delete_event,
        name="delete_event",
    ),

    path(
        "bookings/<int:booking_id>/cancel/",
        views.cancel_booking,
        name="cancel_booking",
    ),
]
