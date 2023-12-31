from django.db import models
from django.utils.crypto import get_random_string

from core.models import User


class TgUser(models.Model):
    """
    Модель объекта телеграмм-пользователя.
    Поля: chat_id, username, user(поле связанное с моделью User), verification_code.
    """
    chat_id = models.PositiveBigIntegerField(primary_key=True, editable=False, unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    verification_code = models.CharField(max_length=20, unique=True, null=True, blank=True)

    @property
    def is_verified(self) -> bool:
        """
        Метод проверка верификации телеграмм пользователя.
        :return: Булевое значение.
        """
        return bool(self.user)

    @staticmethod
    def _generate_verification_code() -> str:
        """
        Метод генерации верификационного кода.
        :return:
        """
        return get_random_string(20)

    def update_verification_code(self) -> None:
        """
        Метод обновления верификационного кода.
        :return:
        """
        self.verification_code = self._generate_verification_code()
        self.save(update_fields=['verification_code'])

    def __str__(self):
        return f'{self.__class__.__name__} ({self.chat_id})'
