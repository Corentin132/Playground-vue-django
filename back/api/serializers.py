from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import serializers

from .models import Project, ProjectMember, Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    def get_members(self, obj):
        members = User.objects.filter(
            Q(id=obj.owner_id) | Q(project_memberships__project=obj)
        ).distinct()
        return UserSerializer(members.order_by("username"), many=True).data

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return obj.owner_id == request.user.id

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "is_owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="project.id", read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source="assigned_to",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    def validate_assigned_to_id(self, value):
        if value is None:
            return value

        project = self.context.get("project")
        if project is None and self.instance is not None:
            project = self.instance.project

        if project is None:
            raise serializers.ValidationError(
                "Impossible de valider l'assignation pour ce projet."
            )

        belongs_to_project = (
            project.owner_id == value.id
            or ProjectMember.objects.filter(
                project=project,
                user=value,
            ).exists()
        )
        if not belongs_to_project:
            raise serializers.ValidationError(
                "L'utilisateur assigné doit appartenir au projet."
            )

        return value

    class Meta:
        model = Task
        fields = [
            "id",
            "project_id",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_to_id",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "project_id", "created_at", "updated_at"]
