"""Helper functions that can be used throughout the program."""
from initconfig import DEFAULT_CLIP_MODE, DEFAULT_DESCRIPTION, DEFAULT_NUM_THREADS, DEFAULT_PRIVACY_STATUS, DEFAULT_TITLE, SAVE_CLIPS_TO, VIDEO_FOLDER
import os
import sys
import termtables as tt
from colorama import Fore, Back, Style
from moviepy.editor import VideoFileClip
from datetime import datetime
from upload import initialize_upload
from apiclient.errors import HttpError


class YoutubeClip():
    def __init__(self, clip=VideoFileClip, title=DEFAULT_TITLE, description=DEFAULT_DESCRIPTION, time_from=None, number_of_threads=DEFAULT_NUM_THREADS, privacy_status=DEFAULT_PRIVACY_STATUS, clip_file_name=None, clip_mode=DEFAULT_CLIP_MODE, interval=None):
        self.title = title
        self.description = description
        self.time_from = time_from
        self.interval = interval
        self.number_of_threads = number_of_threads
        self.privacy_status = privacy_status
        self.clip = clip

        if clip_file_name:
            self.clip_file_name = clip_file_name
        else:
            self.clip_file_name = current_time()

        self.clip_file_name = f"{SAVE_CLIPS_TO}{self.clip_file_name}"

        self.clip_mode = clip_mode

        if self.clip_mode in "es" and self.time_from == None:
            raise Exception(
                "Invalid youtube clip instance (no time_from parameter given).")
        elif self.clip_mode == 'i' and (self.interval == None or len(self.interval) != 2):
            raise Exception(
                "Invalid youtube clip instance (invalid interval parameter given).")

    def write_clip_file(self, fps=60):
        print(self.clip_mode)
        if self.clip_mode in "es":
            self.clip.subclip(self.time_from).write_videofile(self.clip_file_name, fps=fps,
                                                              threads=self.number_of_threads)
        elif self.clip_mode == 'i':
            self.clip.subclip(self.interval[0], self.interval[1]).write_videofile(self.clip_file_name, fps=fps,
                                                                                  threads=self.number_of_threads)

    def upload(self, auth_service):
        try:
            initialize_upload(youtube=auth_service, clip=self)
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def __str__(self):
        header = ["Preference", "Value"]
        data = [
            ["Title", self.title],
            ["Description", self.description.encode(
                'unicode-escape').decode()],
            ["Privacy Status", self.privacy_status],
            ["Num. Threads", self.number_of_threads],
            ["File Name", self.clip_file_name],
            ["Clip Mode", self.clip_mode]
        ]

        if self.clip_mode in "es":
            data.append(["Time", self.time_from])
        elif self.clip_mode == 'i':
            data.append(["Interval", self.interval.__str__])

        return tt.to_string(data, header=header)


class WatchlistFile():
    def __init__(self, filepath, ignored=False, archived=False, uploaded=False, missing=False):
        self.filepath = filepath
        self.relpath = os.path.relpath(filepath)
        self.filename = os.path.basename(filepath)
        self.ignored = ignored
        self.archived = archived
        self.uploaded = uploaded
        self.missing = missing

    def __str__(self):
        data = [
            ["Filepath", self.filepath],
            ["Relpath", self.relpath],
            ["Filename", self.filename],
            ["Ignored?", self.ignored],
            ["Archived?", self.archived],
            ["Uploaded?", self.uploaded]
        ]
        return tt.to_string(data)


class Watchlist():
    def __init__(self, files=None):
        self.archived_count = 0
        self.uploaded_count = 0
        self.ignored_count = 0
        self.files = []
        if files:
            for f in files:
                assert type(f) == WatchlistFile
                self.add_file(f)

    def nonmissing_files(self):
        return filter(lambda f: f.missing == False, self.files)

    def add_file(self, f: WatchlistFile):
        self.files.append(f)
        self.update_counters(f)

    def remove_file(self, f: WatchlistFile):
        self.files.pop(self.files.index(f))
        self.update_counters(f, addition=False)

    def update_counters(self, f: WatchlistFile, addition=True):
        if addition:
            if f.ignored:
                self.ignored_count += 1
            if f.archived:
                self.archived_count += 1
            if f.uploaded:
                self.uploaded_count += 1
        else:
            if f.ignored:
                self.ignored_count -= 1
            if f.archived:
                self.archived_count -= 1
            if f.uploaded:
                self.uploaded_count -= 1

    def __str__(self):
        if len(self.files) == 0:
            return ""

        header = ["Filepath", "Ignored", "Archived", "Uploaded"]
        data = []
        for f in self.files:
            data.append([f.filepath, f.ignored, f.archived, f.uploaded])

        stats = f"\nTotal: {len(self.files)} Ignored: {self.ignored_count} Archived: {self.archived_count} Uploaded: {self.uploaded_count}"
        return tt.to_string(data, header=header) + stats

    def __sizeof__(self):
        return len(self.files)

    def __len__(self):
        return len(self.files)


