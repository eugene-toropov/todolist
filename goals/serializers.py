from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from core.serializers import UserSerializer
from goals.models import GoalCategory, GoalComment, Goal


class GoalCategorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalCategory
        read_only_fields = ("id", "created", "updated", "user", "is_deleted")
        fields = "__all__"


class GoalCategoryWithUserSerializer(GoalCategorySerializer):
    user = UserSerializer(read_only=True)


class GoalSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Goal
        read_only_fields = ("id", "created", "updated", "user")
        fields = "__all__"

    def validate_category(self, value: GoalCategory):
        if value.is_deleted:
            raise NotFound('Category not exist!')
        if self.context['request'].user_id != value.user_id:
            raise PermissionDenied
        return value


class GoalWithUserSerializer(GoalSerializer):
    user = UserSerializer(read_only=True)


class GoalCommentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalComment
        read_only_fields = ("id", "created", "updated", "user")
        fields = "__all__"

    def validate_goal(self, value: Goal):
        if value.status == Goal.Status.archived:
            raise NotFound('Goal not exist!')
        if self.context['request'].user_id != value.user_id:
            raise PermissionDenied
        return value


class GoalCommentWithUserSerializer(GoalCommentSerializer):
    user = UserSerializer(read_only=True)
    goals = serializers.PrimaryKeyRelatedField(read_only=True)
