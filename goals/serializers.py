from django.core.exceptions import ValidationError
from django.db import transaction
from requests import Request
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from core.models import User
from core.serializers import UserSerializer
from goals.models import GoalCategory, GoalComment, Goal, Board, BoardParticipant


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания доски.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        read_only_fields = ("id", "created", "updated", "is_deleted")
        fields = "__all__"

    def create(self, validated_data):
        """
        Метод создания доски.
        :param validated_data:
        :return:
        """
        user = validated_data.pop("user")
        board = Board.objects.create(**validated_data)
        BoardParticipant.objects.create(
            user=user, board=board, role=BoardParticipant.Role.owner
        )
        return board


class BoardParticipantSerializer(serializers.ModelSerializer):
    """
    Сериализатор доски с участниками.
    """
    role = serializers.ChoiceField(required=True, choices=BoardParticipant.editable_roles)
    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = BoardParticipant
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "board")


class BoardWithParticipantsSerializer(serializers.ModelSerializer):
    """
    Сериализатор участников доски.
    """
    participants = BoardParticipantSerializer(many=True)

    class Meta:
        model = Board
        fields = "__all__"
        read_only_fields = ("id", "created", "updated")

    def update(self, instance: Board, validated_data: dict):
        """
        Метод обновления участников доски.
        :param instance:
        :param validated_data:
        :return:
        """
        request: Request = self.context['request']

        with transaction.atomic():
            BoardParticipant.objects.filter(board=instance).exclude(user=request.user).delete()
            participants = [
                BoardParticipant(user=participant['user'], role=participant['role'], board=instance)
                for participant in validated_data.get('participants', [])
            ]
            BoardParticipant.objects.bulk_create(participants, ignore_conflicts=True)

            if title := validated_data.get("title"):
                instance.title = title

            instance.save()

            return instance


class GoalCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор категории цели.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_board(self, board: Board):
        """
        Метод проверки существования доски и доступа к ней.
        :param board:
        :return:
        """
        if board.is_deleted:
            raise ValidationError('Board not exist!')

        if not BoardParticipant.objects.filter(
            board_id=board.id,
            user_id=self.context['request'].user.id,
            role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        ).exists():
            raise PermissionDenied

        return board

    class Meta:
        model = GoalCategory
        read_only_fields = ("id", "created", "updated", "user", "is_deleted")
        fields = "__all__"


class GoalCategoryWithUserSerializer(GoalCategorySerializer):
    user = UserSerializer(read_only=True)


class GoalSerializer(serializers.ModelSerializer):
    """
    Сериализатор цели.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Goal
        read_only_fields = ("id", "created", "updated", "user")
        fields = "__all__"

    def validate_category(self, category: GoalCategory):
        """
        Метод проверки существования категории и доступа к ней.
        :param category:
        :return:
        """
        if category.is_deleted:
            raise ValidationError('Category not exist!')
        if not BoardParticipant.objects.filter(
                board_id=category.board_id,
                user_id=self.context['request'].user.id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        ).exists():
            raise PermissionDenied

        return category


class GoalWithUserSerializer(GoalSerializer):
    user = UserSerializer(read_only=True)


class GoalCommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор комментария цели.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalComment
        read_only_fields = ("id", "created", "updated", "user")
        fields = "__all__"

    def validate_goal(self, goal: Goal):
        """
        Метод проверки существования цели и доступа к ней.
        :param goal:
        :return:
        """
        if goal.status == Goal.Status.archived:
            raise ValidationError('Goal not found!')
        if not BoardParticipant.objects.filter(
                board_id=goal.category.board_id,
                user_id=self.context['request'].user.id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        ).exists():
            raise PermissionDenied

        return goal


class GoalCommentWithUserSerializer(GoalCommentSerializer):
    user = UserSerializer(read_only=True)
    goals = serializers.PrimaryKeyRelatedField(read_only=True)
