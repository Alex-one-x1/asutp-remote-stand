excess_counter = 0
max_power = 0

number_of_measurements = int(input("Введите количество замеров N = "))

for _ in range(number_of_measurements):
    voltage = float(input("Введите значение напряжения (В): "))
    current = float(input("Введите значение тока (А): "))
    power = voltage * current
    print(f"Результат расчета мощности: {power} Вт")
    max_power = max(max_power, power)
    
    if power > 3000:
        excess_counter += 1
        
        
print(f"Итог: из {number_of_measurements} замеров предел превышен в {excess_counter}")
print(f"Максимальная мощность за серию = {max_power} Вт")
