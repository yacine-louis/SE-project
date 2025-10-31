import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ExifTags
import os
import mimetypes
from datetime import datetime
import webbrowser

# --- Configurable layout & style ---
LEFT_COL_WIDTH = 250
IMAGE_PREVIEW_SIZE = 150
IMAGE_BORDER_COLOR = "#000000"
IMAGE_BORDER_WIDTH = 4

root = tk.Tk()
root.title("Route Plotter from Images")
root.geometry("700x700")
root.resizable(False, False)

# --- Center window ---
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (width // 2)
y = (screen_height // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

# --- Grid configuration ---
root.grid_columnconfigure(0, minsize=LEFT_COL_WIDTH, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

# --- NAVBAR ---
navbar_left = tk.Frame(root, bg="#1E90FF", height=64, width=LEFT_COL_WIDTH)
navbar_right = tk.Frame(root, bg="#104E8B", height=64)
navbar_left.grid(row=0, column=0, sticky="nsew")
navbar_right.grid(row=0, column=1, sticky="nsew")
navbar_left.grid_propagate(False)
navbar_right.grid_propagate(False)

# --- MAIN CONTENT ---
main_left = tk.Frame(root, bg="lightblue", width=LEFT_COL_WIDTH)
main_right = tk.Frame(root, bg="lightgreen")
main_left.grid(row=1, column=0, sticky="nsew")
main_right.grid(row=1, column=1, sticky="nsew")
main_left.grid_propagate(False)
main_left.pack_propagate(False)

# --- Scrollable container for images ---
canvas = tk.Canvas(main_left, bg="lightblue", highlightthickness=0)
v_scroll = tk.Scrollbar(main_left, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=v_scroll.set)
v_scroll.pack(side="right", fill="y")
v_scroll.config(width=14)
canvas.pack(side="left", fill="both", expand=True)

images_frame = tk.Frame(canvas, bg="lightblue")
canvas_window = canvas.create_window((0, 0), window=images_frame, anchor="nw")

def _on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

def _on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

images_frame.bind("<Configure>", _on_frame_configure)
canvas.bind("<Configure>", _on_canvas_configure)

def _on_mousewheel(event):
    canvas.yview_scroll(-1 * int(event.delta / 120), "units")

def _bind_mousewheel(event):
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

def _unbind_mousewheel(event):
    canvas.unbind_all("<MouseWheel>")

canvas.bind("<Enter>", _bind_mousewheel)
canvas.bind("<Leave>", _unbind_mousewheel)

# --- Data structures ---
loaded_images = []
image_frames = []
image_data = []  # store metadata for route plotting
selected_border = {'widget': None}

# --- Helper functions for EXIF ---
def _rational_to_float(rat):
    try:
        return float(rat[0]) / float(rat[1])
    except Exception:
        try:
            return float(rat)
        except Exception:
            return 0.0

def _dms_to_decimal(dms, ref):
    try:
        deg = _rational_to_float(dms[0])
        minute = _rational_to_float(dms[1])
        sec = _rational_to_float(dms[2])
        dec = deg + (minute / 60.0) + (sec / 3600.0)
        if ref in ['S', 'W']:
            dec = -dec
        return round(dec, 6)
    except Exception:
        return 'N/A'

def extract_exif(image):
    exif_data = {}
    try:
        raw = image._getexif() or {}
        for tag, value in raw.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            exif_data[decoded] = value
    except Exception:
        pass
    return exif_data

def parse_gps(exif):
    gps_lat = gps_lon = gps_alt = 'N/A'
    gps_info = exif.get('GPSInfo') if exif else None
    if gps_info:
        gps = {}
        for t, val in gps_info.items():
            sub_tag = ExifTags.GPSTAGS.get(t, t)
            gps[sub_tag] = val

        lat = gps.get('GPSLatitude')
        lat_ref = gps.get('GPSLatitudeRef')
        lon = gps.get('GPSLongitude')
        lon_ref = gps.get('GPSLongitudeRef')
        alt = gps.get('GPSAltitude')

        if lat and lat_ref:
            gps_lat = _dms_to_decimal(lat, lat_ref)
        if lon and lon_ref:
            gps_lon = _dms_to_decimal(lon, lon_ref)
        if alt:
            try:
                gps_alt = round(_rational_to_float(alt), 2)
            except Exception:
                gps_alt = 'N/A'

    return gps_lat, gps_lon, gps_alt

# --- Metadata panel setup ---
info_frame = tk.Frame(main_right, bg="lightgreen")
info_frame.pack(fill="both", expand=True, padx=10, pady=10)

meta_fields = {
    'CreateDate': tk.StringVar(value='N/A'),
    'ModifyDate': tk.StringVar(value='N/A'),
    'GPSLatitude': tk.StringVar(value='N/A'),
    'GPSLongitude': tk.StringVar(value='N/A'),
    'GPSAltitude': tk.StringVar(value='N/A'),
    'ImageWidth': tk.StringVar(value='N/A'),
    'ImageHeight': tk.StringVar(value='N/A'),
    'FileName': tk.StringVar(value='N/A'),
    'FileSize': tk.StringVar(value='N/A'),
    'FileType': tk.StringVar(value='N/A'),
    'FileExtension': tk.StringVar(value='N/A'),
}

for key, var in meta_fields.items():
    row = tk.Frame(info_frame, bg="lightgreen")
    row.pack(fill='x', pady=2)
    tk.Label(row, text=f"{key}:", width=15, anchor='w', bg="lightgreen", font=("Arial", 10, "bold")).pack(side='left')
    tk.Label(row, textvariable=var, anchor='w', bg="lightgreen", font=("Arial", 10)).pack(side='left')

# --- Upload images ---
def upload_image():
    file_paths = filedialog.askopenfilenames(
        title="Select Image(s)",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
    )
    if not file_paths:
        messagebox.showwarning("No Selection", "No image was selected.")
        return

    for file_path in file_paths:
        try:
            img = Image.open(file_path)
            img.thumbnail((IMAGE_PREVIEW_SIZE, IMAGE_PREVIEW_SIZE))
            photo = ImageTk.PhotoImage(img)
            loaded_images.append(photo)

            # Extract EXIF and GPS
            exif = extract_exif(img)
            lat, lon, alt = parse_gps(exif)
            stat = os.stat(file_path)
            create_ts = datetime.fromtimestamp(stat.st_ctime)

            # Store route data
            image_data.append({
                'path': file_path,
                'lat': lat,
                'lon': lon,
                'date': create_ts
            })

            # Display in UI
            border_frame = tk.Frame(images_frame, bg=IMAGE_BORDER_COLOR, padx=IMAGE_BORDER_WIDTH, pady=IMAGE_BORDER_WIDTH)
            border_frame.pack(pady=(10, 5))
            image_frames.append(border_frame)

            content_frame = tk.Frame(border_frame, bg="white")
            content_frame.pack(expand=True, fill="both")

            img_label = tk.Label(content_frame, image=photo, bg="white")
            img_label.pack(expand=True, fill="both")

            remove_btn = tk.Button(
                content_frame,
                text="×",
                font=("Arial", 12, "bold"),
                fg="red",
                bg="white",
                relief="solid",
                bd=1,
                width=2,
                height=1,
                cursor="hand2",
                command=lambda f=border_frame: remove_image(f)
            )
            remove_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)
            img_label.bind("<Button-1>", lambda e, p=file_path, b=border_frame: on_image_click(p, b))

        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

# def remove_image(frame):
#     if selected_border.get('widget') == frame:
#         for var in meta_fields.values():
#             var.set('N/A')
#         selected_border['widget'] = None
    
#     if frame in image_frames:
#         image_frames.remove(frame)
#     frame.destroy()
#     canvas.configure(scrollregion=canvas.bbox("all"))

def remove_image(frame):
    if not messagebox.askyesno("Remove Image", "Are you sure you want to remove this image?"):
        return

    index = image_frames.index(frame) if frame in image_frames else None
    if index is not None and index < len(image_data):
        del image_data[index]

    if selected_border.get('widget') == frame:
        for var in meta_fields.values():
            var.set('N/A')
        selected_border['widget'] = None
    
    if frame in image_frames:
        image_frames.remove(frame)
    frame.destroy()
    canvas.configure(scrollregion=canvas.bbox("all"))


def on_image_click(file_path, border_widget):
    prev = selected_border.get('widget')
    if prev and prev.winfo_exists():
        prev.config(bg=IMAGE_BORDER_COLOR)
    try:
        border_widget.config(bg='#FF8C00')
        selected_border['widget'] = border_widget
    except Exception:
        pass
    show_metadata(file_path)

def show_metadata(file_path):
    try:
        stat = os.stat(file_path)
        create_ts = datetime.fromtimestamp(stat.st_ctime)
        modify_ts = datetime.fromtimestamp(stat.st_mtime)
        meta_fields['CreateDate'].set(create_ts.strftime('%Y-%m-%d %H:%M:%S'))
        meta_fields['ModifyDate'].set(modify_ts.strftime('%Y-%m-%d %H:%M:%S'))
        meta_fields['FileSize'].set(f"{stat.st_size} bytes")
    except Exception:
        meta_fields['CreateDate'].set('N/A')
        meta_fields['ModifyDate'].set('N/A')
        meta_fields['FileSize'].set('N/A')

    try:
        base = os.path.basename(file_path)
        meta_fields['FileName'].set(base)
        ext = os.path.splitext(base)[1]
        meta_fields['FileExtension'].set(ext)
        mtype, _ = mimetypes.guess_type(file_path)
        meta_fields['FileType'].set(mtype or 'N/A')
    except Exception:
        meta_fields['FileName'].set('N/A')
        meta_fields['FileExtension'].set('N/A')
        meta_fields['FileType'].set('N/A')

    try:
        with Image.open(file_path) as im:
            w, h = im.size
            meta_fields['ImageWidth'].set(str(w))
            meta_fields['ImageHeight'].set(str(h))
            exif = extract_exif(im)
            lat, lon, alt = parse_gps(exif)
            meta_fields['GPSLatitude'].set(lat)
            meta_fields['GPSLongitude'].set(lon)
            meta_fields['GPSAltitude'].set(alt)
    except Exception:
        meta_fields['ImageWidth'].set('N/A')
        meta_fields['ImageHeight'].set('N/A')
        meta_fields['GPSLatitude'].set('N/A')
        meta_fields['GPSLongitude'].set('N/A')
        meta_fields['GPSAltitude'].set('N/A')

# --- Generate route using Google Maps ---
def generate_route():
    valid_images = [
        img for img in image_data
        if isinstance(img['lat'], (float, int)) and isinstance(img['lon'], (float, int))
    ]
    if len(valid_images) < 2:
        messagebox.showwarning("Not enough data", "You need at least two images with GPS coordinates to generate a route.")
        return

    valid_images.sort(key=lambda x: x['date'])
    coords = [f"{img['lat']},{img['lon']}" for img in valid_images]
    route_url = "https://www.google.com/maps/dir/" + "/".join(coords)
    webbrowser.open(route_url)

# --- Navbar content ---
upload_btn = tk.Button(
    navbar_left,
    text="+ Add Image",
    command=upload_image,
    bg="white",
    font=("Arial", 11, "bold"),
    relief="groove",
    width=18,
    height=1
)
upload_btn.place(relx=0.5, rely=0.3, anchor="center")

route_btn = tk.Button(
    navbar_left,
    text="🗺️ Generate Route",
    command=generate_route,
    bg="white",
    font=("Arial", 11, "bold"),
    relief="groove",
    width=18,
    height=1
)
route_btn.place(relx=0.5, rely=0.7, anchor="center")

header_label = tk.Label(
    navbar_right,
    text="Meta Data",
    bg="#104E8B",
    fg="white",
    font=("Arial", 16, "bold"),
    anchor="w"
)
header_label.pack(anchor="w", padx=20, pady=15)

root.mainloop()

