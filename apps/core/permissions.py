from rest_framework import permissions


class IsAdminOrInstructor(permissions.BasePermission):
    """
    Custom permission to allow access only to Admin or instructor users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_superuser or
            getattr(request.user, 'role', None) == 'admin' or
            getattr(request.user, 'role', None) == 'instructor'
        )


class IsAdminRole(permissions.BasePermission):
    """
    Custom permission to allow only admin users or users with the 'admin' role
    to perform create, update, or delete operations.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_superuser or
            getattr(request.user, 'role', None) == 'admin'
        )
