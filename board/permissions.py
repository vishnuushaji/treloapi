from rest_framework import permissions

class IsBoardMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the request user is the board member of the project
        return request.user == obj.board_member


class IsDeveloper(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_developer:
            return True
        return False
    


