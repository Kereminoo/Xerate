import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from os import environ
from os.path import join, basename, dirname
from .map_generator import MapGenerator


class XerateApp:
    def __init__(self, root, img_path):
        self.root = root
        self.root.title("Xerate")
        self.map_queue = []
        self.map_generator = MapGenerator()

        # Load icon
        try:
            self.img = PhotoImage(file=img_path)
            self.root.iconphoto(False, self.img)
        except Exception:
            pass

        self.create_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        self.file_frame = ttk.Frame(self.root)
        self.file_label = ttk.Label(self.file_frame, text="No file selected")
        self.select_file_button = ttk.Button(
            self.file_frame, text="Add files", command=self.select_file)
        self.deselect_file_button = ttk.Button(
            self.file_frame, text="Deselect file", command=self.clear_selected_files)

        self.file_label.pack(side=tk.LEFT)
        self.select_file_button.pack(side=tk.LEFT)
        self.deselect_file_button.pack(side=tk.LEFT)
        self.file_frame.pack()

        self.rate_label = ttk.Label(self.root, text="Rate:")
        self.rate_entry = ttk.Entry(self.root)

        self.overall_difficulty_label = ttk.Label(
            self.root, text="OD (Leave empty for no change)")
        self.overall_difficulty_entry = ttk.Entry(self.root)

        self.approach_rate_label = ttk.Label(
            self.root, text="AR (Leave empty for no change)")
        self.approach_rate_entry = ttk.Entry(self.root)

        self.break_length_label = ttk.Label(
            self.root, text="Break length (Leave empty if you are not merging maps.)")
        self.break_length_entry = ttk.Entry(self.root)

        self.export_frame = ttk.Frame(self.root)
        self.add_to_map_queue_button = ttk.Button(
            self.export_frame, text="Add to queue", command=self.add_to_map_queue)

        self.generate_button = ttk.Button(
            self.export_frame, text="Export", command=self.on_generate)

        self.clear_queue_button = ttk.Button(self.export_frame, text="Clear queue",
                                             command=self.clear_queue)

        self.marathon_name_label = ttk.Label(self.root, text="Marathon title")
        self.marathon_name_entry = ttk.Entry(self.root)

        self.marathon_version_label = ttk.Label(
            self.root, text="Marathon version (difficulty name)")
        self.marathon_version_entry = ttk.Entry(self.root)

        self.make_marathon_checkbox_bool = tk.BooleanVar()
        self.make_marathon_checkbox = ttk.Checkbutton(
            self.root, text="Make marathon", variable=self.make_marathon_checkbox_bool)

        self.is_change_map_speed_with_bpm = tk.BooleanVar()
        self.change_map_speed_with_bpm = ttk.Checkbutton(
            self.root, text="Change map speed with BPM", variable=self.is_change_map_speed_with_bpm, command=self.set_mode_to_bpm)

        self.file_frame.pack()
        self.rate_label.pack()
        self.rate_entry.pack()
        self.overall_difficulty_label.pack()
        self.overall_difficulty_entry.pack()
        self.approach_rate_label.pack()
        self.approach_rate_entry.pack()
        self.marathon_name_label.pack()
        self.marathon_name_entry.pack()
        self.marathon_version_label.pack()
        self.marathon_version_entry.pack()
        self.break_length_label.pack()
        self.break_length_entry.pack()
        self.add_to_map_queue_button.pack(side=tk.LEFT)
        self.clear_queue_button.pack(side=tk.RIGHT)
        self.generate_button.pack(side=tk.RIGHT)
        self.export_frame.pack()
        self.make_marathon_checkbox.pack()
        self.change_map_speed_with_bpm.pack()

    def get_file_path(self):
        local_app_data = environ.get("localappdata")
        osu_directory = join(local_app_data, "osu!", "Songs")
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select .osu File", filetypes=[("osu files", "*.osu")], initialdir=osu_directory)
        if isinstance(file_path, list) and file_path:
            return file_path[0]
        return file_path

    def on_generate(self):
        break_length = self.break_length_entry.get()
        marathon_title_name = self.marathon_name_entry.get()
        marathon_version_name = self.marathon_version_entry.get()
        is_make_marathon = self.make_marathon_checkbox_bool.get() == 1

        if not self.map_queue:
            messagebox.showerror(
                "No map in queue", "No maps in queue. Please add a map to queue before exporting!")
            return

        if is_make_marathon:
            if not break_length:
                messagebox.showerror(
                    "No break length", "You forgot to enter a break length. Please enter a break length.")
                return
            else:
                try:
                    break_length = int(break_length)
                except (ValueError, TypeError):
                    messagebox.showerror(
                        "Invalid break length", "You have entered an invalid break length. Please enter an integer.")
                    return

            if is_make_marathon and not marathon_title_name:
                messagebox.showerror(
                    "No marathon name", "You forgot to enter a marathon name. Please enter a marathon name.")
                return

        if is_make_marathon and len(self.map_queue) > 1:
            try:
                marathon_path = self.map_generator.generate_marathon(
                    self.map_queue, break_length, marathon_title_name, marathon_version_name)
                messagebox.showinfo("Map merging complete!", f"Map merging completed successfully! "
                                    f"Your map is located in {marathon_path}. "
                                    f"Press F5 in osu! to play the map.")

            except Exception as e:
                messagebox.showerror(
                    "Could not generate marathon.", f"Marathon generation error: {e}.")
        else:
            for rate, is_map_speed_with_bpm, overall_difficulty, approach_rate, file_path in self.map_queue:
                new_file_path, new_file_contents = self.map_generator.generate_single_map(
                    rate, is_map_speed_with_bpm, overall_difficulty, approach_rate, file_path)
                try:
                    self.map_generator.export_new_file(
                        new_file_path, new_file_contents)
                except Exception as e:
                    messagebox.showerror(
                        "File exporting error!", f"File exporting error: {e}")
                    return

            messagebox.showinfo("Map generation complete!",
                                "Map generation completed successfully! Press F5 in osu! to play the map.")

        self.clear_selected_files()
        self.clear_queue()
        self.clear_entries()

    def select_file(self):
        new_file_paths = self.get_file_path()
        if new_file_paths:
            self.file_label.file_paths = new_file_paths
            self.file_label.config(text=f"You have selected {basename(new_file_paths)}")

    def add_to_map_queue(self):
        if hasattr(self.file_label, "file_paths"):
            file_path = self.file_label.file_paths
            if file_path:
                try:
                    rate = float(self.rate_entry.get())
                except (ValueError, TypeError):
                    rate = 1.0
                try:
                    overall_difficulty = float(
                        self.overall_difficulty_entry.get())
                except (ValueError, TypeError):
                    overall_difficulty = None
                try:
                    approach_rate = float(self.approach_rate_entry.get())
                except (ValueError, TypeError):
                    approach_rate = None
                change_map_speed_with_bpm = self.is_change_map_speed_with_bpm.get() == 1
                self.map_queue.append(
                    (rate, change_map_speed_with_bpm, overall_difficulty, approach_rate, file_path))
                self.file_label.config(
                    text=f"No files selected,{len(self.map_queue)} files in queue")
                self.clear_entries()
            else:
                messagebox.showerror("No files selected",
                                     "You haven't selected any files.")
        else:
            messagebox.showerror("No files selected",
                                 "You haven't selected any files.")

    def set_mode_to_bpm(self):
        if self.is_change_map_speed_with_bpm.get():
            self.rate_label.config(text="BPM (integer):")
        else:
            self.rate_label.config(text="Rate (floating point value):")

    def on_close(self):
        self.root.quit()

    def clear_queue(self):
        self.map_queue = []
        self.file_label.config(text="No files in queue")

    def clear_selected_files(self):
        if hasattr(self.file_label, "file_paths"):
            self.file_label.file_paths = []
            self.file_label.config(text="No files selected")

    def clear_entries(self):
        self.rate_entry.delete(0, "end")
        self.approach_rate_entry.delete(0, "end")
        self.overall_difficulty_entry.delete(0, "end")
        self.break_length_entry.delete(0, "end")
        self.marathon_name_entry.delete(0, "end")
        self.marathon_version_entry.delete(0, "end")


def main():
    root = tk.Tk()
    image_path = join(dirname(__file__), "Xerate.png")
    app = XerateApp(root, image_path)
    root.mainloop()


if __name__ == "__main__":
    main()
