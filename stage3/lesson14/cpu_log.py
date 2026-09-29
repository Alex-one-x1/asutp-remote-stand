import csv
import time
from datetime import datetime

from standlib import LOG_PATH, classify, read_cpu_temp, read_int

FIELDS = ["time", "temp_c", "status"]


def append_rows(rows):
    """Дописывает строки в журнал; заголовок пишется только в новый файл."""
    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerows(rows)


def main():
    count = read_int("Количество замеров N = ")
    period = read_int("Период опроса, с = ")

    for i in range(count):
        temp = read_cpu_temp()
        status = classify(temp)
        row = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "temp_c": temp,
            "status": status,
        }
        append_rows([row])
        print(f"{i + 1}: {temp:.1f} °C, {status}")
        if i < count - 1:
            time.sleep(period)

    print(f"Записано строк: {count} в {LOG_PATH}")


main()