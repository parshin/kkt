# -*- coding: utf-8 -*-

# import web
import sys
import os
import json
import logging

from conf import *
from dto9fptr import Fptr

sys.path.append('/var/www/kkt')
sys.path.append('/var/www')

logging.basicConfig(filename=params["LogFileName"], level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.info('start service.')

os.environ['LD_LIBRARY_PATH'] = os.path.dirname(os.path.realpath(__file__))
logging.info(os.path.dirname(os.path.realpath(__file__)))
logging.info(os.environ)


def application(environ, start_response):
    status = '200 OK'
    # output = 'OK'

    driver = Fptr("/var/www/kkt/libfptr.so", 13)

    if environ['REQUEST_METHOD'] == 'POST':
        post_data = (environ['wsgi.input'].read())
        logging.info("received data: " + post_data)
        try:
            check_data = json.loads(post_data)
        except Exception as e:
            output = b'ERROR: no json data' + str(e)
            logging.error(output)
            response_headers = [('Content-type', 'text/plain'),
                                ('Content-Length', str(len(output)))]
            start_response(status, response_headers)
            return [output]
        else:
            logging.info("printing check...")
            output = print_check(driver, check_data).encode('UTF-8')
    else:
        output = get_kkt_status(driver)

    del driver

    logging.info('sending response: ' + output)
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


def get_kkt_status(driver):
    # 1. Установка параметров
    driver.put_DeviceSingleSetting("Port", params["Port"])
    driver.put_DeviceSingleSetting("IPAddress", params["IPAddress"])
    driver.put_DeviceSingleSetting("IPPort", params["IPPort"])
    driver.put_DeviceSingleSetting("Model", params["Model"])
    driver.put_DeviceSingleSetting("Protocol", params["Protocol"])
    driver.put_DeviceSingleSetting("AccessPassword", params["AccessPassword"])
    driver.put_DeviceSingleSetting("UserPassword", params["UserPassword"])
    driver.put_DeviceSingleSetting("Protocol", params["Protocol"])
    driver.ApplySingleSettings()

    driver.put_DeviceEnabled(True)

    result = driver.GetStatus()
    output = bytes("Статус ККТ:" + '\n' + repr(result).decode("unicode_escape"))

    driver.put_DeviceEnabled(False)

    driver.Beep()

    return output


def print_check(driver, check_data):
    # Установка параметров
    driver.put_DeviceSingleSetting("Port", params["Port"])
    driver.put_DeviceSingleSetting("IPAddress", params["IPAddress"])
    driver.put_DeviceSingleSetting("IPPort", params["IPPort"])
    driver.put_DeviceSingleSetting("Model", params["Model"])
    driver.put_DeviceSingleSetting("Protocol", params["Protocol"])
    driver.put_DeviceSingleSetting("AccessPassword", params["AccessPassword"])
    driver.put_DeviceSingleSetting("UserPassword", params["UserPassword"])
    driver.put_DeviceSingleSetting("Protocol", params["Protocol"])
    driver.ApplySingleSettings()

    # result = driver.get_DeviceSettings()
    # print "get settings: " + repr(result).decode("unicode_escape")

    result = driver.put_DeviceEnabled(True)
    logging.info("put device enabled: " + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # result = driver.GetStatus()
    # logging.info("get status:" + repr(result).decode("unicode_escape"))

    # result = driver.get_DeviceSingleSetting("IPAddress")
    # logging.info("IP address is:" + repr(result).decode("unicode_escape"))

    result = driver.put_TestMode(params["TestMode"])
    logging.info("put test mode:" + repr(result).decode("unicode_escape"))

    # # 2. Открытие чека.
    logging.info("opening check...")
    logging.info("document date: " + check_data['DocDate'])
    logging.info("document number: " + check_data['DocNumber'])
    logging.info("document summ: " + str(check_data['DocSumm']))

    # Режим регистрации
    result = driver.put_Mode(1)
    logging.info("put mode 1:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Метод выполняет GetStatus(), SetMode(), CancelCheck() см. руководство программиста
    result = driver.NewDocument()
    logging.info("new document:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    # Если смена истекла, закроем и попытаемся пробить снова
    if result_code == -3822:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        logging.error("  trying close shift...")
        # Режим снятия отчетов с гашением
        result = driver.put_Mode(3)
        logging.info("      put mode 3:" + repr(result).decode("unicode_escape"))
        result = driver.SetMode()
        logging.info("      set mode 3:" + repr(result).decode("unicode_escape"))
        result_code = driver.get_ResultCode()
        result_description = driver.get_ResultDescription()
        if result_code != 0:
            logging.error("     result code:" + repr(result_code).decode("unicode_escape"))
            logging.error("     result description:" + repr(result_description).decode("unicode_escape"))
            return json.dumps({'result_code': result_code,
                               "result_description": result_description})
        # Суточный отчет с гашением
        result = driver.put_ReportType(1)
        logging.info("      put report type 3:" + repr(result).decode("unicode_escape"))
        result_code = driver.get_ResultCode()
        result_description = driver.get_ResultDescription()
        if result_code != 0:
            logging.error("     result code:" + repr(result_code).decode("unicode_escape"))
            logging.error("     result description:" + repr(result_description).decode("unicode_escape"))
            return json.dumps({'result_code': result_code,
                               "result_description": result_description})
        # Снять отчет
        result = driver.Report()
        logging.info("      report:" + repr(result).decode("unicode_escape"))
        result_code = driver.get_ResultCode()
        result_description = driver.get_ResultDescription()
        if result_code != 0:
            logging.error("     result code:" + repr(result_code).decode("unicode_escape"))
            logging.error("     result description:" + repr(result_description).decode("unicode_escape"))
            return json.dumps({'result_code': result_code,
                               "result_description": result_description})
        # Режим регистрации
        result = driver.put_Mode(1)
        logging.info("put mode 1:" + repr(result).decode("unicode_escape"))
        result_code = driver.get_ResultCode()
        result_description = driver.get_ResultDescription()
        if result_code != 0:
            logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
            logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
            return json.dumps({'result_code': result_code,
                               "result_description": result_description})

        # Метод выполняет GetStatus(), SetMode(), CancelCheck() см. руководство программиста
        result = driver.NewDocument()
        logging.info("new document:" + repr(result).decode("unicode_escape"))
        result_code = driver.get_ResultCode()
        result_description = driver.get_ResultDescription()
        if result_code != 0:
            logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
            logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
            return json.dumps({'result_code': result_code,
                               "result_description": result_description})

    elif result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Тип чека - Продажа
    result = driver.put_CheckType(1)
    logging.info("put check type:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Открытие чека
    result = driver.OpenCheck()
    logging.info("open check:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Регистрация позиций.
    logging.info("registering positions...")
    for position in check_data['Goods']:
        logging.info("position: " + position)
        logging.info("  name: " + check_data['Goods'][position]['Name'])
        logging.info("  price: " + str(check_data['Goods'][position]['Price']))
        logging.info("  quantity: " + str(check_data['Goods'][position]['Quantity']))
        logging.info("  tax: " + str(check_data['Goods'][position]['Tax']))
        logging.info("  summ: " + str(check_data['Goods'][position]['PositionSumm']))

        # result = driver.put_Name(u'Позиция 1')  # Наименование товара
        result = driver.put_Name(check_data['Goods'][position]['Name'])
        logging.info("put name:" + repr(result).decode("unicode_escape"))

        result = driver.put_Price(check_data['Goods'][position]['Price'])  # Цена товара
        logging.info("put price:" + repr(result).decode("unicode_escape"))

        result = driver.put_Quantity(check_data['Goods'][position]['Quantity'])  # Количество товара
        logging.info("put quantity:" + repr(result).decode("unicode_escape"))

        result = driver.put_TaxNumber(3)  # Налог
        logging.info("put tax number:" + repr(result).decode("unicode_escape"))

        result = driver.put_PositionSum(check_data['Goods'][position]['PositionSumm'])  # Сумма строки (позиции)
        logging.info("put sum position:" + repr(result).decode("unicode_escape"))

        result = driver.Registration()  # Регистрация позиции
        logging.info("position registration:" + repr(result).decode("unicode_escape"))

    # Прием оплаты.
    result = driver.put_TypeClose(1)  # Тип оплаты - Платежная карта
    logging.info("put type close:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Сумма оплаты
    result = driver.put_Summ(check_data['DocSumm'])
    logging.info("put summ:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Регистрация платежа
    result = driver.Payment()
    logging.info("pyment:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    result = driver.get_ResultCode()
    logging.info("payment result code:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    # Закрытие чека.
    result = driver.CloseCheck()
    logging.info("close check:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    result = driver.get_CheckNumber()
    logging.info("check number:" + repr(result).decode("unicode_escape"))
    result_code = driver.get_ResultCode()
    result_description = driver.get_ResultDescription()
    if result_code != 0:
        logging.error("  result code:" + repr(result_code).decode("unicode_escape"))
        logging.error("  result description:" + repr(result_description).decode("unicode_escape"))
        return json.dumps({'result_code': result_code,
                           "result_description": result_description})

    driver.Beep()

    return json.dumps({'result_code': result_code,
                       "result_description": result_description,
                       "check_number": result})

# if __name__ == "__main__":
