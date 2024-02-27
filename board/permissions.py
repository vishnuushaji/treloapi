from rest_framework import permissions

class IsBoardMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):     
        return request.user == obj.board_member


class IsDeveloper(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):   
        return request.user.role == 'Developer'


