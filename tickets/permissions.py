from rest_framework.permissions import BasePermission


class TicketPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        is_admin = user.role == 'ADMIN'
        is_owner = obj.created_by == user

        if view.action == 'destroy':
            return is_admin

        if view.action in ['update', 'partial_update']:
            if is_admin:
                return True
            return is_owner and obj.status == 'OPEN'

        if view.action == 'retrieve':
            return is_admin or is_owner

        return True
