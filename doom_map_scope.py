# -*- coding: utf-8 -*-
#! /usr/bin/env python3
"""
Module Name: doom_map_scope.py
Description: Interactive map viewer for DOOM(1/2) levels.
Author: Daniel Carroll (InZane84)
Date: 1/13/2025
License: MIT
"""
"""
Copyright (c) 2025 Daniel Carroll

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

import dearpygui.dearpygui as dpg
import omg
import time


dpg.create_context()
dpg.create_viewport(title="DOOM Map Scope", width=1280, height=720)
dpg.show_documentation()
dpg.show_imgui_demo()

def cb_scale_slider(sender, app_data):
    dpg.set_global_font_scale(app_data)

def cb_remove_drawlist():
    dpg.delete_item("drawlist")

"""def cb_mapscale_slider(sender, app_data):
    # can't get this working as needed
    snapped_value = round(app_data / 50) * 30
    print(f"Snapped value: {snapped_value}")
    current_value = dpg.get_value(sender)
    print(f"Current value: {current_value}")
    if current_value != snapped_value:
        dpg.set_value(sender, snapped_value)
        wadfile.maxpixels = snapped_value
        wadfile.plot_map(sender, snapped_value, level=None)"""

def combo_callback(sender, app_data):
    print(f"Selected Option: {app_data}")
    match app_data:
        case "100":
            wadfile.maxpixels = 2000
            wadfile.plot_map(sender, app_data, level=None)
        case "75":
            wadfile.maxpixels = 1500
            wadfile.plot_map(sender, app_data, level=None)
        case "50":
            wadfile.maxpixels = 1000
            wadfile.plot_map(sender, app_data, level=None)
        case "25":
            wadfile.maxpixels = 750
            wadfile.plot_map(sender, app_data, level=None)
        case "0":
            wadfile.maxpixels = 500
            wadfile.plot_map(sender, app_data, level=None)

"""def cb_open_wadfile(sender, app_data):
    
    print(f"Wadfile(s) selected: { app_data['file_path_name'] }")
    dpg.set_item_label("map_viewer_id", f"Map Viewer - Wadfile: { app_data['file_path_name'] }")
