# Импорт модулей и переменных
from config import access_token
from datetime import datetime
import vk_api
from vk_api.exceptions import ApiError


class Main:
    def __init__(self, access_token):
        self.vkapi = vk_api.VkApi(token=access_token)

    def get_user_info(self, user_id):
        try:
            info = self.vkapi.method('users.get', {'user_ids': user_id, 'fields': 'city,bdate,sex'})[0]
        except ApiError as err:
            info = {}
            print('Произошла ошибка при получении информации о пользователе!')
            print(f'Ошибка: {err}')

        output = {
            'Name': info['first_name'] + ' ' + info['last_name'] if 'first_name' in info and 'last_name' in info else None,
            'Sex': info.get('sex'),
            'City': info['city']['title'] if 'city' in info and 'title' in info['city'] else None,
            'Year': datetime.now().year - int(info['bdate'].split('.')[-1]) if 'bdate' in info else None
        }

        return output

    def search_list(self, userinfo, offset):
        try:
            pairs = self.vkapi.method('users.search', {
                'count': 10,
                'offset': offset,
                'hometown': userinfo['City'],
                'sex': 1 if userinfo['Sex'] == 2 else 2,
                'has_photo': 1,
                'age_from': userinfo['Year'] - 3,
                'age_to': userinfo['Year'] + 3
            })['items']
        except ApiError as err:
            pairs = []
            print('Произошла ошибка при поиске анкет!')
            print(f'Ошибка: {err}')

        output = [{
            'name': item['first_name'] + ' ' + item['last_name'],
            'profile_id': item['id']
        } for item in pairs if not item['is_closed']]

        return output

    def search_photos(self, profile_id):
        try:
            photos = self.vkapi.method('photos.get', {'owner_id': profile_id, 'album_id': 'profile', 'extended': 1})['items']
        except ApiError as err:
            photos = []
            print('Произошла ошибка при поиске фотографий!')
            print(f'Ошибка: {err}')

        output = [{
            'owner_id': photo['owner_id'],
            'id': photo['id'],
            'likes': photo['likes']['count'],
            'comments': photo['comments']['count']
        } for photo in photos]

        output.sort(key=lambda x: (x['likes'], x['comments']), reverse=True)

        return output[:3]


if __name__ == '__main__':
    user_id = 000000
    prm = Main(access_token)
    userinfo = prm.get_user_info(user_id)
    searchlists = prm.search_list(userinfo, 10)
    searched = searchlists.pop()['profile_id']
    photos = prm.search_photos(searched)
