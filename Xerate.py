# Huge credits to ChatGPT and all testers

import os
import tkinter as tk
from pydub import AudioSegment
from math import floor
from tkinter import filedialog,PhotoImage
from pydub.generators import WhiteNoise
import tkinter.messagebox
os.environ["PATH"] += os.pathsep + os.path.join(os.path.dirname(os.path.realpath(__file__)),'bin').replace('\\','/')

# Function to read sections from an osu file and organize them into a dictionary
def read_osu_sections(file_path):
    with open(file_path, 'r',encoding='utf-8') as file:
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


# Function to convert sections into a list for writing back to an osu file
def write_osu_sections(sections):
    new_file = ['osu file format v14\n']
    # Get the values and add them to the new file list
    for value in sections.values():
        new_file.extend(value)
    return new_file

# Function to change the pitch and speed of an audio file
def change_pitch_and_speed(input_file, output_file, pitch_factor=1.0, speed_factor=1.0):
    # Load the audio file
    audio = AudioSegment.from_file(input_file)

    # Determine output file format based on the input file extension
    output_format = os.path.splitext(input_file)[1][1:]

    # Apply pitch and speed changes
    adjusted_audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * speed_factor)
    })
    adjusted_audio = adjusted_audio.set_frame_rate(audio.frame_rate)
    adjusted_audio = adjusted_audio.set_channels(audio.channels)
    adjusted_audio = adjusted_audio.set_sample_width(audio.sample_width)
    adjusted_audio = adjusted_audio._spawn(
        adjusted_audio.raw_data, overrides={
            "frame_width": int(adjusted_audio.frame_width * pitch_factor)
        }
    )

    # Export the adjusted audio to a file with the determined format
    adjusted_audio.export(output_file, format=output_format)

def crop_audio(audio, start_ms, end_ms, fade_duration=1000):
    # Crop the audio
    cropped_audio = audio[start_ms:end_ms]

    # Apply fade-out effect
    if fade_duration > 0:
        fade_out = cropped_audio[-fade_duration:].fade_out(fade_duration)
        cropped_audio = cropped_audio[:-fade_duration] + fade_out

    return cropped_audio

# Function to change the speed of hit objects in an osu file
def change_hitobjects_speed(hitobjects_section, rate):
    # Initialize new hitobjects variable
    modified_hitobjects_section = []
    for line in hitobjects_section:
        # Get the elements of a line
        line_elements = line.strip().split(',')
        if len(line_elements) >= 3:
            # Extract type and time information
            type_of_object = int(line_elements[3])
            original_time = int(line_elements[2])
            modified_time = floor(original_time / rate)
            line_elements[2] = str(modified_time)
            # Check and modify long notes accordingly
            if type_of_object == 128:
                # Extract endTime information
                splitNoteParams = line_elements[5].split(':')
                original_end_time = int(splitNoteParams[0])
                
                # Modify endTime information
                modified_end_time = floor(original_end_time / rate)
                splitNoteParams[0] = str(modified_end_time)

                # Apply changes
                noteParams = ':'.join(splitNoteParams)
                line_elements[5] = str(noteParams)
            # Check and modify spinners accordingly
            elif type_of_object == 12:
                # Extract endTime information
                original_end_time = int(line_elements[5])

                # Modify endTime information
                modified_end_time = floor(original_end_time / rate)

                # Apply changes
                line_elements[5] = str(modified_end_time)
            modified_line = ','.join(line_elements)
            modified_hitobjects_section.append(modified_line + '\n') # Add the new line with new timing info into the new section
        else:
            modified_hitobjects_section.append(line) # Since we reached a line with probably no timing info, we add it without making any changes
    return modified_hitobjects_section