"""

class WadFile_IO:
    def __init__(self):
        self.wadfile = None
        self.level = None
        self.maxpixels = 1000
        #self.map_names = []
        #self.map_data = []

    def open_wadfile(self, sender, app_data):
        self.wadfile = omg.WAD(app_data['file_path_name'])
        dpg.set_item_label("map_viewer_id", f"Map Viewer - Wadfile: { app_data['file_path_name'] }")
        dpg.configure_item("show_map_btn", enabled=True)
        #self.map_names = self.wadfile.maps.keys()
        #self.map_data = [self.wadfile.maps[map_name] for map_name in self.map_names]

    def plot_map(self, sender, app_data, level):
        if self.wadfile:

            dpg.delete_item("drawlist")

            if not self.level:
                self.level = "MAP25"

            scales = 0
            total  = 0
            #alias = 3
            alias = 0
            border = 4
            sptdim = 10
            txtdim = 16
            dmtcol = (0,   176,   0) # deathmatch green
            blucol = (0,   112, 255) # CTF team blue
            redcol = (240,   0,   0) # CTF team red
            grncol = (0,   176,   0) # CTF team green
            txtcol = (255, 216,   0) # yellow text
            whtcol = (255, 255, 255) # white border

            #self.maxpixels = 1000
            reqscale = 0

            dmspawns = False
            ctfspawns = False
            
            wad_level = omg.MapEditor(self.wadfile.maps[self.level])

            # determine scale = map area unit / pixel
            xmin = min([v.x for v in wad_level.vertexes])
            xmax = max([v.x for v in wad_level.vertexes])
            ymin = min([-v.y for v in wad_level.vertexes])
            ymax = max([-v.y for v in wad_level.vertexes])
            xsize = xmax - xmin
            ysize = ymax - ymin
            scale = (self.maxpixels - border*2) / float(max(xsize, ysize))

            # tally for average scale or compare against requested scale
            if reqscale == 0:
                scales += scale
                total += 1
            else:
                if scale > 1.0 / reqscale:
                    scale = 1.0 / reqscale

            # size up if anti-aliasing
            ascale = scale * alias
            aborder = border * alias

            # convert all numbers to (aliased) image space
            axmin = int(xmin * ascale)
            aymin = int(ymin * ascale)
            xmin  = int(xmin * scale)
            ymin  = int(ymin * scale)
            axsize = int(xsize * ascale) + aborder*2;
            aysize = int(ysize * ascale) + aborder*2;
            xsize  = int(xsize * scale) + border*2;
            ysize  = int(ysize * scale) + border*2;
        
            for v in wad_level.vertexes:
                v.x = int(v.x * scale); v.y = int(v.y * -scale)
        
            if dmspawns or ctfspawns:
                for t in wad_level.things:
                    t.x = int(t.x * ascale); t.y = int(t.y * -ascale)

            # draw 1s lines after 2s lines so 1s lines are never obscured
            wad_level.linedefs.sort(key=lambda a: not a.two_sided)


            with dpg.drawlist(width=xsize, height=ysize, id="drawlist", parent="map_viewer_id"):
                    

                # draw all lines from their vertexes
                for line in wad_level.linedefs:
                    p1x = wad_level.vertexes[line.vx_a].x - xmin + border
                    p1y = wad_level.vertexes[line.vx_a].y - ymin + border
                    p2x = wad_level.vertexes[line.vx_b].x - xmin + border
                    p2y = wad_level.vertexes[line.vx_b].y - ymin + border
                    color = (175, 0, 0)
                    if line.two_sided:   color = (100, 100, 150)
                    #if line.special:    color = (220, 130, 50)
                    #if line.id > defid: color = (200, 110, 30)

                    # draw multiple lines to simulate thickness
                    """
                    draw.line((p1x, p1y,   p2x, p2y),   fill=color)
                    draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
                    draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
                    draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
                    draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)
                    """

                    dpg.draw_line((p1x, p1y), (p2x, p2y), color=color, thickness=1)
                    #dpg.render_dearpygui_frame()
                    #print("Drawing line: {}", {line.front})

                    # DON'T DELETE THIS!===================
                    delay = dpg.get_value("delay_slider")
                    time.sleep(float(delay))
                    # =====================================
                    # scale up to anti-alias
                    """
                    if alias > 1:
                        im = im.resize((axsize, aysize))
                        del draw
                        draw = ImageDraw.Draw(im)
                        """

                    # scale down to anti-alias
                    """
                    if alias > 1:
                        im = im.resize((xsize, ysize), Image.ANTIALIAS)
                    """

        if not self.wadfile:
            print("load a wad first")

    def get_map(self, map_name):
        return self.wadfile.maps[map_name]

    def get_map_names(self):
        return self.map_names

    def get_map_data(self):
        return self.map_data

    def close_wadfile(self):
        self.wadfile = None
        self.map_names = []
        self.map_data = []

wadfile = WadFile_IO()


with dpg.file_dialog(directory_selector=False, show=False, callback=wadfile.open_wadfile, id="file_dialog_id", width=800, height=400):
    dpg.add_file_extension(".wad", color=(255, 0, 0))
    dpg.add_file_extension(".iwad")
    dpg.add_file_extension(".pwad")
    dpg.add_file_extension("*.*")
    #dpg.add_file_extension(".pk3")
    #dpg.add_file_extension(".wad2")
    #dpg.add_file_extension(".wad3")
    #dpg.add_file_extension(".deh")
    #dpg.add_file_extension(".bex")

with dpg.window(label="UI Scaling", width=200, height=100, id="scale_slider_window", show=False):
    dpg.add_slider_float(label="Scale", default_value=1.0, min_value=0.5, max_value=10.0, callback=cb_scale_slider)

with dpg.viewport_menu_bar():
    dpg.add_menu_item(label="UI Scaling...", callback= lambda: dpg.show_item("scale_slider_window"))

with dpg.window(label="Map Viewer", width=1280, height=720, id="map_viewer_id"):
    #dpg.show_documentation()
    with dpg.child_window(height=65, no_scrollbar=True, autosize_x=True):
        with dpg.collapsing_header(label="Map Viewer Options"):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Show MAP01", callback=wadfile.plot_map, tag="show_map_btn")
                dpg.add_button(label="Clear...", callback=cb_remove_drawlist)
                #dpg.add_slider_float(label="delay", default_value=0.000, min_value=0.000, max_value=0.100, tag="delay_slider", width=200)
                #dpg.add_slider_int(label="Map Scale", default_value=1000, min_value=250, max_value=2500, callback=cb_mapscale_slider, clamped=True)
            #with dpg.group(horizontal=True):
                dpg.add_text("Delay:")
                dpg.add_combo(width=100, items=["0.000", "0.001", "0.005", "0.010", "0.050", "0.100"], default_value="0.000", tag="delay_slider")
                dpg.add_text("Map Scale:")
                dpg.add_combo(width=100, items=["100", "75", "50", "25", "0"], default_value="Scale 50", callback=combo_callback)
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Open a WAD file...", callback= lambda: dpg.show_item("file_dialog_id"))
            
            #dpg.show_documentation()
            #dpg.add_menu_item(label="Save")
            #dpg.add_menu_item(label="Exit")

dpg.setup_dearpygui()


dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