def input_interval(message: str, minimum=None, maximum=None, integer=True):
    invalid_input = True
    while invalid_input:
        value = input(f"[{minimum},{maximum}] " + message)

        try:
            interval = value.split(" ")

            if len(interval) != 2:
                print_error(
                    f"Please insert a valid interval in ascending order, between {minimum} and {maximum}")

            if integer:
                interval[0] = int(interval[0])
                interval[1] = int(interval[1])
            else:
                interval[0] = float(interval[0])
                interval[1] = float(interval[1])
        except Exception as e:
            print_error(
                f"Please insert a valid number between {minimum} and {maximum}.")
        else:
            if interval[0] < minimum or interval[0] > maximum:
                print_error(
                    f"Please insert valid numbers between {minimum} and {maximum}.")
            elif interval[1] < minimum or interval[1] > maximum:
                print_error(
                    f"Please insert valid numbers between {minimum} and {maximum}.")
            elif interval[0] > interval[1]:
                print_error(
                    f"Please insert a valid interval in ascending order, between {minimum} and {maximum}.")
            else:
                invalid_input = False
                break
    return tuple(interval)


def input_selection(options: dict, message="Select from these options: ", description=None, default=None, error_message="Please insert from the available options."):
    """input from a selection of options

    Parameters
    ----------
    options : dict
        options accepted in input, e.g: {"u": "unlisted"}
    message : str, optional
        message to show in input, by default "Select from these options {}: "
    default : str, optional
        default value to use if input is empty, by default is None
    error_message : str, optional
        if input isn't in options, by default "Please insert from the available options."

    Returns
    -------
    str
        returns input from user as string
    """

    if len(options) < 2:
        raise Exception(
            f"Options parameter is invalid (length={len(options)}).")

    header = ["Option Description", "Option Value"]
    data = [[opt, key] for key, opt in options.items()]
    tt.print(data, header=header)

    if description:
        print(description + "\n")

    if default != None:
        message = f"[default={default}] " + message

    invalid_input = True
    while invalid_input:
        value = input(message)

        if default != None and value == '':
            return default

        invalid_input = value not in options.keys()
        if invalid_input:
            print_error(f"{error_message}\n")
    return value


def input_range(message="Please insert a value: ", default=None, minimum=None, maximum=None, integer=True, errors=(None, None, None)):
    """input within a range (inclusive limits)

    Parameters
    ----------
    message : str, optional
        message to show in input, by default "Please insert a value: "
    default : int | float, optional
        default value if user doesn't input anything, by default None
    minimum : int | float, optional
        minimum value for input, by default None
    maximum : int | float, optional
        maximum value for input, by default None
    integer : bool, optional
        if input is integer (or float), by default True
    errors : tuple, optional
        ("input isn't integer", "input is below minimum", "input is above maximum"), by default (None,None,None)

    Returns
    -------
    int | float
        return is determined by integer parameter
    """
    # TODO: syntax for errors is a bit wonky
    if len(errors) != 3:
        raise Exception(f"Errors parameter is invalid (length={len(errors)}).")

    if integer:
        input_type = "integer"
    else:
        input_type = "float"

    message = f"[{minimum},{maximum}] " + message
    if default != None:
        message = f"[default={default}] " + message

    invalid_input = True
    while invalid_input:
        try:
            value = input(message)
            if default != None and value == '':
                return default
            if integer:
                value = int(value)
            else:
                value = float(value)
        except:
            if errors[0] == None:
                print_error(f"Please insert an {input_type}.\n")
            else:
                print_error(errors[0])

        else:
            if minimum != None and value < minimum:
                if errors[1] == None:
                    print_error(
                        f"Please insert a {input_type} greater or equal to {minimum}.\n")
                else:
                    print_error(errors[1])

            elif maximum != None and value > maximum:
                if errors[2] == None:
                    print_error(
                        f"The maximum value is {maximum}, please insert a valid {input_type}.\n")
                else:
                    print_error(errors[2])
            else:
                invalid_time = False
                break
    return value


