
import sys
import random
import ctypes
from collections import defaultdict
from itertools import chain

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from wrapperQWidget5.WrapperWidget import wrapper_widget

import recourse
from wrapperQWidget5.modules.scene.RectangleScene_new import RectangleScene
from wrapperQWidget5.modules.scene.Scene import Scene


__version__ = '1.0.0'

if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'volkov.boardgames.aqualin.{__version__}')


SIZE = 70
COUNT = {
    1: 0,
    2: 1,
    3: 3,
    4: 6,
    5: 10,
    6: 15,
}


class HexTile1(RectangleScene):
    height = 697
    width = 807
    image = ":/g24.png"


class HexTile(RectangleScene):
    height = width = (SIZE * 6) + 8
    image = ":/filed.jpg"


class TextTile(QGraphicsTextItem):

    def __init__(self, scene, text, size, point_size=30):
        super().__init__(text)

        self.setPos(QPointF(*size))

        font = QFont()
        font.setPointSize(point_size)
        self.setFont(font)

        scene.addItem(self)


class MoveTile(RectangleScene):
    height = width = SIZE

    def activated(self):
        self.scene.mobilized_unit[
            self.scene.mobilized_unit.index((self.scene.active.start_point_x, self.scene.active.start_point_y))
        ] = (self.start_point_x, self.start_point_y)

        self.scene.active.move_item(self)
        self.scene.check_move = True
        self.scene.get_score()


class FieldTile(RectangleScene):
    height = width = SIZE

    def activated(self):
        if self.scene.active:
            if self.scene.active.status == 'buy':
                new_point = (self.scene.active.start_point_x, self.scene.active.start_point_y)

                self.scene.active.status = 'field'
                self.scene.units.append(self.scene.active)
                self.scene.active.move_item(self)
                self.scene.mobilized_unit.append((self.start_point_x, self.start_point_y))

                UnitTile(scene=self.scene, status='buy', **self.scene.get_new_unit(), point=new_point)
                self.scene.player_change()
                self.scene.check_move = False
                self.scene.get_score()


class UnitTile(RectangleScene):
    height = width = SIZE

    def __init__(self, color, dweller, status='field', *args, **kwargs):
        if color:
            self.color = color
            self.dweller = dweller
            self.image = f":/{self.color}_{self.dweller}.png"
            self.status = status
            super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"UnitTile {self.color}:{self.dweller}"

    def set_image(self, path, bias=(0, 0)):
        super().set_image(path, bias=(5, 5))

    def activated(self):
        if self.scene.active:
            self.scene.active.deactivated()

        if self.status == 'field' and self.scene.check_move:
            pass
        else:
            self.scene.active = self
            self.setPen(QPen(QColor("Red"), 6))

            if self.status == 'field':
                self.check_move_field()  # Получение мест куда может двигатся юнит.

    def deactivated(self):
        self.scene.active = None
        self.setPen(QPen(QColor('Black'), 1))

        for value in self.scene.move_tile.values():
            for item in value:
                item.remove_item()

        self.scene.move_tile = {
            "up": [],
            "down": [],
            "right": [],
            "left": []
        }

    def check_move_field(self):
        """ Получение месту куда может двигатся юнит """

        for i in range(1, 6):
            if (self.start_point_x, self.start_point_y - (SIZE * i)) not in self.scene.mobilized_unit:
                if self.start_point_y - (SIZE * i) >= -(SIZE * 3):
                    self.scene.move_tile['up'].append(
                        MoveTile(self.scene, point=(self.start_point_x, self.start_point_y - (SIZE * i)))
                    )
            else:
                break

        for i in range(1, 6):
            if (self.start_point_x, self.start_point_y + (SIZE * i)) not in self.scene.mobilized_unit:
                if self.start_point_y + (SIZE * i) <= (SIZE * 2):
                    self.scene.move_tile['down'].append(
                        MoveTile(self.scene, point=(self.start_point_x, self.start_point_y + (SIZE * i)))
                    )
            else:
                break

        for i in range(1, 6):
            if (self.start_point_x + (SIZE * i), self.start_point_y) not in self.scene.mobilized_unit:
                if self.start_point_x + (SIZE * i) <= (SIZE * 2):
                    self.scene.move_tile['right'].append(
                        MoveTile(self.scene, point=(self.start_point_x + (SIZE * i), self.start_point_y))
                    )
            else:
                break

        for i in range(1, 6):
            if (self.start_point_x - (SIZE * i), self.start_point_y) not in self.scene.mobilized_unit:
                if self.start_point_x - (SIZE * i) >= -(SIZE * 3):
                    self.scene.move_tile['left'].append(
                        MoveTile(self.scene, point=(self.start_point_x - (SIZE * i), self.start_point_y))
                    )
            else:
                break


