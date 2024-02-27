from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProjectViewSet, TaskViewSet, CategoryViewSet, CommentViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'projects/(?P<project_id>[0-9]+)/tasks/(?P<task_id>[0-9]+)/comments', CommentViewSet, basename='comment')
router.register(r'projects/(?P<project_id>\d+)/tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='user_login'),
   
]
