from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
import socket
import smtplib
import traceback

class TestMailView(APIView):
    def get(self, request):
        try:
            # Debug info so we KNOW env is loaded
            debug_info = {
                "EMAIL_HOST": settings.EMAIL_HOST,
                "EMAIL_PORT": settings.EMAIL_PORT,
                "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
                "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
            }

            # try DNS resolve first (to detect network block / ISP issue)
            socket.getaddrinfo(settings.EMAIL_HOST, settings.EMAIL_PORT)

            subject = "Test Mail from Django"
            body = "If you see this, SMTP is working."
            from_email = settings.DEFAULT_FROM_EMAIL          # Brevo verified sender
            to_list = ["officeazizur@gmail.com"]               # your inbox

            sent_count = send_mail(
                subject,
                body,
                from_email,
                to_list,
                fail_silently=False,
            )

            return Response({
                "status": "ok",
                "sent_count": sent_count,
                "debug": debug_info,
            }, status=200)

        except (socket.gaierror, socket.timeout) as net_err:
            # DNS / network problem
            return Response({
                "status": "network_error",
                "error_type": str(type(net_err).__name__),
                "error": str(net_err),
                "hint": "If this fails, your PC/network cannot reach Brevo on port 587. That's not a code bug."
            }, status=500)

        except smtplib.SMTPAuthenticationError as auth_err:
            # Brevo didn't accept login
            return Response({
                "status": "auth_error",
                "error": str(auth_err),
                "hint": "Bad EMAIL_HOST_USER or EMAIL_HOST_PASSWORD or Brevo blocked the IP."
            }, status=500)

        except smtplib.SMTPRecipientsRefused as rcpt_err:
            # Recipient rejected
            return Response({
                "status": "recipient_error",
                "error": str(rcpt_err),
                "hint": "Brevo refused to send to that 'to' address. Try another recipient."
            }, status=500)

        except Exception as e:
            # Any other SMTP / TLS / SSL / policy issue
            return Response({
                "status": "unknown_error",
                "error_type": str(type(e).__name__),
                "error": str(e),
                "trace": traceback.format_exc(),
                "hint": "If you see 'Connection refused' or 'timed out' this is environment/firewall. If you see 'must be authenticated', check credentials."
            }, status=500)
