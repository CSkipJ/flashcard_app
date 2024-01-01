import tkinter as tk
from tkinter import ttk


def function1():
    print("function1")


def function2():
    print("function2")


class RootWindow:
    def __init__(self, **funcs):

        print(funcs)
        # Settings and stuff go here
        self.funcs = funcs
        self.funcs = {
            'function1': function1,
            'function2': function2
        }

        self.root_window = tk.Tk()
        self.root_window.title("Flash Card")
        self.root_window.geometry('400x400')
        print('init')

    def __enter__(self):
        # I think actions and functions to be used need to go here
        self.funcs['on_button_click'] = self.on_button_click
        welcome_page = WelcomePage(self.root_window, **self.funcs)
        print('enter')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exit')
        self.root_window.mainloop()

    def on_button_click(self):
        for widget in self.root_window.winfo_children():
            widget.destroy()

        main_menu = MainMenu(self.root_window)


class WelcomePage:
    def __init__(self, root_window, **funcs):
        self.function1 = funcs.get('function1')

        self.root = root_window

        tk_label = tk.Label(self.root, text='tk_label')
        tk_label.pack()

        ttk_label = ttk.Label(self.root, text='ttk_label')
        ttk_label.pack()

        if funcs.get('on_button_click'):
            print('on_button_click passed if condition')
            some_func = funcs['on_button_click']
        else:
            some_func = funcs['function1']

        test_btn = tk.Button(text='test function', command=some_func)
        test_btn.pack()

    def test_btn(self):
        print('You pressed a button.')


class MainMenu:
    def __init__(self, root_window, **funcs):
        self.root = root_window
        self.root.title("Main Menu")

        label = tk.Label(self.root, text="Main Menu")
        label.pack()