class AqualinScene(Scene):
    draw_sketch = False

    def __init__(self, widget, *args, **kwargs):
        self.widget = widget
        self.type_units: list = []
        for color in ['red', 'blue', 'pink', 'orange', 'green', 'purple']:
            for dweller in ['skate', 'fish', 'star', 'turtle', 'jellyfish', 'crab']:
                self.type_units.append({"color": color, "dweller": dweller})

        self.type_users = {
            "color": "Player_color",
            "dweller": "Player_dweller"
        }

        self.users_type = {
            "Player_color": "color",
            "Player_dweller": "dweller"
        }

        self.player = random.choice(list(self.users_type.keys()))  # Первый игрок
        self.enemy = list(filter(lambda x: x != self.player, list(self.users_type.keys())))[0]

        self.two_player = self.enemy  # Игрок который начинал ходить вторым.
        self.mobilized_unit = []
        self.check_move = False  # Проверка на то перемещался ли юнит по полю в этом ходу.
        self.units = []
        self.move_tile = {
            "up": [],
            "down": [],
            "right": [],
            "left": []
        }

        super().__init__(widget=self.widget, size=(810, 700), *args, **kwargs)

    def draw(self):
        """ Отрисовка сцены """

        HexTile1(self, point=(80, 0))
        HexTile(self, point=(-35, -35))

        TextTile(self, self.type_users['color'], (200, -240))
        TextTile(self, "Цвет:", (200, -195))
        self.score_color = TextTile(self, "0", (310, -195))

        TextTile(self, self.type_users['dweller'], (200, -100))
        TextTile(self, "Вид:", (200, -55))
        self.score_dweller = TextTile(self, "0", (310, -55))

        TextTile(self, "Ход игрока:", (200, 70))
        self.player_tyrn = TextTile(self, self.player, (210, 120))

        TextTile(self, "by Aleksey Volkov", (-320, 327), point_size=8)
        TextTile(self, f"v:{__version__}", (430, 327), point_size=8)

        for x in range(-3, 3):
            for y in range(-3, 3):
                FieldTile(self, bias=(x, y))

        for x in range(-3, 3):
            UnitTile(scene=self, status='buy', **self.get_new_unit(), bias=(x, 3.5))

    def player_change(self):
        """ Действие по смене активного игрока. """
        self.player, self.enemy = self.enemy, self.player
        self.player_tyrn.setPlainText(self.player)

    def get_new_unit(self) -> dict:
        """ Получение нового рандомного юнита """
        if self.type_units:
            random_unit = random.choice(self.type_units)
            del self.type_units[self.type_units.index(random_unit)]
            return random_unit
        else:
            if len(self.mobilized_unit) == 36:
                self.game_over()
            return {"color": None, "dweller": None}

    def get_score(self):
        score_color_dict = defaultdict(list)
        score_dweller_dict = defaultdict(list)
        for unit in self.units:
            score_color_dict[unit.color].append((unit.start_point_x, unit.start_point_y))
            score_dweller_dict[unit.dweller].append((unit.start_point_x, unit.start_point_y))

        count_score_color = self.count_score(score_color_dict)
        count_score_dweller = self.count_score(score_dweller_dict)

        self.score_color.setPlainText(str(count_score_color['score']))
        self.score_dweller.setPlainText(str(count_score_dweller['score']))

        return {"color": count_score_color, "dweller": count_score_dweller}

    def count_score(self, score_list) -> dict:
        dict_score = {"score": 0}
        for unit, point in score_list.items():
            unit_score = sum(list(map(lambda x: COUNT[len(x)], self.group_units(point))))
            dict_score[unit] = unit_score
            dict_score['score'] += unit_score

        return dict_score

    @staticmethod
    def group_units(list_units) -> list:
        """ Функция группировки юнитов для подсчета очков """
        new_array = []

        def test(search_point, current_point, check1):
            for arrays in new_array:
                if search_point in arrays:
                    arrays.append(current_point)
                    check1 += 1
            else:
                if not check1:
                    new_array.append([current_point])
                else:
                    if check1 > 1:
                        new = set()
                        for b in new_array:
                            if current_point in b:
                                new_array[new_array.index(b)] = []
                                new.update(set(b))
                        new_array.append(list(new))

            return check1

        for unit in list_units:
            check = 0

            if (unit[0], unit[1] + SIZE) in chain(*new_array):
                check = test((unit[0], unit[1] + SIZE), unit, check)
            if (unit[0], unit[1] - SIZE) in chain(*new_array):
                check = test((unit[0], unit[1] - SIZE), unit, check)
            if (unit[0] + SIZE, unit[1]) in chain(*new_array):
                check = test((unit[0] + SIZE, unit[1]), unit, check)
            if (unit[0] - SIZE, unit[1]) in chain(*new_array):
                check = test((unit[0] - SIZE, unit[1]), unit, check)
            if not check:
                new_array.append([unit])

        return list(filter(lambda x: x, new_array))

    def game_over(self):
        result = self.get_score()

        result['color']['name'] = self.type_users['color']
        result['dweller']['name'] = self.type_users['dweller']

        if result['color']['score'] == result['dweller']['score']:
            result['win'] = self.two_player
        elif result['color']['score'] > result['dweller']['score']:
            result['win'] = self.type_users["color"]
        else:
            result['win'] = self.type_users["dweller"]

        self.widget.set_hide()
        win_player_dialog = InfoWinPlayerDialog(result)
        win_player_dialog.exec_()

        if win_player_dialog.repeat:
            pass
        else:
            self.widget.show_app()


