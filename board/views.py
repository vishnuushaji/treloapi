from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Project, Task, Category, Comment
from .serializers import UserSerializer, ProjectSerializer, TaskSerializer, CategorySerializer, CommentSerializer
from .permissions import IsBoardMember, IsDeveloper
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        name = serializer.validated_data.get('name')
        phone = serializer.validated_data.get('phone')
        role = serializer.validated_data.get('role')
                
        user = User.objects.create_user(email=email, password=password, name=name, phone=phone, role=role, is_active=True)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        allowed_fields = {'phone', 'name'}
        data = {key: value for key, value in data.items() if key in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
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


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(board_member=request.user)
        self.send_project_creation_email(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def send_project_creation_email(self, project):
        subject = f'New project created: {project.title}'
        message = f'A new project has been created by {project.board_member.email}.'
        from_email = 'noufalmhd112@gmail.com'
        recipient_list = [member.email for member in project.developers.all()]
        send_mail(subject, message, from_email, recipient_list)

    def list_projects(self, request):
        projects = Project.objects.filter(board_member=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        project = self.get_object()
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    def update(self, request, pk=None):
            project = self.get_object()
            if request.user != project.board_member:
                return Response({"error": "You are not allowed to update this project."}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(project, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_project = serializer.save()

            developers = request.data.get('developers', [])
            if developers:
                for developer_id in developers:
                    developer = User.objects.get(id=developer_id)
                    if developer not in updated_project.developers.all():
                        updated_project.developers.add(developer)
                    else:
                        updated_project.developers.remove(developer)

            self.send_project_update_email(updated_project)
            
            return Response(serializer.data)

    def send_project_update_email(self, project):
        subject = f'Project updated: {project.title}'
        message = f'The project {project.title} has been updated by {project.board_member.email}.'
        from_email = 'noufalmhd112@gmail.com'
        recipient_list = [member.email for member in project.developers.all()]
        send_mail(subject, message, from_email, recipient_list)


    def perform_destroy(self, instance):
        if instance.board_member == self.request.user:
            self.send_project_deletion_email(instance)
            super().perform_destroy(instance)
        else:
            raise PermissionDenied("You do not have permission to delete this project")

    # def send_project_deletion_email(self, project):
    #     pass


def send_new_task_email(task):
        subject = f'New task created: {task.title}'
        message = f'A new task has been created by {task.project.board_member.email} in the project {task.project.title}.'
        from_email = 'noufalmhd112@gmail.com'
        recipient_list = [member.email for member in task.project.developers.all()]
        send_mail(subject, message, from_email, recipient_list)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    http_method_names = ['get', 'post', 'put', 'delete']

    def create(self, request, project_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = get_object_or_404(Project, id=project_id)

        if project.board_member == request.user:
            developer_id = request.data.get('developer')
            if developer_id is None:
                raise serializers.ValidationError({'developer': 'Developer is required'})
            developer = User.objects.get(id=developer_id)
            task = serializer.save(project=project, developer=developer)
            send_new_task_email(task)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'You do not have permission to create a task in this project'}, status=status.HTTP_401_UNAUTHORIZED)


    def get(self, request, project_id):
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
            serializer = self.get_serializer(task, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request, project_id, pk=None):
        project = get_object_or_404(Project, id=project_id)
        task = get_object_or_404(Task, id=pk, project=project)
        task_name = task.title
        task_description = task.description
        success_message = self.send_task_deleted_email(task_name, task_description)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def send_task_deleted_email(self, task_name, task_description, developer_email=None):
        subject = 'Task Deleted'
        message = f'Task "{task_name}" with description "{task_description}" has been deleted.'
        from_email = 'noufalmhd112@gmail.com'
        recipient_list = [developer_email] if developer_email else []
        send_mail(subject, message, from_email, recipient_list)
        return f'Task "{task_name}" has been deleted.'


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
        self.perform_create(serializer) 
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

        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def update_text(self, request, project_id, task_id, pk=None):
        return self.update_comment(request, project_id, task_id, pk)


    def delete_comment(self, request, project_id, task_id, pk=None):
        task = get_object_or_404(Task, id=task_id, project__id=project_id)
        comment = get_object_or_404(Comment, id=pk, task=task)

        if comment.author != request.user:
            return Response({'error': 'You do not have permission to delete this comment'}, status=status.HTTP_401_UNAUTHORIZED)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
