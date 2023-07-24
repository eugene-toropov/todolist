from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, filters

from goals.filters import GoalDateFilter
from goals.models import Goal
from goals.permission import GoalPermission
from goals.serializers import GoalSerializer, GoalWithUserSerializer


class GoalCreateView(CreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]


class GoalListView(ListAPIView):
    serializer_class = GoalWithUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = GoalDateFilter
    ordering_fields = ['title', 'description']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Goal.objects.select_related('user').filter(
            user=self.request.user, category__is_deleted=False
        ).exclude(status=Goal.Status.archived)


class GoalDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [GoalPermission]
    serializer_class = GoalWithUserSerializer

    def get_queryset(self):
        return Goal.objects.select_related('user').filter(
            category__is_deleted=False).exclude(status=Goal.Status.archived)

    def perform_destroy(self, instance: Goal):
        instance.status = Goal.Status.archived
        instance.save()