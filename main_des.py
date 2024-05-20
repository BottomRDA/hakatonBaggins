import tkinter as tk
from tkinter import scrolledtext, ttk
import Pmw
from google.oauth2 import service_account
import googleapiclient.discovery
from datetime import datetime, timedelta, timezone

# Название json-файла с учетными данными сервиса
KEY_FILE_NAME = 'bagginscoffeehakaton-45c797388a24.json'

# Для доступа к API Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_EMAIL = 'sillitimsuai@bagginscoffeehakaton.iam.gserviceaccount.com'
ACCOUNT_EMAIL = 'sillitimsuai@gmail.com'

def create_service():
    creds = service_account.Credentials.from_service_account_file(KEY_FILE_NAME, scopes=SCOPES)
    service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
    return service

def list_files(service, text_widget):
    results = service.files().list(fields='files(id, name, createdTime, owners)').execute()
    items = results.get('files', [])

    text_widget.delete(1.0, tk.END)

    if not items:
        text_widget.insert(tk.END, 'Файлы не найдены.\n')
    else:
        text_widget.insert(tk.END, 'Файлы с непереданными правами:\n')
        for item in items:
            file_created_time = datetime.strptime(item['createdTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            file_created_time = file_created_time.replace(tzinfo=timezone.utc)
            formatted_time = file_created_time.strftime('%d-%m-%Y %H:%M:%S')
            if item['owners'][0]['emailAddress'] != SERVICE_ACCOUNT_EMAIL and item['owners'][0]['emailAddress'] != ACCOUNT_EMAIL and (
                    datetime.now(timezone.utc) - file_created_time) > timedelta(days=7):
                text_widget.insert(tk.END, u'"{0}" - создан {1}.\n Владелец: {2}\n'.format(
                    item['name'], formatted_time, item['owners'][0]['displayName']))

def get_folder_id(service, folder_name):
    results = service.files().list(q=f"name='{folder_name}'", fields='files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        return None
    else:
        return items[0]['id']

def check_ownership(service, folder_id, owner_email, text_widget):
    query = f'\'{folder_id}\' in parents'
    results = service.files().list(q=query, fields='files(id, name, owners)').execute()
    items = results.get('files', [])

    for item in items:
        if item['owners'][0]['emailAddress'] == owner_email:
            text_widget.insert(tk.END, f'Создание копии файла  {item["name"]}. \nВладелец оригинала: {owner_email}\n\n')
            copy_file(service, item['id'], item['name'], text_widget)

def copy_file(service, file_id, file_name, text_widget):
    copied_file = {'name': f'{file_name}'}
    try:
        service.files().copy(fileId=file_id, body=copied_file).execute()
        text_widget.insert(tk.END, f'Успешно скопирован файл {file_name}\n\n')
    except Exception as e:
        text_widget.insert(tk.END, f'Произошла ошибка: {e}\n\n')

def on_list_files_button_click(text_widget):
    service = create_service()
    list_files(service, text_widget)

def on_check_ownership_button_click(folder_name_entry, owner_email_entry, text_widget):
    folder_name = folder_name_entry.get()
    owner_email = owner_email_entry.get()
    if not folder_name or not owner_email:
        text_widget.insert(tk.END, 'Пожалуйста, заполните оба поля.\n')
        return
    service = create_service()
    folder_id = get_folder_id(service, folder_name)
    if folder_id:
        check_ownership(service, folder_id, owner_email, text_widget)
    else:
        text_widget.insert(tk.END, 'Папка не найдена.\n')

# Создаем главное окно
root = tk.Tk()
root.title("Google Drive File Manager")

# Цвета для тёмной темы
bg_color = "#131313"  # Цвет фона
fg_color = "#ffffff"  # Цвет текста
btn_color = "#8B0000"  # Цвет кнопок
scroll_bg_color = "#ffffff"  # Цвет фона поля с прокруткой
btn_t_color = "#ffffff" # Цвет текста кнопок

# Задаем цвета фона и текста для всех виджетов
root.configure(bg=bg_color)
root.option_add('*background', bg_color)
root.option_add('*foreground', fg_color)

# Создаем стиль для ttk элементов
style = ttk.Style()
style.theme_use('clam')  # Используем стиль из темы "clam"

# Создаем стиль для кнопок
style.configure('Rounded.TButton', background=btn_color, foreground=btn_t_color, font=('Arial', 10), relief=tk.FLAT, borderwidth=0, padding=5, border='5', bordercolor='black')
style.map('Rounded.TButton', background=[('active', btn_color)], foreground=[('active', fg_color)])

# Создаем рамки для разделения зон
highlight_thickness = 1

left_frame = tk.Frame(root, bg=bg_color, borderwidth=1, highlightbackground="white", highlightthickness=highlight_thickness)
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

right_frame = tk.Frame(root, bg=bg_color, borderwidth=1, highlightbackground="white", highlightthickness=highlight_thickness)
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")


# Создаем текстовое поле с прокруткой для отображения результатов
text_area = scrolledtext.ScrolledText(left_frame, width=50, height=20, font=('Arial', 10), bg=scroll_bg_color, fg=bg_color)
text_area.pack(padx=10, pady=10)

# Создаем кнопку для запуска функции list_files с использованием ttk
list_files_button = ttk.Button(left_frame, text="Показать файлы с непереданными правами", style='Rounded.TButton', command=lambda: on_list_files_button_click(text_area))
list_files_button.pack(pady=10)

# Создаем метки для полей ввода
folder_name_label = tk.Label(right_frame, text="Имя папки:", bg=bg_color, fg=fg_color)
folder_name_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
owner_email_label = tk.Label(right_frame, text="Email сотрудника:", bg=bg_color, fg=fg_color)
owner_email_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")

# Создаем поля для ввода с использованием ttk
folder_name_entry = ttk.Entry(right_frame, width=30, style='TEntry')
folder_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
owner_email_entry = ttk.Entry(right_frame, width=30, style='TEntry')
owner_email_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Создаем кнопку для проверки владения и копирования файлов с использованием ttk
check_ownership_button = ttk.Button(right_frame, text="Скопировать файлы сотрудника", style='Rounded.TButton', command=lambda: on_check_ownership_button_click(folder_name_entry, owner_email_entry, text_area))
check_ownership_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="we")  # Изменено значение columnspan

from PIL import Image, ImageTk  # Импортируем необходимые модули для работы с изображениями

# Создаем изображение
image = Image.open("logow.png")
image = image.resize((100, 100))  # Масштабируем изображение по необходимым размерам
tk_image = ImageTk.PhotoImage(image)  # Создаем объект PhotoImage

# Создаем пустой виджет для отступа вверху
top_spacer = tk.Frame(right_frame, bg=bg_color)
top_spacer.grid(row=0, column=0, pady=10)  # Отступ сверху

# Создаем метку с изображением и размещаем ее вверху по центру
image_label = tk.Label(right_frame, image=tk_image, bg=bg_color)
image_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5)  # Картинка вверху

# Создаем пустые виджеты для выравнивания элементов по центру
middle_spacer1 = tk.Frame(right_frame, bg=bg_color)
middle_spacer1.grid(row=2, column=0, pady=5)  # Отступ для центрирования

# Создаем метки и поля для ввода, выравнивая их по центру
folder_name_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
owner_email_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
folder_name_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
owner_email_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

# Создаем пустой виджет для выравнивания элементов по центру
middle_spacer2 = tk.Frame(right_frame, bg=bg_color)
middle_spacer2.grid(row=5, column=0, pady=5)  # Отступ для центрирования

# Размещаем кнопку по центру внизу
check_ownership_button.grid(row=6, column=0, columnspan=2, padx=5, pady=10, sticky="we")


# Запускаем главный цикл обработки событий Tkinter
root.mainloop()