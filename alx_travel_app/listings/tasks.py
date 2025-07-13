from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_payment_confirmation_email(booking_id, user_email):
    """
    Task to send a payment confirmation email.
    """
    send_mail(
        subject='Payment Successful - Booking Confirmation',
        message=f'Your booking with ID {booking_id} has been confirmed and is successful.',
        from_email=None,
        recipient_list=[user_email],
        fail_silently=False
    )

@shared_task
def send_booking_confirmation_email(booking_id, user_email):
    """
    Task to send a booking confirmation email.
    """
    send_mail(
        subject='Booking Confirmation',
        message=f'Your booking with ID {booking_id} has been successfully created.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False
    )
    return f'Booking confirmation email sent to {user_email} for booking ID {booking_id}'
