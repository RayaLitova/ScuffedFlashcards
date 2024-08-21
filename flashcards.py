from pypdf import PdfWriter, PdfReader
import pdfplumber
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import os.path as path
import os
import random
import json
from datetime import date

def select_input_file():
    currdir = os.getcwd()
    tempdir = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select a file')
    filename = os.path.basename(tempdir)
    if len(tempdir) > 0:
        print ("You chose: %s" % filename)
    return os.path.basename(filename)

def save_progress():
    if page_number % 2 == 0:
        available["Unprocessed"].append(page_number)
    date_json = json.dumps(str(date.today()))
    data_json = json.dumps(data)
    available_json = json.dumps(available)
    with open(json_data_filename, "w") as outfile:
        outfile.write(date_json + '\n')
        outfile.write(data_json + '\n')
        outfile.write(available_json)

def load_progress():
    if not path.isfile(json_data_filename):
        return
    global saved_date, data, available
    with open(json_data_filename, 'r') as handle:
        json_data = [json.loads(line) for line in handle]
        saved_date = json_data[0]
        data = json_data[1]
        if saved_date == str(date.today()):
            available = json_data[2]
        else:
            available = data

def generate_cards(pdf_path, output_file):
    unprocessed = len(data["Hard"]) == 0 and len(data["Medium"]) == 0 and len(data["Easy"]) == 0
    with open(pdf_path, "rb") as in_f:
        reader = PdfReader(in_f)
        writer = PdfWriter()

        global page_count
        page_count = len(reader.pages)
        
        for i in range(page_count):
            if unprocessed and i%2 == 0:
                data["Unprocessed"].append(i)
                available["Unprocessed"].append(i)
            page = reader.get_page(i)
            right = page.mediabox.right
            top = page.mediabox.top
            for i in range(4):
                page.mediabox.lower_left = (
                    (right / 2) + (i % 2) * (right / 2),
                    (top / 2) + (0 if i < 2 else 1) * (top / 2),
                )
                page.mediabox.upper_right = (
                    (i % 2) * (right / 2),
                    (0 if i < 2 else 1) * (top / 2),
                )
                writer.add_page(page)

        with open(output_file, "wb") as out_f:
            writer.write(out_f)


root = tk.Tk()

def get_page_image(path):
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[page_number]
        image = page.to_image()

        pil_image = image.original
        resized_image= pil_image.resize((int(page.width) * 2, int(page.height) * 2))
        tk_image = ImageTk.PhotoImage(resized_image)
        return tk_image

def show_answer():
    for widget in root.winfo_children():
        widget.destroy()
    global page_number
    page_number += 1
    show_pdf_page(output_file, False)

def set_question_level(level):
    data[level].append(page_number - 1)
    if page_number - 1 in data["Unprocessed"]:
        data["Unprocessed"].remove(page_number - 1)

def select_next_question():
    global page_number, available, data
    if len(available["Unprocessed"]) > 0:
        page_number = random.choice(available["Unprocessed"])
        available["Unprocessed"].remove(page_number)
        return
    level = ["Hard"] * 100 * len(available["Hard"]) + ["Medium"] * 60 * len(available["Medium"]) + ["Easy"] * 15 * len(available["Easy"])
    level = random.choice(level)
    if len(available["Hard"]) == 0 and len(available["Medium"]) == 0 and len(available["Easy"]) == 0 and len(available["Unprocessed"]) == 0:
        available = data
    page_number = random.choice(available[level])
    available[level].remove(page_number)

def show_question(level):
    set_question_level(level)
    for widget in root.winfo_children():
        widget.destroy()
    select_next_question()
    show_pdf_page(output_file, True)

def on_closing():
    save_progress()
    root.destroy()

def show_pdf_page(pdf_path, is_question):
    tk_image = get_page_image(pdf_path)
    label = tk.Label(root, image=tk_image)
    label.pack()
    if is_question:
        button = tk.Button(root, text= "Show answer", command = show_answer)
        button.pack(padx=20, pady=20)
    else:
        button1 = tk.Button(root, text= "Hard", command = lambda: show_question("Hard"))
        button2 = tk.Button(root, text= "Medium", command = lambda: show_question("Medium"))
        button3 = tk.Button(root, text= "Easy", command = lambda: show_question("Easy"))
        button1.pack(side='left')
        button3.pack(side='right')
        button2.pack(side='top')
    
    root.protocol("WM_DELETE_WINDOW", on_closing)   
    root.mainloop()

data = {"Hard": [],
        "Medium": [],
        "Easy": [],
        "Unprocessed": []}

available = {"Hard": [],
            "Medium": [],
            "Easy": [],
            "Unprocessed": []}

input_file = select_input_file()
output_file = input_file[:-4] + "_output.pdf"
json_data_filename = input_file[:-4] + "_data.json"

page_number = 0
page_count = 0
saved_date = False

generate_cards(input_file, output_file)
load_progress()
select_next_question()
show_pdf_page(output_file, True)



