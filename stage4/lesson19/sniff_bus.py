#!/usr/bin/env python3
"""Прослушка шины Modbus RTU: только приём. Кадры — по паузе между байтами."""

import argparse
import time

import serial


def crc16(data):
    """CRC-16/MODBUS."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def describe(frame):
    """Короткая расшифровка: слейв, функция, исключение, CRC."""
    if len(frame) < 4:
        return "обрывок"
    crc_ok = crc16(frame[:-2]) == int.from_bytes(frame[-2:], "little")
    addr, fn = frame[0], frame[1]
    text = f"слейв {addr:3d}  функция {fn:02X}"
    if fn & 0x80 and len(frame) == 5:
        text += f"  ИСКЛЮЧЕНИЕ {frame[2]:02X}"
    text += "  CRC ок" if crc_ok else "  CRC ОШИБКА"
    return text


def parse_args():
    p = argparse.ArgumentParser(description="Сниффер Modbus RTU, только приём")
    p.add_argument("--port", default="/dev/ttyUSB1")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--gap", type=float, default=0.003,
                   help="пауза между байтами, после которой кадр считается законченным, с")
    return p.parse_args()


def main():
    args = parse_args()
    ser = serial.Serial(args.port, args.baud, timeout=0)   # чтение без ожидания
    ser.reset_input_buffer()   # выбросить байты, накопленные до запуска
    print(f"Слушаю {args.port}, {args.baud} 8N1, граница кадра {args.gap * 1000:.1f} мс. Ctrl+C — выход.")

    buf = bytearray()
    t_last = None        # время последнего принятого байта
    t_frame = None       # время начала текущего кадра
    t_prev_frame = None  # время начала прошлого кадра

    def flush():
        nonlocal t_prev_frame
        delta = "" if t_prev_frame is None else f"+{(t_frame - t_prev_frame) * 1000:7.1f} мс"
        print(f"{delta:>12}  {buf.hex(' ').upper():<40} {describe(bytes(buf))}")
        t_prev_frame = t_frame
        buf.clear()

    try:
        while True:
            chunk = ser.read(256)
            now = time.monotonic()
            if chunk:
                if buf and now - t_last > args.gap:
                    flush()               # пауза перед этими байтами — прошлый кадр закончен
                if not buf:
                    t_frame = now
                buf.extend(chunk)
                t_last = now
            else:
                if buf and now - t_last > args.gap:
                    flush()               # байтов нет дольше паузы — кадр закончен
                time.sleep(0.0005)
    except KeyboardInterrupt:
        print("\nВыход")
    finally:
        ser.close()


if __name__ == "__main__":
    main()