class InfoWinPlayerDialog(QDialog):
    @wrapper_widget
    def __init__(self, data):
        super().__init__()

        self.repeat = False

        self.setGeometry(580, 350, 781, 469)
        self.setWindowFlag(Qt.FramelessWindowHint)  # Убрана строка заголовка

        self.label_2 = QLabel(self)
        self.label_2.setStyleSheet("background-image : url(:/field_close.png)")
        self.label_2.resize(781, 469)

        font = QFont()
        font.setPointSize(34)
        font.setFamily('Garamond')

        label = QLabel(data['win'], self)
        label.setGeometry(360, 84, 900, 50)
        label.setFont(font)

        label_dweller = QLabel(data['color']['name'], self)
        label_dweller.setGeometry(82, 135, 900, 50)
        label_dweller.setFont(font)

        label_color = QLabel(data['dweller']['name'], self)
        label_color.setGeometry(376, 135, 900, 50)
        label_color.setFont(font)

        font.setPointSize(26)

        label_blue = QLabel(f"- {data['color'].get('blue', 0)}", self)
        label_blue.setGeometry(128, 180, 900, 50)
        label_blue.setFont(font)

        label_green = QLabel(f"- {data['color'].get('green', 0)}", self)
        label_green.setGeometry(128, 218, 900, 50)
        label_green.setFont(font)

        label_pink = QLabel(f"- {data['color'].get('pink', 0)}", self)
        label_pink.setGeometry(128, 253, 900, 50)
        label_pink.setFont(font)

        label_purple = QLabel(f"- {data['color'].get('purple', 0)}", self)
        label_purple.setGeometry(128, 290, 900, 50)
        label_purple.setFont(font)

        label_red = QLabel(f"- {data['color'].get('red', 0)}", self)
        label_red.setGeometry(128, 326, 900, 50)
        label_red.setFont(font)

        label_orange = QLabel(f"- {data['color'].get('orange', 0)}", self)
        label_orange.setGeometry(128, 363, 900, 50)
        label_orange.setFont(font)

        label_color_total = QLabel(f"- {data['color']['score']}", self)
        label_color_total.setGeometry(128, 400, 900, 50)
        label_color_total.setFont(font)

        label_crab = QLabel(f"- {data['dweller'].get('crab', 0)}", self)
        label_crab.setGeometry(425, 180, 900, 50)
        label_crab.setFont(font)

        label_fish = QLabel(f"- {data['dweller'].get('fish', 0)}", self)
        label_fish.setGeometry(425, 218, 900, 50)
        label_fish.setFont(font)

        label_jellyfish = QLabel(f"- {data['dweller'].get('jellyfish', 0)}", self)
        label_jellyfish.setGeometry(425, 253, 900, 50)
        label_jellyfish.setFont(font)

        label_skate = QLabel(f"- {data['dweller'].get('skate', 0)}", self)
        label_skate.setGeometry(425, 290, 900, 50)
        label_skate.setFont(font)

        label_star = QLabel(f"- {data['dweller'].get('star', 0)}", self)
        label_star.setGeometry(425, 326, 900, 50)
        label_star.setFont(font)

        label_turtle = QLabel(f"- {data['dweller'].get('turtle', 0)}", self)
        label_turtle.setGeometry(425, 363, 900, 50)
        label_turtle.setFont(font)

        label_color_total = QLabel(f"- {data['dweller']['score']}", self)
        label_color_total.setGeometry(425, 400, 900, 50)
        label_color_total.setFont(font)

        btn_close = QPushButton("", self)
        btn_close.setStyleSheet("background-image : url(:/btn_close.png)")
        btn_close.setGeometry(639, 12, 128, 30)
        btn_close.setFlat(True)
        btn_close.clicked.connect(self.action_close)

        # btn_repeat = QPushButton("", self)
        # btn_repeat.setStyleSheet("background-image : url(:/btn_repeat.png)")
        # btn_repeat.setGeometry(560, 410, 218, 48)
        # btn_repeat.setFlat(True)
        # btn_repeat.clicked.connect(self.action_repeat)

    def action_close(self):
        self.close()

    def action_repeat(self):
        self.repeat = True
        self.close()


class WrapperGraphicsView2(QWidget):
    def __init__(self, app_widget):
        super().__init__()
        self.app_widget = app_widget
        self.widget = AqualinScene(self)

    def set_hide(self):
        self.app_widget.set_hide()

    def show_app(self):
        self.app_widget.show_app()


class AppStart(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"Аквалин")
        self.setWindowIcon(QIcon(":/pink_turtle.png"))

        self.setGeometry(560, 200, 806, 700)
        self.setFixedSize(806, 700)
        self.setContentsMargins(0, 0, 0, 0)
        win = "Вид"

        self.widget = WrapperGraphicsView2(self)
        self.setCentralWidget(self.widget)
        self.show()

    def set_hide(self):
        self.setVisible(False)

    def show_app(self):
        self.setVisible(True)


if __name__ == "__main__":
    app = QApplication([])
    window = AppStart()
    app.exec_()

