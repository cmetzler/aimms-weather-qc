import os
import sys
import pathlib
from shutil import rmtree, copy, move
import fnmatch
import re
from utils.loggers import Logger

logger = Logger(__name__,
                console_logger=True,
                console_log_level="INFO")


def check_if_file(in_path, must_exist=False, max_extension_length=4):
    """Check if a path represents a file or a directory.

    Returns True if the given path represents a file. The parameter 'must_exist'
    can be used to check paths that may not currently exist on the filesystem.
    If 'must_exist' is True, the check will use os.isfile(), but if 'must_exist'
    is False, the check will attempt to parse the string to determine if the path
    ends in a file extension.

    Parameters
    ----------
    in_path : str
        A regular string path.
    must_exist : bool
        If False, the check will not assume that the input path currently
        exists on the file system and if True, the check will assume that
        the path should already exist (the default is False).
    max_extension_length : int
        For checking paths that don't currently exist, you may specify a
        max extension length if you may be dealing with odd files with
        very long extensions (default is 4). Using longer extension lengths
        increases the risk of false positives from paths that have '.' characters.

    Returns
    -------
    is_file : bool
        True if the path is a file, false if it is not.

    """
    in_path = os.path.abspath(in_path)

    if os.path.exists(in_path):
        if os.path.isfile(in_path):
            return True
        elif os.path.isdir(in_path):
            return False
    elif not must_exist:
        # if the file doesn't currently exist
        # we can parse the string and see if there is a file extension
        if len(in_path.split(".")) == 1:
            return False
        if len(in_path.split(".")) > 1:
            if len(in_path.split(".")[-1]) <= max_extension_length:
                return True
    else:
        return False


def drop_filename(in_path, max_extension_length=4):
    """Ignore the filename in a file path.

    Uses os.path.dirname() to remove the file name from a file path.
    The path does not need to currently exist on the file system.
    If the path does not include the filename, it will remain unchanged.
    
    Parameters
    ----------
    in_path : str
        A regular string path.
    max_extension_length : int, optional
        For checking paths that don't currently exist, you may specify a
        max extension length if you may be dealing with odd files with
        very long extensions (default is 4). Using longer extension lengths
        increases the risk of false positives from paths that have '.' characters.

    Returns
    -------
    dir_path : str
        A path without a filename.

    """
    in_path = os.path.abspath(in_path)

    is_file = check_if_file(in_path, must_exist=False, max_extension_length=max_extension_length)

    if is_file:
        dir_path = os.path.dirname(in_path)
    else:
        dir_path = in_path

    return dir_path
    
    
def get_drive_letter(in_path):
    """
    The drive letter of a given file or directory path.

    Returns the letter of the drive for a given file or directory path, eg 'I'.
    Any ":" or "/" characters are stripped so only the letter is returned.

    Parameters
    ----------
    in_path : str
        A regular string path.

    Returns
    -------
    drive_letter : str
        String of the drive letter.

    """
    in_path = os.path.abspath(in_path)

    try:
        drive_letter = os.path.splitdrive(in_path)[0].strip(":")
    except AttributeError:
        drive_letter = None
        logger.info(f"No drive letter found when parsing path {drive_letter}")

    return drive_letter


def get_mission_str(in_path, ignore_filename=True):
    """
    The PDX-style mission designation string.

    Searches the path using regex and returns the pdx-style
    mission designation string, eg '230204A_SN6390'. If the path
    has more than one designation string, only the first is returned.

    Parameters
    ----------
    in_path : str
        A regular string path.
    ignore_filename : bool
        If true, the regex search will only look at the directory tree name.

    Returns
    -------
    mission_str : str
        String of the mission designator.

    """
    in_path = os.path.abspath(in_path)

    if ignore_filename:
        in_path = drop_filename(in_path)
    try:
        mission_str_pattern = r"(\d{6})\w?_SN\d+"
        mission_str = re.search(mission_str_pattern, str(in_path))
        mission_str = mission_str.group(0)
    except AttributeError:
        mission_str = None
        logger.info(f"No mission ID found when parsing path {in_path}")

    return mission_str