# Function to change the speed of events in an osu file
def change_events_speed(events_section, rate):
    # Initialize new events variable
    modified_events_section = []
    for line in events_section:
        # Get the elements of a line
        line_elements = line.split(',')

        # Parse the event type
        event_type = line_elements[0]
        
        # If we have an event type,continue
        if event_type:
            if event_type in ["0","1","2","Break"]: 
                modified_events_section.append(line) # For these events we don't need to change timing info
            elif event_type != "[Events]":
                try:
                    original_start_time = int(line_elements[1])
                    original_end_time = int(line_elements[2])
                    modified_start_time = floor(original_start_time / rate)
                    modified_end_time = floor(original_end_time / rate)
                    line_elements[1] = str(modified_start_time)
                    line_elements[2] = str(modified_end_time)
                    modified_line = ','.join(line_elements)
                    modified_events_section.append(modified_line)
                except (ValueError, IndexError):
                    if event_type.strip() in ["L","_L","T","_T"]:
                        if event_type.strip() in ["L","_L"]:
                            original_start_time = int(line_elements[1])
                            modified_start_time = floor(original_start_time / rate)
                            line_elements[1] = str(modified_start_time)
                        else:
                            original_start_time = int(line_elements[2])
                            original_end_time = int(line_elements[3])
                            modified_start_time = floor(original_start_time / rate)
                            modified_end_time = floor(original_end_time / rate)
                            line_elements[2] = str(original_start_time)
                            line_elements[3] = str(original_end_time)
                        modified_line = ','.join(line_elements)
                        modified_events_section.append(modified_line)
                    else:
                        try:
                            original_start_time = int(line_elements[1])
                            original_end_time = int(line_elements[2])
                            modified_start_time = floor(original_start_time / rate)
                            modified_end_time = floor(original_end_time / rate)
                            line_elements[1] = str(modified_start_time)
                            line_elements[2] = str(modified_end_time)
                            modified_line = ','.join(line_elements)
                            modified_events_section.append(modified_line)
                        except (ValueError,IndexError):
                            modified_events_section.append(line)
            else: modified_events_section.append(line)

    return modified_events_section

def change_timing_points_speed(timing_points_section,rate):
    modified_timing_points_section = []
    for line in timing_points_section:
        line_elements = line.strip().split(',')
        if len(line_elements) >= 3:
            original_time = float(line_elements[0])
            modified_time = floor(original_time / rate)
            uninherited = True if line_elements[6] == "1" else False
            if uninherited:
                beatLength = float(line_elements[1])
                modifiedBeatLength = beatLength / rate
                line_elements[1] = str(modifiedBeatLength)
            line_elements[0] = str(modified_time)
            modified_line = ','.join(line_elements)
            modified_timing_points_section.append(modified_line + '\n')
        else:
            modified_timing_points_section.append(line)
    return modified_timing_points_section

def change_variable(section,variable,new_variable):
    modified_section = []
    for line in section:
        if line.startswith(variable):
            line_elements = line.split(':')
            line_elements[1] = new_variable
            modified_line = ':'.join(line_elements)
            modified_section.append(modified_line + '\n')
        else:
            modified_section.append(line)
    return modified_section

def get_variable(section,variable):
    for line in section:
        if line.startswith(variable):
            line_elements = line.split(':') # Most variables are seperated with a colon
            return line_elements[1].strip() # Return the variable without any whitespaces because it can cause problems

def merge_hitobjects(sections,break_length,map_cuts):
    merged_hitobjects = ['[HitObjects]\n']
    current_offset = 0
    for idx,lines in enumerate(sections):
        current_offset -= map_cuts[idx][0]
        for line in lines:
            line_elements = line.strip().split(',')             
            if len(line_elements) >= 3:
                type_of_object = int(line_elements[3])
                original_start_time = int(line_elements[2])
                        
                modified_start_time = floor(original_start_time + current_offset)
                line_elements[2] = str(modified_start_time)
                        
                if type_of_object == 128:
                    splitObjectParams = line_elements[5].split(':')
                    original_end_time = int(splitObjectParams[0])
                    modified_end_time = floor(original_end_time + current_offset)
                    splitObjectParams[0] = str(modified_end_time)
                    objectParams = ':'.join(splitObjectParams)
                    line_elements[5] = objectParams
                elif type_of_object == 12:
                    original_end_time = int(line_elements[5])
                    modified_end_time = floor(original_end_time + current_offset)
                    line_elements[5] = str(modified_end_time)
                        
                modified_line = ','.join(line_elements)
                merged_hitobjects.append(modified_line + '\n')
            else:
                continue
        current_offset += floor(map_cuts[idx][1] + break_length)
    return merged_hitobjects

