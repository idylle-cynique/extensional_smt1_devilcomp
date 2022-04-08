
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox


# 自作プログラム群
import windowsystems as ws
import devilsfusionsystem as dfs


class MainSystem:
    def __init__(self):
        '''一連の合体システムに関するモジュールを準備しておく'''
        self.startmenu = ws.StartMenu()

    def startup(self):
        self.startmenu.startup()
    

def main():
    root = MainSystem()
    root.startup()
    pass

if __name__ == "__main__":
    main()