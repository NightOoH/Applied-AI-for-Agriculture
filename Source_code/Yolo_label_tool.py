import tkinter as tk
from tkinter import filedialog, simpledialog
import cv2
import os
from PIL import Image, ImageTk


class YOLOLabelingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Labeling Tool")

        # Variables
        self.image_dir = None
        self.image_list = []
        self.current_image_index = 0
        self.current_image = None
        self.current_image_path = None
        self.annotations = []  # [class, x_center, y_center, width, height]
        self.class_names = ["class_0"]  # Default class
        self.drawing = False
        self.start_x, self.start_y = None, None
        self.undo_stack = []
        self.redo_stack = []

        # GUI Layout
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill=tk.X, side=tk.BOTTOM)


        tk.Button(self.btn_frame, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Prev", command=self.prev_image).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Next", command=self.next_image).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Save", command=self.save_annotations).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Redo", command=self.redo).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Add Class", command=self.add_class).pack(side=tk.LEFT)

        self.class_var = tk.StringVar()
        self.class_var.set(self.class_names[0])

        self.class_menu = tk.OptionMenu(self.btn_frame, self.class_var, *self.class_names)
        self.class_menu.pack(side=tk.LEFT)

        # Canvas bindings
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.update_draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

    def open_folder(self):
        """Open folder dialog to load images."""
        self.image_dir = filedialog.askdirectory(title="Select Image Folder")
        if not self.image_dir:
            return
        self.image_list = [os.path.join(self.image_dir, f) for f in os.listdir(self.image_dir)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.image_list.sort()
        self.current_image_index = 0
        self.load_image()

    def load_image(self):
        """Load and display the current image."""
        if not self.image_list:
            return
        self.current_image_path = self.image_list[self.current_image_index]
        self.current_image = cv2.cvtColor(cv2.imread(self.current_image_path), cv2.COLOR_BGR2RGB)
        self.annotations = []
        self.display_image()

    def display_image(self):
        """Display the image on the canvas."""
        self.canvas.delete("all")
        img = Image.fromarray(self.current_image)
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Draw existing annotations
        for annotation in self.annotations:
            self.draw_bbox(annotation)

    def draw_bbox(self, annotation):
        """Draw a bounding box for a given annotation."""
        class_name, x, y, w, h = annotation
        x1 = int((x - w / 2) * self.current_image.shape[1])
        y1 = int((y - h / 2) * self.current_image.shape[0])
        x2 = int((x + w / 2) * self.current_image.shape[1])
        y2 = int((y + h / 2) * self.current_image.shape[0])
        if class_name == "class_0":
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
            self.canvas.create_text(x1, y1, anchor="nw", text=class_name, fill="red")
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=2)
            self.canvas.create_text(x1, y1, anchor="nw", text=class_name, fill="black")
    def start_draw(self, event):
        """Start drawing a bounding box."""
        self.drawing = True
        self.start_x, self.start_y = event.x, event.y

    def update_draw(self, event):
        """Update the bounding box while drawing."""
        if self.drawing:
            self.canvas.delete("temp_box")
            self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y,
                                         outline="blue", width=2, tags="temp_box")

    def end_draw(self, event):
        """Finish drawing the bounding box and save the annotation."""
        if self.drawing:
            self.drawing = False
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            x_min, x_max = sorted([x1, x2])
            y_min, y_max = sorted([y1, y2])

            img_h, img_w, _ = self.current_image.shape
            x_center = ((x_min + x_max) / 2) / img_w
            y_center = ((y_min + y_max) / 2) / img_h
            width = (x_max - x_min) / img_w
            height = (y_max - y_min) / img_h

            class_name = self.class_var.get()
            self.annotations.append((class_name, x_center, y_center, width, height))
            self.undo_stack.append(("add", self.annotations[-1]))
            self.redo_stack.clear()
            self.draw_bbox((class_name, x_center, y_center, width, height))

    def save_annotations(self):
        """Save annotations in YOLO format to a separate folder."""
        if not self.current_image_path:
            return

        # Ask the user to select a folder for saving annotations
        annotation_dir = filedialog.askdirectory(title="Select Annotation Folder")
        if not annotation_dir:
            return

        # Create the annotation file path
        base_name = os.path.basename(self.current_image_path)
        label_file = os.path.splitext(base_name)[0] + ".txt"
        label_path = os.path.join(annotation_dir, label_file)

        # Save annotations
        with open(label_path, "w") as f:
            for annotation in self.annotations:
                class_index = self.class_names.index(annotation[0])
                x, y, w, h = annotation[1:]
                f.write(f"{class_index} {x} {y} {w} {h}\n")

        print(f"Annotations saved to {label_path}")

    def prev_image(self):
        """Navigate to the previous image."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image()

    def next_image(self):
        if self.current_image_index < len(self.image_list) - 1:
            self.current_image_index += 1
            self.load_image()

    def undo(self):

        if self.undo_stack:
            action, data = self.undo_stack.pop()
            if action == "add":
                self.annotations.remove(data)
                self.redo_stack.append((action, data))
            self.display_image()

    def redo(self):

        if self.redo_stack:
            action, data = self.redo_stack.pop()
            if action == "add":
                self.annotations.append(data)
                self.undo_stack.append((action, data))
                self.display_image()

    def add_class(self):

        new_class = simpledialog.askstring("Add Class", "Enter new class name:")
        if new_class and new_class not in self.class_names:
            self.class_names.append(new_class)
            self.class_var.set(new_class)
            self.class_menu["menu"].add_command(label=new_class,
                                                command=lambda: self.class_var.set(new_class))

        # Run the tool
if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOLabelingTool(root)
    root.mainloop()