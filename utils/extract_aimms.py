import os
import sys
import shutil
import subprocess


def extract_aimms(aimms_file,
                  out_dir=None,
                  exe_dir=r"C:\Scripts\pdx_bridge\tasks\aimms_weather",
                  weather_exe="ekf560A30.exe"):
    """ Extracts aimms data from weather probe using
    custom executables supplied by the manufacturer.

    Required Parameters
    ----------
    aimms_file : str
        A path to a raw aventech weather probe data file

    Optional Parameters
    ----------
    out_dir : str
        The output location. Defaults to the input aimms file directory.
    exe_dir : str
        The processing directory containing the weather executable files and parameter files.
        Defaults to the bridge repo.
    weather_exe : str
        The executable to use, which can depend on the specific probe utilized. Defaults to ekf560A30.exe.

    Returns
    -------
    met file
        The extracted meteorological data file.
    """

    # the executables tend to only work when the input parameter and data files are in the same directory
    file_name = os.path.basename(aimms_file)
    shutil.copy(aimms_file, exe_dir)

    # the output is created in the same directory as the exe
    out_file_name = os.path.splitext(file_name)[0] + "_extract.out"
    out_file_path = os.path.join(exe_dir, out_file_name)

    print(f"\nExtracting file {aimms_file}")
    print(f"Using directory {exe_dir}")
    print(f"Using extraction tool {weather_exe}")

    try:
        if weather_exe == "ekf560A30.exe":
            args = [r"ekf560A30.exe",
                    r"ekf560A30_param.dat",
                    file_name,
                    "-c", "on",
                    "-f", "on",
                    "-t", "on",
                    "-w", "on",
                    "-o", out_file_name]
        elif weather_exe == "ekf612A30.exe":
            args = [r"ekf612A30.exe",
                    r"ekf612A30_param.dat",
                    file_name,
                    "-c", "on",
                    "-f", "on",
                    "-t", "on",
                    "-w", "on",
                    "-o", out_file_name]
        elif weather_exe == "canextr4_ssii.exe":
            args = [r"canextr4_ssii.exe",
                    file_name,
                    out_file_name]
        else:
            sys.exit(f"Weather_exe {weather_exe} not recognized!")

        # run the executable as a subprocess
        subprocess.run(args, cwd=exe_dir, shell=True)

    except Exception as e:
        raise e

    # copy the output file to the input aimms directory or a new directory
    try:
        if out_dir:
            out_file_copy = os.path.join(out_dir, out_file_name)
        else:
            out_file_copy = os.path.join(os.path.dirname(aimms_file), out_file_name)
        shutil.move(out_file_path, out_file_copy)
    except Exception as e:
        raise e

    # delete the raw data file from the exe dir
    try:
        os.remove(os.path.join(exe_dir, file_name))
    except Exception as e:
        print(e)

    # check if the output is empty which can happen if the exe is not compatible with the raw data file
    if os.path.getsize(out_file_copy) == 0:
        sys.exit("Output file is empty, weather extraction failed.")

    return out_file_copy
