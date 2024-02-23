import os
from os.path import join, dirname, basename
from .audio_processor import AudioProcessor
from .map_processor import MapProcessor


class MapGenerator:
    # Class to generate maps.

    @staticmethod
    def generate_marathon(map_queue, break_length, marathon_title_name, marathon_version_name) -> str:
        """
        Generate a marathon from a list of maps.

        Parameters:
        map_queue (list[tuple]): The list of maps to generate the marathon from.
        break_length (int): The length of the break in milliseconds.
        marathon_title_name (str): The name of the marathon.
        marathon_version_name (str): The version of the marathon (difficulty name).

        Returns:
        str: The path to the generated marathon.
        """
        first_maps_sections = MapProcessor.read_osu_sections(
            map_queue[0][4])
        sections = MapGenerator.handle_map_queue(map_queue)
        merged_sections = MapProcessor.merge_maps(first_maps_sections,
                                                  sections["hitobjects"],
                                                  sections["timing_points"],
                                                  sections["events"],
                                                  sections["bookmarks"],
                                                  break_length,
                                                  sections["first_and_last_objects"])

        for variable in ["Title", "TitleUnicode"]:
            merged_sections["Metadata"] = MapProcessor.change_variable(
                merged_sections["Metadata"], variable, marathon_title_name)

        merged_sections["Metadata"] = MapProcessor.change_variable(
            merged_sections["Metadata"], "Version", marathon_version_name)

        new_file_name = f"{marathon_title_name}.osu"
        new_file_folder = join(
            dirname(dirname(map_queue[0][4])), new_file_name.split('.')[0])
        new_file_path = join(new_file_folder, new_file_name)

        merged_audio_filename = f"{marathon_title_name}.mp3"
        merged_audio_directory = join(dirname(new_file_folder),
                                      merged_audio_filename)

        AudioProcessor.merge_audio_files_with_breaks(sections["audio_files"],
                                                     merged_audio_directory,
                                                     break_length,
                                                     sections["first_and_last_objects"],
                                                     map_queue)
        merged_sections["General"] = MapProcessor.change_variable(
            merged_sections["General"],
            "AudioFilename",
            merged_audio_filename)

        new_file_content = MapProcessor.combine_map_sections(
            merged_sections)

        os.makedirs(new_file_folder, exist_ok=True)
        MapGenerator.export_new_file(new_file_path, new_file_content)
        return new_file_path

    @staticmethod
    def generate_single_map(rate, is_map_speed_with_bpm, od, ar, file_path) -> tuple[str, list[str]]:
        """
        Generate a single map based on the given parameters.

        Parameters:
        rate (float): The rate to change the map speed to.
        is_map_speed_with_bpm (bool): Whether the map speed should be changed with BPM.
        od (float): The overall difficulty of the map.
        ar (float): The approach rate of the map.
        file_path (str): The path to the osu! file.

        Returns:
        new_file_path (str): The path to the new osu! file.
        new_file_contents (list[str]): The content of the new osu! file.
        """

        file_sections = MapProcessor.read_osu_sections(
            file_path=file_path)
        map_rate = MapProcessor.calculate_map_rate(
            file_sections["TimingPoints"], rate, is_map_speed_with_bpm)

        file_folder = dirname(file_path)
        file_name = basename(file_path)

        new_file_name = f"{map_rate}x {file_name}"
        new_file_path = join(file_folder, new_file_name)

        new_audio_file_name = f"{map_rate}x{MapProcessor.get_variable(file_sections['General'], 'AudioFilename')}"
        new_audio_file_path = join(file_folder, new_audio_file_name)
        AudioProcessor.generate_map_audio(join(file_folder, MapProcessor.get_variable(
            file_sections["General"], "AudioFilename")), new_audio_file_path, rate=map_rate)

        new_file_sections = MapProcessor.change_map_speed(
            sections=file_sections, rate=map_rate)
        current_version = MapProcessor.get_variable(
            new_file_sections["Metadata"], "Version")
        new_version = f"{current_version} ({rate}BPM)" if is_map_speed_with_bpm else f"{current_version} {rate}x"
        new_file_sections["General"] = MapProcessor.change_variable(
            new_file_sections["General"], "AudioFilename", new_audio_file_name)

        new_file_sections["Metadata"] = MapProcessor.change_variable(
            new_file_sections["Metadata"], "Version", new_version)
        new_file_sections["Difficulty"] = MapProcessor.change_od_and_ar(
            file_sections["Difficulty"], od, ar)
        new_file_contents = MapProcessor.combine_map_sections(
            new_file_sections)
        return new_file_path, new_file_contents

    @staticmethod
    def export_new_file(new_file_path, file_contents) -> None:
        """
        Export a new file to the specified path.

        Parameters:
        new_file_path (str): The file path to export the new file to.
        file_contents (str): The contents of the new file (In this case, the modified .osu file).
        """
        with open(new_file_path, 'w', encoding='utf-8') as file:
            file.writelines(file_contents)

    @staticmethod
    def handle_map_queue(map_queue) -> dict:
        """
        Convert the map queue to a dict of sections (HitObjects, TimingPoints, Events, Bookmarks) for the generate_marathon function to merge them

        Parameters:
        map_queue (list[tuple]): The map queue to convert to the sections listed above.

        Returns:
        sections (dict): The organized sections for the generate_marathon function
        """
        # Initialize sections
        sections = {
            "hitobjects": [],
            "timing_points": [],
            "events": [],
            "bookmarks": [],
            "audio_files": [],
            "first_and_last_objects": []
        }

        for rate, is_map_speed_with_bpm, od, ar, file_path in map_queue:
            # Get each maps sections
            file_sections = MapProcessor.read_osu_sections(
                file_path=file_path)

            # Calculate the rate
            rate = MapProcessor.calculate_map_rate(
                file_sections["TimingPoints"], rate, is_map_speed_with_bpm)

            # Change the map speed according to the rate
            new_file_sections = MapProcessor.change_map_speed(
                file_sections, rate)

            new_bookmarks = MapProcessor.get_variable(
                new_file_sections["Editor"], "Bookmarks")
            # Append the sections and the first and last object time
            sections["hitobjects"].append(new_file_sections["HitObjects"])
            sections["timing_points"].append(new_file_sections["TimingPoints"])
            sections["events"].append(new_file_sections["Events"])
            sections["bookmarks"].append(new_bookmarks)
            sections["audio_files"].append(join(dirname(file_path),
                                           MapProcessor.get_variable(file_sections["General"],
                                                                     "AudioFilename")))
            first_object_time, last_object_time = MapGenerator.get_first_and_last_objects_time(
                file_sections["HitObjects"][1:])
            sections["first_and_last_objects"].append(
                (first_object_time / rate, last_object_time / rate))

        return sections

    @staticmethod
    def get_first_and_last_objects_time(hit_objects) -> tuple[int, int]:
        """
        Get the first and last object time.

        Parameters:
        hit_objects (list): The hit objects to get the first and last object time.

        Returns:
        tuple[int, int]: The first and last object time.
        """

        # Find the first non-empty hit object
        first_object = hit_objects[0]

        # Extract time from the first hit object
        first_object_time = int(first_object.strip().split(',')[2])

        # Find the last non-empty hit object
        last_object = None
        for obj in reversed(hit_objects):
            if obj.strip():
                last_object = obj
                break

        # Extract object properties
        last_object_elements = last_object.strip().split(',')
        last_object_type = int(last_object_elements[3])

        # Extract time from the last hit object
        last_object_time = int(last_object_elements[2])

        # If the last object is a long note or spinner adjust the time accordingly
        if MapProcessor.is_hold_note(last_object_type):
            last_object_time = int(last_object_elements[5].split(':')[0])
        elif MapProcessor.is_spinner(last_object_type):
            last_object_time = int(last_object_elements[5])

        return first_object_time, last_object_time
