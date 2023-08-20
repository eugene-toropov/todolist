import json

from django.core.management import BaseCommand
from django.db import IntegrityError

from bot.models import TgUser
from bot.tg.client import TgClient
from bot.tg.schemas import Message
from goals.models import Goal, GoalCategory, BoardParticipant
from goals.serializers import GoalSerializer, GoalCategorySerializer


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient()
        self.users_data = {}

    def handle(self, *args, **options):
        offset = 0
        while True:
            res = self.tg_client.get_updates(offset=offset)
            for item in res.result:
                offset = item.update_id + 1
                self.handle_message(item.message)

    def handle_message(self, message: Message):
        """
        Обработчик сообщений от телеграмм пользователя.

        :param message: Объект message.
        """
        tg_user, _ = TgUser.objects.get_or_create(chat_id=message.chat.id, defaults={'username': message.chat.username})
        if not tg_user.is_verified:
            tg_user.update_verification_code()
            self.tg_client.send_message(message.chat.id, f'Verification code: {tg_user.verification_code}')
        else:
            self.handle_auth_user(tg_user, message)

    def get_user_goals(self, user_id: int) -> str:
        """
        Обработчик команды /goals.

        :param user_id:
        :return: Список целей пользователя.
        """
        priority = dict(Goal.Priority.choices)
        status = dict(Goal.Status.choices)

        goals = (
            Goal.objects.select_related('user')
            .filter(category__board__participants__user_id=user_id, category__is_deleted=False)
            .exclude(status=Goal.Status.archived)
            .all()
        )

        if not goals.exists():
            return "You don't have any goals."

        serializer = GoalSerializer(goals, many=True)

        data = []
        for item in serializer.data:
            goal_data = {'title': item['title'],
                         'due_date': item['due_date'] if item['due_date'] else '',
                         'priority': priority[item['priority']],
                         'status': status[item['status']]}
            data.append(goal_data)

        message = []
        for index, item in enumerate(data, start=1):
            goal = (
                f'{index}) {item["title"]}, status: {item["status"]}, priority: {item["priority"]},'
                f' due_date : {item["due_date"]}'
            )
            message.append(goal)

        response = '\n'.join(message)
        return response

    def show_categories(self, user_id: int, chat_id: int, users_data) -> str:
        """
        Возвращаем список категорий, в которых пользователь либо владелец, либо редактор.

        :param user_id:
        :param chat_id:
        :param users_data:
        :return:
        """
        categories = (
            GoalCategory.objects.select_related('user')
            .filter(
                board__participants__user_id=user_id,
                board__participants__role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            )
            .exclude(is_deleted=True)
        )

        if not categories.exists():
            return "You don't have any categories to create a goal. Please create a category first."

        serializer = GoalCategorySerializer(categories, many=True)

        data = []
        for item in serializer.data:
            cat_data = {
                'cat_id': item['id'],
                'title': item['title']}
            data.append(cat_data)

        # Присваиваем численное значение к каждой категории для удобства дальнейшего выбора
        users_data[chat_id] = {index: item['cat_id'] for index, item in enumerate(data, start=1)}
        users_data[chat_id]['next_handler'] = self.choose_category

        message = [f'{index}) {item["title"]}' for index, item in enumerate(data, start=1)]

        response = '\n'.join(message)
        return 'Choose category for goal:\n' + response

    def choose_category(self, **kwargs) -> str:
        """
        Принимаем от пользователя category_id и помещаем его в словарь users_data.

        :param kwargs:
        :return:
        """
        chat_id: int = kwargs.get('chat_id')
        message: str = kwargs.get('message')
        users_data: dict[int, dict[str | int, ...]] = kwargs.get('users_data')
        if message.isdigit():
            value = int(message)
            category_id = users_data.get(chat_id, {}).get(value)
            if category_id is not None:
                users_data[chat_id]['next_handler'] = self.create_goal
                users_data[chat_id]['category_id'] = category_id
                return f'You chose category {value}. Please, send the title for the goal.'
            else:
                return f'Invalid category index. Please choose a valid category.'
        else:
            return f'You sent not valid category index.'

    def create_goal(self, **kwargs) -> str:
        """
        Принимаем от пользователя название цели и создаем ее на основе параметров.

        :param kwargs:
        :return:
        """
        user_id: int = kwargs.get('user_id')
        chat_id: int = kwargs.get('chat_id')
        message: str = kwargs.get('message')
        users_data: dict[int, dict[str | int, ...]] = kwargs.get('users_data')
        try:
            category_id = users_data.get(chat_id, {}).get('category_id')
            Goal.objects.create(title=message, user_id=user_id, category_id=category_id)
            users_data.pop(chat_id, None)
            return f'Goal "{message}" added!'
        except IntegrityError:
            return 'Something went wrong. Goal not created.'
        except Exception as e:
            return f'Error: {str(e)}'

    def handle_auth_user(self, tg_user: TgUser, message: Message) -> None:
        """
        Обработчик команд от пользователя. Принимает команду и вызывает соответствующую функцию.

        :param tg_user:
        :param message:
        :return:
        """
        if message.text.startswith('/'):
            match message.text:
                case '/goals':
                    text = self.get_user_goals(tg_user.user.id)
                case '/create':
                    text = self.show_categories(user_id=tg_user.user.id, chat_id=message.chat.id,
                                                users_data=self.users_data)
                case _:
                    text = 'Unknown command'
        elif message.chat.id in self.users_data:
            next_handler = self.users_data[message.chat.id].get('next_handler')
            text = next_handler(
                user_id=tg_user.user.id, chat_id=message.chat.id, message=message.text, users_data=self.users_data
            )
        else:
            text = 'List of commands:\n/goals - Show your goals\n' '/create - Create a goal'
        self.tg_client.send_message(chat_id=message.chat.id, text=text)
