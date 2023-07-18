import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
from datetime import datetime
from config import community_token, access_token
from main import Main
from bd import check_user, add_user, engine


class BotInterface:
    def __init__(self, community_token, access_token):
        self.vkapi = vk_api.VkApi(token=community_token)
        self.longpoll = VkLongPoll(self.vkapi)
        self.main = Main(access_token)
        self.searchlists = []
        self.keys = []
        self.prm = {}
        self.offset = 0

    def send_msg(self, user_id, message, attachment=None):
        self.vkapi.method(
            'messages.send', {
                'user_id': user_id,
                'message': message,
                'attachment': attachment,
                'random_id': get_random_id()
            }
        )

    def _bdatereform(self, bdate):
        user_year = bdate.split('.')[2]
        now_year = datetime.now().year
        years = now_year - int(user_year)
        return years

    def send_photos(self, searched):
        photos = self.main.search_photos(searched['profile_id'])
        photo_str = ''
        for photo in photos:
            photo_str += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photo_str

    def kill_gaps(self, nn):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if nn == 0:
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break
                    if contains_digit:
                        self.send_msg(event.user_id, 'Имя и фамилия не должны содержать цифры')
                    else:
                        return event.text

                if nn == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.send_msg(event.user_id, 'Неверно введён пол. Введите 1 или 2 (1-М, 2-Ж):')

                if nn == 2:
                    contains_digit = False
                    for i in event.text:
                        if i.isdigit():
                            contains_digit = True
                            break
                    if contains_digit:
                        self.send_msg(event.user_id, 'Название города не должно содержать цифры')
                    else:
                        return event.text

                if nn == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.send_msg(event.user_id, 'Дата рождения должна быть в формате ДД.ММ.ГГГГ')
                    else:
                        return self._bdatereform(event.text)

    def gap_looking(self, event):
        if self.prm['Name'] is None:
            self.send_msg(event.user_id, 'Ваше имя и фамилия?')
            return self.kill_gaps(0)

        if self.prm['Sex'] is None:
            self.send_msg(event.user_id, 'Укажите пол (1-М, 2-Ж)')
            return self.kill_gaps(1)

        elif self.prm['City'] is None:
            self.send_msg(event.user_id, 'Ваш город?')
            return self.kill_gaps(2)

        elif self.prm['Year'] is None:
            self.send_msg(event.user_id, 'Укажите дату рождения по формату - 11.06.1997..пример')
            return self.kill_gaps(3)

    def find_profile(self, search_lists, event):
        while True:
            if search_lists:
                searched = search_lists.pop()
                if not check_user(engine, event.user_id, searched['profile_id']):
                    add_user(engine, event.user_id, searched['profile_id'])
                    yield searched
            else:
                search_lists = self.main.search_list(self.prm, self.offset)

    def cmd_events(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.prm = self.main.get_user_info(event.user_id)
                    self.send_msg(event.user_id, f'Здраствуй, {self.prm["Name"]}')

                    self.keys = self.prm.keys()
                    for i in self.keys:
                        if self.prm[i] is None:
                            self.prm[i] = self.gap_looking(event)

                    self.send_msg(event.user_id, 'Регистрация пройдена!')

                elif event.text.lower() == 'поиск':
                    self.send_msg(event.user_id, 'Ищем...')

                    msg = next(iter(self.find_profile(self.searchlists, event)))
                    if msg:
                        photo_string = self.send_photos(msg)
                        self.offset += 10

                        self.send_msg(
                            event.user_id,
                            f'имя: {msg["name"]} ссылка: vk.com/id{msg["profile_id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'бб':
                    self.send_msg(event.user_id, 'До новых встреч!')
                else:
                    self.send_msg(event.user_id, 'Неизвестный запрос')


if __name__ == '__main__':
    bot_interface = BotInterface(community_token, access_token)
    bot_interface.cmd_events()
