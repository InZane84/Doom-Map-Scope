# -*- coding: utf-8 -*-
#! /usr/bin/env python3
"""
Module Name: doom_map_scope.py
Description: Interactive map viewer for DOOM(1/2) levels.
Author: InZane84
Date: 3/30/2026
License: MIT
"""
"""
Copyright (c) 2026 InZane84

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""
import time, re, threading, zipfile, io, tempfile, os
import dearpygui.dearpygui as dpg
from omg.wad import WAD
from omg.mapedit import MapEditor
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import TypedDict

# need to ask about this class as it relates
# to the annotated return type
class IdGamesEntry(TypedDict):
    """To satisfy pylance..."""
    name: str
    url: str
    is_folder: bool
    type: str


def get_idgames_html(url: str) -> list[IdGamesEntry]:
    """Get the dir listings from a url"""
    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        entries = []
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if not href or not text or text == "Parent Directory" or href == '../':
                continue
            full_url = urljoin(url, href)
            is_folder = href.endswith('/')
            entries.append({'name': text,
                            'url': full_url,
                            'is_folder': is_folder,
                            'type': 'folder' if is_folder else 'file'})
        return entries
    except Exception as e:
        print(f"Error parsing directory: {e}")
        return []
    
class IdGamesBrowser:
    """Browser for idGames archive"""

    def __init__(self, root_url=None):
        self.root_url = root_url
        self.current_url = root_url
        self.current_entries = []
        self.history_stack = []
        self.window_tag = "idgames_browser_window"
        self.table_tag = "idgames_table"
        self.path_tag = "current_path"
        
        self.create_window()
    
    def create_window(self):
        """Create the DearPyGui window"""
        with dpg.window(label="idGames Browser", 
                       width=900, 
                       height=600, 
                       pos=(50, 50),
                       tag=self.window_tag):
            
            # Navigation bar
            with dpg.group(horizontal=True):
                dpg.add_button(label="◄ Back", 
                             width=80, 
                             callback=self.go_back)
                #dpg.add_same_line()
                dpg.add_button(label="⌂ Home", 
                             width=80, 
                             callback=self.go_home)
                #dpg.add_same_line()
                dpg.add_text("", tag=self.path_tag, wrap=700)
            
            # Directory table
            with dpg.table(header_row=True, 
                         row_background=True,
                         borders_innerH=True,
                         borders_outerH=True,
                         borders_innerV=True,
                         borders_outerV=True,
                         tag=self.table_tag):
                dpg.add_table_column(label="Name", width=500)
                dpg.add_table_column(label="Type", width=100)
        
        # Load initial directory
        self.navigate_to_url(self.current_url)
    
    def navigate_to_url(self, url):
        """Navigate to a new URL and update the table"""
        
        # Add current URL to history before navigating
        if self.current_url != url:
            self.history_stack.append(self.current_url)
        
        self.current_url = url
        self.current_entries = get_idgames_html(url)
        
        # Clear and rebuild table
        if dpg.does_item_exist(self.table_tag):
            dpg.delete_item(self.table_tag)
        with dpg.table(header_row=True, 
                 row_background=True,
                 borders_innerH=True,
                 borders_outerH=True,
                 borders_innerV=True,
                 borders_outerV=True,
                 tag=self.table_tag,
                 parent=self.window_tag):
            dpg.add_table_column(label="Name", width=500)
            dpg.add_table_column(label="Type", width=100)
        
        # Skip header row and rebuild
        for entry in self.current_entries:
            with dpg.table_row(parent=self.table_tag):
                if entry['is_folder']:
                    dpg.add_button(label=entry['name'], 
                                 width=400,
                                 callback=lambda s, a, u=entry['url']: self.navigate_to_url(u))
                else:
                    if entry['name'].lower().endswith('.wad'):
                        dpg.add_button(label=entry['name'],
                                     width=400,
                                     callback=lambda s, a, f=entry['name']: self.download_wad_callback(f))
                    else:
                        dpg.add_text(entry['name'])
                
                dpg.add_text(entry['type'])
        
        # Update breadcrumb/title
        dpg.set_value(self.path_tag, self.current_url)
    
    def go_back(self):
        """Go back to previous directory"""
        if self.history_stack:
            url = self.history_stack.pop()
            self.navigate_to_url(url)
    
    def go_home(self):
        """Go back to root idGames directory"""
        self.history_stack.clear()
        self.navigate_to_url(self.root_url)
    
    '''def download_wad_callback(self, filename):
        """Handle WAD download when clicked"""
        download_url = urljoin(self.current_url, filename)
        print(f"Download: {download_url}")
        # Pass to your wadfile_downloader here
        # wadfile_downloader(download_url)
    '''

def get_wad_metadata():
    """get the filename and title values from the
       WAD Details window.   
    """

    filename = None
    title = None
    #TODO: Have to fix this shit...
    try:
        window_items = dpg.get_item_children("Wadfile Details")[1]
        
        for item_id in window_items:
            if dpg.get_item_type(item_id) == "table":
                table_rows = dpg_get_item_children(item_id)[1]
                for row in table_rows:
                    row_cells = dpg.get_item_children(row)[1]
                    field = dpg.get_value(row_cells[0])
                    value = dpg.get_value(row_cells[1])
                    if field == 'filename':
                        filename = value
                    if field == 'title':
                        title = value
                    if filename and title:
                        return filename, title
    except:
        return None

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
    """Callback for the map scale combo box."""

    # TODO: after switching maps the combo box is stuck on the last map!

    print(f"Selected Option: {app_data}")
    match app_data:
        case "100":
            wadfile.maxpixels = 2000
            wadfile.plot_map(sender, app_data, level=wadfile.level)
        case "75":
            wadfile.maxpixels = 1500
            wadfile.plot_map(sender, app_data, level=wadfile.level)
        case "50":
            wadfile.maxpixels = 1000
            wadfile.plot_map(sender, app_data, level=wadfile.level)
        case "25":
            wadfile.maxpixels = 750
            wadfile.plot_map(sender, app_data, level=wadfile.level)
        case "0":
            wadfile.maxpixels = 500
            wadfile.plot_map(sender, app_data, level=wadfile.level)

def map_selection_callback(sender, app_data):
    """Callback for the map selection combo box."""
    print(f"sender: {sender}")
    print(f"app_data: {app_data}")
    wadfile.level = app_data
    wadfile.plot_map(sender, app_data, level=app_data)

"""def cb_open_wadfile(sender, app_data):
    
    print(f"Wadfile(s) selected: { app_data['file_path_name'] }")
    dpg.set_item_label("map_viewer_id", f"Map Viewer - Wadfile: { app_data['file_path_name'] }")
