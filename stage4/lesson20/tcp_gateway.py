#!/usr/bin/env python3
"""Шлюз Modbus TCP → RTU: запросы по TCP уходят на шину RS-485, ответы возвращаются клиенту."""

import argparse
import logging
import socketserver
import struct
import threading
import time

import serial

GATEWAY_NO_RESPONSE = 0x0B   # исключение «целевое устройство не ответило»
log = logging.getLogger("gw")


def crc16(data):
    """CRC-16/MODBUS."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


class RtuBus:
    """Шина RS-485: один мастер, запросы строго по очереди."""

    def __init__(self, port, baud, timeout, gap):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.gap = gap
        self.lock = threading.Lock()
        self.last_activity = 0.0

    def transact(self, unit, pdu):
        """PDU → RTU-кадр на шину, ответ → PDU. None — тишина или битый ответ."""
        frame = bytes([unit]) + pdu
        frame += crc16(frame).to_bytes(2, "little")

        with self.lock:
            wait = self.gap - (time.monotonic() - self.last_activity)
            if wait > 0:
                time.sleep(wait)             # пауза между запросами — для медленного модуля
            self.ser.reset_input_buffer()
            self.ser.write(frame)

            head = self.ser.read(3)          # адрес, функция, число байт или код исключения
            if len(head) < 3:
                self.last_activity = time.monotonic()
                return None
            fn = head[1]
            if fn & 0x80:
                rest = 2                     # исключение: остался только CRC
            elif fn in (1, 2, 3, 4):
                rest = head[2] + 2           # чтение: данные + CRC
            else:
                rest = 5                     # запись 05, 06, 15, 16: всего 8 байт
            tail = self.ser.read(rest)
            self.last_activity = time.monotonic()

        reply = head + tail
        if len(tail) < rest or reply[0] != unit:
            return None
        if crc16(reply[:-2]) != int.from_bytes(reply[-2:], "little"):
            return None
        return reply[1:-2]                   # без адреса и CRC — это PDU


def recv_exact(sock, n):
    """Прочитать из сокета ровно n байт. None — клиент закрыл соединение."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


class Handler(socketserver.BaseRequestHandler):
    """Одно TCP-соединение: запросы клиента по одному, пока он не отключится."""

    def handle(self):
        peer = "%s:%d" % self.client_address
        log.info("подключился %s", peer)
        while True:
            header = recv_exact(self.request, 7)
            if header is None:
                break
            tid, pid, length, unit = struct.unpack(">HHHB", header)
            pdu = recv_exact(self.request, length - 1)
            if pdu is None:
                break

            reply = self.server.bus.transact(unit, pdu)
            if reply is None:
                reply = bytes([pdu[0] | 0x80, GATEWAY_NO_RESPONSE])
                log.warning("%s: unit %d, функция %02X — нет ответа, исключение 0B", peer, unit, pdu[0])
            else:
                log.info("%s: unit %d, функция %02X — ответ %d байт", peer, unit, pdu[0], len(reply))

            mbap = struct.pack(">HHHB", tid, pid, len(reply) + 1, unit)
            self.request.sendall(mbap + reply)
        log.info("отключился %s", peer)


class Gateway(socketserver.ThreadingTCPServer):
    allow_reuse_address = True   # перезапуск без ожидания освобождения порта
    daemon_threads = True        # потоки клиентов не мешают выходу по Ctrl+C


def main():
    p = argparse.ArgumentParser(description="Шлюз Modbus TCP → RTU")
    p.add_argument("--port", default="/dev/ttyUSB0", help="порт RS-485")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--tcp-port", type=int, default=5020)
    p.add_argument("--timeout", type=float, default=0.2, help="ожидание ответа прибора, с")
    p.add_argument("--gap", type=float, default=0.02, help="пауза между запросами на шине, с")
    args = p.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)-7s %(message)s", level=logging.INFO)
    server = Gateway(("0.0.0.0", args.tcp_port), Handler)
    server.bus = RtuBus(args.port, args.baud, args.timeout, args.gap)
    log.info("Шлюз: TCP %d → %s, %d 8N1", args.tcp_port, args.port, args.baud)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Остановлен")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()