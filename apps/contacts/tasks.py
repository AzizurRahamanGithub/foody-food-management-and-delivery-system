
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_contract_email(contract_details, recipient_email):
    """ Send email when a new contract is created. """
    subject = f"Contract Created: {contract_details['contract_name']}"
    message = f"Dear {contract_details['client_name']},\n\nYour contract with the following details has been created:\n\n{contract_details['details']}\n\nRegards,\nThe Team"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
    )