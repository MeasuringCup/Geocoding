import requests
import pytest
import logging
import csv
import allure

logging.basicConfig(filename="main.log", level=logging.INFO, filemode="w",
                    format='%(asctime)s %(levelname)s:%(message)s')


def get_test_file(data_file):
    test_data = []
    with open(data_file, newline="") as csvfile:
        data = csv.reader(csvfile, delimiter=",")
        next(data)
        for row in data:
            test_data.append(row)
    return [test_data][0]


def get_data_address(street, city, country):
    data_address = street.split(', ')
    address_list = [city, country]
    for i in range(2):
        if address_list[i] != '':
            data_address.append(address_list[i])
    return data_address


@allure.step('Step 1: Запрос к API')
def generating_request(params, response_type):
    url = 'https://nominatim.openstreetmap.org/' + response_type
    request = requests.get(url, params=params)
    return request


@allure.step('Step 2: Проверка ответа на:')
def checking_response(response, *args):
    with allure.step("код ошибки"):
        if response.status_code != 200:  # код ответа сервера
            if response.status_code == 414:
                logging.error(f"Ошибка {response.status_code}: Request URI Too Large.")
            else:
                logging.error(f"Ошибка {response.status_code}: {response.json()['error']['message']}.")
            logging.info('Конец поиска')
            assert False
    with allure.step("пустой ответ"):
        if response.json() == []:  # проверка на пустой ответ
            logging.error(f"Запрашиваемый адрес \"{''.join(args)}\" не найден.")
            logging.info('Конец поиска')
            assert False
    with allure.step("unable to geocode"):
        if response.json() == {'error': 'Unable to geocode'}:  # проверка на невозможность геокодирования
            logging.error(f'По указанным координатам {args} отсутствует адрес: {response.json()}.')
            logging.info('Конец поиска')
            assert False


@allure.suite('Geocoding suit')
@allure.sub_suite('Forward geocoding suit')
@allure.feature('Прямое геокодирование')
class TestForwardSearch:

    @allure.story('Простое прямое геокодирование')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.high
    @allure.title('High: Простое прямое геокодирование')
    @pytest.mark.parametrize("test_data", get_test_file("data_forward.csv"))
    def test_simple_forward_search(self, test_data):  # Метод с тестом на простое прямое геокодирование
        """Простое прямое геокодирование: отправляем адрес в произвольной форме, получаем ответ в виде координат, сверяем координаты из ответа с ожидаемым результатом."""

        street, city, country, data_lat, data_lon = test_data
        with allure.step("Формирование произвольной формы адреса"):
            data_address = ', '.join(get_data_address(street, city, country))
        logging.info(f'Простой поиск координат адреса: "{data_address}".')
        request = generating_request({'q': data_address, 'format': 'json'}, 'search')
        checking_response(request, data_address)
        self.asserting_for_forward_search(request.json(), data_lat, data_lon)

    @allure.story('Структурированное прямое геокодирование')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @allure.title('Critical: Структурированное прямое геокодирование')
    @pytest.mark.parametrize("test_data", get_test_file("data_forward.csv"))
    def test_structured_forward_search(self, test_data):  # Метод с тестом на структурированное прямое геокодирование
        """Структурированное прямое геокодирование: отправляем адрес в виде нескольких разделённых параметров, получаем ответ в виде координат, сверяем координаты из ответа с ожидаемым результатом."""
        street, city, country, data_lat, data_lon = test_data
        with allure.step("Формирование структурированной формы адреса"):
            data_address = ', '.join(get_data_address(street, city, country))
        logging.info(f'Структурированный поиск координат адреса: "{data_address}".')
        request = generating_request({'street': street, 'city': city, 'country': country, 'format': 'json'}, 'search')
        checking_response(request, data_address)
        self.asserting_for_forward_search(request.json(), data_lat, data_lon)

    @staticmethod
    @allure.step('Step 3: Сверка координат из ответа с ожидаемым результатом')
    def asserting_for_forward_search(json, data_lat, data_lon):
        response_lat = float(json[0]['lat'])
        response_lon = float(json[0]['lon'])
        if (response_lat, response_lon) == (
                float(data_lat), float(data_lon)):  # проверка на соответствие ожидаемому результату
            logging.info(
                f'Координаты из ответа соответствуют ожидаемому результату.')
            logging.info('Конец поиска')
            assert True
        else:  # проверка на соответствие ожидаемому результату
            logging.error(f'Координаты из ответа {response_lat} и {response_lon} не соответствуют ожидаемому '
                          f'результату {data_lat} и {data_lon}.')
            logging.info('Конец поиска')
            assert False


@allure.suite('Geocoding suit')
@allure.sub_suite('Reverse geocoding suit')
@allure.feature('Обратное геокодирование')
class TestReverseGeocoding:

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @allure.title('Critical: Обратное геокодирование')
    @pytest.mark.parametrize("test_data", get_test_file("data_reverse.csv"))
    def test_reverse_geocoding(self, test_data):  # Метод с тестом на обратное геокодирование
        """Обратное геокодирование: отправляем координаты, получаем в ответе адрес, сверяем ожидаемый адрес с фактическим."""
        street, city, country, data_lat, data_lon = test_data
        logging.info(f"Поиск адреса по координатам: {data_lat}, {data_lon}.")
        request = generating_request({'lat': data_lat, 'lon': data_lon, 'format': 'json'}, 'reverse')
        data_address = get_data_address(street, city, country)
        checking_response(request, data_lat, data_lon)
        self.asserting_for_reverse_geocoding(request.json(), data_address)

    @staticmethod
    @allure.step('Step 3: Сверка ожидаемого адреса с фактическим')
    def asserting_for_reverse_geocoding(json, data_address):
        response_address = json['display_name']
        b = response_address.split(', ')
        flag = True
        no_match = []
        for i in range(len(data_address)):
            if data_address[i] not in b and data_address[i] != '':
                no_match.append(data_address[i])
                flag = False
        if flag == False:
            logging.error(f"Ожидаемый адрес \"{', '.join(no_match)}\" отсутствует в ответе.")
        else:
            logging.info('Адрес из ответа соответствует ожидаемому результату.')
        logging.info('Конец поиска')
        assert flag
