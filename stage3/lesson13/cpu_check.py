import time

THERMAL_PATH = "/sys/class/thermal/thermal_zone0/temp"
WARN_C = 60.0
ALARM_C = 75.0


def read_int(prompt, min_value=1):
    """Запрашивает целое число не меньше min_value, пока ввод не станет корректным."""
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Некорректный ввод. Нужно целое число.")
            continue
        if value < min_value:
            print(f"Нужно число не меньше {min_value}. Получено {value}")
            continue
        return value


def read_cpu_temp():
    """Температура процессора, °C. Ядро отдаёт миллиградусы."""
    with open(THERMAL_PATH) as f:
        raw = f.read()
    return int(raw) / 1000


def classify(temp, warn=WARN_C, alarm=ALARM_C):
    """Статус по порогам: норма / предупреждение / авария."""
    if temp >= alarm:
        return "авария"
    if temp >= warn:
        return "предупреждение"
    return "норма"


def summarize(values):
    """Минимум, среднее, максимум серии."""
    return min(values), sum(values) / len(values), max(values)


def main():
    count = read_int("Количество замеров N = ")
    period = read_int("Период опроса, с = ")

    temps = []
    for i in range(count):
        temp = read_cpu_temp()
        temps.append(temp)
        print(f"{i + 1}: {temp:.1f} °C, {classify(temp)}")
        if i < count - 1:
            time.sleep(period)

    t_min, t_mean, t_max = summarize(temps)
    print(f"Мин {t_min:.1f}, средн {t_mean:.1f}, макс {t_max:.1f} °C")
    print(f"Итог по максимуму: {classify(t_max)}")


main()