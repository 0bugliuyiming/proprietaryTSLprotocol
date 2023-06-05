import sys
import os

# response_fram_of_cmd1_length = 57
response_fram_of_cmd1_length = 35
polling_frame_length = 35
response_payload_index = 10
polling_payload_index = 25

def preprocess_device_type(device_type):
    device_type = hex(int(device_type))[2:]
    if len(device_type) % 2 != 0:
        device_type = '0' + device_type
    return device_type

def frame_add_f4(frame, modle):
    new_frame = frame
    #应答
    if modle == 0:
        f4_index = response_payload_index
        for e in frame[response_payload_index:-2]:
            if e == 'f4':
                new_frame.insert(f4_index, 'f4')
            f4_index += 1
    #轮询
    else:
        f4_index = polling_payload_index
        for e in frame[polling_payload_index:-2]:
            if e == 'f4':
                new_frame.insert(f4_index, 'f4')
            f4_index += 1
    return new_frame

def calculate_crc_8(buf):
    crc = 0
    for e in buf:
        crc = crc ^ int(e, 16)
    crc = hex(crc)[2:]
    if len(crc) < 2:
        crc = '0' + crc
    return crc

def calculate_crc_16(buf):
    crc_code = 0xFFFF
    for e in buf:
        crc_code = crc_code ^ int(e, 16)
        for i in range(0, 8):
            if (crc_code & 0x0001):
                crc_code = (crc_code >> 1) ^ 0xa001
            else:
                crc_code = crc_code >> 1
    crc_code = hex(crc_code)[2:]
    if len(crc_code) % 2 != 0:
        crc_code = '0' + crc_code
    return crc_code

def generate_hex_from_str(dec_name):
    dec_hex = list()
    for e in dec_name:
        dec_hex.append(e.encode('utf-8').hex())
    return dec_hex

def generate_frame_of_cmd1(device_name, device_type):
    frame = ['f4', 'f5', '00', '23', '0b', '16', '01', '02', '00', '00']
    frame_len = hex(int(response_fram_of_cmd1_length))[2:]
    if len(frame_len) < 2:
        frame_len = '0' + frame_len
    frame[3] = frame_len 
    frame[4] = device_type[:2]
    frame[5] = device_type[2:]
    frame += device_name
    frame += ['00' for n in range(response_fram_of_cmd1_length - len(frame) + 2)]
    # frame[-1] = '03'
    crc_8bit = calculate_crc_8(frame)
    frame += ['00', crc_8bit]
    frame = frame_add_f4(frame, 0)
    return frame

def generate_frame_of_cmd4(device_type):
    frame = ['f4', 'f5', '00', '09', '0b', '16', '04', '01', '00', '00', '0a']
    frame[4] = device_type[:2]
    frame[5] = device_type[2:]
    crc_8bit = calculate_crc_8(frame)
    frame += ['00', crc_8bit]
    frame = frame_add_f4(frame, 0)
    return frame

def generate_handshake_frame(device_type):
    frame = ['f4', 'f5', '08', '01', '08', '04', '00', 'f4', '00', '00', '00']
    frame[5] = device_type[:2]
    frame[6] = device_type[2:]
    crc_16bit = calculate_crc_16(frame[:-2])
    frame[-2] = crc_16bit[2:]
    frame[-1] = crc_16bit[:2]
    frame = frame_add_f4(frame, 1)
    return frame

def generate_polling_frame(device_type):
    frame = ['f4', 'f5', '23', '02', '08', '04', '00', 'f4', '0a']
    frame[2] = hex(polling_frame_length).lower()[2:]
    frame[5] = device_type[:2]
    frame[6] = device_type[2:]
    frame += ['00' for n in range(polling_frame_length - len(frame) + 1)]
    crc_16bit = calculate_crc_16(frame)
    frame += ['00', '00']
    frame[-2] = crc_16bit[2:]
    frame[-1] = crc_16bit[:2]
    frame = frame_add_f4(frame, 1)
    return frame

def generate_uart_frame(device_name, device_type, modle=0):
    #应答
    if modle == 0:
        frame_cmd1 = generate_frame_of_cmd1(device_name, device_type)
        frame_cmd4 = generate_frame_of_cmd4(device_type)
        return frame_cmd1, frame_cmd4
    #轮询
    else:
        handshake_frame = generate_handshake_frame(device_type)
        poling_frame = generate_polling_frame(device_type)
        return handshake_frame, poling_frame

def read_config_file(file_path):
    if not os.path.exists(file_path):
        print("ERROR! file is not exists!" + file_path)
        return []
    else:
        ret_list = []
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                ret_list.append(line.strip())
        return ret_list

if __name__ == "__main__":
    file_path = sys.argv[-1]
    dec_name, dec_type, modle = read_config_file(file_path)
    dec_name_hex = generate_hex_from_str(dec_name)
    dec_type_hex = preprocess_device_type(dec_type)
    mcu_response_frame, mcu_send_wifi_frame = generate_uart_frame(dec_name_hex, dec_type_hex, int(modle))
    print("MCU response WiFi:")
    for e in mcu_response_frame:
        print(e, end=' ')
    print("\nstart link WiFi:")
    for e in mcu_send_wifi_frame:
        print(e, end=' ')
    print()
