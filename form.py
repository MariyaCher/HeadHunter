import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, \
    QTabWidget, QWidget, QSlider, QFrame, QComboBox, QLabel, QMessageBox, QCheckBox
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd

import model
import work_with_data
from work_with_data import AREA, LANGUAGES, AREA_COORD, MIN_SALARY, SIZE_COMPANY, EXPERIENCE, EMPLOYMENT

MAX_LANG_MODEL = 5

WIND_HEIGHT = 1000
WIND_WIDTH = 600

BUTTON_MENU_HEIGHT = WIND_HEIGHT / 4
BUTTON_MENU_WIDTH = WIND_WIDTH / 10

FRAME_WIDTH = WIND_HEIGHT / 4
FRAME_HEIGHT = (WIND_WIDTH - BUTTON_MENU_WIDTH) / 3


class Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setFixedSize(QSize(WIND_HEIGHT, WIND_WIDTH))
        self.setWindowTitle('HeadHunter')
        self.setWindowIcon(QIcon('sources/hh.png'))
        self.color = '#cfebfd'
        self.second_color = '#87cefa'
        self.third_color = '#0000cc'
        self.start_sal = MIN_SALARY

        self.data = work_with_data.get_prepocess_data(False)
        self.categorical_columns = ['Area', 'Employment', 'Experience']
        self.binary_columns = list(LANGUAGES) + list(SIZE_COMPANY.keys())
        self.model = model.get_forest_model(self.data, self.categorical_columns, self.binary_columns)

        # 1 Widget
        self.tabs_lang = QTabWidget(self)
        self.tabs_lang1 = QWidget()
        self.tabs_lang2 = QWidget()
        self.tabs_lang.resize(WIND_HEIGHT, WIND_WIDTH - BUTTON_MENU_WIDTH - 5)
        self.tabs_lang.move(0, BUTTON_MENU_WIDTH + 5)
        self.tabs_lang.addTab(self.tabs_lang1, 'Статистика по средней зарплате')
        self.tabs_lang.addTab(self.tabs_lang2, 'Статистика по количеству вакансий')

        # 2 Widget
        self.tabs_city = QTabWidget(self)
        self.tabs_city1 = QWidget()
        self.tabs_city2 = QWidget()
        self.tabs_city.resize(WIND_HEIGHT, WIND_WIDTH - BUTTON_MENU_WIDTH - 5)
        self.tabs_city.move(0, BUTTON_MENU_WIDTH + 5)
        self.tabs_city.addTab(self.tabs_city1, 'Статистика по средней зарплате')
        self.tabs_city.addTab(self.tabs_city2, 'Статистика по количеству вакансий')

        # 3 Widget
        self.tabs_map = QTabWidget(self)
        self.tab_map1 = QWidget()
        self.tabs_map.resize(WIND_HEIGHT, WIND_WIDTH - BUTTON_MENU_WIDTH - 25)
        self.tabs_map.move(0, BUTTON_MENU_WIDTH + 25)
        self.tabs_map.addTab(self.tab_map1, '')

        # 4 Widget
        self.tabs_model = QTabWidget(self)
        self.tab_model1 = QWidget()
        self.tabs_model.resize(WIND_HEIGHT, WIND_WIDTH - BUTTON_MENU_WIDTH - 25)
        self.tabs_model.move(0, BUTTON_MENU_WIDTH + 25)
        self.tabs_model.addTab(self.tab_model1, '')

        # 1,2 plot
        self.plot_lang1 = MatPlot(WIND_HEIGHT * 0.25, 0, self.tabs_lang1, self.second_color)
        self.plot_lang2 = MatPlot(WIND_HEIGHT * 0.25, 0, self.tabs_lang2, self.second_color)

        # 3,4 plot
        self.plot_city1 = MatPlot(WIND_HEIGHT * 0.25, 0, self.tabs_city1, self.second_color)
        self.plot_city2 = MatPlot(WIND_HEIGHT * 0.25, 0, self.tabs_city2, self.second_color)

        # map
        self.plot_map1 = MatPlot(0, 0, self.tab_map1, self.color, self.third_color)

        # button
        self.button_lang = QPushButton('Статистика\nпо языкам', self)
        self.button_lang.clicked.connect(lambda: self.show_tab(self.tabs_lang))
        self.button_lang.resize(BUTTON_MENU_HEIGHT, BUTTON_MENU_WIDTH)
        self.button_lang.move(BUTTON_MENU_HEIGHT * 0, 0)

        self.button_city = QPushButton('Статистика\nпо городам', self)
        self.button_city.clicked.connect(lambda: self.show_tab(self.tabs_city))
        self.button_city.resize(BUTTON_MENU_HEIGHT, BUTTON_MENU_WIDTH)
        self.button_city.move(BUTTON_MENU_HEIGHT * 1, 0)

        self.button_map = QPushButton('Востребованность\nв городах', self)
        self.button_map.clicked.connect(lambda: self.show_tab(self.tabs_map))
        self.button_map.resize(BUTTON_MENU_HEIGHT, BUTTON_MENU_WIDTH)
        self.button_map.move(BUTTON_MENU_HEIGHT * 2, 0)

        self.button_model = QPushButton('Заработная\nплата', self)
        self.button_model.clicked.connect(lambda: self.show_tab(self.tabs_model))
        self.button_model.resize(BUTTON_MENU_HEIGHT, BUTTON_MENU_WIDTH)
        self.button_model.move(BUTTON_MENU_HEIGHT * 3, 0)

        self.button_update = QPushButton('Обновить', self)
        self.button_update.clicked.connect(self.update_data)
        self.button_update.resize(BUTTON_MENU_HEIGHT / 3, BUTTON_MENU_WIDTH / 3)
        self.button_update.move(BUTTON_MENU_HEIGHT * 3 + 2 * BUTTON_MENU_HEIGHT / 3, BUTTON_MENU_WIDTH + 2)

        # 1-2 filter
        self.all_filters = {}
        self.filters_city1 = QFrame(self.tabs_city1)
        self.filters_city1.resize(FRAME_WIDTH, FRAME_HEIGHT-50)
        self.filters_city1.move(10, 10)
        self.all_filters['City1'] = (self.create_filters(self.filters_city1, 'City1', lang=True, sal=False))

        self.filters_city2 = QFrame(self.tabs_city2)
        self.filters_city2.resize(FRAME_WIDTH, FRAME_HEIGHT)
        self.filters_city2.move(10, 10)
        self.all_filters['City2'] = (self.create_filters(self.filters_city2, 'City2', lang=True))

        # 3-4 filter
        self.filters_lang1 = QFrame(self.tabs_lang1)
        self.filters_lang1.resize(FRAME_WIDTH, FRAME_HEIGHT-50)
        self.filters_lang1.move(10, 10)
        self.all_filters['Lang1'] = (self.create_filters(self.filters_lang1, 'Lang1', area=True, sal=False))

        self.filters_lang2 = QFrame(self.tabs_lang2)
        self.filters_lang2.resize(FRAME_WIDTH, FRAME_HEIGHT)
        self.filters_lang2.move(10, 10)
        self.all_filters['Lang2'] = (self.create_filters(self.filters_lang2, 'Lang2', area=True))

        # model
        self.filter_model = {}
        self.create_filters_model(self.tab_model1)
        self.button_forecast = QPushButton('Расчет', self.tab_model1)
        self.button_forecast.clicked.connect(self.create_forecast)
        self.button_forecast.resize(BUTTON_MENU_HEIGHT, BUTTON_MENU_WIDTH)
        self.button_forecast.move(WIND_HEIGHT / 2 - BUTTON_MENU_HEIGHT / 2, 300)
        self.button_forecast.setEnabled(False)

        self.label_forecast = QLabel(self.tab_model1)
        self.label_forecast.setAlignment(Qt.AlignCenter)
        self.label_forecast.resize(WIND_HEIGHT, BUTTON_MENU_WIDTH)
        self.label_forecast.move(0, 400)

        self.plot_all()
        self.show_tab(self.tabs_lang)
        self.set_style()

    def show_tab(self, item_view):
        self.tabs_lang.hide()
        self.tabs_map.hide()
        self.tabs_city.hide()
        self.tabs_model.hide()

        item_view.show()

    def create_filters(self, parent, code, lang=False, area=False, sal=True):
        if sal:
            label_sal = QLabel(parent)
            label_sal.setText('Зарплата от')
            label_sal.resize(100, 15)
            label_sal.move(5, 125)

            label_sal_val = QLabel(parent)
            label_sal_val.move(FRAME_WIDTH - 50, 125)
            label_sal_val.resize(45, 15)
            label_sal_val.setAlignment(Qt.AlignRight)
            label_sal_val.setText(str(self.start_sal))

            sld_sal = QSlider(Qt.Horizontal, parent)
            sld_sal.setMinimum(int(self.start_sal / 5000))
            sld_sal.setMaximum(40)
            sld_sal.setPageStep(1)
            sld_sal.move(5, 145)
            sld_sal.resize(FRAME_WIDTH - 10, 20)
            sld_sal.valueChanged[int].connect(lambda val, tab=code: self.sld_action(val, tab))
        else:
            label_sal_val = None
            sld_sal = None

        if lang:
            combo_lang = QComboBox(parent)
            combo_lang.setMaxVisibleItems(20)
            combo_lang.addItem("Все языки")
            combo_lang.resize(FRAME_WIDTH - 10, 20)
            combo_lang.move(5, 10)
            combo_lang.addItems(LANGUAGES)
            combo_lang.activated.connect(lambda val, tab=code: self.refresh_plot(tab))
        else:
            combo_lang = None

        if area:
            combo_area = QComboBox(parent)
            combo_area.setMaxVisibleItems(20)
            combo_area.addItem("Все города")
            combo_area.resize(FRAME_WIDTH - 10, 20)
            combo_area.move(5, 10)
            combo_area.addItems([work_with_data.decode_param(val) for val in AREA])
            combo_area.activated.connect(lambda val, tab=code: self.refresh_plot(tab))
        else:
            combo_area = None

        combo_sizecomp = QComboBox(parent)
        combo_sizecomp.setMaxVisibleItems(5)
        combo_sizecomp.addItem("Все компании")
        combo_sizecomp.resize(FRAME_WIDTH - 10, 20)
        combo_sizecomp.move(5, 40)
        combo_sizecomp.addItems([work_with_data.decode_param(size_comp) for size_comp in SIZE_COMPANY])
        combo_sizecomp.activated.connect(lambda val, tab=code: self.refresh_plot(tab))

        combo_exp = QComboBox(parent)
        combo_exp.setMaxVisibleItems(10)
        combo_exp.addItem("Любой опыт")
        combo_exp.resize(FRAME_WIDTH - 10, 20)
        combo_exp.move(5, 70)
        combo_exp.addItems([work_with_data.decode_param(experience) for experience in EXPERIENCE])
        combo_exp.activated.connect(lambda val, tab=code: self.refresh_plot(tab))

        combo_empl = QComboBox(parent)
        combo_empl.setMaxVisibleItems(10)
        combo_empl.addItem("Любой график")
        combo_empl.resize(FRAME_WIDTH - 10, 20)
        combo_empl.move(5, 100)
        combo_empl.addItems([work_with_data.decode_param(employment) for employment in EMPLOYMENT])
        combo_empl.activated.connect(lambda val, tab=code: self.refresh_plot(tab))

        items = {
            'Lang': combo_lang,
            'Area': combo_area,
            'MinSal': sld_sal,
            'SizeComp': combo_sizecomp,
            'Employment': combo_empl,
            'Experience': combo_exp,
            'lbl_min': label_sal_val
        }
        return items

    def create_filters_model(self, parent):
        checks = {}
        for i, lang in enumerate(LANGUAGES):
            check = QCheckBox(parent)
            check.setText(lang)
            check.stateChanged.connect(self.check_action)
            check.move(250 * (i % 4) + 80, 25 * (i // 4) + 25)
            checks[lang] = check

        combo_area = QComboBox(parent)
        combo_area.setMaxVisibleItems(20)
        combo_area.resize(WIND_HEIGHT / 2 - 80 - 20, 20)
        combo_area.move(80, 200)
        combo_area.addItems([work_with_data.decode_param(val) for val in AREA])

        combo_empl = QComboBox(parent)
        combo_empl.setMaxVisibleItems(10)
        combo_empl.resize(WIND_HEIGHT / 2 - 80 - 20, 20)
        combo_empl.move(WIND_HEIGHT / 2, 200)
        combo_empl.addItems([work_with_data.decode_param(employment) for employment in EMPLOYMENT])

        combo_exp = QComboBox(parent)
        combo_exp.setMaxVisibleItems(10)
        combo_exp.resize(WIND_HEIGHT / 2 - 80 - 20, 20)
        combo_exp.move(80, 240)
        combo_exp.addItems([work_with_data.decode_param(experience) for experience in EXPERIENCE])

        combo_sizecomp = QComboBox(parent)
        combo_sizecomp.setMaxVisibleItems(5)
        combo_sizecomp.resize(WIND_HEIGHT / 2 - 80 - 20, 20)
        combo_sizecomp.move(WIND_HEIGHT / 2, 240)
        combo_sizecomp.addItems([work_with_data.decode_param(size_comp) for size_comp in SIZE_COMPANY])

        self.filter_model = {
            'Lang': checks,
            'Area': combo_area,
            'Employment': combo_empl,
            'Experience': combo_exp,
            'SizeComp': combo_sizecomp
        }

    def set_style(self):
        main_style = 'background: #ffffff;'
        style_combobox = """
            QComboBox{{
                font-weight: 600;
                background: {};
                border: none;
            }}
            QComboBox QAbstractItemView {{
                selection-color: #000000;
                selection-background-color: {};
            }}
            QComboBox::drop-down{{
                border: 1px;
            }}
            QComboBox::hover{{
                background: {};
            }}
        """.format(self.color, self.color, self.second_color)
        style_slider = """
                    QSlider::groove:horizontal {{  
                        height: 3px;
                        background: #B0AEB1;
                    }}
                    QSlider::handle:horizontal {{
                        background: {};
                        border: 1px solid {};
                        width: 10px;
                        margin: -10px 0; 
                    }}
                    QSlider::sub-page:qlineargradient {{
                        background: {};
                    }}
        """.format(self.color, self.color, self.third_color)
        style_filters = '''
            background-color: #ffffff
        '''
        style_button = '''
            QPushButton {{
                background-color: {};
                font: bold 12px;
                border: 1px solid #ffffff;
            }}
            QPushButton:hover {{
                background-color: {};
                color: #ffffff;
            }}
        '''.format(self.color, self.third_color)
        style_tabs = '''
            QTabBar::tab {height: 0px; width: 0px;};
        '''
        style_checkbox = """
            QCheckBox::indicator:checked {
                image: url(sources//hh_enabled.png);
            }
            QCheckBox::indicator:unchecked {
                image: url(sources//hh_notenabled.png);
            }
        """

        for key in self.all_filters:
            for name_item in ('Area', 'Lang', 'SizeComp', 'Experience', 'Employment'):
                if self.all_filters[key][name_item] is not None:
                    self.all_filters[key][name_item].setStyleSheet(style_combobox)

            # for name_item in ('SizeComp', 'Experience', 'Employment'):
            #    self.all_filters[key][name_item].setStyleSheet(style_combobox)

            if self.all_filters[key]['MinSal'] is not None:
                self.all_filters[key]['MinSal'].setStyleSheet(style_slider)

        for key in self.filter_model:
            if key in ('Area', 'SizeComp', 'Experience', 'Employment'):
                self.filter_model[key].setStyleSheet(style_combobox)
            if key in ('Lang',):
                for check in self.filter_model[key].values():
                    check.setStyleSheet(style_checkbox)

        self.setStyleSheet(main_style)
        self.filters_city1.setStyleSheet(style_filters)
        self.filters_city2.setStyleSheet(style_filters)
        self.filters_lang1.setStyleSheet(style_filters)
        self.filters_lang2.setStyleSheet(style_filters)

        self.button_lang.setStyleSheet(style_button)
        self.button_city.setStyleSheet(style_button)
        self.button_map.setStyleSheet(style_button)
        self.button_model.setStyleSheet(style_button)
        self.button_update.setStyleSheet(style_button)

        self.tabs_map.setStyleSheet(style_tabs)
        self.tabs_model.setStyleSheet(style_tabs)
        self.button_forecast.setStyleSheet(style_button)
        self.label_forecast.setStyleSheet("""
            QLabel {{
                font: bold 24px;
                border: 1px solid #ffffff;
                color: {};
            }}
        """.format(self.second_color))

        # self.label_forecast.setFont(QFont("Times", 8, QFont.Bold))

    def plot_all(self):
        for nametab in ('Lang1', 'Lang2', 'City1', 'City2'):
            self.refresh_plot(nametab)
        self.draw_plot_map1()

    def sld_action(self, value, nametab):
        self.all_filters[nametab]['lbl_min'].setText(str(value * 5000))
        self.refresh_plot(nametab)

    def check_action(self):
        active_checks = []
        for lang, checkbox in self.filter_model['Lang'].items():
            if checkbox.isChecked():
                active_checks.append(lang)
        if len(active_checks) >= MAX_LANG_MODEL:
            for checkbox in self.filter_model['Lang'].values():
                if not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.filter_model['Lang'].values():
                checkbox.setEnabled(True)

        self.button_forecast.setEnabled(bool(len(active_checks)))

    def refresh_plot(self, tabname):
        df_t = self.data

        sal = self.all_filters[tabname]['MinSal']
        if sal is not None:
            min_sal = sal.value() * 5000
            df_t = self.data[self.data['Salary'] > min_sal]

        area = self.all_filters[tabname]['Area']
        if area is not None and area.currentIndex():
            area = work_with_data.encode_param(area.currentText())
            df_t = df_t[df_t['Area'] == area]

        lang = self.all_filters[tabname]['Lang']
        if lang is not None and lang.currentIndex():
            lang = lang.currentText()
            df_t = df_t[df_t[lang] == 1]

        if self.all_filters[tabname]['SizeComp'].currentIndex():
            size_comp = work_with_data.encode_param(self.all_filters[tabname]['SizeComp'].currentText())
            df_t = df_t[df_t[size_comp] == 1]

        if self.all_filters[tabname]['Experience'].currentIndex():
            exp = work_with_data.encode_param(self.all_filters[tabname]['Experience'].currentText())
            df_t = df_t[df_t['Experience'] == exp]

        if self.all_filters[tabname]['Employment'].currentIndex():
            empl = work_with_data.encode_param(self.all_filters[tabname]['Employment'].currentText())
            df_t = df_t[df_t['Employment'] == empl]

        if tabname == 'Lang1':
            self.draw_plot_lang1(df_t)
        elif tabname == 'Lang2':
            self.draw_plot_lang2(df_t)
        elif tabname == 'City1':
            self.draw_plot_city1(df_t)
        elif tabname == 'City2':
            self.draw_plot_city2(df_t)

    def draw_plot_lang1(self, data=None):
        if data is None:
            data = self.data

        mass_sal = [(lang, data[data[lang] == 1]['Salary'].mean()) for lang in LANGUAGES]
        mass_sal = [val for val in mass_sal if str(val[1]) != 'nan']
        mass_sal.sort(key=lambda x: -x[1])
        temp = list(zip(*mass_sal))

        if not temp:
            temp = [[], []]

        self.plot_lang1.plot_bar(*temp, 'Средняя зарплата по языкам')

    def draw_plot_lang2(self, data=None):
        if data is None:
            data = self.data

        count_vac = [(lang, data[data[lang] == 1].shape[0]) for lang in LANGUAGES]
        count_vac.sort(key=lambda x: -x[1])
        count_vac = filter(lambda x: x[1] > 0, count_vac)

        temp = list(zip(*count_vac))

        if not temp:
            temp = [[], []]

        self.plot_lang2.plot_bar(*temp, 'Количество вакансий по языкам')

    def draw_plot_city1(self, data=None):
        if data is None:
            data = self.data

        mass_sal = [(area, data[data['Area'] == area]['Salary'].mean()) for area in AREA.keys()]
        mass_sal = [val for val in mass_sal if str(val[1]) != 'nan']
        mass_sal.sort(key=lambda x: -x[1])

        temp = list(zip(*mass_sal))

        if not temp:
            temp = [[], []]
        else:
            temp[0] = [work_with_data.decode_param(city) for city in temp[0]]

        self.plot_city1.plot_bar(*temp, 'Средняя зарплата по городам')

    def draw_plot_city2(self, data=None):
        if data is None:
            data = self.data

        count_vac = [(area, data[data['Area'] == area].shape[0]) for area in AREA.keys()]
        count_vac.sort(key=lambda x: -x[1])
        count_vac = filter(lambda x: x[1] > 0, count_vac)

        temp = list(zip(*count_vac))

        if not temp:
            temp = [[], []]
        else:
            temp[0] = [work_with_data.decode_param(city) for city in temp[0]]

        self.plot_city2.plot_bar(*temp, 'Количество вакансий по городам')

    def draw_plot_map1(self, data=None):
        if data is None:
            data = self.data

        mass_sal = [(area, data[data['Area'] == area].shape[0]) for area in AREA.keys()]
        mass_sal = filter(lambda x: x[1] > 0, mass_sal)

        temp = list(zip(*mass_sal))

        min_vac = min(temp[1])
        temp[1] = [vac / min_vac for vac in temp[1]]
        self.plot_map1.plot_map(*temp, 'Количество вакансий по городам')

    def create_forecast(self):
        vacancy = []
        for key in self.categorical_columns:
            vacancy.append(work_with_data.encode_param(self.filter_model[key].currentText()))

        for checkbox in self.filter_model['Lang'].values():
            vacancy.append(int(checkbox.isChecked()))

        for size_comp in SIZE_COMPANY:
            vacancy.append(int(work_with_data.encode_param(self.filter_model['SizeComp'].currentText()) == size_comp))

        df = pd.DataFrame([vacancy], columns=self.categorical_columns + self.binary_columns)
        self.label_forecast.setText('Возможная зарплата: {:.0f} руб'.format(self.model.get_predict(df)[0]))

    def update_data(self):
        answer = QMessageBox.question(self, 'Обновление данных', 'Вы хотите обновить данные?',
                                      QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer == QMessageBox.Ok:
            self.data = work_with_data.get_prepocess_data(True)
            self.model = model.get_forest_model(self.data, self.categorical_columns, self.binary_columns)
            self.plot_all()


class MatPlot(object):
    def __init__(self, x, y, parent, color='blue', second_color='black'):
        self.color = color
        self.second_color = second_color
        self.fig, self.ax1 = plt.subplots()
        self.ax1.format_coord = lambda val1, val2: ''
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(parent)
        self.canvas.move(x, y)
        self.canvas.resize(WIND_HEIGHT - x, WIND_WIDTH - BUTTON_MENU_WIDTH - 5)

        self.toolbar = NavigationToolbarCustom(self.canvas, parent)
        self.toolbar.move(x + 100, 0)
        self.toolbar.resize(450, 40)

    def plot_bar(self, tickets, values, title):
        y_pos = range(len(tickets))
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.barh(y_pos, values, align='center', alpha=0.5, color=self.color)

        if values:
            pad = max(values) / 100
        else:
            pad = 0

        for i, tick in enumerate(tickets):
            self.ax1.annotate(tick, xy=(pad, i), va='center')

        self.ax1.set_yticks([])
        self.ax1.set_title(title)
        self.canvas.draw()

    def plot_map(self, cities, vac_t, title):
        self.ax1.clear()
        m = Basemap(
            llcrnrlon=25.,
            llcrnrlat=40.,
            urcrnrlon=105.,
            urcrnrlat=65.,
            rsphere=(6378137.00, 6356752.3142),
            resolution='l',
            projection='merc'
        )
        m.fillcontinents(color=self.color)
        m.drawcountries()

        for i, city in enumerate(cities):
            if city in AREA_COORD:
                coord = list(reversed(AREA_COORD[city]))
                self.ax1.annotate(work_with_data.decode_param(city), xy=m(*coord))
                circle = plt.Circle(
                    xy=m(*coord),
                    radius=(m.ymax - m.ymin) / 540 * vac_t[i],
                    fill=True,
                    color=self.second_color
                )
                self.fig.gca().add_patch(circle)

        self.ax1.set_title(title)
        self.canvas.draw()


class NavigationToolbarCustom(NavigationToolbar):
    toolitems_temp = []
    for toolitem in NavigationToolbar.toolitems:
        if toolitem[0] in ('Home', 'Zoom', 'Pan', 'Save', 'Back', 'Forward'):
            toolitems_temp.append(toolitem)
    toolitems = toolitems_temp


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app = QApplication(sys.argv)
    main = Window()
    main.show()
    app.exec_()