def get_mission_date(in_path, ignore_filename=True):
    """
    The PDX-style mission date string

    Searches the path using regex and returns the pdx-style
    mission date string, eg '230204'. If the path has more
    than one mission date, only the first is returned.

    Parameters
    ----------
    in_path : str
        A regular string path.
    ignore_filename : bool
        If true, the regex search will only look at the directory tree name.

    Returns
    -------
    mission_date : str
        String of the mission date.

    """
    in_path = os.path.abspath(in_path)

    if ignore_filename:
        in_path = drop_filename(in_path)
    try:
        mission_date_pattern = r"(\d{6})"
        mission_date = re.search(mission_date_pattern, str(in_path))
        mission_date = mission_date.group(0)
    except AttributeError:
        mission_date = None
        logger.info(f"No mission date found when parsing path {in_path}")

    return mission_date


def get_mission_index(in_path, ignore_filename=True):
    """
    The PDX-style mission index string

    Searches the path using regex and returns the pdx-style
    mission index string, eg 'A' or 'B'. If the path has more
    than one mission index, only the first is returned.

    Parameters
    ----------
    in_path : str
        A regular string path.
    ignore_filename : bool
        If true, the regex search will only look at the directory tree name.

    Returns
    -------
    str
        String of the mission date.

    """
    in_path = os.path.abspath(in_path)

    if ignore_filename:
        in_path = drop_filename(in_path)
    try:
        mission_index_pattern = r"(?<=\d{6})\D"
        mission_index = re.search(mission_index_pattern, str(in_path))
        mission_index = (mission_index.group(0))
    except AttributeError:
        mission_index = None
        logger.info(f"No mission index found when parsing path {in_path}")

    return mission_index


def get_sensor_number(in_path, ignore_filename=True):
    """
    The PDX-style sensor serial identifier string

    Searches the path using regex and returns the PDX-style
    sensor serial identifier string, eg 'SN4040' or 'SN9967'.
    If the path has more than one sensor serial identifier,
    only the first is returned.

    Parameters
    ----------
    in_path : str
        A regular string path.
    ignore_filename : bool
        If true, the regex search will only look at the directory tree name.

    Returns
    -------
    sensor_serial : str
        String of the sensor serial number, including the 'SN'.

    """
    in_path = os.path.abspath(in_path)

    if ignore_filename:
        in_path = drop_filename(in_path)
    try:
        sensor_number_pattern = r"SN\d+"
        sensor_number = re.search(sensor_number_pattern, str(in_path))
        sensor_serial = (sensor_number.group(0))
    except AttributeError:
        sensor_serial = None
        logger.info(f"No sensor number found when parsing path {in_path}")

    return sensor_serial


def get_aircraft(in_path, ignore_filename=True):
    """
    The PDX-style aircraft tail number identifier string

    Searches the path using regex and returns the PDX-style
    aircraft tail number string, eg 'N740JA' or 'N9984K'.
    Because of the variability in aircraft naming, this search
    looks for the full string 'mission_sensor_aircraft', then splits
    the string and takes the last element.

    Parameters
    ----------
    in_path : str
        A regular string path.
    ignore_filename : bool
        If true, the regex search will only look at the directory tree name.

    Returns
    -------
    aircraft_identifier : str
        String of the aircraft tail number.

    """
    in_path = os.path.abspath(in_path)

    if ignore_filename:
        in_path = drop_filename(in_path)
    try:
        aircraft_identifier_pattern = r"(\d{6})\w?_SN\d+_[A-Za-z0-9]+"
        aircraft_identifier = re.search(aircraft_identifier_pattern, str(in_path))
        aircraft_identifier = (aircraft_identifier.group(0))
        aircraft_identifier = aircraft_identifier.split("_")[-1]
    except AttributeError:
        aircraft_identifier = None
        logger.info(f"No sensor number found when parsing path {in_path}")

    return aircraft_identifier


def parse_filepath(in_path):
    """Returns some useful parts of a filepath.

    Parameters
    ----------
    in_path : str
        A regular string path.

    Returns
    -------
    tuple(str, str, str, str, str)
        Parent directory only, Parent directory with filename,
        Filename without extension, Filename with extension, Only the filetype extension

    """
    in_path = os.path.abspath(in_path)

    try:
        parent_dir = os.path.dirname(in_path)
        parent_dir_with_filename, ext = os.path.splitext(in_path)
        filename_with_ext = os.path.basename(in_path)
        filename_without_ext = os.path.splitext(filename_with_ext)[0]
    except AttributeError:
        parent_dir = None
        parent_dir_with_filename, ext = None, None
        filename_with_ext = None
        filename_without_ext = None
        logger.info(f"No file or folder name found when parsing path {in_path}")

    return parent_dir, parent_dir_with_filename, filename_without_ext, filename_with_ext, ext


