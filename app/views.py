# channel_layer/views.py

import random
import json
import requests
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


P = 0.11  # вероятность ошибки
R = 0.01  # вероятность потери кадра
g = '10011'
err_table = ['0001', '0010', '0100', '1000', '0011', '0110', '1100', '1011', '0101', '1010', '0111', '1110', '1111', '1101', '1001']

def bin_dev(arg_first, arg_second):
    arg_first_int = int(arg_first, 2)
    arg_second_int = int(arg_second, 2)
    a = bin(arg_first_int)[2:]
    b = bin(arg_second_int)[2:]
    len_dif = len(a) - len(b)
    result = ''
    if len_dif > 0:
        res_str = ''
        devisible_int = int(a[0:len(b)], 2)
        position = len(b)
        for i in range(len_dif+1):
            if len(bin(devisible_int)[2:]) < len(b):
                if position + i > len(a) - 1:
                    res_str = bin(devisible_int)[2:]
                    break
                devisible_int = int(bin(devisible_int)[2:] + a[position + i], 2)
                continue
            res = devisible_int ^ arg_second_int
            res_str = bin(res)[2:]
            if position + i > len(a) - 1:
                break
            devisible_int = int(res_str + a[position + i], 2)
        return res_str

    if len_dif < 0:
        res_str = '0' + bin(arg_first_int)[2:]
        return res_str

    result_int = arg_first_int ^ arg_second_int
    result_str = '0' + bin(result_int)[2:]
    return result_str

def bin_sum(arg_first, arg_second):
    arg_first_int = int(arg_first, 2)
    arg_second_int = int(arg_second, 2)
    result_int = arg_first_int ^ arg_second_int
    result_str = bin(result_int)[2:]
    while len(result_str) < 15:
        result_str = '0' + result_str
    return result_str

def find_err(res_dev, err_table):
    number = -1
    for f in range(len(err_table)):
        int_residue = int(res_dev, 2)
        int_err = int(err_table[f], 2)
        if int_residue == int_err:
            number = f
            break
    return number

def encode(message):
    residue = len(message) % 11
    if residue != 0:
        message = '0' * (11 - residue) + message
    res_message = ''
    for i in range(0, len(message), 11):
        m0 = message[i:i+11]
        m = m0 + '0000'
        p = bin_dev(m, g)
        v = bin_sum(m, p)
        res_message += ''.join(v)
    print(f"enc: {res_message=}")
    return res_message

def make_error(message):
    if random.random() < P:
        error_pos = random.randrange(0, len(message))
        pos = len(message) - 1 - error_pos
        message = message[:pos] + str(int(message[pos]) ^ 1) + message[pos + 1:]
    return message

def decode(message):
    res_message = ''
    for i in range(0, len(message), 15):
        r = message[i:i+15]
        res_dev = bin_dev(r, g)
        position = find_err(res_dev, err_table)
        if position != -1: 
            pos = len(r) - 1 - position
            new_r = r[:pos] + str(int(r[pos]) ^ 1) + r[pos + 1:]
        else:
            new_r = r
        new_r = str(new_r[:-4])
        res_message += ''.join(new_r)
    print(f"dec: {res_message=}")
    return res_message

@api_view(['POST'])
def code(request):
    data = request.data
    sender = data.get('login')
    part_message_id = data.get('part_message_id')
    timestamp = data.get('timestamp')
    message = data.get('message')
    amount_segments = data.get('amount_segments')
    error_fg = False

    # Кодирование
    len_mes = len(message)
    encoded_message = encode(message)
        
    # Внесение ошибок
    corrupted_message = make_error(encoded_message)
        
    # Потеря сообщения
    if random.random() < R:
        decoded_message = ''
        error_fg = True
    else:
        decoded_message = decode(corrupted_message)
        len_dec_mes = len(decoded_message)
        l = len_dec_mes - len_mes
        print(l)
        decoded_message = str(decoded_message[l:])
        print(f"dec1: {decoded_message=}")
    print(f"dec2: {decoded_message=}")  
    if decoded_message != message:
        decoded_message = ''
        error_fg = True
  

    # Отправка на транспортный уровень
    transfer_data = {
        "sender": sender,
        "part_message_id": part_message_id,
        "timestamp": timestamp,
        "message": decoded_message,
        "amount_segments": amount_segments,
    }
    if not error_fg:
        response = requests.post('http://158.160.87.211:8888/transfer/', json=transfer_data)
        if response.status_code == 200:
            return HttpResponse(status=200)
        #return HttpResponse(status=404)
    else:
        print('LOST!!!!')
    '''
    response_data = {
        "status": "ok",
        "data": transfer_data
    }

    return Response(response_data, status=status.HTTP_200_OK)'''
