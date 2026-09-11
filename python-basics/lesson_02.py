# вход:
voltage = float(input("Введите значение напряжения (В): "))
current = float(input("Введите значение тока (А): "))

# обработка:
power = voltage * current

# выход:
print(f"Результат расчета мощности: {power} Вт")

if power < 2500:
    print("В норме")
elif 3000 >= power >= 2500:
    print("Близко к пределу")
else:
    print("Превышение")
 