def input_file(message: str, directory=VIDEO_FOLDER):
    invalid_input = True
    while invalid_input:
        fname = input(
            f"[IN: '{directory}'] Enter the filename that you wish to clip: ")
        if not fname:
            print("Please insert a valid filename.")
            # TODO: Print valid files in directory?
        else:
            if not os.path.exists(f"{directory}{fname}"):
                print("The file you entered does not exist.")
            else:
                invalid_input = False


def print_error(message: str):
    msg = f"{Fore.WHITE + Back.RED}[ERROR]{Style.RESET_ALL} {message}"
    print(msg)


def print_info(message: str):
    msg = f"{Fore.BLACK + Back.LIGHTWHITE_EX}[INFO]{Style.RESET_ALL} {message}"
    print(msg)


def print_warning(message: str):
    msg = f"{Fore.WHITE + Back.YELLOW}[WARN]{Style.RESET_ALL} {message}"
    print(msg)


def current_time():
    return round(datetime.utcnow().timestamp() * 1000)


def read_watchlist_file():
    print_info("Reading watchlist file...")

    # We're dealing with filepaths, need exaggerated separators
    fname = "watchlist.txt"
    arg_separator = " ---------- "  # - x 10

    files = Watchlist()
    invalid_files = 0

    with open(fname, "r") as data_file:
        lines = list(filter(lambda line: len(line) > 0, data_file.readlines()))

        for line in lines:
            f, ignored, archived, uploaded = line.split(sep=arg_separator)

            missing = False
            if not os.path.exists(f):
                print_warning(f"Couldn't find file: {f}")
                invalid_files += 1
                missing = True

            try:
                archived = bool(int(archived))
                uploaded = bool(int(uploaded))
                ignored = bool(int(ignored))
            except Exception as e:
                print_error(
                    f"Error parsing watchlist file arguments! [f={f},i={ignored},a={archived},u={uploaded}]")
                raise

            files.add_file(WatchlistFile(
                f, ignored, archived, uploaded, missing))

        data_file.seek(0)

    print_info(
        f"Successfully parsed watchlist file! {len(files)} files parsed. {invalid_files} files missing.")

    return files


def write_watchlist_file(watchlist: Watchlist):
    print_info("Writing watchlist file...")

    arg_separator = " ---------- "  # - x 10

    with open("watchlist.txt", "w+") as watchfile:
        for f in watchlist.files:
            line = f"{f.filepath}{arg_separator}{int(f.ignored)}{arg_separator}{int(f.archived)}{arg_separator}{int(f.uploaded)}\n"
            watchfile.write(line)

    print_info("Done.")


def get_videos_in_directory():
    """Goes down to 2 levels recursively, since NVIDIA groups clips by game"""
    videos = []
    for folder, sub_folders, dir_files in os.walk(VIDEO_FOLDER):
        for sub_folder in sub_folders:
            for _, _, sub_files in os.walk(VIDEO_FOLDER + sub_folder):
                for sub_file in sub_files:
                    if sub_file[-4:] == '.mp4':
                        incomplete = os.path.join(
                            os.path.abspath(sub_folder), sub_file)
                        filepath = os.path.join(
                            os.path.abspath(folder), incomplete)
                        dir_files.append((sub_file, filepath))

        for f in dir_files:
            if f[-4:] == '.mp4':
                videos.append((f, os.path.join(os.path.abspath(folder), f)))

    return videos


def delete_video(f: WatchlistFile, watchlist: Watchlist):
    print_info(f"Deleting video: {f.filepath}")
    try:
        os.remove(f.filepath)
        watchlist.remove_file(f)
    except:
        print_error("There was a problem deleting the video!")
    else:
        print_info("Successfully deleted the video.")


def preview_video(f: WatchlistFile):
    if sys.platform == 'linux':
        os.system(f'xdg-open "{f.filepath}"')
    elif sys.platform == 'win32':
        os.startfile(f.filepath)
    else:
        raise Exception("Video preview isn't available in your OS.")


if __name__ == "__main__":  # DEBUG
    pass
