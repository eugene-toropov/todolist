from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response

from bot.models import TgUser
from bot.serializers import TgUserSerializer
from bot.tg.client import TgClient


class VerificationView(UpdateAPIView):
    serializer_class = TgUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TgUser.objects.all()

    def patch(self, request, *args, **kwargs):
        try:
            tg_user = self.get_queryset().get(verification_code=request.data.get('verification_code'))
        except TgUser.DoesNotExist:
            raise AuthenticationFailed

        tg_user.user = request.user
        tg_user.save(update_fileds=['user'])
        TgClient().send_message(chat_id=tg_user.chat_id, text='Bot has been verified')
        return Response(TgUserSerializer(tg_user).data)
