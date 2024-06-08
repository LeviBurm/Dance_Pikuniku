import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from pynput.keyboard import Key, Controller
from PIL import ImageGrab
import time
import pyautogui
import threading
import traceback

# Загрузка образцов изображений и их соответствующих клавиш
images = {
    'up': (cv2.imread('up.png', cv2.IMREAD_GRAYSCALE), Key.up),
    'down': (cv2.imread('down.png', cv2.IMREAD_GRAYSCALE), Key.down),
    'left': (cv2.imread('left.png', cv2.IMREAD_GRAYSCALE), Key.left),
    'right': (cv2.imread('right.png', cv2.IMREAD_GRAYSCALE), Key.right)
}

keyboard = Controller()

# Проверка загрузки изображений и их размеров
for direction, (template, key) in images.items():
    if template is None:
        print(f"Error loading template for {direction}. Make sure the file exists and is an image.")
    else:
        print(f"{direction} template size: {template.shape}")

# Глобальная переменная для хранения координат
scan_area = (875, 880, 1093, 1040)  # Значение по умолчанию

# Создание окна
root = tk.Tk()

def show_error(message):
    error_window = tk.Toplevel(root)
    error_window.title("Ошибка")
    
    text_area = tk.Text(error_window, wrap='word', width=80, height=20)
    text_area.pack(padx=20, pady=20)
    text_area.insert(tk.END, message)
    text_area.config(state=tk.DISABLED)  # Запрещаем редактирование текста

    ok_button = tk.Button(error_window, text="OK", command=error_window.destroy)
    ok_button.pack(pady=10)

# Функция для выбора области захвата изображения
def select_area():
    global scan_area
    area_root = tk.Toplevel(root)  # Создаем дочернее окно
    area_root.title("Select Area")

    global cursor_position_label, coordinates_label  # Используем global здесь
    cursor_position_label = tk.Label(area_root, text="Координаты курсора: (0, 0)")
    cursor_position_label.pack()

    update_coordinates_button = tk.Button(area_root, text="Посмотреть координаты курсора в реальном времени", command=update_coordinates)
    update_coordinates_button.pack()

    coordinates_label = tk.Label(area_root, text="Координаты курсора: (0, 0) to (0, 0)")
    coordinates_label.pack()

    x1_entry_label = tk.Label(area_root, text="X1:")
    x1_entry_label.pack(side=tk.LEFT)
    x1_entry = tk.Entry(area_root)
    x1_entry.pack(side=tk.LEFT)
    x1_entry.insert(0, str(scan_area[0]))  # Устанавливаем текущее значение по умолчанию

    y1_entry_label = tk.Label(area_root, text="Y1:")
    y1_entry_label.pack(side=tk.LEFT)
    y1_entry = tk.Entry(area_root)
    y1_entry.pack(side=tk.LEFT)
    y1_entry.insert(0, str(scan_area[1]))  # Устанавливаем текущее значение по умолчанию

    x2_entry_label = tk.Label(area_root, text="X2:")
    x2_entry_label.pack(side=tk.LEFT)
    x2_entry = tk.Entry(area_root)
    x2_entry.pack(side=tk.LEFT)
    x2_entry.insert(0, str(scan_area[2]))  # Устанавливаем текущее значение по умолчанию

    y2_entry_label = tk.Label(area_root, text="Y2:")
    y2_entry_label.pack(side=tk.LEFT)
    y2_entry = tk.Entry(area_root)
    y2_entry.pack(side=tk.LEFT)
    y2_entry.insert(0, str(scan_area[3]))  # Устанавливаем текущее значение по умолчанию

    def set_coordinates():
        global scan_area
        try:
            x1 = int(x1_entry.get())
            y1 = int(y1_entry.get())
            x2 = int(x2_entry.get())
            y2 = int(y2_entry.get())
            scan_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            coordinates_label.config(text=f"Координаты курсора: ({x1}, {y1}) to ({x2}, {y2})")
            area_root.after(1200, area_root.destroy)  # Закрываем окно через 2 секунды после установки координат
        except ValueError:
            coordinates_label.config(text="Ошибка: Введите корректные целые числа.")

    set_coordinates_button = tk.Button(area_root, text="Сохранить координаты", command=set_coordinates)
    set_coordinates_button.pack()

    area_root.mainloop()

