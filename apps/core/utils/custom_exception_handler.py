from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response_data = {
            'success': False,
            'statusCode': response.status_code,
            'message': '',
            'error': response.data
        }
        if response.status_code == 400:
            response_data['message'] = "Bad request. Please check the data you've provided."
        elif response.status_code == 401:
            response_data['message'] = "Authentication failed. Please log in."
        elif response.status_code == 403:
            response_data['message'] = "Permission denied. You don't have access to this resource."
        elif response.status_code == 404:
            response_data['message'] = "The requested resource could not be found."
        elif response.status_code == 405:
            response_data['message'] = "Method not allowed. Please check the request method."
        elif response.status_code == 409:
            response_data['message'] = "Conflict detected. The resource already exists or there is a conflict in your request."
        elif response.status_code == 500:
            response_data['message'] = "Internal server error. Please try again later."
        else:
            response_data['message'] = "Something went wrong."

        if 'detail' in response.data:
            response_data['message'] = response.data['detail']
        response.data = response_data

    return response