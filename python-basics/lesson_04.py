above_average = 0
powers = []


number_of_measurements = int(input("Введите количество замеров N = "))

for _ in range(number_of_measurements):
    voltage = float(input("Введите значение напряжения (В): "))
    current = float(input("Введите значение тока (А): "))
    power = voltage * current
    powers.append(power)

if len(powers) > 0:
    mean_power = sum(powers)/len(powers)
    peak = max(powers)
    for value in powers:
        print(f"{value} Вт")        
        if value > mean_power:
            above_average += 1

    print(f"Средняя мощность за серию {mean_power} Вт")

    print(f"Максимальная мощность за серию {peak} Вт, максимальный замер по счету {powers.index(peak)+1}")

    print(f"Итог: из {number_of_measurements} замеров выше средней {above_average}")

else:
    print("Замеров не было")
