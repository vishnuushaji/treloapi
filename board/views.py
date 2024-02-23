from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Project, Task, Category, Comment
from .serializers import UserSerializer, ProjectSerializer, TaskSerializer, CategorySerializer, CommentSerializer
from .permissions import IsBoardMember, IsDeveloper
from rest_framework.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_204_NO_CONTENT

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from .serializers import UserSerializer
from .models import User

class UserViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email is already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save(is_active=True)

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': serializer.data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }, status=status.HTTP_201_CREATED)

    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)

            refresh = RefreshToken.for_user(user)

            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
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
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(board_member=request.user)
        self.send_project_creation_email(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list_projects(self, request):
        projects = Project.objects.filter(board_member=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def retrieve_project(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def update_project(self, request, pk=None):
        project = self.get_object()
        serializer = self.get_serializer(project, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.send_project_update_email(project) 
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save() 

    def send_project_update_email(self, project):
        pass

    def destroy(self, request, pk=None):
        project = self.get_object()
        if project.board_member == request.user:  
            self.send_project_deletion_email(project)  
            self.perform_destroy(project)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'You do not have permission to delete this project'}, status=status.HTTP_403_FORBIDDEN)

    def send_project_deletion_email(self, project):
        pass



class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def create(self, request, project_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)     
        project = get_object_or_404(Project, id=project_id)
        
        if project.board_member == request.user:
            task = serializer.save(project=project)
            self.send_new_task_email(task)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'You do not have permission to create a task in this project'}, status=status.HTTP_401_UNAUTHORIZED)

    def send_new_task_email(self, task):
        pass



    def list(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        tasks = self.queryset.filter(project=project)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    def retrieve(self, request, project_id, pk=None):
        project = get_object_or_404(Project, id=project_id)
        task = get_object_or_404(Task, id=pk, project=project)
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    def update(self, request, project_id, pk=None):
        project = get_object_or_404(Project, id=project_id)
        task = get_object_or_404(Task, id=pk, project=project)
        if task.developer == request.user:
            serializer = self.get_serializer(task, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'error': 'You do not have permission to update this task'}, status=status.HTTP_401_UNAUTHORIZED)

    def destroy(self, request, project_id, pk=None):
        project = get_object_or_404(Project, id=project_id)
        task = get_object_or_404(Task, id=pk, project=project)
        if task.developer == request.user:
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'You do not have permission to delete this task'}, status=status.HTTP_401_UNAUTHORIZED)

    def send_new_task_email(self, task):
        pass

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDeveloper]

    def create_comment(self, request, project_id, task_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, task_id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list_comments(self, request, project_id, task_id):
        task = get_object_or_404(Task, id=task_id, project__id=project_id)
        comments = self.queryset.filter(task=task)
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)

    def retrieve_comment(self, request, project_id, task_id, pk=None):
        task = get_object_or_404(Task, id=task_id, project__id=project_id)
        comment = get_object_or_404(Comment, id=pk, task=task)
        serializer = self.get_serializer(comment)
        return Response(serializer.data)
   
    def update_comment(self, request, project_id, task_id, pk=None):
        task = get_object_or_404(Task, id=task_id, project__id=project_id)
        comment = get_object_or_404(Comment, id=pk, task=task)

        if comment.author != request.user:
            return Response({'error': 'You do not have permission to update this comment'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

    def delete_comment(self, request, project_id, task_id, pk=None):
        task = get_object_or_404(Task, id=task_id, project__id=project_id)
        comment = get_object_or_404(Comment, id=pk, task=task)

        if comment.author != request.user:
            return Response({'error': 'You do not have permission to delete this comment'}, status=status.HTTP_401_UNAUTHORIZED)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


   