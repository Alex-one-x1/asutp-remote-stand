print("Количество замеров должно быть больше или равно 1 и должно быть целым числом")
while True:
    try:
        number_of_measurements = int(input("Введите количество замеров N = "))
        if number_of_measurements < 1:
            print(f"Нужно целое число больше или равно 1. Получено {number_of_measurements}")
            continue
        else:
            break
    except ValueError:
        print("Некорректный ввод. Введите заново.")

print(f"Ввод корректный. Получено число замеров {number_of_measurements}")