"""

def download_wadfile(sender, app_data):
    """spawn a thread which calls wadfile_downloader"""

    #TOO:Is this function needed? Can be moved into wadfile_downloader?
    
    # disable the OK btn on the download widget...
    #dpg.configure_item(sender, enabled=False)
    user_input = dpg.get_value("user_input_field")
    print(f"process_idgames_input: {user_input}")
    
    #dpg.set_value("loading_status_text", "Downloading from idgames...")
    
    #downloader_thread = threading.Thread(target=run_async_task, args=(user_input,))
    #downloader_thread.start()
    threading.Thread(target=wadfile_downloader,
                     args=(user_input,),
                     daemon=True).start()
    print("below thread!")

def wadfile_downloader(user_input):
    """get a wadfile over http from the idGames database"""
    wad_id = user_input
    print(f"wad_id: {wad_id}")
    wad_id = user_input.split("://")[-1].strip()
    
    try:
        with httpx.Client(follow_redirects=True) as client:
            api_url = f"https://doomworld.com/idgames/api/api.php?action=get&id={wad_id}&out=json"
            print(f"Requesting: {api_url}")
            response = client.get(api_url)
            data = response.json()
            
            #viewport_width = dpg.get_viewport_client_width()
            #viewport_height = dpg.get_viewport_client_height()

            # show wadfile info ============================================
            with dpg.window(label="Wadfile Details",
                            width=1000,
                            height=1175,
                            pos=(1350,
                                 50)):
                with dpg.table(header_row=True,
                               row_background=True,
                               borders_innerH=True,
                               borders_outerH=True,
                               borders_innerV=True,
                               borders_outerV=True):
                    dpg.add_table_column(label="Field", width_fixed=True, width=100)
                    dpg.add_table_column(label="Value", width_fixed=False)
                    for key, value in data["content"].items():
                        with dpg.table_row():
                            dpg.add_text(str(key), color=(255, 0, 0))
                            dpg.add_text(str(value), color=(255, 100, 0), wrap=500)
                            '''dpg.add_selectable(label=str(value),
                                               span_columns=False,
                                               width=800)
                                               '''
            # ==============================================================
            # download wadfile
            if 'content' in data:
                file_path = data['content']['dir'].strip('/')
                file_name = data['content']['filename']
                download_url = f"https://gamers.org/pub/idgames/{file_path}/{file_name}"
                #download_url = f"https://doomworld.org/idgames/{file_path}/{file_name}"
                print(f"Downloading from: {download_url}")                
                _headers = {"User-Agent": "Mozilla/5.0 (Doom Map Scope)"}
                r = client.get(download_url, headers=_headers)
                r.raise_for_status() #check for 404
                
                print(f"wadfile_downloader: downloading wadfile...")
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    wads = [f for f in z.namelist() if f.lower().endswith('.wad')]
                    print(f"wad is: {len(wads)}")
                    if wads:
                        print("WE HAVE A WAD")
                        # IMPORTANT: Use dpg.configure_item or set_value to update 
                        # the UI from a background thread safely.
                        #dpg.set_value("status_text", f"Loaded: {wads[0]}")
                        wad_data = z.read(wads[0])
                        
                        # Try a fix reccomended by Claude...
                        # my way
                        #global wadfile
                        #wadfile = WadFile_IO()
                        # Claude's way...
                        wadfile.open_wadfile(sender='foo',
                                             app_data=io.BytesIO(wad_data))
                        print(f"Successfully loaded {wads[0]}")
    except httpx.ConnectError:
        dpg.set_value("status_text", "Error: Could not connect to idGames")
    except Exception as e:
        dpg.set_value("status_text", f"Error: {str(e)}")
    finally:
        pass
        #dpg.configure_item(args[sender], enabled=True)


class WadFile_IO:
    """Class for handling WAD file I/O operations."""
    def __init__(self):
        
        # set by open_wadfile
        self.wadfile = None

        # set by plot_map
        self.level = None
        self.maxpixels = 1000

        # populatated once open_wadfile is called
        self.map_ids = None

        # set by identify_game
        self.game = None
        
        #self.map_data = None

        # is a wadfile loaded
        self._isloaded = None

    def _wadfile_to_tempfile(self, app_data):
        """Write a loaded wadfile from idGames to /tmp"""
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wad") as tmp:
            tmp.write(app_data.getvalue())
            tmp_path = tmp.name
            self.wadfile = WAD(tmp_path)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            self._isloaded = True

    def open_wadfile(self, sender, app_data):
        """Open a wadfile and load the map data."""

        # local wadfile
        if isinstance(app_data, dict) and 'file_path_name' in app_data:
            print(f"Wadfile(s) selected: { app_data['file_path_name'] }")
            self.wadfile = WAD(app_data['file_path_name'])
            self._isloaded = True
            dpg.set_item_label("map_viewer_id", f"Map Viewer - WAD file: { app_data['file_path_name'] }")

        # downloaded wadfile
        elif isinstance(app_data, io.BytesIO):
            print(f"open_wadfile: io.BytesIO")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wad") as tmp:
                tmp.write(app_data.getvalue())
                tmp_path = tmp.name
                self.wadfile = WAD(tmp_path)

                # SET THE TITLEBAR LABEL FOR THE MAP VIEWER HERE!
                dpg.set_item_label("map_viewer_id", f"idGames WAD file: {get_wad_metadata()}")
                print(f"loaded wadfile: {tmp_path}")
                print(f'wadfile is: {self.wadfile}')
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            self._isloaded = True
        
        #dpg.configure_item("show_map_btn", enabled=True)
        
        # get the key from wadfile.maps to identify the game format
        first_key = self.wadfile.maps.keys()[0]
        print(f"first key is: {first_key}")

        if "E" in first_key:
            self.game = "DOOM"
        elif "MAP" in first_key:
            self.game = "DOOM2"
        else:
            self.game = "UNKNOWN/UNSUPPORTED"
        self.wadfile.game = self.game
        print(f"self.wadfile.game is: {self.game}")

        #self.game = GameIdentify().identify_game(first_key)
        # now set the regex pattern for the map IDs
        if self.game == "DOOM":
            mapID_format = r"E\d{1}M\d{1}"
            print(f"Game format: {self.game}")
        elif self.game == "DOOM2":
            mapID_format = r"MAP\d{2}"
            print(f"Game format: {self.game}")
        else:
            print("Unsupported game format!")
            return
        self.get_map_ids(self.wadfile.maps, mapID_format)
        print(f"Map IDs: {self.map_ids}")

        maps_sorted = sorted(self.map_ids)

        if dpg.does_item_exist("map_selection_box"):
            dpg.configure_item("map_selection_box",
                               items=maps_sorted,
                               default_value=wadfile.map_ids[0])
        else:
            with dpg.group(horizontal=True, parent="map_viewer_options"):
                dpg.add_text("Select Map:")
                dpg.add_combo(items=maps_sorted,
                              default_value=wadfile.map_ids[0],
                              parent="map_viewer_options",
                              width=100, tag="map_selection_box",
                              callback=map_selection_callback)


    def plot_map(self, sender, app_data, level=None):
        """Plot the map data to the map viewer window."""
        if self.wadfile:

            dpg.delete_item("drawlist")

            if not self.level:
                self.level = level

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
            
            wad_level = MapEditor(self.wadfile.maps[level])

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
                    color = (180, 40, 0)
                    if line.two_sided:   color = (120, 85, 0)
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

                    if line.two_sided:
                        thickness = 1
                    else:
                        thickness = 1.5

                    dpg.draw_line((p1x, p1y), (p2x, p2y), color=color, thickness=thickness)
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

    def get_map_ids(self, map_dict, mapID_format):
        """Get the map names from the WAD file."""
        def find_maps(map_dict, mapID_format):
            regex = re.compile(mapID_format)
            matched_keys = [key for key in map_dict.keys() if regex.match(key)]
            return matched_keys
        self.map_ids = find_maps(map_dict, mapID_format)

    def get_map_data(self):
        return self.map_data

    def close_wadfile(self):
        self.wadfile = None
        self.map_names = []
        self.map_data = []

wadfile = WadFile_IO()

class GameIdentify:
    """Class for identifying the game format of the WAD file."""
    def __init__(self):
        # set by identify_game
        self.game = None
    
    def identify_game(self, map_name):
        if "E" in map_name:
            self.game = "DOOM"
        elif "MAP" in map_name:
            self.game = "DOOM2"
        else:
            self.game = "UNKNOWN/UNSUPPORTED"
        
        wadfile.game = self.game
    
    
    # Delete me!
    """def switch_map(self, map_name):
        
        map_format = self.identify_game(map_name)
        
        if map_format == "DOOM":
            return omg.WAD(map_name)
        elif map_format == "DOOM2":
            return omg.WAD(map_name)
        else:
            print(f"Unsupported map format: {map_name}")"""
    # ===================================================

#game = GameIdentify()

def main():

    

    dpg.create_context()

    #TODO: dynamically size viewport according to host resolution
    dpg.create_viewport(title="DOOM Map Scope", width=2400, height=1250)
    #dpg.show_documentation()
    #dpg.show_imgui_demo()

    with dpg.file_dialog(directory_selector=False, show=False, callback=wadfile.open_wadfile, id="file_dialog_id", width=800, height=400):
        # TODO: Fix this shit!
        dpg.add_file_extension(".wad", color=(255, 0, 0))
        dpg.add_file_extension(".WAD", color=(0, 255, 0))
        dpg.add_file_extension(".iwad")
        dpg.add_file_extension(".pwad")
        dpg.add_file_extension(".*")
        #dpg.add_file_extension(".pk3")
        #dpg.add_file_extension(".wad2")
        #dpg.add_file_extension(".wad3")
        #dpg.add_file_extension(".deh")
        #dpg.add_file_extension(".bex")

    with dpg.window(label="UI Scaling", width=200, height=100, id="scale_slider_window", show=False):
        dpg.add_slider_float(label="Scale", default_value=1.0, min_value=0.5, max_value=10.0, callback=cb_scale_slider)

    with dpg.viewport_menu_bar():
        dpg.add_menu_item(label="UI Scaling...", callback= lambda: dpg.show_item("scale_slider_window"))

    with dpg.window(label="Map Viewer", width=1280, height=1175, pos=(25, 50), id="map_viewer_id"):
        with dpg.child_window(height=65, no_scrollbar=True, autosize_x=True):
            with dpg.collapsing_header(label="Map Viewer Options"):
                with dpg.group(horizontal=True, tag="map_viewer_options"):
                    #dpg.add_button(label="Show MAP01", callback=wadfile.plot_map, tag="show_map_btn")

                    # trigger this when the ok button is clicked in the idgames downloader widget
                    #dpg.add_text("Loading wadfile...", tag="loading_status_text", color=(200, 200, 200))

                    dpg.add_button(label="Clear Map", callback=cb_remove_drawlist)
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
                dpg.add_menu_item(label="Open a wadfile from the idgames database...", callback=lambda: dpg.show_item("idgames_wad_id"))

    with dpg.window(label="Enter the 'idgames://123' ID to open",
                    modal=True,
                    show= False,
                    tag="idgames_wad_id",
                    no_title_bar=False):
        dpg.add_text("idgames id URL")
        dpg.add_input_text(tag="user_input_field", hint="idgames address...")
        with dpg.group(horizontal=True):
            dpg.add_button(label="OK",
                           width=75,
                           callback=download_wadfile)
            # Add logic to hide the window after clicking OK
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("idgames_wad_id", show=False))



    dpg.setup_dearpygui()

    idgames_browser = IdGamesBrowser("https://www.gamers.org/pub/idgames/")

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()