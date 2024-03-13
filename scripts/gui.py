from customtkinter import *
from tkinter import messagebox
from os.path import join, dirname
from os import environ

from scripts.map_generator import MapExistsError, MapGenerator


# from map_generator import MapGenerator


class XerateApp:

    def __init__(self, root, img_path) -> None:
        self.root = root
        self.root.title("Xerate")
        self.map_queue = []
        # self.map_generator = MapGenerator()
        set_appearance_mode("system")
        self.file_path = []

        # Load icon
        try:
            self.img = CTkImage(img_path)
            self.root.iconphoto(False, self.img)
        except Exception:
            pass

        self._create_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.mainloop()

    def _create_widgets(self) -> None:
        self.file_frame = CTkFrame(self.root)
        self.file_label = CTkLabel(self.file_frame, text="No file selected")
        self.select_file_button = CTkButton(
            self.file_frame, text="Add files", command=self.select_file)
        self.deselect_file_button = CTkButton(
            self.file_frame, text="Deselect file", command=self.clear_selected_files)

        self.file_label.pack(side=LEFT)
        self.select_file_button.pack(side=LEFT)
        self.deselect_file_button.pack(side=LEFT)
        self.file_frame.pack()

        self.rate_label = CTkLabel(self.root, text="Rate:")
        self.rate_entry = CTkEntry(self.root)

        self.overall_difficulty_label = CTkLabel(
            self.root, text="OD (Leave empty for no change)")
        self.overall_difficulty_entry = CTkEntry(self.root)

        self.approach_rate_label = CTkLabel(
            self.root, text="AR (Leave empty for no change)")
        self.approach_rate_entry = CTkEntry(self.root)

        self.break_length_label = CTkLabel(
            self.root, text="Break length (Leave empty if you are not merging maps.)")
        self.break_length_entry = CTkEntry(self.root)

        self.export_frame = CTkFrame(self.root)
        self.add_to_map_queue_button = CTkButton(
            self.export_frame, text="Add to queue", command=self.add_to_map_queue)

        self.generate_button = CTkButton(
            self.export_frame, text="Export", command=self.on_generate)

        self.clear_queue_button = CTkButton(self.export_frame, text="Clear queue",
                                            command=self.clear_queue)

        self.marathon_name_label = CTkLabel(self.root, text="Marathon title")
        self.marathon_name_entry = CTkEntry(self.root)

        self.marathon_version_label = CTkLabel(self.root, text="Marathon version (difficulty name)")
        self.marathon_version_entry = CTkEntry(self.root)

        self.make_marathon_checkbox_bool = BooleanVar()
        self.make_marathon_checkbox = CTkCheckBox(self.root, text="Make marathon", variable=self.make_marathon_checkbox_bool)

        self.is_change_map_speed_with_bpm = BooleanVar()
        self.change_map_speed_with_bpm = CTkCheckBox(
            self.root, text="Change map speed with BPM", variable=self.is_change_map_speed_with_bpm,
            command=self.set_mode_to_bpm)

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
        self.add_to_map_queue_button.pack(side=LEFT)
        self.clear_queue_button.pack(side=RIGHT)
        self.generate_button.pack(side=RIGHT)
        self.export_frame.pack()
        self.make_marathon_checkbox.pack()
        self.change_map_speed_with_bpm.pack()

    def on_generate(self) -> None:
        break_length = self.break_length_entry.get()
        marathon_title_name = self.marathon_name_entry.get()
        marathon_version_name = self.marathon_version_entry.get()
        is_make_marathon = self.make_marathon_checkbox_bool.get() == 1
        overall_difficulty = self.get_float_from_entry(self.overall_difficulty_entry)
        approach_rate = self.get_float_from_entry(self.approach_rate_entry)

        if not self.map_queue:
            messagebox.showerror("No map in queue",
                                 "No maps in queue. Please add a map to queue before exporting!")
            return

        if is_make_marathon:
            if not break_length:
                messagebox.showerror("No break length",
                                     "You forgot to enter a break length. Please enter a break length.")
                return
            else:
                try:
                    break_length = int(break_length)
                except (ValueError, TypeError):
                    messagebox.showerror("Invalid break length",
                                         "You have entered an invalid break length. Please enter an integer.")
                    return

            if not marathon_title_name:
                messagebox.showerror("No marathon name",
                                     "You forgot to enter a marathon name. Please enter a marathon name.")
                return

        if is_make_marathon and len(self.map_queue) > 1:
            try:
                marathon_path = self.map_generator.generate_marathon(self.map_queue,
                                                                     break_length,
                                                                     marathon_title_name,
                                                                     marathon_version_name,
                                                                     overall_difficulty,
                                                                     approach_rate)
                messagebox.showinfo("Map merging complete!", f"Map merging completed successfully! "
                                                             f"Your map is located in {marathon_path}. "
                                                             f"Press F5 in osu! to play the map.")
            # If it returns OSError, the user probably has entered an invalid marathon name.
            except OSError:
                messagebox.showerror("Could not generate marathon.", "Could not generate marathon."
                                                                     "Please don't use invalid symbols in the marathon name. (?, ! etc.)")
            # If it returns MapExistsError, then the marathon already exists, or it's conflicting with a different map.
            except MapExistsError:
                messagebox.showerror("Could not generate marathon",
                                     "Could not generate marathon."
                                     "This marathon already exists or the name conflicts with a different map."
                                     "Please enter a different marathon name!")
            # For other errors I have no idea just don't make it shit itself
            except Exception as e:
                messagebox.showerror("Could not generate marathon.",
                                     f"Marathon generation error: {e}.")
        else:
            for rate, is_map_speed_with_bpm, overall_difficulty, approach_rate, file_path in self.map_queue:
                new_file_path, new_file_contents = self.map_generator.generate_single_map(
                    rate, is_map_speed_with_bpm, overall_difficulty, approach_rate, file_path)
                try:
                    self.map_generator.export_new_file(
                        new_file_path, new_file_contents)
                except Exception as e:
                    messagebox.showerror("File exporting error!",
                                         f"File exporting error: {e}")
                    return

            messagebox.showinfo("Map generation complete!",
                                "Map generation completed successfully! Press F5 in osu! to play the map.")

        self.clear_selected_files()
        self.clear_queue()
        self.clear_entries()

    def clear_queue(self) -> None:
        self.map_queue = []
        self.file_label.config(text="No files in queue")

    @staticmethod
    def get_float_from_entry(entry: CTkEntry) -> float | None:
        try:
            value = float(entry.get())
            return value
        except (ValueError, TypeError):
            return None

    def on_close(self) -> None:
        self.root.quit()

    def set_mode_to_bpm(self) -> None:
        if self.is_change_map_speed_with_bpm.get():
            self.rate_label.config(text="BPM (integer):")
        else:
            self.rate_label.config(text="Rate (floating point value):")

    def add_to_map_queue(self) -> None:
        if self.file_path:
            rate = self.get_float_from_entry(self.rate_entry)
            if not rate:
                rate = 1.0
            approach_rate = self.get_float_from_entry(self.approach_rate_entry)
            overall_difficulty = self.get_float_from_entry(
                self.overall_difficulty_entry)
            change_map_speed_with_bpm = self.is_change_map_speed_with_bpm.get() == 1
            self.map_queue.append(
                (rate, change_map_speed_with_bpm, overall_difficulty, approach_rate, file_path))
            self.file_label.config(
                text=f"No files selected,{len(self.map_queue)} files in queue")
            if self.make_marathon_checkbox_bool == 1:
                self.clear_entries(clear_od_and_ar=False, clear_marathon_entries=False)
            else:
                self.clear_entries()
        else:
            messagebox.showerror("No files selected",
                                 "You haven't selected any files.")

    def select_file(self) -> None:
        new_file_paths = self.get_file_path()
        if new_file_paths:
            self.file_label.file_paths = new_file_paths
            self.file_label.config(
                text=f"You have selected {basename(new_file_paths)}")

    def get_file_path(self) -> str:
        local_app_data = environ.get("localappdata")
        osu_directory = join(local_app_data, "osu!", "Songs")
        root = CTk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select .osu File",
                                               filetypes=[
                                                   ("osu files", "*.osu")],
                                               initialdir=osu_directory)
        if isinstance(file_path, list) and file_path:
            return file_path[0]
        return file_path

    def clear_selected_files(self) -> None:
        if self.file_path:
            self.file_path = []
            self.file_label.config(text="No files selected")

    def clear_entries(self, clear_od_and_ar: bool = True, clear_marathon_entries: bool = True) -> None:
        self.rate_entry.delete(0, "end")

        if clear_od_and_ar:
            self.approach_rate_entry.delete(0, "end")
            self.overall_difficulty_entry.delete(0, "end")

        if clear_marathon_entries:
            self.break_length_entry.delete(0, "end")
            self.marathon_name_entry.delete(0, "end")
            self.marathon_version_entry.delete(0, "end")

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


def main():
    root = CTk()
    image_path = join(dirname(__file__), "Xerate.png")
    app = XerateApp(root, image_path)


if __name__ == '__main__':
    main()