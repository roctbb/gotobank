from bank_server import app
from bank_bot import bot
from models import *
from config import IS_POSVYAT

team1 = """Мазитов Тимур
Плотникова Таисия
Ярославский Алексей
Журавлева-Емельяненко Агата
Москалевич Александр
Нгуен Виолетта
Васильев Никита
Ушенин Евгений
Буглаков Григорий
Баркевич Полина
Инденбом Денис"""

team2 = """Лабазников Иван
Яцишин Лев
Перламутров Егор
Крылов Матвей
Беляков Пётр
Бобров Дмитрий
Вилисов Георгий
Вязовик Тимофей
Григорьев Артём
Догадин Максим
Калмыков Максим"""

team3 = """Копеин Денис
Третьяков Иван
Лучинкин Константин
Бабак Дмитрий
Персидский Максим
Труфанов Александр
Макиевский Кирилл
Ткалин Владислав
Самбюи Алекснадр
Жукова Алиса"""

team4 = """Макаров Глеб
Яснов Михаил
Фатхутдинов Никита
Фрейман Вячеслав
Вергун Антон
Ларичев Прохор
Казаченко Александр
Харитонов Тимофей
Москвин Павел
Турубанов Никита
Бородин Ростислав"""

teams = [
    {
        "members": team1.split('\n'),
        "location": "Баня"
    },
    {
        "members": team2.split('\n'),
        "location": "Беседка"
    },
    {
        "members": team3.split('\n'),
        "location": "Веранда"
    },
    {
        "members": team4.split('\n'),
        "location": "11 учебка"
    }
]

text = """Уважаемый клиент!

Уведомляем Вас о том, что в результате внеплановой проверки, службой финансового контроля инновационного кластера GoLoWinka был обнаружен факт нецелевого использования бюджетных средств.

В частности, Вы подозреваетесь в использовании грантового финансирования в азартных играх. В соответствие со статьей 285.1 УК РФ, все выданные ранее средства возвращаются грантодателю, а ваше имущество (ноутбуки) конфискуется с целью продажи для покрытия неустойки.

Если Вы хотите выкупить ваше имущество, Вам необходимо в течение ближайших 5 минут сообщить об этом в ломбарде, располагающемся по адресу «{}». Не забудьте мобильный телефон для подтверждения транзакций.

Также с Вами должны явиться: {}, {}."""

with app.app_context():
    for team in teams:
        members = team['members']
        for i, member in enumerate(members):
            user = Account.query.filter_by(surname=member.split()[0]).first()
            n1 = members[i + 1 % len(members)]
            n2 = members[i + 2 % len(members)]

            if not user:
                print("Cant find {}".format(member))
            else:
                if not IS_POSVYAT and user.name != "Ростислав":
                    print("I will send to {}".format(member))
                else:
                    print("sent to {}".format(member))
                    bot.send_message(user.telegram_id, text.format(team['location'], n1, n2))
