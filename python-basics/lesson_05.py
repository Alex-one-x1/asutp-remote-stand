journal = []
sum_power = 0
peak_record_dict = None

number_of_measurements = int(input("Введите количество замеров N = "))

if number_of_measurements > 0:
    
    for _ in range(number_of_measurements):
        voltage = float(input("Введите значение напряжения (В): "))
        current = float(input("Введите значение тока (А): "))
        power = voltage * current
        journal.append({"voltage":voltage, "current":current, "power":power})

    for entry in journal:
        print(f'{entry["voltage"]} В х {entry["current"]} А = {entry["power"]} Вт')
        sum_power += entry["power"]
        if peak_record_dict is None or entry["power"] > peak_record_dict["power"]:
            peak_record_dict = entry
        
    mean_power = sum_power/len(journal)

    print(f'Средняя мощность по журналу = {mean_power} Вт')
    print(f'Максимальный замер: напряжение {peak_record_dict["voltage"]} В, '
          f'ток {peak_record_dict["current"]} А, мощность {peak_record_dict["power"]} Вт')
    
else:
    print("Замеров не было")
