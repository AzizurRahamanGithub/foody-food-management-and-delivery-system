from rest_framework.response import Response
from rest_framework import status

class ResponseMixin:
    def success_response(self, data, message="success"):
        return Response({'message': message, 'data': data}, status=status.HTTP_200_OK)

    def error_response(self, errors, message="false"):
        return Response({'message': message, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