def merge_timing_points(sections,break_length,map_cuts):
    merged_timing_points = ['[TimingPoints]\n']
    current_offset = 0
    for idx,lines in enumerate(sections):
        current_offset -= map_cuts[idx][0]
        for line in lines:
            line_elements = line.strip().split(',')
            if len(line_elements) >= 3:
                original_start_time = int(line_elements[0])
                modified_start_time = original_start_time + current_offset
                line_elements[0] = str(modified_start_time)
                modified_line = ','.join(line_elements)
                merged_timing_points.append(modified_line + '\n')
            else: 
                continue
        current_offset = floor(map_cuts[idx][1] + break_length)
    return merged_timing_points

def merge_events(sections,break_length,map_cuts):
    merged_events = ['[Events]\n']
    current_offset = 0
    for idx,lines in enumerate(sections):
        current_offset -= map_cuts[idx][0]
        for line in lines:
            line_elements = line.split(',')
            event_type = line_elements[0]
            if event_type != "[Events]":
                if event_type in ["0","1","2"]: continue
                else:
                    try:
                        original_start_time = int(line_elements[1])
                        original_end_time = int(line_elements[2])
                        modified_start_time = floor(original_start_time + current_offset)
                        modified_end_time = floor(original_end_time + current_offset)
                        line_elements[1] = str(modified_start_time)
                        line_elements[2] = str(modified_end_time)
                        modified_line = ','.join(line_elements)
                        merged_events.append(modified_line)
                    except (ValueError, IndexError):
                        if event_type.strip() in ["L","_L","T","_T"]:
                            if event_type.strip() in ["L","_L"]:
                                original_start_time = int(line_elements[1])
                                modified_start_time = floor(original_start_time + current_offset)
                                line_elements[1] = str(modified_start_time)
                                modified_line = ','.join(line_elements)
                                merged_events.append(modified_line)
                            else:
                                original_start_time = int(line_elements[2])
                                original_end_time = int(line_elements[3])
                                modified_start_time = floor(original_start_time + current_offset)
                                modified_end_time = floor(original_end_time + current_offset)
                                line_elements[2] = str(original_start_time)
                                line_elements[3] = str(original_end_time)
                                modified_line = ','.join(line_elements)
                                merged_events.append(modified_line)
                        else:
                            try:
                                original_start_time = int(line_elements[1])
                                original_end_time = int(line_elements[2])
                                modified_start_time = floor(original_start_time + current_offset)
                                modified_end_time = floor(original_end_time + current_offset)
                                line_elements[1] = str(modified_start_time)
                                line_elements[2] = str(modified_end_time)
                                modified_line = ','.join(line_elements)
                                merged_events.append(modified_line)
                            except (ValueError,IndexError):
                                continue
            else:
                continue
        current_offset = floor(map_cuts[idx][1] + break_length)
    return merged_events

def merge_audio_files_with_breaks(files,output_file, break_duration_ms,audio_cuts):
    # Initialize an empty audio segment to merge the files
    merged_audio = AudioSegment.empty()

    # Iterate through the list of files
    for i, file_path in enumerate(files):
        # Load the audio file
        audio = AudioSegment.from_file(file_path)

        audio_start_and_end_ms = audio_cuts[i]
        audio_start_ms = audio_start_and_end_ms[0]
        audio_end_ms = audio_start_and_end_ms[1]

        audio = crop_audio(audio,audio_start_ms,audio_end_ms)

        wind_noise = WhiteNoise().to_audio_segment(break_duration_ms).fade_in(100).fade_out(100).apply_gain(-30)

        # Append the current audio file to the merged audio
        merged_audio += audio
    
        # If it's not the last file, add a break of specified duration
        if i < len(files) - 1:
            merged_audio += wind_noise

    # Export the adjusted audio to a file with the determined format
    merged_audio.export(output_file, format='mp3')

def merge_maps(sections,hitobjects_sections,timing_points_sections,events_sections,break_length,map_cuts):
    merged_sections = sections

    merged_hitobjects_sections = merge_hitobjects(hitobjects_sections,break_length,map_cuts)
    merged_timing_points_sections = merge_timing_points(timing_points_sections,break_length,map_cuts)
    merged_events_sections = merge_events(events_sections,break_length,map_cuts)

    merged_sections["HitObjects"] = merged_hitobjects_sections
    merged_sections["TimingPoints"] = merged_timing_points_sections
    merged_sections["Events"] = merged_events_sections

    return merged_sections

