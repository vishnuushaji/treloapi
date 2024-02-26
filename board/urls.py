from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProjectViewSet, TaskViewSet, CategoryViewSet, CommentViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'projects/(?P<project_id>[0-9]+)/tasks/(?P<task_id>[0-9]+)/comments', CommentViewSet, basename='comment')


urlpatterns = [
    path('', include(router.urls)),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='user_login'),
    path('projects/<int:project_id>/tasks/', TaskViewSet.as_view({'post': 'create'}), name='task-create'),
    path('projects/<int:project_id>/tasks/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve'}), name='task-detail'),
    path('projects/<int:project_id>/tasks/<int:pk>/delete/', TaskViewSet.as_view({'delete': 'destroy'}), name='task-delete'),
    path('projects/<int:project_id>/tasks/<int:pk>/update/', TaskViewSet.as_view({'put': 'update'}), name='task-update'),

]
