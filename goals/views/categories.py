from django.db import transaction
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, filters
from rest_framework.pagination import LimitOffsetPagination

from goals.models import GoalCategory, Goal
from goals.permission import GoalCategoryPermission
from goals.serializers import GoalCategorySerializer, GoalCategoryWithUserSerializer


class CategoryCreateView(CreateAPIView):
    model = GoalCategory
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategorySerializer


class CategoryListView(ListAPIView):
    model = GoalCategory
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategoryWithUserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    ordering_fields = ["title", "created"]
    ordering = ["title"]
    search_fields = ["title"]

    def get_queryset(self):
        return GoalCategory.objects.select_related('user').filter(
            user=self.request.user, is_deleted=False
        )


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    model = GoalCategory
    serializer_class = GoalCategoryWithUserSerializer
    permission_classes = [GoalCategoryPermission]

    def get_queryset(self):
        return GoalCategory.objects.select_related('user').filter(is_deleted=False)

    def perform_destroy(self, instance: GoalCategory):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save()
            instance.goal_set.update(status=Goal.Status.archived)
