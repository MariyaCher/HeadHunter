import json
from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import requests

URL = 'https://api.hh.ru/vacancies?'
URL_CURRENCY = 'https://www.cbr.ru/currency_base/daily/'

PATH_DUMP_RAW = 'sources/hh_data.pkl'
PATH_DUMP_PREPROC = 'sources/hh_data_preproc.pkl'

MIN_SALARY = 30000

AREA = {
    "Perm": "72",
    "Volgograd": "24",
    "Voronezh ": "26",
    "Yekaterinburg": "3",
    "Kazan": "88",
    "Krasnoyarsk": "54",
    "Krasnodar": "53",
    "Moscow": "1",
    "Nizhny Novgorod": "66",
    "Novosibirsk": "4",
    "Omsk": "68",
    "Rostov-on-don ": "76",
    "Samara": "78",
    "St. Petersburg": "2",
    "Ufa ": "99",
    "Chelyabinsk": "104"
}

AREA_COORD = {
    "Perm": (58.01, 56.25),
    "Volgograd": (48.72, 44.5),
    "Voronezh ": (51.67, 39.18),
    "Yekaterinburg": (56.85, 60.61),
    "Kazan": (55.79, 49.12),
    "Krasnoyarsk": (56.02, 92.87),
    "Krasnodar": (45.04, 38.98),
    "Moscow": (55.75, 37.62),
    "Nizhny Novgorod": (56.33, 44.0),
    "Novosibirsk": (55.04, 82.93),
    "Omsk": (54.99, 73.37),
    "Rostov-on-don ": (47.23, 39.72),
    "Samara": (53.2, 50.15),
    "St. Petersburg": (59.94, 30.31),
    "Ufa ": (54.74, 55.97),
    "Chelyabinsk": (55.15, 61.43),
}

LANGUAGES = (
    "JavaScript", "SQL", "ABAP",
    "PHP", "Java", "Python",
    "C#", "C++", "Haskell",
    "Go", "Ruby", "Perl",
    "Swift", "Kotlin", "Scala",
    "Groovy", "Erlang", "Solidity"
)

EXPERIENCE = (
    'noExperience', 'between1And3', 'between3And6', 'moreThan6'
)

EMPLOYMENT = (
    'full', 'part', 'probation', 'project'
)

SIZE_COMPANY = {
    'SmallCompany': (0, 5),
    'MediumCompany': (5, 10),
    'LargeCompany': (10, float('inf')),
}

SYNONYMS = {
    # EXP
    'noExperience': 'Без опыта',
    'between1And3': '1-3 года',
    'between3And6': '3-6 лет',
    'moreThan6': 'более 6 лет',
    # EMPL
    'full': 'Полная занятость',
    'part': 'Частичная занятость',
    'probation': 'Испытательный срок',
    'project': 'Проектная работа',
    # SIZE COMPANY
    'SmallCompany': 'Малая компания',
    'MediumCompany': 'Средняя компания',
    'LargeCompany': 'Крупная компания',
    # AREA
    "Perm": "Пермь",
    "Volgograd": "Волгоград",
    "Voronezh ": "Воронеж",
    "Yekaterinburg": "Екатеринбург",
    "Kazan": "Казань",
    "Krasnoyarsk": "Красноярск",
    "Krasnodar": "Краснодар",
    "Moscow": "Москва",
    "Nizhny Novgorod": "Нижний Новгород",
    "Novosibirsk": "Новосибирск",
    "Omsk": "Омск",
    "Rostov-on-don ": "Ростов-на-Дону",
    "Samara": "Самара",
    "St. Petersburg": "Санкт Петербург",
    "Ufa ": "Уфа",
    "Chelyabinsk": "Челябинск"
}


def decode_param(param):
    if param in SYNONYMS:
        return SYNONYMS[param]
    return param


def encode_param(param):
    for param_code, synonym in SYNONYMS.items():
        if synonym == param:
            return param_code
    return param


def get_prepocess_data(refresh=False):
    if not refresh:
        try:
            return pd.read_pickle(PATH_DUMP_PREPROC)
        except:
            pass

    df = preprocess_data(get_data(refresh))
    df.to_pickle(PATH_DUMP_PREPROC)
    return df


