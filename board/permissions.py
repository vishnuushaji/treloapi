from rest_framework import permissions

class IsBoardMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_board_member:
            return True
        return False

class IsDeveloper(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_developer:
            return True
        return False