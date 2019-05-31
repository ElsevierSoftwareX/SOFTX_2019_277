try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cHSI as chsi

    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cMakeTable as cmkt
    import cFlows as cq
    import cInputOutput as cio
    import fGlobal as fg
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class HHSIgui(object):
    def __init__(self, master, unit, fish_applied, *args):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_lvl_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cover_applies = False
        self.dir_conditions = self.path_lvl_up + "\\01_Conditions\\"
        self.dir_input_ras = ""
        self.condition = ""
        self.condition_list = fg.get_subdir_names(self.dir_conditions)
        self.xlsx_flow_dur = ""
        self.max_columnspan = 5
        self.discharge_xlsx = []
        self.unit = unit
        self.fish_applied = fish_applied

        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        try:
            # test if a boundary shapefile was provided
            self.boundary_shp = args[0]
        except:
            self.boundary_shp = ""

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 390
        wh = 307
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Generate hydraulic habitat condition (HSI) rasters")  # window title

        self.l_condition = tk.Label(top, text="ii) Available hydraulic conditions:")
        self.l_condition.grid(sticky=tk.W, row=2, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.l_inpath_curr = tk.Label(top, fg="gray60", text="Source: "+str(self.dir_conditions))
        self.l_inpath_curr.grid(sticky=tk.W, row=5, column=0, columnspan=self.max_columnspan + 1, padx=self.xd, pady=self.yd)

        self.l_dummy = tk.Label(top, text="                                                                          ")
        self.l_dummy.grid(sticky=tk.W, row=2, column=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.l_run_info = tk.Label(top, text="")
        self.l_run_info.grid(sticky=tk.W, row=8, column=0, columnspan=self.max_columnspan - 1, padx=self.xd,
                             pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=2, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.E, row=2, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)

        # BUTTONS
        self.b_flowdur_make = tk.Button(top, bg="white", text="    Optional: Generate flow duration curve (.XLSX)",
                                        anchor='w', command=lambda: self.make_flow_dur())
        self.b_flowdur_make.grid(sticky=tk.EW, row=0, column=0, columnspan=self.max_columnspan,
                                 padx=self.xd, pady=self.yd)
        
        self.b_flowdur_select = tk.Button(top, bg="white", text="i) Select flow duration curve (.XLSX)",
                                          anchor='w', command=lambda: self.select_flowdur_xlsx())
        self.b_flowdur_select.grid(sticky=tk.EW, row=1, column=0, columnspan=self.max_columnspan,
                                   padx=self.xd, pady=self.yd)

        self.b_c_select = tk.Button(top, width=8, bg="white", text="Confirm\nselection", command=lambda:
                                    self.select_condition())
        self.b_c_select.grid(sticky=tk.W, row=2, rowspan=3, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        self.b_c_select["state"] = "disabled"

        self.b_Q = tk.Button(top, fg="RoyalBlue3", width=30, bg="white",
                             text="    Optional: View discharge dependency file (xlsx workbook)", anchor='w',
                             command=lambda: self.user_message("CONFIRM HYDRAULIC CONDITION!"))
        self.b_Q.grid(sticky=tk.EW, row=6, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_HSC = tk.Button(top, width=30, bg="white",
                               text="    Optional: Edit Habitat Suitability Curves", anchor='w',
                               command=lambda: self.open_files([self.path + "\\.templates\\Fish.xlsx"]))
        self.b_HSC.grid(sticky=tk.EW, row=7, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_run = tk.Button(top, fg="gray60", width=30, bg="white", text="iii) Run (generate habitat condition)",
                               anchor='w', command=lambda: self.user_message("CONFIRM HYDRAULIC CONDITION!"))
        self.b_run.grid(sticky=tk.EW, row=8, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW", command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=9, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def make_flow_dur(self):
        msg0 = "Select flow series (.XLSX format) for flow duration curve generation."
        showinfo("INFORMATION ", msg0)
        flow_series_xlsx = askopenfilename(initialdir=os.path.dirname(__file__) + "\\FlowDurationCurves\\",
                                           title="Select flow series workbook (xlsx)",
                                           filetypes=[("Workbooks", "*.xlsx")])
        flow_processor = cq.SeasonalFlowProcessor(flow_series_xlsx)
        for species in self.fish_applied.keys():
            for ls in self.fish_applied[species]:
                flow_processor.get_fish_seasons(species, ls)
        last_file = flow_processor.make_fish_flow_duration()
        self.b_flowdur_make.config(bg="PaleGreen1")
        try:
            webbrowser.open(last_file)
        except:
            pass

    def open_files(self, f_list):
        for _f in f_list:
            self.user_message("Do not forget to save files after editing ...")
            fg.open_file(_f)

    def prepare_discharge_file(self):
        for species in self.fish_applied.keys():
            for ls in self.fish_applied[species]:
                fish_shortname = str(species).lower()[0:2] + str(ls[0])
                # copy spreadsheet with discharge dependencies (if not yet existent)
                spreadsheet_handle = cmkt.MakeFishFlowTable()
                template = os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\Q_def_hab_template_" + str(
                                           self.unit) + ".xlsx"
                spreadsheet_handle.set_directories(self.condition, template)
                self.discharge_xlsx.append(spreadsheet_handle.make_condition_fish_xlsx(fish_shortname))

                # get discharge statistics and write them to workbook
                Q_stats = cq.FlowAssessment()
                Q_stats.get_flow_data(self.xlsx_flow_dur)
                exceedances = []

                error_msg = []
                for qq in spreadsheet_handle.discharges:
                    try:
                        exceedances.append(Q_stats.interpolate_flow_exceedance(float(qq)) * 100.0)  # in percent
                    except:
                        error_msg.append("Invalid exceedances found for Q_flowdur = " + str(qq) + ".")
                        exceedances.append(0.0)

                spreadsheet_handle.write_data_column("E", 4, exceedances)
                spreadsheet_handle.save_close_wb()
                spreadsheet_handle.copy_wb(spreadsheet_handle.wb_out_name,
                                           spreadsheet_handle.wb_out_name.split(".xlsx")[0] + "_cov.xlsx")

                if error_msg.__len__() > 0:
                    showinfo("ERRORS FOUND", "\n".join(error_msg))
        self.b_flowdur_select.config(bg="PaleGreen1")

    def remake_buttons(self):
        self.b_c_select.config(bg="PaleGreen1")
        self.b_Q.config(fg="black", text="View discharge dependency file (xlsx workbook)",
                        command=lambda: self.open_files(self.discharge_xlsx), bg="PaleGreen1")
        self.b_run.config(fg="black", text="iii) Run (generate habitat condition)", command=lambda: self.run_raster_calc())

    def run_raster_calc(self):
        msg0 = "Analysis takes a while. \nPython windows seem unresponsive in the meanwhile. \nCheck console messages."
        msg1 = "\n\nClick OK to start DHSI and VHSI calculation."
        showinfo("INFORMATION ", msg0 + msg1)
        hhsi = chsi.HHSI(self.dir_input_ras, self.condition, self.unit)

        hhsi.make_hhsi(self.fish_applied, self.boundary_shp)
        self.top.bell()

        try:
            if not hhsi.error:
                fg.open_folder(hhsi.path_hsi)
                self.l_run_info.config(fg="forest green", text="RUN SUCCESSFULLY COMPLETED (close window)")
                self.b_run.config(width=30, bg="PaleGreen1", text="RE-run (generate habitat condition)",
                                  command=lambda: self.run_raster_calc())
            else:
                self.l_run_info.config(fg="red", text="RUN COMPLETED WITH ERRORS")
                self.b_run.config(bg="salmon", text="RE-run (generate habitat condition)",
                                  command=lambda: self.run_raster_calc())
        except:
            pass
        try:
            hhsi.clear_cache()
        except:
            pass
        showinfo("COMPUTATION FINISHED", "Check logfile (logfile.log).")

    def select_condition(self):
        items = self.lb_condition.curselection()
        self.condition = [self.condition_list[int(item)] for item in items][0]
        self.dir_input_ras = self.path_lvl_up + "\\01_Conditions\\" + self.condition + "\\"

        if os.path.exists(self.dir_input_ras):
            self.l_inpath_curr.config(fg="forest green", text="Selected: " + str(self.dir_input_ras))
        else:
            self.l_inpath_curr.config(fg="red", text="SELECTION ERROR                                 ")
        self.prepare_discharge_file()
        self.remake_buttons()

    def select_flowdur_xlsx(self):
        self.xlsx_flow_dur = askopenfilename(initialdir=self.path + "\\FlowDurationCurves\\", title="Select xlsx file containing the discharge duration curve (Q_flowdur-days)")
        self.b_flowdur_select.config(
            text="i) Selected flow duration curve: " + str(self.xlsx_flow_dur).split("/")[-1].split("\\")[-1],
            fg="forest green")
        self.b_c_select["state"] = "normal"

    def user_message(self, msg):
        showinfo("INFO", msg)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()