# Функция для обновления координат курсора
def update_coordinates():
    try:
        global cursor_position_label
        cursor_x, cursor_y = pyautogui.position()
        cursor_position_label.config(text=f"Координаты курсора: ({cursor_x}, {cursor_y})")
        cursor_position_label.after(100, update_coordinates)  # Обновляем координаты каждые 100 миллисекунд
    except Exception as e:
        show_error(f"Ошибка при обновлении координат: {e}\n{traceback.format_exc()}")

# Функция для отображения изображения в реальном времени
def show_realtime_area():
    try:
        if scan_area:
            start_time = time.time()
            while True:
                # Захват экрана в указанной области
                screen = np.array(ImageGrab.grab(bbox=scan_area))
                # Получение координат курсора
                cursor_x, cursor_y = pyautogui.position()
                # Рисование курсора на изображении
                cv2.circle(screen, (cursor_x - scan_area[0], cursor_y - scan_area[1]), 5, (0, 255, 0), -1)  # Рисуем зеленый круг вокруг курсора
                cv2.imshow("Realtime Area", cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
                # Ожидание нажатия клавиши 'q' для выхода или завершение через 6 секунд
                if cv2.waitKey(1) & 0xFF == ord('q') or time.time() - start_time > 6:
                    break
                
            cv2.destroyAllWindows()
        else:
            print("Область захвата не выбрана.")
    except Exception as e:
        show_error(f"Ошибка в show_realtime_area: {e}\n{traceback.format_exc()}")

# Глобальная переменная-флаг для управления потоком
running = False

# Функция для детекции и нажатия клавиш
# Функция для детекции и нажатия клавиш
def detect_and_press():
    try:
        global running
        running = True
        while running:
            # Захват экрана в указанной области
            screen = np.array(ImageGrab.grab(bbox=scan_area))
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)  # Преобразование в черно-белый формат
            
            screen_height, screen_width = screen_gray.shape

            for direction, (template, key) in images.items():
                template_height, template_width = template.shape

                # Проверяем, что размеры шаблона меньше или равны размерам захваченной области
                if template_height <= screen_height and template_width <= screen_width:
                    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    # Уровень уверенности для обнаружения шаблона
                    threshold = 0.8

                    if max_val >= threshold:
                        print(f"Detected {direction} with confidence {max_val}")
                        keyboard.press(key)
                        keyboard.release(key)
                        break
                else:
                    print(f"Template size is larger than screen area for {direction}. Skipping this template.")
            
            time.sleep(0.07)  # Добавляем задержку, чтобы не нагружать процессор
        
        print("Thread stopped.")
    except Exception as e:
        show_error(f"Ошибка в detect_and_press: {e}\n{traceback.format_exc()}")

# Функция для запуска кода
def start():
    try:
        print("Start button pressed")
        thread = threading.Thread(target=detect_and_press)
        thread.start()
    except Exception as e:
        show_error(f"Ошибка при запуске: {e}\n{traceback.format_exc()}")

# Функция для остановки кода
def stop():
    global running
    running = False

# Кнопки
button_select_area = tk.Button(root, text="Область захвата", command=select_area)
button_start = tk.Button(root, text="Запустить", command=start)
button_stop = tk.Button(root, text="Остановить", command=stop)
button_show_area = tk.Button(root, text="Посмотреть область захвата", command=show_realtime_area)

# Размещение кнопок на окне
button_select_area.pack()
button_start.pack()
button_stop.pack()
button_show_area.pack()

# Увеличиваем размер окна, чтобы оно не было слишком маленьким
root.geometry("400x200")

# Корректное завершение работы приложения
def on_closing():
    global running
    running = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()