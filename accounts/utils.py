from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse

def detect_user(user):
    if user.role == 0 or user.role == 1 and user.is_superadmin:
        redirect_url = '/admin'
    elif user.role == 2:
        redirect_url = '/manager-dashboard'
    elif user.role == 3:
        redirect_url = '/developer-dashboard'
    elif user.role == 4:
        redirect_url = '/qa-dashboard'
    elif user.role == 5:
        redirect_url = '/guest-dashboard'
    return redirect_url

def send_verification_email(user, action='set_password'):
    print('came inside send_verification_email')
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    domain = settings.DOMAIN
    reset_path = reverse('accounts:reset_password_validate', kwargs={'uidb64': uid, 'token': token})
    reset_url = f"{domain}{reset_path}"

    message = render_to_string('accounts/email/reset_password_email.html', {
        'user': user,
        'reset_url': reset_url,
        'action': action,
    })

    email = EmailMessage(
        subject="Set your password – TaskFlow" if action != 'reset_password' else "Reset your password – TaskFlow",
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.send()
