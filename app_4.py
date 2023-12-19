from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from threading import Thread
import time
import random  # Для генерации случайных данных

app = Flask(__name__)

# Данные для графика напряжения
voltage_data = {
    'labels': [],
    'values': [],
}

# Данные для графика тока
current_data = {
    'labels': [],
    'values': [],
}

# Путь к видеофайлу
video_path = 'kyb.mp4'

# Определение области интереса (ROI)
roi_x, roi_y, roi_width, roi_height = 390, 340, 100, 150
roi_end_x, roi_end_y = roi_x + roi_width, roi_y + roi_height

# Порог для определения, горит ли буква (вы можете настроить)
red_threshold = 100  # Уменьшьте значение, если требуется более строгий красный

# Флаг статуса горения буквы
is_letter_on = False

# Функция для обработки изображения и определения статуса вывески
def detect_letters():
    global is_letter_on
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Определение области с буквой "Д"
        roi = frame[roi_y:roi_end_y, roi_x:roi_end_x]

        # Определение, горит ли буква "Д"
        new_letter_on = np.mean(roi[:, :, 2]) > red_threshold

        # Если статус горения буквы изменился, обновляем глобальную переменную
        if new_letter_on != is_letter_on:
            is_letter_on = new_letter_on

        # Отображение статуса горения буквы
        status = "YES, TRUE" if is_letter_on else "4 positions, D, FALSE"
        cv2.putText(frame, f"Status: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Преобразование кадра в формат JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

        # Генерация случайных данных для графиков
        if len(current_data['labels']) < 60:
            current_data['labels'].append(len(current_data['labels']) + 1)
            voltage_data['labels'].append(len(voltage_data['labels']) + 1)
            # Имитация падения данных через 10 секунд
            if len(current_data['labels']) > 10:
                current_data['values'].append(random.uniform(0, 2))
                voltage_data['values'].append(random.uniform(200, 220))
            else:
                current_data['values'].append(2)
                voltage_data['values'].append(220)
        else:
            current_data['labels'].pop(0)
            voltage_data['labels'].pop(0)
            current_data['values'].pop(0)
            voltage_data['values'].pop(0)

    cap.release()

# Сценарий для графика тока
def current_scenario():
    pass  # Ваш текущий сценарий, если нужен

# Сценарий для графика напряжения
def voltage_scenario():
    pass  # Ваш текущий сценарий, если нужен

# Функция для генерации данных для графиков
def generate_chart_data():
    global voltage_data, current_data
    while True:
        yield {
            'current_labels': current_data['labels'],
            'current_values': current_data['values'],
            'voltage_labels': voltage_data['labels'],
            'voltage_values': voltage_data['values'],
        }
        time.sleep(1)

# Запуск потока обработки изображения
video_thread = Thread(target=detect_letters)
video_thread.start()

# Запуск сценариев в отдельных потоках
current_thread = Thread(target=current_scenario)
voltage_thread = Thread(target=voltage_scenario)
current_thread.start()
voltage_thread.start()

# Генерация данных для графиков
chart_data_generator = generate_chart_data()

# Маршруты Flask
@app.route('/')
def index():
    return render_template('index_with_charts.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_letters(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/status')
def video_status():
    global is_letter_on
    return 'The sign is lit' if is_letter_on else 'the letter d went out in 4 positions'

@app.route('/chart_data')
def chart_data():
    return jsonify(next(chart_data_generator))

if __name__ == '__main__':
    app.run(host='192.168.56.1', port=5000, debug=True)