def generate_new_map(file_path,rate,pitch):
    try:
        file_sections = read_osu_sections(file_path=file_path)
    except Exception as e:
        tkinter.messagebox.showerror("File reading error!",f"Couldn't read file. Error:{e}")
        return
    file_name = os.path.basename(file_path)
    file_folder = os.path.dirname(file_path)

    audio_file_name = get_variable(file_sections["General"],"AudioFilename")
    audio_directory = os.path.join(file_folder,audio_file_name)

    new_audio_file_name = f"{rate}x{audio_file_name}"
    new_audio_file_directory = os.path.join(file_folder,new_audio_file_name)
    try:
        change_pitch_and_speed(audio_directory,new_audio_file_directory,pitch,rate)
    except Exception as e:
        tkinter.messagebox.showerror("Error!",f"Audio generation error: {e}.Make sure the audio file exists and/or try installing ffmpeg.")
        return

    diff_name = get_variable(file_sections["Metadata"],"Version")
    new_diff_name = f"{diff_name} {rate}x"
    file_sections["Metadata"] = change_variable(file_sections["Metadata"],"Version",new_diff_name)
    file_sections["General"] = change_variable(file_sections["General"],"AudioFilename",new_audio_file_name)

    file_sections["HitObjects"] = change_hitobjects_speed(file_sections["HitObjects"],rate=rate)
    file_sections["TimingPoints"] = change_timing_points_speed(file_sections["TimingPoints"],rate=rate)
    file_sections["Events"] = change_events_speed(file_sections["Events"],rate=rate)

    new_file_content = write_osu_sections(file_sections)
    new_file_name = f"{rate}x{file_name}"
    new_file_path = os.path.join(file_folder,new_file_name)

    with open(new_file_path,'w') as file:
        file.writelines(new_file_content)
    
    print(file_folder)

    for file in os.listdir(file_folder):
        print(file)
        if file.endswith(".osb"):
            tkinter.messagebox.showinfo("Found .osb file","Note: Detected .osb file for storyboards. Xerate can't change the speed of storyboards because a map can only have one .osb file.")
    
    tkinter.messagebox.showinfo("Map generation complete!","Map generation completed successfully! Press F5 in osu! to play the map.")

def get_file_paths():
    local_app_data = os.environ.get('localappdata') # Most osu installations are in %localappdata%\osu!\
    osu_directory = os.path.join(local_app_data,'osu!','Songs')
    root = tk.Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(title="Select .osu Files", filetypes=[("osu files", "*.osu")],initialdir=osu_directory)
    return file_paths


