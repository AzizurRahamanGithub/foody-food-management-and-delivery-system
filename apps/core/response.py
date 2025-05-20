
from rest_framework import status
from rest_framework.response import Response


def success_response(message, data=None, status=status.HTTP_200_OK):
    return Response({
        "success": True,
        "status_code": status,
        "message": message,
        "data": data or {}
    }, status=status)


def failure_response(message, error=None, status=status.HTTP_400_BAD_REQUEST):
    return Response({
        "success": False,
        "status_code": status,
        "message": message,
        "error": error or {}
    }, status=status)