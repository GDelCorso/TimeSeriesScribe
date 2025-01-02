#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI of the Time Series Scribe.
This GUI is adapted to label refluxes on signal obtained from Hz digitrapper,
(Medtronic). The code can be easily modified to work on different temporal 
signals.

Giulio Del Corso and Simon Kanka
01-02-2025
"""



#%% Libraries
import os
import customtkinter

# Tkinter to define the GUI
from tkinter import filedialog
from tkinter import Menu

# Aux libraries to analyze the signal
import pandas as pd
import numpy as np

# Plot figures (including the shown canvas)
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Simplify parameters
plt.rcParams['path.simplify'] = True
plt.rcParams['agg.path.chunksize'] = 10000



#%% Main GUI class
class GUI_generate():

    ###########################################################################    
    def __init__(self):
        '''
        _init_: initializes all the aux class parameters, defines the tkinter
        root, and starts the main loop.
        '''
        
        # Path of the original .txt to be converted
        self.path_signal = None
        
        # Tmp path to store intermediate csv during import.
        self.tmp_path = os.path.join(os.getcwd(),'tmp') 
        if not os.path.isdir(self.tmp_path):
            os.mkdir(self.tmp_path)
        
        # Number of rows included in each intermediate csv
        self.how_many_signals = 1000000
        
        # Initialize the parameters to import labelling
        self.category = []                  # Category of labelled signal
        self.x_values = []                  # Time of labelled signal
        self.color_category = []            # Color of labelled signal
        self.label_n = 0                    # Number of labelled signals
        # Define the colors of the plots and the categories
        self.colors = ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', 
                       '#ca9161', '#fbafe4', '#949494', '#ece133', '#56b4e9', 
                       '#0173b2', '#de8f05']       
        
        self.click_counts = 0               # Aux count to select the signal

        # Initialize the vector position to plot the signals
        self.cond_min = None                # Minimum value
        self.cond_max = None                # Maximum value
        
        self.cond_min_ph = None             # Minimum value (ph-signal)
        self.cond_max_ph = None             # Minimum value (ph-signal)
        
        
        self.switch_draw = False    # If TRUE starts to draw the signal
        self.switch_update = False  # Needed to False to define the first plot
        
        # List of buttons to activate and deactivate the buttons on the canvas
        self.button_list = []       

        # Initialize dataframes
        self.impedence_df = pd.DataFrame()  # Multiple impedence signals df
        self.df_ph = pd.DataFrame()         # Ph values df
    
        
        # Initialize the dimension of the canvas (import window) and the Root
        self.x_size = 200                   # Horizontal dimension
        self.y_size = 150                   # Vertical dimension
        self.fontsize = 6                   # Initial fontsize
        customtkinter.set_appearance_mode("light")  # Light appearance
        
        self.root = customtkinter.CTk()     # Initialize root
        self.root.geometry(str(self.x_size)+"x"+str(self.y_size))
        self.root.title("Time Series Scribe")
        
        # Set the grid
        self.root.rowconfigure(list(range(8)), weight = 1, 
                                                        uniform="Silent_Creme")
        self.root.columnconfigure(list(range(12)), weight = 1, 
                                                        uniform="Silent_Creme")

        menubar = Menu(self.root)           # Create a menubar
        self.root.config(menu=menubar)      # Add the menubar to the root

        file_menu = Menu(menubar, tearoff=False, font = (" ",12)) 

        # Add the File menu to the menubar
        menubar.add_cascade(
            label="File",
            menu=file_menu,
            )

        # Add a menu item to the menu
        file_menu.add_command(
            label='Import raw file',
            command=self.import_signal_raw,
            )      
        file_menu.add_command(
            label='Save processed signal',
            command=self.save_processed_signal
            )   
        file_menu.add_command(
            label='Import processed signal',
            command=self.import_signal
            )
        file_menu.add_command(
            label='Exit',
            command=self.root.destroy
            )

        # Main loop and GUI update
        self.root.update()
        self.root.mainloop()
    ###########################################################################        



    ###########################################################################        
    def slider_event(self, value):
        """
        Slider to select the dimension of the time window to plot in the figure
        It is called when the "zoom" is changed
        """

        if self.switch_update:

            # Update the interval of time window shown
            self.par_time_window = 1000*60*self.slider_1.get()

            # Update the label
            self.slider_val.configure(text=
                                        str(float(self.slider_1.get()))+' min')
            
            self.update_graph()
    ###########################################################################                         
                              
         
            
    ###########################################################################                 
    def minor_right_shift(self):
        """
        Button to make a minor shift (10%) of the time window to the right
        """
        
        shift_amount = self.par_time_window/10
        
        if self.par_left_time + shift_amount <= self.par_max_time:
            self.par_left_time = min(self.par_left_time + shift_amount, 
                                        self.par_max_time-self.par_time_window)
        
        self.update_graph()
    ###########################################################################        


        
    ###########################################################################            
    def right_shift(self):
        """
        Button to make a minor shift (100%) of the time window to the right
        """
        
        shift_amount = self.par_time_window
        
        if self.par_left_time + shift_amount <= self.par_max_time:
            self.par_left_time = min(self.par_left_time + shift_amount, 
                                        self.par_max_time-self.par_time_window)
        
        self.update_graph()
    ###########################################################################        



    ###########################################################################            
    def minor_left_shift(self):
        """
        Button to make a minor shift (10%) of the time window to the left
        """
        
        shift_amount = self.par_time_window/10
        
        self.par_left_time = max(self.par_left_time - shift_amount, 
                                                             self.par_min_time)
        
        self.update_graph()
    ###########################################################################  


        
    ###########################################################################            
    def left_shift(self):
        """
        Button to make a major shift (100%) of the time window to the left
        """
        
        shift_amount = self.par_time_window
        
        self.par_left_time = max(self.par_left_time - shift_amount, 
                                                             self.par_min_time)
        
        self.update_graph()
    ###########################################################################        
        
    

    ###########################################################################   
    def mark_signal(self, signal_type, signal_color):
        '''
        Aux function to mark the signal given a certain signal_type (to add the 
        label) and signal_color (to draw it)
        '''

        # Dectivate each button in the list
        for button in self.button_list:
            button.configure(state="disabled",fg_color="light gray")

        # Temporary activate the tcross shape of the cursor
        self.root.config(cursor = "tcross")

        # Initialize the help values click_counts to find when two clicks occur
        self.click_counts = 0
        
        # Temporary store on tmp class parameters the values to be passed
        self.signal_type_temp = signal_type
        self.signal_color_temp = signal_color
        
        # Temporary store the x_values to be passed at interval_select method 
        # to save the labeled time interval
        self.signal_xvalues_temp = []

        # Call the event handler on the self.interval_select method
        self.id = self.fig.canvas.mpl_connect('button_press_event',
                                                          self.interval_select)
    ###########################################################################
    
    
    
    ###########################################################################           
    def interval_select(self, event):
        ''' 
        Aux function called by the event handler. It waits two left clicks of
        the mouse to identify the part of the graph to be labelled.
        
        It is called by the method "mark_signal()"
        '''
        
        # First (left) click inside the canvas
        if event.inaxes==self.ax and event.button == 1 and self.click_counts<2: 
            self.signal_xvalues_temp.append(event.xdata)
            self.click_counts = self.click_counts + 1
        
        if self.click_counts == 2:              # Second (left) click 
            (self.signal_xvalues_temp).sort()   # Sort the two values       
            
            # Append to the main lists
            self.x_values.append(self.signal_xvalues_temp)
            self.color_category.append(self.signal_color_temp)
            self.category.append(self.signal_type_temp)
            
            
            self.label_n = self.label_n + 1     # Increase number of labels

            self.fig.canvas.mpl_disconnect(self.id)
            self.root.config(cursor = "arrow")
            
            # Activate again deactivated buttons
            for button in self.button_list:
                button.configure(state="normal", fg_color="cornflower blue",
                                               hover_color = "dark slate blue")
            
            self.update_graph()
    ###########################################################################   
    
    

    ###########################################################################           
    def remove_mark(self):
        """
        Aux function to remove the labeled interval by selecting a point in the 
        region. The method removes all the labels in the given region.
        """

        # Dectivate each button in the list    
        for button in self.button_list:
            button.configure(state="disabled",fg_color="light gray")
        
        # Temporary activate the tcross shape of the cursor
        self.root.config(cursor = "tcross")

        # Function to select the interval to remove
        def identify_interval(event):
            
            if event.inaxes == self.ax:    
                x = event.xdata
                
                selected_values_shape = []
                selected_values_category = []
                selected_values_color_category = []
                self.labels_n = 0

                for n in range(len(self.x_values)):
                    if not((x >= self.x_values[n][0]) 
                                               and (x <= self.x_values[n][1])):
                        selected_values_shape.append(
                                     [self.x_values[n][0],self.x_values[n][1]])
                        selected_values_category.append(self.category[n])
                        selected_values_color_category.append(
                                                        self.color_category[n])
                        self.labels_n = self.labels_n + 1
    
                self.x_values = selected_values_shape
                self.category = selected_values_category
                self.color_category = selected_values_color_category

                self.root.config(cursor = "arrow")
            
                # Activate again deactivated buttons
                for button in self.button_list:
                    button.configure(state="normal",fg_color="cornflower blue",
                                               hover_color = "dark slate blue")
                
                self.fig.canvas.mpl_disconnect(self.id)
                self.update_graph()                            
                
        self.id = self.fig.canvas.mpl_connect('button_press_event',identify_interval)
    ###########################################################################   


        
    ###########################################################################       
    def select_and_see(self,event):
        """
        Aux function to visualize the plot region selected in whole time plot.
        Called by the main "plot_graph()" method.
        """
        
        if event.inaxes == self.ax_total:
            x = event.xdata
            self.par_left_time = x
            
            self.update_graph()
    ###########################################################################   
    
    
    
    ###########################################################################    
    def slider_font_size(self,event):
        """
        Aux function to update the fontsize of the labels in the plot with the 
        input of a slider.
        """
        
        if self.switch_update:
            
            self.fontsize = self.slider_font.get()  # Update the fontsize
            
            self.slider_font_text.configure(text='fontsize plot: ' + 
                                              str(int(self.slider_font.get())))
            
            self.update_graph()
    ###########################################################################



    ###########################################################################        
    def bisection_selection(self, t, t_min, t_max):
        """
        t: (list) time values
        t_min: (int) minimum time of the interval to plot
        t_max: (int) maximum time of the interval to plot
        Aux function to select the indices of the signal slice given the 
        minimum and maximum time. It is based on the bisection algorithm to 
        drastically optimize the searching time.
        """
        
        cond_min = 0            # Minimum starting point
        right_cond_min= len(t)  # Maximum starting point
        
        Found = False           # Found switch
        
        # Iterate to find min condition (cond_min)
        while not Found:
            candidate = int((cond_min+right_cond_min)/2)
            
            if t[candidate]<t_min:
                cond_min = candidate
            else:
                right_cond_min = candidate
                
            if abs(right_cond_min-cond_min)<2:  # Halting criterion
                Found = True
            
        # Search for max condition (cond_max)    
        left_cond_max = cond_min    # Use minimum condition as starting point
        cond_max = len(t)           # Maximum starting point
        
        Found = False               # Found switch
        
        
        # Iterate to find max condition (cond_max)
        while not Found:
            candidate = int((cond_max+left_cond_max)/2)
            if t[candidate]<t_max:
                left_cond_max = candidate
            else:
                cond_max = candidate
                
            if abs(cond_max-left_cond_max)<2:
                Found = True
        
        return cond_min, cond_max
    ###########################################################################



    ###########################################################################    
    def next_signal(self):
        '''
        Method to call to identify the next portion of the signal corresponding
        to a possible window to label. 
        TODO
        '''

        print("This method has to linked with a previously trained model")
    ###########################################################################



    ###########################################################################    
    def plot_graph(self):
        '''
        Aux method to plot the graph for the first time.
        This function initializes all the buttons and the canvas used to plot
        the time signal. 
        Subsequent modifications are applied using the update_graph() method
        '''
        
        # Can be called only if a signal has been imported
        if self.switch_draw:    
            
            # Reshape the window
            self.x_size = 800   # Horizontal size
            self.y_size = 600   # Vertical size
            self.root.geometry(str(self.x_size)+"x"+str(self.y_size))

            # Introduce different font size/characteristics
            # visualizing window 
            my_font_1 = customtkinter.CTkFont(family="Helvetica", size=20, 
            weight="bold", slant="roman", underline=False, overstrike=False) 

            # labelling menu 
            my_font_2 = customtkinter.CTkFont(family="Helvetica", size=12, 
            weight="bold", slant="roman", underline=False, overstrike=False)

            # sliders text
            my_font_3 = customtkinter.CTkFont(family="Helvetica", size=12, 
            weight="bold", slant="roman", underline=False, overstrike=False)

            # Add the buttons to move the signal
            # Left shift
            button_left_shift = customtkinter.CTkButton(master=self.root, 
                           text="<<",font = my_font_1, command=self.left_shift)
            button_left_shift.grid(row=7, column=1, padx=(20,5), pady=(10, 0), 
                                                                    sticky="e")
            self.button_list.append(button_left_shift)

            # Minor left shift
            button_minor_left_shift = customtkinter.CTkButton(master=self.root, 
                      text="<",font = my_font_1, command=self.minor_left_shift)
            button_minor_left_shift.grid(row=7, column=2, padx=(5,20),  
                                                      pady=(10, 0), sticky="w")
            self.button_list.append(button_minor_left_shift)
            
            # Next signal
            button_next_signal = customtkinter.CTkButton(master=self.root, 
                 text="Next signal",font = my_font_1, command=self.next_signal)
            button_next_signal.grid(row=7, column = 3, columnspan = 4, 
                                      padx=(10,20),  pady=(10, 0), sticky="we")
            self.button_list.append(button_next_signal)

            # Minor right shift
            button_minor_right_shift = customtkinter.CTkButton(master=self.root
                   , text=">",font = my_font_1, command=self.minor_right_shift) 
            button_minor_right_shift.grid(row=7, column=7, padx=(20,5), 
                                                      pady=(10, 0), sticky="e")
            self.button_list.append(button_minor_right_shift)

            # Right shift
            button_right_shift = customtkinter.CTkButton(master=self.root, 
                          text=">>",font = my_font_1, command=self.right_shift)
            button_right_shift.grid(row=7, column=8, padx=(5,20), pady=(10, 0), 
                                                                    sticky="w")
            self.button_list.append(button_right_shift)

            # Initialize the time
            self.par_min_time = int(min(self.df_ph['Time_ph(ms)'])) # Min time
            self.par_left_time = self.par_min_time              # Actual time
            self.par_max_time = int(max(self.time_impedence))   # Max time
            
            # Frame of vertical zoom slider 
            self.zoom_frame = customtkinter.CTkFrame(self.root)
            self.zoom_frame.grid(row=0, column=0, rowspan=7, padx=(5, 5), 
                                                  pady=(10, 10), sticky="nsew")
            
            self.zoom_frame.columnconfigure(list(range(1)), weight = 1, 
                                                        uniform="Silent_Creme")
            self.zoom_frame.rowconfigure(list(range(7)), weight = 1, 
                                                        uniform="Silent_Creme")
            
            self.slider_1 = customtkinter.CTkSlider(self.zoom_frame, from_=0.5, 
                             to=20, number_of_steps=39, orientation='vertical')
            self.slider_1.set(2)
            self.slider_1.bind("<ButtonRelease-1>", self.slider_event)
            
            self.par_time_window = 1000*60*self.slider_1.get()
            
            self.slider_val = customtkinter.CTkLabel(self.zoom_frame, 
                 text=str(float(self.slider_1.get()))+' min', font = my_font_3)
            self.slider_val.grid(row=0, column = 0, sticky="ns")        
            
            self.slider_1.grid(row=1, column=0, rowspan=6, pady = (0,10), 
                                                                   sticky="ns")
            
            # Define the frame to add the switches
            self.switch_frame = customtkinter.CTkFrame(self.root)
            self.switch_frame.grid(row=1, column=9, rowspan = 5, columnspan=6, 
                                    padx=(20, 20), pady=(0, 10), sticky="nsew")
            
            self.switch_frame.columnconfigure(list(range(3)), weight = 1, 
                                                        uniform="Silent_Creme")
            self.switch_frame.rowconfigure(list(range(5)), weight = 1, 
                                                        uniform="Silent_Creme")

            # Button: Mark Reflux
            switch_1 = customtkinter.CTkButton(master=self.switch_frame, 
                                              text = "Reflux", font = my_font_2, 
                   command= lambda: self.mark_signal("Reflux", self.colors[0]))
            switch_1.grid(row=0, column=0, padx=5, pady=5, columnspan = 2,
                                                                sticky= "nsew")
            self.button_list.append(switch_1)
            # Reference color: Reflux
            color_switch_1 = customtkinter.CTkButton(master=self.switch_frame, 
                                                text = ' ', state = 'disabled', 
                                      fg_color = self.colors[0], hover = False)
            color_switch_1.grid(row=0, column = 2,padx= 5, pady=5, 
                                                               sticky = 'nsew')

            # Button: Mark Mixed Reflux
            switch_2 = customtkinter.CTkButton(master=self.switch_frame, 
                                          text="Mixed Reflux",font = my_font_2, 
             command= lambda: self.mark_signal("Mixed Reflux", self.colors[1]))
            switch_2.grid(row=1, column=0, padx=5, pady=5, columnspan = 2,
                                                                sticky= "nsew")
            self.button_list.append(switch_2)
            # Reference color: Mixed Reflux
            color_switch_2 = customtkinter.CTkButton(master=self.switch_frame, 
                                                text = ' ', state = 'disabled', 
                                      fg_color = self.colors[1], hover = False)
            color_switch_2.grid(row=1, column = 2,padx= 5, pady=5, 
                                                               sticky = 'nsew')
            
            # Button: Mark Erutation
            switch_3 = customtkinter.CTkButton(master=self.switch_frame, 
                                             text="Erutation",font = my_font_2, 
                command= lambda: self.mark_signal("Erutation", self.colors[2]))
            switch_3.grid(row=2, column=0, padx=5, pady=5, columnspan = 2,
                                                                sticky= "nsew")
            self.button_list.append(switch_3)
            # Reference color: Erutation
            color_switch_3 = customtkinter.CTkButton(master=self.switch_frame, 
                                                text = ' ', state = 'disabled', 
                                      fg_color = self.colors[2], hover = False)
            color_switch_3.grid(row=2, column = 2,padx= 5, pady=5, 
                                                               sticky = 'nsew')
        
            # Button: Mark Swallow
            switch_4 = customtkinter.CTkButton(master=self.switch_frame, 
                                               text="Swallow",font = my_font_2, 
                  command= lambda: self.mark_signal("Swallow", self.colors[3]))
            switch_4.grid(row=3, column=0, padx=5, pady=5, columnspan = 2,
                                                                sticky= "nsew")
            self.button_list.append(switch_4)
            # Reference color: Swallow
            color_switch_4 = customtkinter.CTkButton(master=self.switch_frame, 
                                                text = ' ', state = 'disabled', 
                                      fg_color = self.colors[3], hover = False)
            color_switch_4.grid(row=3, column = 2,padx= 5, pady=5, 
                                                               sticky = 'nsew')
            
            # Button: Mark Meal
            switch_5 = customtkinter.CTkButton(master=self.switch_frame, 
                                                  text="Meal",font = my_font_2, 
                     command= lambda: self.mark_signal("Meal", self.colors[4]))
            switch_5.grid(row=4, column=0, padx=5, pady=5, columnspan = 2,
                                                                sticky= "nsew")
            self.button_list.append(switch_5)
            # Reference color: Meal
            color_switch_5 = customtkinter.CTkButton(master=self.switch_frame, 
                                                text = ' ', state = 'disabled', 
                                      fg_color = self.colors[4], hover = False)
            color_switch_5.grid(row=4, column = 2,padx= 5, pady=5, 
                                                               sticky = 'nsew')
            
            # Button: Remove selected labels/marks
            button_remove_mark = customtkinter.CTkButton(master=self.root, 
                                           text="Remove mark",font = my_font_2, 
                                                      command=self.remove_mark)
            button_remove_mark.grid(row=6, column=9, columnspan = 3, 
                                      padx=(20,20), pady=(10, 10), sticky="ew")
            self.button_list.append(button_remove_mark)

            # Frame: Select font size 
            self.font_frame = customtkinter.CTkFrame(self.root)
            self.font_frame.grid(row=7, column=9, columnspan=3, padx=(20, 20), 
                                                   pady=(0, 10), sticky="nsew")
            
            self.font_frame.columnconfigure(list(range(3)), weight = 1, 
                                                        uniform="Silent_Creme")
            self.font_frame.rowconfigure(list(range(2)), weight = 1, 
                                                        uniform="Silent_Creme")
                
            self.slider_font = customtkinter.CTkSlider(self.font_frame, 
                  from_=6, to=20, number_of_steps=14, orientation='horizontal')
            self.slider_font.set(2)
            self.slider_font.bind("<ButtonRelease-1>", self.slider_font_size)
            self.slider_font.grid(row=0, column=0, columnspan = 3,rowspan=1, 
                                                                    pady=(5,0))

            self.slider_font_text = customtkinter.CTkLabel(self.font_frame, 
                     text='fontsize plot: ' + str(int(self.slider_font.get())),
                                                              font = my_font_3) 
            self.slider_font_text.grid(row=1, column = 0, columnspan = 3, 
                                                    padx = (0,0), pady = (0,5))        

            self.switch_update = True   # Activate the "update" switch
            
            # Activate the list of buttons
            for button in self.button_list:
                button.configure(state="normal",fg_color="cornflower blue",
                                               hover_color = "dark slate blue")
            
            # Create the figure with two subplots. The first plot is 10 times
            # higher than the second one
            self.fig, self.axes = plt.subplots(nrows=2, ncols=1, 
              gridspec_kw={'height_ratios': [10, 1]}, figsize=(10,6),dpi = 100)
             
            self.ax = self.axes[0]
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            
            self.signal_names = np.array(['signal_' + str(i) + '_selected' 
                                            for i in range(1,7)],dtype = 'str')
            self.signal_names = np.append('signal_ph_selected',
                                                             self.signal_names)
            
            # Creation of the yaxis ticks and labels
            self.yticks = np.array([0,9])
                
            for m in range(len(self.signal_names)-1):
                self.yticks = np.append(self.yticks,9+7*(m+1))
        
            self.yticks_labels_null = []*len(self.yticks)

            self.ax.set_yticks(self.yticks)
            self.ax.set_yticklabels(self.yticks_labels_null)

            # Add the transformation specification of scale for the text 
            # positioning
            trans = transforms.blended_transform_factory(self.ax.transAxes,
                                                             self.ax.transData)
        
            for n in range(len(self.signal_names)):
                self.ax.text(-0.01, self.yticks[n] + 0.06 ,f'{0:.1f}',
                           horizontalalignment='right', fontsize=self.fontsize, 
                           color='black', transform = trans)

            for n in range(len(self.signal_names)):
                if n == 0:
                    self.ax.text(-0.01, self.yticks[n+1] - 9*0.15, f'{9:.1f}',
                           horizontalalignment='right', fontsize=self.fontsize, 
                           color='black', transform = trans)
                else:
                    self.ax.text(-0.01, self.yticks[n+1] - 7*0.2, f'{7:.1f}',
                           horizontalalignment='right', fontsize=self.fontsize, 
                           color='black', transform = trans)

            for n in range(len(self.signal_names)):
                if n == 0:
                    self.ax.text(-0.1, 4.5, 'ph1', fontsize = 6,
                                transform = trans,horizontalalignment='center',
                           bbox = dict(facecolor = self.colors[0],alpha = 0.4))
                else:    
                    self.ax.text(-0.1, self.yticks[n] + 3.5, f'Z{n+1}', 
                                   fontsize = self.fontsize, transform = trans, 
                                                  horizontalalignment='center',
                           bbox = dict(facecolor = self.colors[n],alpha = 0.4))
            
            self.ax_total = self.axes[1]
            
            # Number of time visualization in the total time plot 
            steps = 8

            min_time_imp = np.min(self.time_impedence)
            max_time_imp = np.max(self.time_impedence)
            min_time_ph = np.min(self.time_ph)
            max_time_ph = np.max(self.time_ph)
            max_time_vis = np.min([max_time_imp,max_time_ph])
            min_time_vis = np.max([min_time_ph,min_time_imp])
                           
            stringa_visualiza = []
            time_visualize = []

            indice = np.floor((max_time_vis-min_time_vis)/steps)

            for n in range(steps):
                time_vis = (min_time_vis + indice*(n))*10**-3
                ore = int(np.floor(time_vis/3600))
                minutes = int(np.floor((time_vis - ore*3600)/60))
                secondi = int(np.floor(time_vis - ore*3600 - minutes*60))

                if ore >= 24:
                    ore = ore-24
                
                stringa_visualiza.append(f'{ore:02}:{minutes:02}:{secondi:02}')
                time_visualize.append(min_time_vis + indice*(n))
            
            self.ax_total.plot([min_time_vis,max_time_vis],[1,1],'k--')
            self.ax_total.set_ylim([0.95,1.05])
            self.ax_total.set_xlim([time_visualize[0],time_visualize[-1]])
            self.ax_total.set_xticks(time_visualize)
            self.ax_total.set_xticklabels(stringa_visualiza, 
                                                      fontsize = self.fontsize)
            
            self.ax_total.set_yticks([])            
            
            # Adjust the figure to the window
            self.fig.subplots_adjust(left=0.2,right=0.95, bottom=0.1, top=0.95,
                                                       wspace=0, hspace = 0.15)

            # Activate the possibility to zoom on a selected piece of the signal 
            self.fig.canvas.mpl_connect('button_press_event', lambda event: 
                        self.select_and_see(event) if event.dblclick else None)

            self.update_graph()
    ###########################################################################
    
    
    
    ###########################################################################    
    def import_signal_raw(self):
        '''
        Aux function to import the raw signal as exported from the main 
        software.
        '''
        
        # if self.switch_import:
        self.path_signal = filedialog.askopenfilename(
                                          filetypes = (("Txt Files","*.txt"),))
        
        
        # Open the file
        opener = open(self.path_signal, 'r')  
        list_lines = opener.readlines()
        
        # Find the beginning of the 7 signals
        # Ph Array
        start_ph_array = list_lines.index('Ph Array\n')+ 4

        # Impedance Array
        start_impedence_array = list_lines.index('Impedance Array\n') + 4

        # Medical Diary
        start_diary = list_lines.index('Diary\n')
        
        # Database ph:
        list_ph = []

        for i_temp in range(start_ph_array,start_impedence_array-5):
            
            temp_row = list_lines[i_temp]
            list_ph.append([int(temp_row.split('\t')[0]),
                              float((temp_row.split('\t')[1]).split('\n')[0])])
          
        self.df_ph = pd.DataFrame(list_ph, columns =['Time_ph(ms)','Value_ph'])    
        self.time_ph = self.df_ph['Time_ph(ms)']
        
        # Database Impedence (6 channels)
        # Warning: should be saved every self.how_many_signals
        list_impedence = []
        count_subdivision = 0
        
        for i_temp in range(start_impedence_array,start_diary-1):
            temp_row = list_lines[i_temp]
            
            temp_row_list = (temp_row.replace('\n','')).split('\t')
            
            list_impedence.append([int(temp_row_list[0]),
                               float(temp_row_list[1]),float(temp_row_list[2]),
                               float(temp_row_list[3]),float(temp_row_list[4]),
                              float(temp_row_list[5]),float(temp_row_list[5])])
            
            if i_temp%self.how_many_signals == 0:
                count_subdivision += 1
                df_impedence = pd.DataFrame(list_impedence, 
                            columns = ['Time(ms)','Value_1','Value_2',
                              'Value_3','Value_4','Value_5','Value_6'])
                df_impedence.to_csv(os.path.join(self.tmp_path, 
                           'impedence_'+str(count_subdivision)+'.csv'), 
                                                         index = False)
                # Reset the list
                list_impedence = []
            
        # Merge the datasets
        list_datasets = os.listdir(self.tmp_path)
        list_datasets= [i for i in os.listdir(self.tmp_path) 
                                                        if ("impedence_" in i)]
        
        # Range over the number
        self.impedence_df= pd.DataFrame() 
        
        for i in range(0, len(list_datasets)):
            tmp_path_df = os.path.join(self.tmp_path,
                                                  "impedence_"+str(i+1)+'.csv')
            tmp_df = pd.read_csv(tmp_path_df)
            self.impedence_df = pd.concat([self.impedence_df, tmp_df], 
                                                             ignore_index=True)
            
            # Remove the tmp csv
            os.remove(tmp_path_df)
        
        self.switch_draw = True
        
        # Define the list of the signals
        self.time_impedence = self.impedence_df['Time(ms)'].to_list()
        self.signal_1 = self.impedence_df['Value_1'].to_list()
        self.signal_2 = self.impedence_df['Value_2'].to_list()
        self.signal_3 = self.impedence_df['Value_3'].to_list()
        self.signal_4 = self.impedence_df['Value_4'].to_list()
        self.signal_5 = self.impedence_df['Value_5'].to_list()
        self.signal_6 = self.impedence_df['Value_6'].to_list()   
        
        for name in self.signal_names:
            vector = np.array(getattr(self,name)) 
            x = np.where(vector > 11)[0]
            vector[x] = 11
            setattr(self,name,vector)
        
        self.plot_graph()
    ###########################################################################        
        
    
    
    ###########################################################################    
    def update_axis_test(self):
        """
        Aux function to update the axis of the plot.
        """
        
        self.ax.set_yticks(self.yticks)
        self.ax.set_yticklabels(self.yticks_labels_null)

        # Add the transformation specification of scale for the text positioning
        trans = transforms.blended_transform_factory(self.ax.transAxes,
                                                             self.ax.transData)
    
        for n in range(len(self.signal_names)):
            self.ax.text(-0.01, self.yticks[n] + 0.06 ,f'{0:.1f}',
                                    horizontalalignment='right', color='black',
                                    transform = trans,fontsize = self.fontsize)

        for n in range(len(self.signal_names)):
            if n == 0:
                self.ax.text(-0.01, self.yticks[n+1] - 9*0.15  ,f'{9:.1f}',
                                    horizontalalignment='right', color='black',
                                    transform = trans,fontsize = self.fontsize)
            else:
                self.ax.text(-0.01, self.yticks[n+1] - 7*0.2 ,f'{7:.1f}',
                                    horizontalalignment='right', color='black',
                                    transform = trans,fontsize = self.fontsize)

        self.ax.text(0.01,4-9*0.15,f'{4:.1f}', horizontalalignment = 'left', 
                    color = 'grey', transform = trans,fontsize = self.fontsize)

        for n in range(len(self.signal_names)):
            if n == 0:
                self.ax.text(-0.1, 4.5, 'ph1', transform = trans,
                                                  horizontalalignment='center',
                           bbox = dict(facecolor = self.colors[0],alpha = 0.4),
                                                      fontsize = self.fontsize)
            else:
                self.ax.text(-0.1, self.yticks[n] + 3.5, f'Z{n+1}', 
                               transform = trans, horizontalalignment='center',
                           bbox = dict(facecolor = self.colors[n],alpha = 0.4),
                                                      fontsize = self.fontsize)
        
        self.ax_total = self.axes[1]
        steps = 8
        
        # selecting the time window to visualize the measurement time: hh:mm:ss
        min_time_vis = np.min(self.time_impedence)
        max_time_vis = np.max(self.time_impedence)

        stringa_visualiza = []
        time_visualize = []

        indice = np.floor((max_time_vis-min_time_vis)/steps)

        for n in range(steps):
            time_vis = (min_time_vis + indice*(n))*10**-3
            ore = int(np.floor(time_vis/3600))
            minutes = int(np.floor((time_vis - ore*3600)/60))
            secondi = int(np.floor(time_vis - ore*3600 - minutes*60))

            if ore >= 24:
                ore = ore-24
            
            stringa_visualiza.append(f'{ore:02}:{minutes:02}:{secondi:02}')
            time_visualize.append(min_time_vis + indice*(n))
         
        time_vis = (max_time_vis)*10**-3
        ore = int(np.floor(time_vis/3600))
        minutes = int(np.floor((time_vis - ore*3600)/60))
        secondi = int(np.floor(time_vis - ore*3600 - minutes*60))

        if ore >= 24:
            ore = ore-24
        
        stringa_visualiza.append(f'{ore:02}:{minutes:02}:{secondi:02}')
        time_visualize.append(max_time_vis)
        
        time_vis = (min_time_vis)*10**-3
        ore = int(np.floor(time_vis/3600))
        minutes = int(np.floor((time_vis - ore*3600)/60))
        secondi = int(np.floor(time_vis - ore*3600 - minutes*60))

        if ore >= 24:
            ore = ore-24
        
        self.ax_total.plot([min_time_vis,max_time_vis],[1,1],'k--')
        self.ax_total.set_ylim([0.95,1.05])
        self.ax_total.set_xlim([min_time_vis,max_time_vis])
        self.ax_total.set_xticks(time_visualize)
        self.ax_total.set_xticklabels(stringa_visualiza, 
                                                      fontsize = self.fontsize)
        
        self.ax_total.set_yticks([])            
    ###########################################################################            
    
    
    
    ###########################################################################              
    def update_graph(self):
        '''
        Aux function to update the graph at each iteraction. 
        '''
        
        if self.par_left_time + self.par_time_window >= self.par_max_time:
            self.par_left_time = self.par_max_time - self.par_time_window

        self.cond_min, self.cond_max  = self.bisection_selection(
                                       self.time_impedence, self.par_left_time, 
                                       self.par_left_time+self.par_time_window)
        
        time_impedence_selected = self.time_impedence[self.cond_min:self.cond_max]
        
        self.signal_1_selected = np.array(
                                    self.signal_1[self.cond_min:self.cond_max])
        self.signal_2_selected = np.array(
                                    self.signal_2[self.cond_min:self.cond_max])
        self.signal_3_selected = np.array(
                                    self.signal_3[self.cond_min:self.cond_max])
        self.signal_4_selected = np.array(
                                    self.signal_4[self.cond_min:self.cond_max])
        self.signal_5_selected = np.array(
                                    self.signal_5[self.cond_min:self.cond_max])
        self.signal_6_selected = np.array(
                                    self.signal_6[self.cond_min:self.cond_max])
        
        self.time_ph = self.df_ph['Time_ph(ms)']
        signal_ph = self.df_ph['Value_ph']
        
        self.cond_min_ph, self.cond_max_ph  = self.bisection_selection(
                                              self.time_ph, self.par_left_time, 
                                       self.par_left_time+self.par_time_window)
        
        time_ph_selected = self.time_ph[self.cond_min_ph:self.cond_max_ph]
        self.signal_ph_selected = signal_ph[self.cond_min_ph:self.cond_max_ph]

        times_dictionary = {'time_ph':time_ph_selected, 
                                          'time_imped':time_impedence_selected}
        
        # Clean axes to avoid multiple plot instances
        self.ax.cla()

        # Makes a single plot with all the signals in it.
        # Each signal is plotted with different colors and has an offset in 
        # order to be visualized.                
        for (p,n) in enumerate(self.signal_names):
            if p == 0:
                self.ax.plot(times_dictionary['time_ph'],getattr(self,n),
                                                        color = self.colors[p])
                discriminator =4*np.ones(len(times_dictionary['time_ph']))
                self.ax.plot(times_dictionary['time_ph'], discriminator, 
                                                                color = 'grey')

                self.ax.fill_between(times_dictionary['time_ph'], 
                              getattr(self,self.signal_names[0]),4,color = 'r', 
                                 where= getattr(self,self.signal_names[0]) < 4)     
        
            else:
                # Adding the plot to the signal in order to visualize it 
                # in the same plot
                self.ax.plot(times_dictionary['time_imped'], 
                      getattr(self,n) + self.yticks[p], color = self.colors[p]) 

        steps = 6
        indice = np.floor((time_impedence_selected[-1]
                                            -time_impedence_selected[0])/steps)

        stringa_visualiza = []
        time_visualize = []

        for n in range(steps):
            time_impedence_selected_s = (time_impedence_selected[0]  
                                                           + indice*(n))*10**-3
            ore = int(np.floor(time_impedence_selected_s/3600))
            minutes = int(np.floor((time_impedence_selected_s - ore*3600)/60))
            secondi = int(np.floor(time_impedence_selected_s - ore*3600 
                                                                 - minutes*60))
            
            if ore >= 24:
                    ore = ore-24
                
            stringa_visualiza.append(f'{ore:02}:{minutes:02}:{secondi:02}')
            time_visualize.append(time_impedence_selected[0] + indice*(n))

        min_plot = np.max([np.min(time_impedence_selected),
                                                     np.min(time_ph_selected)])
        max_plot = np.min([np.max(time_impedence_selected),
                                                     np.max(time_ph_selected)])
        time_impedence_selected_s = (max_plot)*10**-3

        ore = int(np.floor(time_impedence_selected_s/3600))
        minutes = int(np.floor((time_impedence_selected_s - ore*3600)/60))
        secondi = int(np.floor(time_impedence_selected_s - ore*3600 - 
                                                                   minutes*60))
        
        if ore >= 24:
                ore = ore-24
            
        stringa_visualiza.append(f'{ore:02}:{minutes:02}:{secondi:02}')
        time_visualize.append(max_plot)

        self.ax.set_xticks(time_visualize)
        self.ax.set_xticklabels(stringa_visualiza,fontsize = self.fontsize)
        self.ax.set_ylim([0,self.yticks[-1]+4])
        self.ax.set_xlim([min_plot,max_plot])

        # plot the labeled intervals in the plot if there is any 
        for i in range(len(self.x_values)):    
            self.ax.axvspan(self.x_values[i][0], self.x_values[i][1], 
                                       color=self.color_category[i], alpha=0.2)

        # clean the total axis plot to avoid multiple plot instances    
        self.ax_total.cla()

        # update the labels of the plots
        self.update_axis_test()
        
        # add the intervals for the different labels
        for i in range(len(self.x_values)):    
            self.ax_total.axvspan(self.x_values[i][0], self.x_values[i][1], 
                                       color=self.color_category[i], alpha=0.5)

        
        canvas = FigureCanvasTkAgg(self.fig,master=self.root)

        canvas.draw_idle()
        canvas.get_tk_widget().grid(row=0, column=1,rowspan = 7, columnspan=8, 
                                      padx = (0,0), pady=(0, 0), sticky="nsew")
        plt.close(self.fig)
    ###########################################################################

        
        
    ###########################################################################            
    def save_processed_signal(self):
        '''
        Aux function to save the processed signal as csv.
        '''
        # Activate only if the df are non empty:
        if not self.impedence_df.empty:
            save_path = filedialog.asksaveasfilename(
                                          filetypes = (("CSV Files","*.csv"),))
            
            # Check if the extension has been added
            if '.csv' not in save_path:
                save_path = save_path +'.csv'
                
            # Define the dataframe list of signals and etiquettes:
            labelling_df = pd.DataFrame()
            labelling_df['labels'] = self.category
            labelling_df['color_label'] = self.color_category
            labelling_df['intervals'] = self.x_values
         
            impedence_df_merged = pd.concat([self.impedence_df,
                                              self.df_ph,labelling_df], axis=1)     
            impedence_df_merged.to_csv(save_path, index = False)
    ###########################################################################


    
    ###########################################################################    
    def import_signal(self):
        '''
        Aux function to import the processed signal previously saved.
        '''
        # if self.switch_import:
        self.path_signal = filedialog.askopenfilename(
                                          filetypes = (("CSV Files","*.csv"),))
        # self.switch_import = True
        
        # Load the dataframe
        impedence_df_merged = pd.read_csv(self.path_signal, low_memory=False)
        
        # Split the dataframe
        self.impedence_df = impedence_df_merged[['Time(ms)','Value_1',
                            'Value_2','Value_3','Value_4','Value_5','Value_6']]
        self.df_ph = impedence_df_merged[ ['Time_ph(ms)','Value_ph']]
        
        self.df_ph = self.df_ph.dropna()
        self.time_ph = self.df_ph['Time_ph(ms)']
        
        self.switch_draw = True
        
        # Define the list of the signals
        self.time_impedence = self.impedence_df['Time(ms)'].to_list()
        self.signal_1 = self.impedence_df['Value_1'].to_list()
        self.signal_2 = self.impedence_df['Value_2'].to_list()
        self.signal_3 = self.impedence_df['Value_3'].to_list()
        self.signal_4 = self.impedence_df['Value_4'].to_list()
        self.signal_5 = self.impedence_df['Value_5'].to_list()
        self.signal_6 = self.impedence_df['Value_6'].to_list()   
        
        if 'labels' in impedence_df_merged.keys():
            # Import the labelling parameters
            labelling_df = impedence_df_merged[['labels','intervals',
                                                                'color_label']]
            labelling_df = labelling_df.dropna()
                    
            self.category = labelling_df['labels'].to_list() 
            self.x_values = []
            tmp_intervals = labelling_df['intervals'].to_list()
            self.color_category = []
            tmp_color = labelling_df['color_label'].to_list()            
            
            
            # Convert to correct datatype
            for i in tmp_intervals:
                self.x_values.append([
                                   int(float(i.split(",")[0].replace('[',''))),
                                  int(float(i.split(",")[1].replace(']','')))])
                
            for i in tmp_color:
                self.color_category.append(i)
        
            self.label_n = len(self.category)

        #plot the figure for the first time
        self.plot_graph()
    ###########################################################################        
            
            
          
###############################################################################          
#%% Start the GUI:
gui = GUI_generate()
###############################################################################          