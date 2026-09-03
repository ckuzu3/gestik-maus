"""Systemlautstärke über die Standard-Medientasten von Windows steuern."""

import pyautogui


class VolumeController:
    def step_up(self):
        pyautogui.press("volumeup")

    def step_down(self):
        pyautogui.press("volumedown")
