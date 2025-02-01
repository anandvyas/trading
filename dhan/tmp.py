import ttkbootstrap as ttk
from ttkbootstrap.constants import *

root = ttk.Window()

b1 = ttk.Button(root, text='primary', bootstyle=PRIMARY)
b1.pack(side=LEFT, padx=5, pady=5)

b2 = ttk.Button(root, text='secondary', bootstyle=SECONDARY)
b2.pack(side=LEFT, padx=5, pady=5)

b3 = ttk.Button(root, text='success', bootstyle=SUCCESS)
b3.pack(side=LEFT, padx=5, pady=5)

b4 = ttk.Button(root, text='info', bootstyle=INFO)
b4.pack(side=LEFT, padx=5, pady=5)

b5 = ttk.Button(root, text='warning', bootstyle=WARNING)
b5.pack(side=LEFT, padx=5, pady=5)

b6 = ttk.Button(root, text='danger', bootstyle=DANGER)
b6.pack(side=LEFT, padx=5, pady=5)

b7 = ttk.Button(root, text='light', bootstyle=LIGHT)
b7.pack(side=LEFT, padx=5, pady=5)

b8 = ttk.Button(root, text='dark', bootstyle=DARK)
b8.pack(side=LEFT, padx=5, pady=5)

root.mainloop()



# # importing tkinter module and Widgets
# from tkinter import Tk

# # from tkinter.font import BOLD, Font
# # from tkinter.ttk import Label, Button
  
  
# # Creating App class which will contain
# # Label Widgets
# class App:
#     def __init__(self, master) -> None:
  
#         # Instantiating master i.e toplevel Widget
#         self.master = master
  
#         # Creating first Label i.e with default font-size
#         Label(self.master, text="I have default font-size").pack(pady=20)
  
#         # Creating second label
#         # This label has a font-family of Arial
#         # and font-size of 25
#         Label(self.master,
#               text="I have a font-size of 25",
  
#               # Changing font-size here
#               font=(25)
#               ).pack()
        
#         # Creating Font, with a "size of 25" and weight of BOLD
#         self.bold25 = Font(self.master, size=25, weight=BOLD)

#         Label(self.master, text="I have a font-size of 25",
#               font=self.bold25).pack()
        
#         Label(self.master, text="This is a sample line with font size 15.",  font=('Times New Roman', 15, 'bold')).pack()
  
# if __name__ == "__main__":
  
#     # Instantiating top level
#     root = Tk()
  
#     # Setting the title of the window
#     root.title("Option Scalping v0.1")
  
#     # Setting the geometry i.e Dimensions
#     root.geometry("800x900")
#     root.configure(bg="#333333")
  
#     # Calling our App
#     app = App(root)
  
#     # Mainloop which will cause this toplevel
#     # to run infinitely
#     root.mainloop()


# # #importing modules
# # from tkinter import *
# # from tkinter import ttk

# # window = Tk()
# # window.geometry('800x900')
# # window.title("")
# # window.configure(bg="#333333")
# # window.resizable(False, False)

# # frame = Frame(window, bg="#333333")
# # frame.pack()

# # global_setting_frame = LabelFrame(frame, text="Global Setting", bg="#333333", fg="#FFFFFF", font=("Arial", 30))
# # global_setting_frame.grid(row=0, column=0, padx=20, pady=20)

# # budget = Label(global_setting_frame, text="Option Buying Budget", bg="#333333", fg="#FFFFFF", font=("Arial", 30))
# # budget.grid(row=0, column=0)
# # budget_input = Entry(global_setting_frame)
# # budget_input.grid(row=0, column=1)


# # # maxLoss = Label(global_setting_frame, text="Max Loss")
# # # maxLoss.grid(row=0, column=2)
# # # maxLoss_input = Entry(global_setting_frame)
# # # maxLoss_input.grid(row=0, column=3)


# # # cbox = ttk.Combobox(global_setting_frame,values=["Nifty", "BankNifty", "FinNifty"])
# # # cbox.grid(row=1, column=1)

# # # spinbox = Spinbox(global_setting_frame, from_=10, to=100)
# # # spinbox.grid(row=2, column=1)


# # window.mainloop()
