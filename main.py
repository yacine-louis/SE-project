import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # Pillow for image handling

# --- Configurable layout & style ---
LEFT_COL_WIDTH = 250
IMAGE_PREVIEW_SIZE = 150
IMAGE_BORDER_COLOR = "#000000"
IMAGE_BORDER_WIDTH = 4

root = tk.Tk()
root.title("Test")
root.geometry("700x700")
root.resizable(False, False)

# --- Center the window ---
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
# Prevent the left frame from resizing to fit packed children (canvas + scrollbar)
main_left.grid_propagate(False)
main_left.pack_propagate(False)

# --- Scrollable container for images (keeps left area size fixed) ---
# Use a Canvas + inner Frame so the image list can scroll vertically
canvas = tk.Canvas(main_left, bg="lightblue", highlightthickness=0)
v_scroll = tk.Scrollbar(main_left, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=v_scroll.set)

# Pack scrollbar first (right) then canvas so the canvas doesn't cover the scrollbar.
# Also give the scrollbar a fixed width so it's clearly visible.
v_scroll.pack(side="right", fill="y")
v_scroll.config(width=14, troughcolor="#d9d9d9")
canvas.pack(side="left", fill="both", expand=True)

images_frame = tk.Frame(canvas, bg="lightblue")
canvas_window = canvas.create_window((0, 0), window=images_frame, anchor="nw")

def _on_frame_configure(event):
    # Update scroll region to encompass inner frame
    canvas.configure(scrollregion=canvas.bbox("all"))

def _on_canvas_configure(event):
    # Keep the inner frame width equal to the canvas width so widgets wrap correctly
    canvas.itemconfig(canvas_window, width=event.width)

images_frame.bind("<Configure>", _on_frame_configure)
canvas.bind("<Configure>", _on_canvas_configure)

def _on_mousewheel(event):
    # Windows: event.delta is multiple of 120
    canvas.yview_scroll(-1 * int(event.delta / 120), "units")

def _bind_mousewheel(event):
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

def _unbind_mousewheel(event):
    canvas.unbind_all("<MouseWheel>")

canvas.bind("<Enter>", _bind_mousewheel)
canvas.bind("<Leave>", _unbind_mousewheel)

# Keep references to avoid garbage collection
loaded_images = []

# --- Upload button function ---
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

            # Frame for border
            border_frame = tk.Frame(
                images_frame,
                bg=IMAGE_BORDER_COLOR,
                padx=IMAGE_BORDER_WIDTH,
                pady=IMAGE_BORDER_WIDTH
            )
            border_frame.pack(pady=10)

            # Inner label to display the image (centered)
            img_label = tk.Label(border_frame, image=photo, bg="white")
            img_label.pack()

        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

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
upload_btn.place(relx=0.5, rely=0.5, anchor="center")

header_label = tk.Label(
    navbar_right,
    text="Meta Data",
    bg="#104E8B",
    fg="white",
    font=("Arial", 16, "bold"),
    anchor="w"
)
header_label.pack(anchor="w", padx=20, pady=15)

tk.Label(main_right, text="Right Content Area", bg="lightgreen", font=("Arial", 12, "bold")).pack(pady=20)

root.mainloop()