def get_data(refresh=False):
    if not refresh:
        try:
            return pd.read_pickle(PATH_DUMP_RAW)
        except:
            pass
    list_vacancy = []
    currencies = get_currency()
    for area in AREA:
        for experience in EXPERIENCE:
            for employment in EMPLOYMENT:
                for language in LANGUAGES:
                    while True:
                        try:
                            num_page = 0
                            lim_page = 1
                            while num_page < lim_page:
                                r = requests.get(URL + params(lang=language, area=AREA[area], sal=True,
                                                              page=num_page, exp=experience, emp=employment))
                                data_raw = json.loads(r.text)
                                list_vacancy.extend(
                                    data_process(
                                        data_raw['items'],
                                        area,
                                        language,
                                        experience,
                                        employment,
                                        currencies
                                    )
                                )
                                if num_page == 0:
                                    lim_page = data_raw['pages']

                                num_page += 1
                            break
                        except:
                            pass
                        # except Exception as err:
                        #     print(err)

    df = pd.DataFrame(list_vacancy, columns=['id', 'Employer', 'Salary From', 'Salary To',
                                             'Area', 'Language', 'Experience', 'Employment'])
    df.to_pickle(PATH_DUMP_RAW)

    return df


def preprocess_data(df):
    df = df.astype(str).groupby(df.columns.difference(['Language']).tolist()).agg(' , '.join).reset_index()

    for lang in LANGUAGES:
        df[lang] = df['Language'].apply(lambda x: int(lang in x.split(' , ')))

    df['SmallCompany'], df['MediumCompany'], df['LargeCompany'] = 0, 0, 0

    for name_company in pd.unique(df['Employer']):
        count_vac = df[df['Employer'] == name_company].shape[0]
        if count_vac < SIZE_COMPANY['SmallCompany'][1]:
            column_size = 'SmallCompany'
        elif count_vac >= SIZE_COMPANY['LargeCompany'][0]:
            column_size = 'LargeCompany'
        else:
            column_size = 'MediumCompany'
        df.loc[df['Employer'] == name_company, column_size] = 1

    df['Salary From'] = df['Salary From'].astype('float')
    df['Salary To'] = df['Salary To'].astype('float')
    df['Salary'] = df[['Salary From', 'Salary To']].mean(axis=1)
    df = df[(df['Salary'] >= MIN_SALARY) & (df['Salary'] <= 300000)]
    df = df.drop(['id', 'Language', 'Employer'], axis=1)
    return df


def get_currency():
    try:
        data = requests.get(URL_CURRENCY)
        page_text = data.text
        soup = BeautifulSoup(page_text, "html.parser")
        table_body = soup.find("table")
        rows = table_body.find_all('tr')
        currency = {}
        for row in rows[1:]:
            cols = row.find_all('td')
            currency[cols[1].text] = float(cols[4].text.replace(',', '.')) / float(cols[2].text)
    except:
        currency = {
            'USD': 63.95,
            'EUR': 72.36
        }
        print('Error: Could not get current rate. The values are set from 17.04.2019')
    return currency


def data_process(data, area, lang, experience, empl, currencies):
    results = []
    for vacancy in data:
        vac_id = vacancy['id']
        salary_from = vacancy['salary']['from']
        salary_to = vacancy['salary']['to']
        currency = vacancy['salary']['currency']
        if currency != 'RUR':
            if currency not in currencies:
                continue
            if salary_from is not None:
                salary_from *= currencies[currency]
            if salary_to is not None:
                salary_to *= currencies[currency]
        employer = vacancy['employer']['name']
        results.append((vac_id, employer, salary_from, salary_to, area, lang, experience, empl))
    return results


def params(**args):
    list_params = []
    for param in args:
        if param == 'lang':
            list_params.append('text={}'.format(quote(args[param])))
        if param == 'area':
            list_params.append('area={}'.format(args[param]))
        if param == 'sal':
            list_params.append('only_with_salary={}'.format(args[param]))
        if param == 'page':
            list_params.append('page={}'.format(args[param]))
        if param == 'exp':
            list_params.append('experience={}'.format(args[param]))
        if param == 'emp':
            list_params.append('employment={}'.format(args[param]))
    return '&'.join(list_params)


if __name__ == '__main__':
    print('Start updating...')
    get_prepocess_data(True)
    print('Success updating')
