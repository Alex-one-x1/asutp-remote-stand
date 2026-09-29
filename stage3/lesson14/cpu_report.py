import csv

from standlib import LOG_PATH, classify, summarize


def load_temps():
    """Температуры из журнала списком чисел."""
    temps = []
    with open(LOG_PATH, newline="") as f:
        for row in csv.DictReader(f):
            temps.append(float(row["temp_c"]))
    return temps


def main():
    if not LOG_PATH.exists():
        print(f"Журнала нет: {LOG_PATH}")
        return

    temps = load_temps()
    t_min, t_mean, t_max = summarize(temps)
    print(f"Замеров в журнале: {len(temps)}")
    print(f"Мин {t_min:.1f}, средн {t_mean:.1f}, макс {t_max:.1f} °C")
    print(f"Итог по максимуму: {classify(t_max)}")


main()