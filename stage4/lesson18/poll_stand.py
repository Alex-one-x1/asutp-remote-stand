#!/usr/bin/env python3
"""Периодический опрос стенда: TS1, HS1 (XY-MD02), SW1 и RL1–RL4 (релейный модуль)."""

import argparse
import logging
import time
from pathlib import Path

import minimalmodbus

LOG_FILE = Path(__file__).parent / "poll_stand.log"
SENSOR_ADDR = 1
RELAY_ADDR = 2
TS1_RANGE = (-40.0, 80.0)   # °C, правдоподобный диапазон
HS1_RANGE = (0.0, 100.0)    # %


def setup_logging():
    """Журнал в консоль и в файл, уровень INFO."""
    log = logging.getLogger("poll")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")
    for handler in (logging.StreamHandler(),
                    logging.FileHandler(LOG_FILE, encoding="utf-8")):
        handler.setFormatter(fmt)
        log.addHandler(handler)
    return log


def parse_args():
    p = argparse.ArgumentParser(description="Периодический опрос стенда Modbus RTU")
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--period", type=float, default=1.0, help="период опроса, с")
    p.add_argument("--cycles", type=int, default=0, help="число циклов, 0 — без конца")
    p.add_argument("--timeout", type=float, default=0.2, help="ожидание ответа, с")
    p.add_argument("--gap", type=float, default=0.02,
                    help="пауза перед запросом к следующему прибору, с")
    p.add_argument("--naive", action="store_true",
                    help="sleep(period) после опроса — режим с дрейфом")
    return p.parse_args()


def make_instrument(port, address, baud, timeout):
    inst = minimalmodbus.Instrument(port, address)
    inst.serial.baudrate = baud
    inst.serial.timeout = timeout
    return inst


def to_signed(raw):
    """16-битное значение регистра → число со знаком."""
    return raw - 65536 if raw >= 32768 else raw


def read_sensor(inst):
    """TS1, HS1: input 0x0001–0x0002, масштаб 0,1. Возвращает строку для журнала."""
    try:
        raw_t, raw_h = inst.read_registers(1, 2, functioncode=4)
        t = to_signed(raw_t) / 10
        h = raw_h / 10
        plausible = (TS1_RANGE[0] <= t <= TS1_RANGE[1]
                    and HS1_RANGE[0] <= h <= HS1_RANGE[1]
                    and not (raw_t == 0 and raw_h == 0))
        mark = "" if plausible else "  НЕДОСТОВЕРНО"
        return f"TS1 {t:5.1f} °C  HS1 {h:5.1f} %{mark}"
    except minimalmodbus.ModbusException as err:
        return f"датчик: нет данных ({type(err).__name__})"


def read_relay_module(inst):
    """SW1: вход 0; RL1–RL4: coils 0–3. Количество 8 — особенность прошивки."""
    try:
        inputs = inst.read_bits(0, 8, functioncode=2)
        coils = inst.read_bits(0, 8, functioncode=1)
        relays = "".join(str(bit) for bit in coils[:4])
        return f"SW1 {inputs[0]}  RL1–4 {relays}"
    except minimalmodbus.ModbusException as err:
        return f"модуль: нет данных ({type(err).__name__})"


def main():
    args = parse_args()
    log = setup_logging()
    sensor = make_instrument(args.port, SENSOR_ADDR, args.baud, args.timeout)
    relay = make_instrument(args.port, RELAY_ADDR, args.baud, args.timeout)

    mode = "наивный sleep" if args.naive else "фиксированное расписание"
    log.info("Старт: период %.3f с, режим — %s", args.period, mode)

    start = time.monotonic()
    cycle = 0
    try:
        while args.cycles == 0 or cycle < args.cycles:
            t0 = time.monotonic()
            drift = (t0 - start) - cycle * args.period
            sensor_text = read_sensor(sensor)
            time.sleep(args.gap)
            relay_text = read_relay_module(relay)
            log.info("цикл %4d  смещение %+.3f с | %s | %s",
                        cycle, drift, sensor_text, relay_text)
            cycle += 1

            if args.naive:
                time.sleep(args.period)
            else:
                next_start = start + cycle * args.period
                delay = next_start - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    log.warning("цикл не уложился в период на %.3f с", -delay)
    except KeyboardInterrupt:
        log.info("Остановлено пользователем, циклов: %d", cycle)


if __name__ == "__main__":
    main()