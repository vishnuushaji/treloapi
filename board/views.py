from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import User, Project, Task, Category, Comment
from .serializers import UserSerializer, ProjectSerializer, TaskSerializer, CategorySerializer, CommentSerializer
from .permissions import IsBoardMember, IsDeveloper

class UserViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email is already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save(is_active=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return Response({'message': 'Logged in successfully'})
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        if request.user.is_authenticated:
            serializer = self.serializer_class(request.user)
            return Response(serializer.data)
        else:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        if request.user.is_authenticated:
            serializer = self.serializer_class(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(board_member=request.user)
        self.send_project_creation_email(project)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        if user != instance.board_member:
            return Response({'error': 'You do not have permission to update this project'}, status=HTTP_401_UNAUTHORIZED)
        project = serializer.save()
        self.send_project_update_email(project)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if user != instance.board_member:
            return Response({'error': 'You do not have permission to delete this project'}, status=HTTP_401_UNAUTHORIZED)
        self.send_project_deletion_email(instance)
        self.perform_destroy(instance)
        return Response(status=HTTP_204_NO_CONTENT)

    def send_project_creation_email(self, project):
        pass

    def send_project_update_email(self, project):
        pass

    def send_project_deletion_email(self, project):
        pass






class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def create(self, request, project_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, project_id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, project_id):
        user = self.request.user
        project = get_object_or_404(Project, id=project_id)
        task = serializer.save(developer=user, project=project)
        send_mail('Task Created', f'{user.name} created a new task: {task.title}', 'your_email@example.com', [user.email])

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def assign_task(self, request, pk=None, project_id=None):
        task = self.get_object()
        user = request.user
        if user != task.developer:
            return Response({'error': 'You do not have permission to assign this task'}, status=status.HTTP_401_UNAUTHORIZED)
        if 'developer' in request.data:
            new_developer = User.objects.get(id=request.data['developer'])
            task.developer = new_developer
            task.save()
            return Response({'message': 'Task assigned to new developer'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Developer not provided'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_task_status(self, request, pk=None, project_id=None):
        task = self.get_object()
        user = request.user
        if user != task.developer:
            return Response({'error': 'You do not have permission to change the status of this task'}, status=status.HTTP_401_UNAUTHORIZED)
        if 'status' in request.data:
            new_status = request.data['status']
            if new_status in ['Not Started', 'In Progress', 'Completed']:
                task.status = new_status
                task.save()
                return Response({'message': 'Task status changed'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid status provided'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Status not provided'}, status=status.HTTP_400_BAD_REQUEST)



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer




class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDeveloper]

    def create(self, request, project_id, task_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, task_id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, task_id):
        user = self.request.user
        task = get_object_or_404(Task, id=task_id)
        
        if user != task.developer and user != task.project.board_member:
            raise PermissionError('You do not have permission to create a comment for this task')

        comment = serializer.save(user=user, task=task)
        send_mail('Comment Created', f'{user.name} created a new comment: {comment.text}', 'your_email@example.com', [user.email])

    def perform_update(self, serializer, **kwargs):
        user = self.request.user
        comment_id = kwargs.get('pk')
        comment = get_object_or_404(Comment, id=comment_id)
        
        if user != comment.user:
            raise PermissionError('You do not have permission to update this comment')
        
        serializer.save()

    def perform_destroy(self, instance, **kwargs):
        user = self.request.user
        comment_id = kwargs.get('pk')
        comment = get_object_or_404(Comment, id=comment_id)
        
        if user != comment.user:
            raise PermissionError('You do not have permission to delete this comment')
        
        instance.delete()




@api_view(['POST'])
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_view(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    serializer = ProjectSerializer(project)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    serializer = TaskSerializer(task)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsBoardMember])
def board_projects_view(request):
    projects = Project.objects.filter(board_member=request.user)
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsDeveloper])
def developer_tasks_view(request):
    tasks = Task.objects.filter(developer=request.user)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsDeveloper])
def developer_project_tasks_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project, developer=request.user)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsBoardMember])
def board_member_project_tasks_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsDeveloper])
def developer_project_categories_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    categories = Category.objects.filter(project=project)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsBoardMember])
def board_member_project_categories_view(request, project_id):
    project = get_object_or_404(Project, id=project_id) 
    categories = Category.objects.filter(project=project) 
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)