def get_user_input():
    root = tk.Tk()
    root.title("Xerate")

    img = PhotoImage(file=os.path.join(os.path.dirname(__file__),'Xerate.png'))
    root.iconphoto(False,img)

    root.geometry("350x220")
    def on_generate():
        file_paths = getattr(file_label, "file_paths", None)
        if file_paths:
            rate = float(rate_entry.get()) if rate_entry.get() else 1.0 # Incase the user leaves it empty
            pitch = float(pitch_entry.get()) if pitch_entry.get() else 1.0 # Incase the user leaves it empty
            break_length = float(break_length_entry.get()) if break_length_entry.get() else 5000 # Incase the user leaves it empty
            marathon_name = marathon_name_entry.get() if marathon_name_entry.get() else "Bro you forgot to enter a marathon name"
            hitobjects_sections = []
            timing_points_sections = []
            events_sections = []
            # Check if multiple files are selected. If multiple files are selected, Xerate merges them. Otherwise it will change the rate of a map.
            if len(file_paths) > 1:
                try:
                    sections = read_osu_sections(file_paths[0])
                except Exception as e:
                    tkinter.messagebox.showerror("File reading error!",f"File reading error: {e}")
                    return
                audio_files = []
                map_cuts = []
                # Get the hitobjects, timing points and events and combine them
                for file_path in file_paths:
                    file_sections = read_osu_sections(file_path=file_path)
                    hitobjects_sections.append(file_sections["HitObjects"])
                    timing_points_sections.append(file_sections["TimingPoints"])
                    events_sections.append(file_sections["Events"])
                    audio_files.append(os.path.join(os.path.dirname(file_path),get_variable(file_sections["General"],"AudioFilename")))
                    # Get the first and last hitobjects of a song to cut audio appropriately
                    split_first_object = file_sections["HitObjects"][1].strip().split(',')
                    split_last_object = file_sections["HitObjects"][-1].strip().split(',')
                    first_object_time = int(split_first_object[2])
                    if int(split_last_object[3]) == 128:
                        # Get the end time of a long note
                        splitNoteParams = split_last_object[5].split(':')
                        last_object_time = int(splitNoteParams[0])
                    elif int(split_last_object[3]) == 12:
                        # Get the end time of a spinner
                        last_object_time = int(split_last_object[5])
                    else:
                        # Get the time of a slider or a regular circle
                        last_object_time = int(split_last_object[2])
                    map_cuts.append([first_object_time,last_object_time])

                merged_sections = merge_maps(sections,hitobjects_sections,timing_points_sections,events_sections,break_length,map_cuts)
                merged_audio_filename = f"{marathon_name}.mp3"
                merged_audio_directory = os.path.join(os.path.dirname(audio_files[0]),merged_audio_filename)
                try:
                    merge_audio_files_with_breaks(audio_files,merged_audio_directory,break_length,map_cuts)
                except Exception as e:
                    tkinter.messagebox.showerror("Audio generation error!",f"Audio generation error: {e}. Make sure the audio file exists and/or try installing ffmpeg.")
                    return
                merged_sections["General"] = change_variable(merged_sections["General"],"AudioFilename",merged_audio_filename)

                # Change the map metadata for it to match the marathon name
                merged_sections["Metadata"] = change_variable(merged_sections["Metadata"],"Title",marathon_name)
                merged_sections["Metadata"] = change_variable(merged_sections["Metadata"],"TitleUnicode",marathon_name)
                merged_sections["Metadata"] = change_variable(merged_sections["Metadata"],"Version",marathon_name)

                new_file_content = write_osu_sections(merged_sections)
                new_file_name = f"{marathon_name}.osu"
                new_file_path = os.path.join(os.path.dirname(file_paths[0]), new_file_name)  # Saving in the same directory as the first file

                try:
                    with open(new_file_path, 'w',encoding='utf-8') as file:
                        file.writelines(new_file_content)
                except Exception as e:
                    tkinter.messagebox.showerror("File generation error!",f"File generation error: {e}")
                    return
                
                tkinter.messagebox.showinfo("Map merging complete!",f"Map merging completed successfully! Your map is located in {os.path.dirname(file_paths[0])}. Press F5 in osu! to play the map.")
            else:
                generate_new_map(file_path=file_paths[0], rate=rate, pitch=pitch)
        else:
            tkinter.messagebox.showerror("No files selected","You haven't selected any files.")

    def on_browse():
        file_paths = get_file_paths()
        file_label.file_paths = file_paths
        if file_paths:
            if len(file_paths) > 1:
                file_label.config(text=f"{len(file_paths)} files selected. These will be merged.")
            else:
                file_label.config(text=f"You have selected {os.path.basename(file_paths[0])}")
        else:
            file_label.config(text="No files selected")

    file_frame = tk.Frame(root)
    file_label = tk.Label(file_frame, text="No file selected")
    file_button = tk.Button(file_frame, text="Browse", command=on_browse)
    file_label.pack(side=tk.LEFT)
    file_button.pack(side=tk.LEFT)

    rate_label = tk.Label(root, text="Rate (floating point value):")
    rate_entry = tk.Entry(root)

    pitch_label = tk.Label(root, text="Pitch (Leave empty or type 1 for no change):")
    pitch_entry = tk.Entry(root)
    
    break_length_label = tk.Label(root,text="Break length (Leave empty if you are not merging maps.)")
    break_length_entry = tk.Entry(root)
    generate_button = tk.Button(root, text="Export map", command=on_generate)

    marathon_name_label = tk.Label(root,text="Marathon name (Leave empty if you are not merging maps.)")
    marathon_name_entry = tk.Entry(root)

    file_frame.pack()
    rate_label.pack()
    rate_entry.pack()
    pitch_label.pack()
    pitch_entry.pack()
    marathon_name_label.pack()
    marathon_name_entry.pack()
    break_length_label.pack()
    break_length_entry.pack()
    generate_button.pack()

    def on_close():
        root.destroy()  # Close the window

    root.protocol("WM_DELETE_WINDOW", on_close)  # Close button action

    root.mainloop()

def main():
    get_user_input()

if __name__ == "__main__":
    main()