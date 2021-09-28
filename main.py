from tkinter import *
from tkinter import messagebox
import pyautogui
import pygetwindow as gw
import time
import cv2
import pytesseract
import numpy as np
import re
import shutil
import os
import sys

# 180, 330 portrait
# 180, 115


main = Tk()


def get_greyscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def remove_noise(img):
    return cv2.medianBlur(img, 5)


def thresholding(img):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def dilate(img):
    kernel = np.ones((5,5), np.uint8)
    return cv2.dilate(img, kernel, iterations=1)


def erode(img):
    kernel = np.ones((5,5), np.uint8)
    return cv2.erode(img, kernel, iterations=1)


def opening(img):
    kernel = np.ones((5,5), np.uint8)
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)


def canny(img):
    return cv2.Canny(img, 100, 200)


def deskew(img):
    cords = np.column_stack(np.where(img > 0))
    angle = cv2.minAreaRect(cords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    center = (w//2, h//2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def match_template(img, template):
    return cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)


def process_image(img):
    gray = get_greyscale(img)
    return thresholding(gray)


def process_images_clicked():
    sheet_data = sheet_input.get("1.0", "end-1c")
    result = {}
    changes = {}
    missing_ids = []
    ig_ids = []
    for line in sheet_data.splitlines():
        split = line.split("\t")
        result[split[0]] = int(split[1])

    print(result.keys())
    print(result.values())

    for uid in os.listdir("screenshots"):
        ig_ids.append(uid)
        if uid not in result:
            missing_ids.append(uid)
            continue

        img = cv2.imread(f"screenshots/{uid}/profile_lvl.png")
        img = process_image(img)
        d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=r"--psm 13 outputbase digits")
        print(f"screenshots/{uid}/profile_lvl.png", d["text"], d["conf"])

        level_pattern = "\d{2}"
        n_boxes = len(d["text"])
        level = 0
        for j in range(n_boxes):
            text = d["text"][j]
            if re.match(level_pattern, text) and float(d["conf"][j]) > 90.0:
                level = int(text)

        print(result[uid], level)
        if result[uid] != level and level > result[uid]:
            changes[uid] = (result[uid], level)
            result[uid] = level

    sheet_output.delete("1.0", "end")
    for value in result.values():
        sheet_output.insert(END, f"{value}\n")

    sheet_changes.delete("1.0", END)
    for key, (oldLevel, newLevel) in changes.items():
        sheet_changes.insert(END, f"{key}\t{oldLevel} => {key}\t{newLevel}\n")

    print("The following uids are not present in-game", (set(result.keys()).difference(ig_ids)))

    print("The following uids are not on the sheet", (set(ig_ids).difference(result.keys())))


def capture_clicked():
    shutil.rmtree("screenshots")
    os.mkdir("screenshots")
    member_count = int(member_count_input.get())
    honkai = gw.getWindowsWithTitle("Honkai Impact 3")[0]
    honkai.activate()

    copy_uid_x = 1020
    copy_uid_y = 200
    lvl_screenshot_x = 353
    for i in range(member_count):
        profile_x = 180
        profile_y = 330
        movement_y = -240

        if member_count - 1 - i == 3:
            profile_y = 410

        if member_count - 1 - i == 2:
            profile_y = 625

        if member_count - 1 - i == 1:
            profile_y = 840

        pyautogui.moveTo(profile_x, profile_y)
        pyautogui.click()
        time.sleep(0.5)

        pyautogui.moveTo(copy_uid_x, copy_uid_y)
        pyautogui.click()

        uid = main.clipboard_get()
        os.mkdir(f"screenshots/{uid}")

        pyautogui.screenshot(f"screenshots/{uid}/profile.png", region=(675, 110, 600, 125))

        pyautogui.moveTo(1, 1)
        pyautogui.click()
        pyautogui.click()

        pyautogui.screenshot(f"screenshots/{uid}/profile_lvl.png", region=(lvl_screenshot_x, profile_y + 25, 47, 40))

        pyautogui.moveTo(profile_x, profile_y)
        pyautogui.mouseDown()
        pyautogui.moveTo(profile_x, profile_y + movement_y, 0.5)
        time.sleep(0.5)
        pyautogui.mouseUp()


member_count_input = Entry(main)
member_count_input.pack()
capture_button = Button(main, text="Start Capture", command=capture_clicked)
capture_button.pack()
process_images_button = Button(main, text="Process Images", command=process_images_clicked)
process_images_button.pack()
sheet_input = Text(main)
sheet_input.pack()

sheet_output = Text(main)
sheet_output.pack()

sheet_changes = Text(main)
sheet_changes.pack()

main.mainloop()