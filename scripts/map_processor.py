from math import floor
from os.path import join, dirname

class MapProcessor:
    # Class to read, process and write .osu files
    DEFAULT_FILE_FORMAT = 'osu file format v14'
    @staticmethod
    def read_osu_sections(file_path) -> dict:
        """
        Get the sections of an .osu file as a dictionary

        Parameters:
        file_path (str): The path of the file to read

        Returns:
        sections (dict): The sections of the file organized as a dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            sections = {}
            current_section = None
            for line in lines:
                strip_line = line.strip()
                if strip_line.startswith('[') and strip_line.endswith(']'):
                    current_section = strip_line[1:-1]
                    sections[current_section] = [line]
                elif current_section:
                    sections[current_section].append(line)
            return sections
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file {file_path}.")
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")

    @staticmethod
    def combine_map_sections(sections) -> list[str]:
        """
        Reorganize the sections of the dictionary to a new list

        Parameters:
        sections (dict): The sections of the file organized as a dictionary

        Returns:
        new_file (list): The new file as a list to write to a new file
        """
        new_file = ['osu file format v14\n']
        # Get the values and add them to the new file list (assuming they're in the correct order)
        for value in sections.values():
            new_file.extend(value)
        return new_file

    @staticmethod
    def is_hold_note(num) -> bool:
        # In osu!, the 7th bit represents if a note is a hold note
        # We can use bitwise AND to find out if its a hold note or not
        return num & 128 != 0

    @staticmethod
    def is_spinner(num) -> bool:
        # In osu!, the 3rd bit represents if a hitobject is a spinner
        # So convert the number into binary and check if the 3rd bit (index 4 from the right) is 1
        return num & 8 != 0

    @staticmethod
    def change_hitobjects_speed(hitobjects_section, rate) -> None:
        """
        Change the timing info of all hitobjects to match the rate

        Parameters:
        hitobjects_section (list): The HitObjects section from the .osu file
        rate (float): The rate to update the HitObjects' timing info

        Returns:
        modified_hitobjects_section (list): The updated HitObjects section
        """
        modified_hitobjects_section = []
        for line in hitobjects_section:
            # Get the elements of a line
            line_elements = line.strip().split(',')
            if len(line_elements) >= 3:
                # Extract type and time information
                type_of_object = int(line_elements[3])
                original_start_time = int(line_elements[2])
                modified_start_time = floor(original_start_time / rate)
                line_elements[2] = str(modified_start_time)

                # Check and modify long notes accordingly
                if MapProcessor.is_hold_note(type_of_object):
                    split_note_params = line_elements[5].split(':')
                    original_end_time = int(split_note_params[0])
                    modified_end_time = floor(original_end_time / rate)
                    split_note_params[0] = str(modified_end_time)
                    note_params = ':'.join(split_note_params)
                    line_elements[5] = str(note_params)

                # Check and modify spinners accordingly
                elif MapProcessor.is_spinner(type_of_object):
                    original_end_time = int(line_elements[5])
                    modified_end_time = floor(original_end_time / rate)
                    line_elements[5] = str(modified_end_time)

                # Reconstruct the line and add it to the new list
                modified_line = ','.join(line_elements)
                modified_hitobjects_section.append(modified_line + '\n')
            else:
                # If it's not a hitobject, just append the line as normal
                modified_hitobjects_section.append(line)

        return modified_hitobjects_section

    @staticmethod
    def change_events_speed(events_section, rate) -> list:
        """
        Change the timing info of all Events to match the rate

        Parameters:
        events_section (list): The Events section from the .osu file
        rate (float): The rate to update the Events' timing info

        Returns:
        modified_events_section (list): The updated Events section
        """
        modified_events_section = []
        for line in events_section:
            # Get the elements of a line
            line_elements = line.rstrip().split(',')

            # Parse the event type
            event_type = line_elements[0].strip()

            # If we have an event type and it's not the header, continue
            if event_type != "[Events]":
                # If it's a background, just append the line as normal
                if event_type == "0":
                    modified_events_section.append(line)
                else:
                    # Change timing info on Videos and Loops
                    if event_type in ["Video", "1", "_L", "L"]:
                        if len(line_elements) >= 2:
                            original_start_time = int(line_elements[1])
                            modified_start_time = floor(
                                original_start_time / rate)
                            line_elements[1] = str(modified_start_time)
                    # Change timing info of Breaks
                    elif event_type in ["2", "Break"]:
                        if len(line_elements) >= 3:
                            original_start_time = int(line_elements[1])
                            original_end_time = int(line_elements[2])
                            modified_start_time = floor(
                                original_start_time / rate)
                            modified_end_time = floor(original_end_time / rate)
                            line_elements[1] = str(modified_start_time)
                            line_elements[2] = str(modified_end_time)
                    # Change timing info for other Events and Storyboard Commands
                    elif len(event_type) <= 3 and len(line_elements) >= 3:
                        original_start_time = int(line_elements[2])
                        modified_start_time = floor(original_start_time / rate)
                        line_elements[2] = str(modified_start_time)

                        # Check if there is an end time (index 3) because sometimes its empty
                        if line_elements[3]:
                            original_end_time = int(line_elements[3])
                            modified_end_time = floor(original_end_time / rate)
                            line_elements[3] = str(modified_end_time)

                    modified_line = ','.join(line_elements)
                    modified_events_section.append(modified_line + '\n')
            else:
                modified_events_section.append(line)

        return modified_events_section

    @staticmethod
    def change_timing_points_speed(timing_points_section, rate) -> list:
        """
        Change the timing info of all TimingPoints to match the rate

        Parameters:
        timing_points_section (list): The TimingPoints section from the .osu file
        rate (float): The rate to update the TimingPoints' timing info

        Returns:
        modified_timing_points_section (list): The updated TimingPoints section
        """
        modified_timing_points_section = []
        for line in timing_points_section:
            # Get the elements of a line
            line_elements = line.strip().split(',')
            if len(line_elements) >= 3:
                # Change the timing info
                original_start_time = float(line_elements[0])
                modified_start_time = floor(original_start_time / rate)

                if line_elements[6] == "1":
                    beat_length = float(line_elements[1])
                    modified_beat_length = beat_length / rate
                    line_elements[1] = str(modified_beat_length)

                line_elements[0] = str(modified_start_time)

                # Reconstruct the line and add it to the new list
                modified_line = ','.join(line_elements)
                modified_timing_points_section.append(modified_line + '\n')
            else:
                # If it's not a timing point, just append the line as normal
                modified_timing_points_section.append(line)
        return modified_timing_points_section

    @staticmethod
    def change_bookmark_speed(bookmarks, rate) -> str:
        """
        Change the timing info of all bookmarks to match the rate

        Parameters:
        bookmarks (str): The bookmarks from the .osu file using the get_variable() function
        rate (float): The rate to update the bookmarks' timing info

        Returns:
        new_bookmarks (str): The new bookmarks as a string

        Usage:
        bookmarks = get_variable(file_sections["Editor"], "Bookmarks")
        new_bookmarks = change_bookmark_speed(bookmarks,rate)
        """
        new_bookmarks = []

        if bookmarks is None:
            return None

        split_bookmarks = bookmarks.split(',')
        for bookmark in split_bookmarks:
            new_bookmarks.append(str(floor(int(bookmark) / rate)))
        new_bookmarks = ','.join(new_bookmarks)
        return new_bookmarks

    @staticmethod
    def change_variable(section, variable, new_variable) -> list:
        """
        Change one variable of a section

        Parameters:
        section (list): The section to change the variable of
        variable (str): The variable name
        new_variable (str): The updated variable

        Returns:
        modified_section (list): The section with the updated variable

        Usage:
        section = file_sections["Bookmarks"]
        section = change_variable(section, "Bookmarks", "128, 695, 900, 10023")
        """
        modified_section = []
        for line in section:
            if line.startswith(variable):
                modified_line = f"{variable}: {new_variable}"
                modified_section.append(modified_line + '\n')
            else:
                modified_section.append(line)
        return modified_section

    @staticmethod
    def get_variable(section, variable) -> str or None:
        """
        Get one variable of a section

        Parameters:
        section (list): The section to get the variable of
        variable (str): The variable name

        Returns:
        str: The variable value
        """
        for line in section:
            if line.startswith(variable):
                # Most variables are separated with a colon
                line_elements = line.split(':')
                if len(line_elements) >= 2:
                    return ':'.join(line_elements[1:]).strip()
                else:
                    return None
        return None

    @staticmethod
    def merge_hitobjects(sections, break_length, first_and_last_objects) -> list:
        """
        Concatenate HitObjects from different maps to a single list with breaks

        Parameters:
        sections (list[*list]): The HitObjects sections from each map
        break_length (int): The break length
        first_and_last_objects (list(*tuple)): The first and last HitObjects of each map to synchronize other sections and audio

        Returns:
        merged_hitobjects (list): The concatenated HitObjects section

        Usage:
        merged_hitobjects = merge_hitobjects(sections,break_length,first_and_last_objects)
        """
        merged_hitobjects = ['[HitObjects]\n']
        current_offset = 0
        for idx, lines in enumerate(sections):
            current_offset -= first_and_last_objects[idx][0]
            for line in lines:
                line_elements = line.strip().split(',')
                if len(line_elements) >= 3:
                    type_of_object = int(line_elements[3])
                    original_start_time = int(line_elements[2])

                    modified_start_time = floor(
                        original_start_time + current_offset)
                    line_elements[2] = str(modified_start_time)

                    if MapProcessor.is_hold_note(type_of_object):
                        split_object_params = line_elements[5].split(':')
                        original_end_time = int(split_object_params[0])
                        modified_end_time = floor(
                            original_end_time + current_offset)
                        split_object_params[0] = str(modified_end_time)
                        object_params = ':'.join(split_object_params)
                        line_elements[5] = object_params
                    elif MapProcessor.is_spinner(type_of_object):
                        original_end_time = int(line_elements[5])
                        modified_end_time = floor(original_end_time + current_offset)
                        line_elements[5] = str(modified_end_time)

                    modified_line = ','.join(line_elements)
                    merged_hitobjects.append(modified_line + '\n')
                else:
                    continue
            current_offset += floor(first_and_last_objects[idx][1] + break_length)
        return merged_hitobjects

    @staticmethod
    def merge_timing_points(sections, break_length, first_and_last_objects) -> list:
        """
        Concatenate TimingPoints from different maps to a single list with breaks in between

        Parameters:
        sections (list[*list]): The TimingPoints sections from each map
        break_length (int): The break length
        first_and_last_objects (list(*tuple)): The first and last HitObjects of each map to synchronize other sections and audio

        Returns:
        merged_timing_points (list): The concatenated TimingPoints section

        Usage:
        merged_timing_points = merge_timing_points(sections,break_length,first_and_last_objects)
        """
        merged_timing_points = ['[TimingPoints]\n']
        current_offset = 0
        for idx, lines in enumerate(sections):
            current_offset -= first_and_last_objects[idx][0]
            for line in lines:
                line_elements = line.strip().split(',')
                if len(line_elements) >= 3:
                    original_start_time = float(line_elements[0])
                    modified_start_time = floor(original_start_time + current_offset)
                    line_elements[0] = str(modified_start_time)
                    modified_line = ','.join(line_elements)
                    merged_timing_points.append(modified_line + '\n')
                else:
                    continue
            current_offset += floor(first_and_last_objects[idx][1] + break_length)
        return merged_timing_points

    @staticmethod
    def merge_events(sections, break_length, first_and_last_objects):
        """
        Concatenate Events from different maps to a single list with breaks

        Parameters:
        sections (list[*list]): The Events sections from each map
        break_length (int): The break length
        first_and_last_objects (list(*tuple)): The first and last HitObjects of each map to synchronize other sections and audio

        Returns:
        merged_events (list): The concatenated Events section

        Usage:
        merged_events = merge_events(sections,break_length,first_and_last_objects)
        """
        merged_events = ['[Events]\n']
        current_offset = 0
        for idx, lines in enumerate(sections):
            current_offset -= first_and_last_objects[idx][0]
            for line in lines:
                # Get the elements of a line
                # Use rstrip() to remove the newline character and append it later because sometimes its missing
                line_elements = line.rstrip().split(',')

                # Parse the event type
                event_type = line_elements[0].strip()

                # If we have an event type and its not the header,continue
                if event_type == "[Events]" or event_type == "0":
                    continue
                # In Videos and Loops there is time located in the 2nd element and no endTime
                if event_type in ["Video", "1", "_L", "L"]:
                    original_start_time = int(line_elements[1])
                    modified_start_time = floor(
                        original_start_time + current_offset)
                    line_elements[1] = str(modified_start_time)
                # Break events have the time located in the 2nd element and the endtime on the 3rd
                elif event_type in ["2", "Break"]:
                    original_start_time = int(line_elements[1])
                    original_end_time = int(line_elements[2])
                    modified_start_time = floor(
                        original_start_time + current_offset)
                    modified_end_time = floor(
                        original_end_time + current_offset)
                    line_elements[1] = str(modified_start_time)
                    line_elements[2] = str(modified_end_time)
                # All other event types have time and endTime but they are placed differently
                elif len(event_type) <= 3 and len(line_elements) >= 3:
                    original_start_time = int(line_elements[2])
                    original_end_time = int(line_elements[3])
                    modified_start_time = floor(
                        original_start_time + current_offset)
                    modified_end_time = floor(
                        original_end_time + current_offset)
                    line_elements[2] = str(modified_start_time)
                    line_elements[3] = str(modified_end_time)
                else:
                    continue
                modified_line = ','.join(line_elements)
                merged_events.append(modified_line + '\n')
            current_offset += floor(
                first_and_last_objects[idx][1] + break_length)
        return merged_events

    @staticmethod
    def merge_bookmarks(sections, break_length, first_and_last_objects):
        """
        Concatenate Bookmarks from different maps to a single string with breaks

        Parameters:
        sections (list[*list]): The bookmarks from each map in a single list
        break_length (int): The break length
        first_and_last_objects (list[tuple]): The first and last HitObjects of each map to synchronize other sections and audio

        Returns:
        str: The concatenated Bookmarks section

        Usage:
        merged_bookmarks = merge_bookmarks(sections,break_length,first_and_last_objects)
        """
        new_bookmarks = []
        current_offset = 0

        for idx, bookmarks in enumerate(sections):
            current_offset -= first_and_last_objects[idx][0]

            if bookmarks:
                split_bookmarks = bookmarks.split(',')
                for bookmark in split_bookmarks:
                    new_bookmarks.append(str(int(bookmark) + current_offset))

            current_offset += first_and_last_objects[idx][1] + break_length
        return ','.join(new_bookmarks)

    @staticmethod
    def merge_maps(first_map_sections, hitobjects_sections, timing_points_sections, events_sections, bookmarks, break_length, first_and_last_objects):
        """
        Concatenate HitObjects,TimingPoints,Events and Bookmarks sections from multiple maps into a single dictionary

        Parameters:
        first_map_sections (dict): All map sections from the first map in queue
        hitobjects_sections (list): The HitObjects returned from the handle_map_queue function in the MapGenerator class
        timing_points_sections (list): The TimingPoints returned from the handle_map_queue function in the MapGenerator class
        bookmarks (list): The Bookmarks returned from the handle_map_queue function in the MapGenerator class
        break_length (int): The break length
        first_and_last_objects (list(*tuple)): The first and last HitObjects of each map to synchronize other sections and audio

        Returns:
        merged_sections (dict): The concatenated sections

        Usage:
        merged_sections = merge_maps(first_map_sections,hitobjects_sections,timing_points_sections,events_sections,bookmarks,break_length,first_and_last_objects)
        """
        merged_sections = first_map_sections.copy()

        merged_hitobjects_sections = MapProcessor.merge_hitobjects(
            hitobjects_sections, break_length, first_and_last_objects)
        merged_timing_points_sections = MapProcessor.merge_timing_points(
            timing_points_sections, break_length, first_and_last_objects)
        merged_events_sections = MapProcessor.merge_events(
            events_sections, break_length, first_and_last_objects)

        if bookmarks:
            merged_bookmarks = MapProcessor.merge_bookmarks(
                bookmarks, break_length, first_and_last_objects)
            merged_sections["Editor"] = MapProcessor.change_variable(
                merged_sections["Editor"], "Bookmarks", merged_bookmarks)

        merged_sections["HitObjects"] = merged_hitobjects_sections
        merged_sections["TimingPoints"] = merged_timing_points_sections
        merged_sections["Events"] = merged_events_sections

        return merged_sections

    @staticmethod
    def get_uninherited_timing_points(timing_points):
        """
        Get the uninherited timing points from the timing points section.

        Parameters:
        timing_points (list): The TimingPoints section.

        Returns:
        uninherited_timing_points (list): The TimingPoints without the inherited points.

        Usage:
        uninherited_timing_points = get_uninherited_timing_points(timing_points)
        """
        uninherited_timing_points = []
        for point in timing_points:
            stripped_point = point.strip()
            # Check if the stripped point is not an empty string or None
            if stripped_point and not point.startswith("[TimingPoints]"):
                point_elements = stripped_point.split(',')
                if point_elements[6] == "1":
                    uninherited_timing_points.append(point)

        return uninherited_timing_points

    @staticmethod
    def convert_bpm_to_rate(timing_points, beats_per_minute):
        """
        Convert a single bpm to rate. Raise ValueError if there are multiple.

        Parameters:
        timing_points (list): The TimingPoints section.
        beats_per_minute (int): The target bpm to convert to rate.

        Returns:
        map_rate (float): The rate to update HitObjects, TimingPoints, Events and Bookmarks.

        Usage:
        map_rate = convert_bpm_to_rate(timing_points,beats_per_minute)
        """
        uninherited_timing_points = MapProcessor.get_uninherited_timing_points(
            timing_points)

        if len(uninherited_timing_points) > 1:
            raise ValueError(
                "Please select a map with only one uninherited Timing Point!")
        else:
            original_bpm = MapProcessor.get_bpm_from_timing_point(
                uninherited_timing_points[0])
            map_rate = beats_per_minute / original_bpm

        return map_rate

    @staticmethod
    def get_bpm_from_timing_point(timing_point):
        """
        Get the BPM of a single timing point.

        Parameters:
        timing_point (str): The timing point to get the BPM from.

        Returns:
        beats_per_minute (float): The BPM of the timing point.
        """
        timing_point_elements = timing_point.split(',')
        if timing_point_elements[6] != "1":
            raise TypeError("Timing Point must be uninherited!")
        beat_length = timing_point_elements[1]
        beats_per_minute = 60000 / (abs(float(beat_length)))

        return beats_per_minute

    @staticmethod
    def calculate_map_rate(timing_points, rate, is_map_speed_with_bpm):
        return MapProcessor.convert_bpm_to_rate(timing_points[1:], rate) if is_map_speed_with_bpm else rate

    @staticmethod
    def change_map_speed(sections, rate):
        """
        Change the timings of HitObjects, TimingPoints, Events and Bookmarks to match the rate

        Parameters:
        sections (dict): All sections from one map
        rate (float): The rate to update HitObjects, TimingPoints, Events and Bookmarks

        Returns:
        new_file_sections (dict): The updated sections
        """
        if rate == 1.0:
            return sections
        new_file_sections = sections.copy()
        new_file_sections["HitObjects"] = MapProcessor.change_hitobjects_speed(new_file_sections["HitObjects"],
                                                                               rate)
        new_file_sections["TimingPoints"] = MapProcessor.change_timing_points_speed(new_file_sections["TimingPoints"],
                                                                                    rate)
        new_file_sections["Events"] = MapProcessor.change_events_speed(new_file_sections["Events"],
                                                                       rate)

        bookmarks = MapProcessor.get_variable(section=new_file_sections["Editor"],
                                              variable='Bookmarks')
        if bookmarks:
            new_file_sections["Editor"] = MapProcessor.change_variable(
                section=new_file_sections["Editor"],
                variable='Bookmarks',
                new_variable=MapProcessor.change_bookmark_speed(bookmarks, rate))

        return new_file_sections

    @staticmethod
    def change_od_and_ar(difficulty_section, overall_difficulty, approach_rate):
        """
        Change the Overall Difficulty and Approach Rate of a map

        Parameters:
        difficulty_sections (list): The difficulty section of the map
        overall_difficulty (float): The new Overall Difficulty
        approach_rate (float): The new approach rate

        Returns:
        modified_difficulty_section (list): The updated difficulty section
        """
        modified_difficulty_section = difficulty_section.copy()
        if overall_difficulty:
            modified_difficulty_section = MapProcessor.change_variable(
                modified_difficulty_section, "OverallDifficulty", str(overall_difficulty))
        if approach_rate:
            modified_difficulty_section = MapProcessor.change_variable(
                modified_difficulty_section, "ApproachRate", str(approach_rate))
        return modified_difficulty_section