def make_dir(in_path, remove_existing=False):
    """If given folder path does not exist, creates the folder
    Do nothing if the folder already exists

    Parameters
    ----------
    in_path : str
        A regular string path.
    remove_existing: bool
        If True, if the input path already exists it will be deleted and replaced.
    """
    in_path = os.path.abspath(in_path)
    logger.info(f"Trying to create directory at {in_path}.")

    # delete the folder if the user wants to remove existing instance
    if remove_existing:
        if os.path.exists(in_path):
            delete_path(in_path)

    # try making the directory
    try:
        pathlib.Path(in_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory {in_path}.")
    except Exception as e:
        logger.error(f"Cannot create directory for path {in_path}.")
        logger.error(e)


def delete_path(in_path):
    """ Delete the given file or folder.

    Only the shutil.rmtree method seems to work,
    otherwise you get permissions errors if using pathlib or os.remove
    eg [WinError 5] Access is denied: 'D:\\01_REPO\\pdx_bridge\\utils\\src\\pathpackage\\test_dir'

    Parameters
    ----------
    in_path : str
        A regular string path.

    """

    # TODO: why doesn't pathlib.path.unlink work?
    # try:
    #     in_path.unlink(missing_ok=True)
    #     logger.info(f"Deleted path at {in_path}.")
    # except Exception as e:
    #     logger.error(f"Cannot delete directory for path {in_path}.")
    #     logger.error(e)

    in_path = os.path.abspath(in_path)
    try:
        if os.path.isdir(in_path):
            rmtree(str(in_path))
            logger.debug(f"Deleted path at {in_path}.")
        elif os.path.isfile(in_path):
            os.remove(in_path)
            logger.debug(f"Deleted file at {in_path}.")
    except Exception as e:
        logger.error(e)


def yield_file_paths(in_path, extensions=None, exclude_strings=None, exclude_folders=None, recursive=True):
    """Yield file paths from a directory or directory tree.

    Walks through a directory and returns all files with a given
    file extension. Can optionally search recursively. Files are returned
    as they are found, so they can be manipulated in a stream.

    Parameters
    ----------
    in_path : str
        A regular string path.
    extensions : list[str], optional
        A list of file extensions to use for filtering. Eg, ['rxp', 'las']
        The extensions given will be kept and other file types ignored.
    exclude_strings : list[str], optional
        A list of strings that, if found in the file name, will cause that file to be ignored. Eg, ['test', 'iter_1']
    exclude_folders : list[str], optional
        A list of folder names that will be ignored. Eg, ['do_not_use', 'ignore', 'bad_lines']
    recursive : bool, optional
        If True, the search will recursively search subdirectories.

    Yields
    -------
    file_path : str
        File paths found in the directory tree.

    """
    in_path = os.path.abspath(in_path)

    # convert all extensions and filters to lowercase
    if extensions is not None:
        extensions = [ext.lower() for ext in extensions]
    if exclude_strings is not None:
        exclude_strings = [ex_str.lower() for ex_str in exclude_strings]
    if exclude_folders is not None:
        exclude_folders = [ex_fldr.lower() for ex_fldr in exclude_folders]

    with os.scandir(in_path) as path_iter:
        for entry in path_iter:
            if entry.is_file() \
                    and (extensions is None
                         or entry.name.lower().endswith(tuple(extensions))) \
                    and (exclude_strings is None
                         or not any(ex_str in entry.name.lower() for ex_str in exclude_strings)):
                yield entry.path
            elif entry.is_dir() \
                    and recursive \
                    and (exclude_folders is None
                         or entry.name.lower() not in exclude_folders):
                yield from yield_file_paths(entry.path,
                                            extensions=extensions,
                                            exclude_strings=exclude_strings,
                                            recursive=recursive,
                                            exclude_folders=exclude_folders)


def get_filecount_and_size(in_path,
                           extensions=None,
                           exclude_strings=None,
                           exclude_folders=None,
                           recursive=True,
                           file_list=False,
                           action=None,
                           out_path=None):
    """File count and total file size for all files in a directory tree.

    Walks through a directory and returns the number of files found
    and their total size. Can be run recursively. Can supply a list
    of all files found. Can move, copy, or delete the files as they are found.

    Parameters
    ----------
    in_path : str
        A regular string path.
    extensions : list[str], optional
        A list of file extensions to use for filtering.
        The extensions given will be kept and other file types ignored.
    exclude_strings : list[str], optional
        A list of strings that, if found in the file name, will cause that file to be ignored.
    exclude_folders : list[str], optional
        A list of folder names that will be ignored. Eg, ['do_not_use', 'ignore', 'bad_lines']
    recursive : bool, optional
        If True, the search will recursively search subdirectories.
    file_list : bool, optional
        If True, a list of all files found will be returned.
    action : str, optional
        Perform an action on each file as it is found. Options are ('delete', 'copy', 'move')
    out_path : str, optional
        Output directory for 'move' and 'copy' actions.

    Returns
    -------
    file_count : int
        File paths found in the directory tree.
    file_size : float
        Total size in GB of all the files found.
    filepath_list : list[str]
        A list of all the filepaths found.

    """
    file_count = 0
    total_size = 0
    file_paths = []

    if action is not None and action.lower() not in ["delete", "copy", "move"]:
        logger.error(f"Action {action} not supported.")
        action = None
    elif action is None:
        pass
    elif action.lower() == "copy" or action.lower() == "move":
        if out_path is None:
            logger.error(f"Files cannot be copied/moved, output path was not specified.")
        elif not os.path.exists(out_path):
            logger.error(f"Files cannot be copied/moved, output path {out_path} does not exist.")
        else:
            logger.info(f"{action.lower()} files to {out_path}.")

    for file_path in yield_file_paths(in_path,
                                      extensions=extensions,
                                      exclude_strings=exclude_strings,
                                      exclude_folders=exclude_folders,
                                      recursive=recursive):
        # if the user wants a file list, append the file name
        if file_list:
            file_paths.append(file_path)

        # work around to deal with long path names (>255 characters)
        long_file_path = "\\\\?\\" + file_path

        # count the files and get a total size
        file_count += 1
        total_size += os.path.getsize(long_file_path)

        # check if the user wanted any actions done
        if action is None:
            pass
        elif action.lower() == "delete":
            try:
                delete_path(long_file_path)
            except Exception as e:
                logger.info(f"Unexpected error {e} when deleting file {file_path}")
        elif action.lower() == "copy":
            try:
                copy(long_file_path, out_path)
            except Exception as e:
                logger.info(f"Unexpected error {e} when copying file {file_path}")
        elif action.lower() == "move":
            try:
                move(long_file_path, out_path)
            except Exception as e:
                logger.info(f"Unexpected error {e} when moving file {file_path}")

    # report size in GB
    total_size = round(total_size / 1_073_741_824.0, 6)

    return file_count, total_size, file_paths


def pattern_matcher(in_file, patterns):
    """Checks for patterns in a file name.

    Returns True if the pattern exists, False if it doesn't.

    Parameters
    ----------
    in_file : str
        A regular string path.
    patterns : list[str]
        A list of patterns to use for filtering.

    Returns
    -------
    match : bool
        True if the file name has the pattern.

    """
    # convert patterns to lowercase
    patterns = [pattern.lower() for pattern in patterns]

    for p in patterns:
        if fnmatch.fnmatch(in_file, p):
            return True
        else:
            return False


def extension_matcher(in_file, extensions):
    """Checks if a file name has a given extension.

    Returns True if the extension exists, False if it doesn't.

    Parameters
    ----------
    in_file : str
        A regular string path.
    extensions : list[str]
        A list of extensions to use for filtering.

    Returns
    -------
    match : bool
        True if the file name has the extension.

    """
    # convert extensions to lowercase
    extensions = [extension.lower() for extension in extensions]

    if in_file.lower().endswith(tuple(extensions)):
        return True
    else:
        return False
