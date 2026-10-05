#!/usr/bin/env python3
"""Сканер шины Modbus RTU: ищет приборы по адресам и скоростям, 8N1."""

import argparse
import logging
from pathlib import Path

import minimalmodbus

LOG_FILE = Path(__file__).parent / "scan_bus.log"

# Пробные функции по очереди: 01 coil 0, 03 holding 0, 04 input 0.
# Несколько функций — потому что прошивки молчат на неподдерживаемое.
PROBE_FUNCTIONS = (1, 3, 4)


def setup_logging(verbose):
    """Журнал: в консоль INFO (или DEBUG с -v), в файл всё."""
    log = logging.getLogger("scan")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(fmt)

    file = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file.setLevel(logging.DEBUG)
    file.setFormatter(fmt)

    log.addHandler(console)
    log.addHandler(file)
    return log


def parse_args():
    p = argparse.ArgumentParser(description="Сканер шины Modbus RTU")
    p.add_argument("--port", default="/dev/ttyUSB0", help="последовательный порт")
    p.add_argument("--bauds", type=int, nargs="+", default=[9600],
                   help="скорости через пробел, например 9600 19200")
    p.add_argument("--start", type=int, default=1, help="первый адрес")
    p.add_argument("--end", type=int, default=247, help="последний адрес, до 255")
    p.add_argument("--timeout", type=float, default=0.2, help="ожидание ответа, с")
    p.add_argument("-v", "--verbose", action="store_true", help="каждая проба в консоль")
    args = p.parse_args()
    if not 1 <= args.start <= args.end <= 255:
        p.error("нужно 1 <= start <= end <= 255")
    return args


def probe(inst, fc):
    """Один пробный запрос выбранной функцией к ячейке 0."""
    if fc == 1:
        return inst.read_bit(0, functioncode=1)
    return inst.read_register(0, functioncode=fc)


def check_address(port, baud, address, timeout, log):
    """Пробует функции по очереди. Возвращает описание ответа или None при тишине."""
    inst = minimalmodbus.Instrument(port, address)
    inst.serial.baudrate = baud
    inst.serial.timeout = timeout

    for fc in PROBE_FUNCTIONS:
        try:
            value = probe(inst, fc)
            return f"функция {fc:02d}: данные {value}"
        except minimalmodbus.NoResponseError:
            log.debug("адрес %3d, функция %02d: тишина", address, fc)
        except minimalmodbus.SlaveReportedException as err:
            return f"функция {fc:02d}: исключение ({err})"
        except minimalmodbus.InvalidResponseError as err:
            log.warning("адрес %3d, функция %02d: битый ответ — %s", address, fc, err)
            return f"функция {fc:02d}: битый ответ"
    return None


def main():
    args = parse_args()
    log = setup_logging(args.verbose)
    found = []

    try:
        for baud in args.bauds:
            log.info("Скорость %d, адреса %d–%d, порт %s", baud, args.start, args.end, args.port)
            for address in range(args.start, args.end + 1):
                result = check_address(args.port, baud, address, args.timeout, log)
                if result:
                    log.info("НАЙДЕН: адрес %d, %d бод — %s", address, baud, result)
                    found.append((address, baud))
    except KeyboardInterrupt:
        log.warning("Прервано пользователем")

    log.info("Итог: найдено %d — %s", len(found),
             ", ".join(f"{a} @ {b}" for a, b in found) or "никого")


if __name__ == "__main__":
    main()