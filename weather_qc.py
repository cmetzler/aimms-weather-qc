import sys
import pandas as pd
import numpy as np
from os.path import dirname, realpath, basename, splitext, join, isdir, isfile
import math
from datetime import datetime
from colorama import init, Fore, Style
import matplotlib.pyplot as plt

# tell python to search for modules from other parts of the bridge team scripts folder
cwd = dirname(dirname(dirname(realpath(__file__))))
sys.path.insert(1, cwd)

from utils.read_weather_data_files import aimms_to_df
from utils.solar_stats import solar_to_stats
from utils.aimms_to_kml import aimms_to_kml
from utils.extract_aimms import extract_aimms
from utils.plot_windspeed_errors import plot_windspeed_errors
from utils.read_lidar_timestamp_source import get_times_from_mission_csv
from utils.gooey_wrapper import gooey_on_empty_args, GooeyParser


__version__ = "0.0.1"

# aimms processing directory
AIMMS_EXE_DIR = join(cwd, "aimms_exe")


def weather_to_stats(aimms_df,
                     weather_stats,
                     wind_smoothing=20,
                     temp_smoothing=10,
                     pressure_smoothing=10,
                     relhumid_smoothing=10):
    """
    Required Arguments
    ----------
    aimms_df : dataframe
        A pandas dataframe of
    weather_stats : str
        The output file that the results will be written to.

    Optional Arguments
    ----------
    wind_smoothing : int
        Period over which to apply a moving average to smooth the data.
    temp_smoothing : int
        Period over which to apply a moving average to smooth the data.
    pressure_smoothing : int
        Period over which to apply a moving average to smooth the data.
    relhumid_smoothing : int
        Period over which to apply a moving average to smooth the data.

    Returns
    -------
    duration : str
        The duration of the weather data.
    utc_start_time : str
        The utc start time of the collection.
    utc_end_time : str
        The utc end time of the collection.
    """

    # smooth the data
    aimms_df["Uw"] = aimms_df["Uw"].rolling(window=wind_smoothing).mean()
    aimms_df["Vw"] = aimms_df["Vw"].rolling(window=wind_smoothing).mean()
    aimms_df["Temp"] = aimms_df["Temp"].rolling(window=temp_smoothing).mean()
    aimms_df["RH"] = aimms_df["RH"].rolling(window=relhumid_smoothing).mean()
    aimms_df["P_stat"] = aimms_df["P_stat"].rolling(window=pressure_smoothing).mean()

    # timing
    duration = aimms_df['Time'].iloc[-1] - aimms_df['Time'].iloc[0]
    length = len(aimms_df['Time'].index)
    utc_start_time = aimms_df['Time'].iloc[0].time()
    utc_end_time = aimms_df['Time'].iloc[-1].time()
    
    # temp, pressure, and humidty
    average_temp = round(aimms_df['Temp'].mean(),3)
    variance_temp = round(aimms_df['Temp'].std(),3)
    average_pstat = round(aimms_df['P_stat'].mean(),3)
    variance_pstat = round(aimms_df['P_stat'].std(),3)
    average_relhumid = round(aimms_df['RH'].mean(),3)
    variance_relhumid = round(aimms_df['RH'].std(),3)

    # compute wind speed from components
    vect_combined_components = np.vectorize(combined_components)
    aimms_df['Computed_WS'] = vect_combined_components(aimms_df['Uw'], aimms_df['Vw'])
    average_wspeed = round(aimms_df['Computed_WS'].mean(),3)
    variance_wspeed = round(aimms_df['Computed_WS'].std(),3)

    print(Fore.YELLOW + "\n\n### AIMMS Probe Statistics ###\n")
   
    print(Style.RESET_ALL + f"Data collected for {duration} hours.")
    print(f"Collected {length} records.\n")
    
    print(f"UTC Start Time: {utc_start_time}")
    print(f"UTC End Time: {utc_end_time}\n")
    
    print(f"Average temperature: {average_temp} C")
    print(f"Temperature StDev: {variance_temp} C")
    print(f"Average pressure: {average_pstat} pascals")
    print(f"Pressure StDev: {variance_pstat} pascals")
    print(f"Average Wind Speed: {average_wspeed} m/sec")
    print(f"Wind Speed StDev: {variance_wspeed} m/sec\n")
    print(f"Average Rel Humidity: {average_relhumid} %")
    print(f"Rel Humidity StDev: {variance_relhumid} %")
    
    
    # zero wind speed errors
    error_zero_ws_df = aimms_df.loc[aimms_df['Computed_WS'] == 0]
    error_zero_ws_length = round(len(error_zero_ws_df['Time'].index)/60,1)
    
    if error_zero_ws_length > 1:
        print(Fore.RED + "WARNING! Potential windspeed recording error " + Style.RESET_ALL + f"of 0 m/sec for {error_zero_ws_length} minutes.")
    
    # high wind speed errors
    error_high_ws_df = aimms_df.loc[aimms_df['Computed_WS'] > 27.0]
    error_high_ws_length = round(len(error_high_ws_df['Time'].index)/60,1)

    if error_high_ws_length > 1:
        print(Fore.RED + "WARNING! Potential windspeed recording error " + Style.RESET_ALL + f"of >27 m/sec for {error_high_ws_length} minutes.")

    # temperature errors
    error_temp_df = aimms_df.loc[aimms_df['Temp'] == 0]
    error_temp_length = round(len(error_temp_df['Time'].index)/60,1)  

    if error_temp_length > 1:
        print(Fore.RED + "WARNING! Potential data recording error " + Style.RESET_ALL + f"of 0 temperature for {error_temp_length} minutes.")
        
        
    # pressure errors
    error_pressure_df = aimms_df.loc[aimms_df['Temp'] == 0]
    error_pressure_length = round(len(error_pressure_df['Time'].index)/60,1)  

    if error_pressure_length > 1:
        print(Fore.RED + "WARNING! Potential data recording error " + Style.RESET_ALL + f"of 0 pressure for {error_pressure_length} minutes.")

    with open(weather_stats, mode='w') as f:
        # write out stats to a log file for future review
        
        f.writelines("####### AIMMS Data QC #########\n\n")

        f.writelines(f"Wind data smoothed with a {wind_smoothing} period moving average.\n")
        f.writelines(f"Temp data smoothed with a {temp_smoothing} period moving average.\n")
        f.writelines(f"Humidity data smoothed with a {relhumid_smoothing} period moving average.\n")
        f.writelines(f"Pressure data smoothed with a {pressure_smoothing} period moving average.\n")

        f.writelines(f"Data collected for {duration} hours.\n")
        f.writelines(f"Collected {length} records.\n\n")
    
        f.writelines(f"UTC Start Time: {utc_start_time}\n")
        f.writelines(f"UTC End Time: {utc_end_time}\n\n")
    
        f.writelines(f"Average temperature: {average_temp} C\n")
        f.writelines(f"Temperature StDev: {variance_temp} C\n")
        f.writelines(f"Average pressure: {average_pstat} pascals\n")
        f.writelines(f"Pressure StDev: {variance_pstat} pascals\n")
        f.writelines(f"Average Wind Speed: {average_wspeed} m/sec\n")
        f.writelines(f"Wind Speed StDev: {variance_wspeed} m/sec\n\n")
        
        if error_zero_ws_length > 1:
            f.writelines(f"WARNING! Potential windspeed recording error of 0 m/sec for {error_zero_ws_length} minutes.\n\n")
        if error_high_ws_length > 1:
            f.writelines(f"WARNING! Potential windspeed recording error of >27 m/sec for {error_high_ws_length} minutes.\n\n")
        if error_temp_length > 1:
            f.writelines(f"WARNING! Potential data recording error of 0 temperature for {error_temp_df} minutes.\n\n")
        if error_pressure_length > 1:
            f.writelines(f"WARNING! Potential data recording error of 0 pressure for {error_pressure_length} minutes.\n\n")

    # make some plots

    # generate timeseries plot for temperature
    fig, ax = plt.subplots()
    plot_name = splitext(weather_stats)[0] + "_temp_timeseries.png"
    aimms_df.plot(x="Time", y="Temp", title=basename(plot_name), ax=ax, figsize=(15,10))
    ax.set_xlabel("UTC Time")
    ax.set_ylabel("Temperature deg C")
    # reference line at 20 degrees celsius
    ax.axhline(y=20, xmin=0, xmax=1, linestyle='--', color='purple')
    plt.savefig(plot_name, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)

    # generate timeseries plot for wind speed
    fig, ax = plt.subplots()
    plot_name = splitext(weather_stats)[0] + "_windspeed_timeseries.png"
    aimms_df.plot(x="Time", y="Computed_WS", title=basename(plot_name), ax=ax, figsize=(15,10))
    ax.set_xlabel("UTC Time")
    ax.set_ylabel("Wind Speed m/s")
    # reference line at 6.7 m/s (15 mph)
    ax.axhline(y=6.7, xmin=0, xmax=1, linestyle='--', color='purple')
    # reference line at 27 m/s (60 mph)
    ax.axhline(y=27, xmin=0, xmax=1, linestyle='--', color='red')
    plt.savefig(plot_name, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)

    # generate timeseries plot for pressure
    fig, ax = plt.subplots()
    plot_name = splitext(weather_stats)[0] + "_pressure_timeseries.png"
    aimms_df.plot(x="Time", y="P_stat", title=basename(plot_name), ax=ax, figsize=(15,10))
    ax.set_xlabel("UTC Time")
    ax.set_ylabel("Pressure (Pa)")
    # reference line at 90k
    ax.axhline(y=90_000, xmin=0, xmax=1, linestyle='--', color='purple')
    plt.savefig(plot_name, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)

    # generate timeseries plot for relative humidity
    fig, ax = plt.subplots()
    plot_name = splitext(weather_stats)[0] + "_humidity_timeseries.png"
    aimms_df.plot(x="Time", y="RH", title=basename(plot_name), ax=ax, figsize=(15,10))
    ax.set_xlabel("UTC Time")
    ax.set_ylabel("Humidity %")
    plt.savefig(plot_name, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)

    # generate spatial plot for windspeed
    plot_windspeed_errors(aimms_df, splitext(weather_stats)[0] + "_georef_windspeed.png")

    # altitude plot
    fig, ax = plt.subplots()
    plot_name = splitext(weather_stats)[0] + "_altitude_timeseries.png"
    aimms_df.plot(x="Time", y="Z", title=basename(plot_name), ax=ax, figsize=(15,10))
    ax.set_xlabel("UTC Time")
    ax.set_ylabel("MSL Altitude")
    plt.savefig(plot_name, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)


    # TODO: create more spatial plots or attributed shapefiles

    return duration, utc_start_time, utc_end_time


def combined_components(x, y, precision=6):
    """ Linear combination of two orthogonal variables

    Required Parameters
    ----------
    x : float
        Component in the x direction.
    y : float
        Component in the y direction.

    Optional Parameters
    ----------
    precision : int
        The number of decimal places to keep on the output. Defaults to 6.

    Returns
    -------
    r : float
        The linear combination of x and y, generally interpreted as a 2D radius.
    """
    r = round(math.sqrt(math.pow(x,2) + math.pow(y,2)), 6)

    return r


def check_weather_data(aimms_file, solar, mission_csv, out_dir, utc_offset, per_line_qc, weather_exe,
                       wind_smoothing, temp_smoothing, relhumid_smoothing, pressure_smoothing, solar_smoothing):
    """ Wrapper function for various weather QC utilities for aimms probe and solar probe data.

    Required Parameters
    ----------
    aimms_file : str
        Component in the x direction.

    Optional Parameters
    ----------
    solar : str
        Component in the y direction.
    out_dir : int
        The number of decimal places to keep on the output. Defaults to 6.
    aimms_file : str
        Component in the x direction.
    aimms_file : str
        Component in the x direction.
    aimms_file : str
        Component in the x direction.

    Returns
    -------
    r : float
        The linear combination of x and y, generally interpreted as a 2D radius.
    """
    # initialize text coloring
    init()

    # setup some names
    file_name = basename(aimms_file)
    name, ext = splitext(file_name)
    if out_dir is None:
        out_dir = dirname(aimms_file)
    kml_file = join(out_dir, name + '.kml')

    weatherfilename = basename(aimms_file)
    name, ext = splitext(weatherfilename)


    weather_stats = join(out_dir, name + '_weather_statistics.txt')

    # extract the data if it is a .RAW binary data file
    if aimms_file.endswith('.RAW'):
        print("\nParsing Raw aimms data.\n")
        aimms_file = extract_aimms(aimms_file,
                                   out_dir=out_dir,
                                   exe_dir=AIMMS_EXE_DIR,
                                   weather_exe=weather_exe)

    # read the aimms data into a dataframe
    raw_weather_df = aimms_to_df(aimms_file)

    # make a reference kml
    aimms_to_kml(raw_weather_df, kml_file)

    # convert smoothing periods to time intervals

    # estimate sample rate:
    sample_rate = raw_weather_df['Time'].diff().median()
    print(raw_weather_df['Time'].head(50))
    # TODO: fix utc midnight issue where plot is split and second part of the flight is plotted before the first part.
    print(sample_rate)
    print(sample_rate.total_seconds())
    wind_smoothing = int(wind_smoothing / sample_rate.total_seconds())
    temp_smoothing = int(temp_smoothing / sample_rate.total_seconds())
    pressure_smoothing = int(pressure_smoothing / sample_rate.total_seconds())
    relhumid_smoothing = int(relhumid_smoothing / sample_rate.total_seconds())

    # compute the start/stop and duration and generate statistics
    duration, utc_start_time, utc_end_time = weather_to_stats(raw_weather_df,
                                                              weather_stats,
                                                              wind_smoothing=wind_smoothing,
                                                              temp_smoothing=temp_smoothing,
                                                              pressure_smoothing=pressure_smoothing,
                                                              relhumid_smoothing=relhumid_smoothing)

    if mission_csv and isfile(mission_csv):
        lidar_start_time, lidar_end_time = get_times_from_mission_csv(mission_csv)

        utc_start_time_datetime = datetime.strptime(str(utc_start_time), '%H:%M:%S')
        lidar_start_time_datetime = datetime.strptime(str(lidar_start_time), '%H:%M:%S.%f')

        utc_end_time_datetime = datetime.strptime(str(utc_end_time), '%H:%M:%S')
        lidar_end_time_datetime = datetime.strptime(str(lidar_end_time), '%H:%M:%S.%f')

        with open(weather_stats, mode='a') as f:
            print(Fore.YELLOW + "\n\n### AIMMS probe and Lidar time Comparison ###")
            print(Style.RESET_ALL + "\nAIMMS Start Time: {}".format(utc_start_time))
            print("Lidar Start Time: {}".format(lidar_start_time))
            print("\nLidar End Time: {}".format(lidar_end_time))
            print("AIMMS End Time: {}".format(utc_end_time))

            print("\nAIMMS duration before lidar: {}".format(lidar_start_time_datetime - utc_start_time_datetime))
            print("AIMMS duration after lidar: {}".format(utc_end_time_datetime - lidar_end_time_datetime))

            f.writelines("\n### AIMMS probe and Lidar time Comparison ###\n")
            f.writelines("\nAIMMS Start Time: {}\n".format(utc_start_time))
            f.writelines("Lidar Start Time: {}\n".format(lidar_start_time))
            f.writelines("Lidar End Time: {} \n".format(lidar_end_time))
            f.writelines("AIMMS End Time: {} \n".format(utc_end_time))


            f.writelines("\nAIMMS duration before lidar: {} \n".format(lidar_start_time_datetime - utc_start_time_datetime))
            f.writelines("AIMMS duration after lidar: {} \n".format(utc_end_time_datetime - lidar_end_time_datetime))

            if lidar_start_time_datetime < utc_start_time_datetime:
                print(Fore.RED + "\nWARNING! Might be missing AIMMS coverage at the start of the mission!" + Style.RESET_ALL)
                f.writelines("WARNING! Might be missing AIMMS coverage at the start of the mission!\n")
            if lidar_end_time_datetime > utc_end_time_datetime:
                print(Fore.RED + "\nWARNING! Might be missing AIMMS coverage at the end of the mission!" + Style.RESET_ALL)
                f.writelines("WARNING! Might be missing AIMMS coverage at the end of the mission!\n")

            if per_line_qc is True:
                # TODO: split aimms data by rxp start and stop times, run QC per flightline
                pass

        if solar is not None:
            duration, utc_start_time, utc_end_time, output_stats, timeseries_plot = \
                solar_to_stats(solar,
                               out_dir=out_dir,
                               utc_offset=utc_offset,
                               start_time=lidar_start_time,
                               end_time=lidar_end_time,
                               smoothing=solar_smoothing)
    else:
        if solar is not None:
            duration, utc_start_time, utc_end_time, output_stats, timeseries_plot = \
                solar_to_stats(solar,
                               out_dir=out_dir,
                               utc_offset=utc_offset,
                               smoothing=solar_smoothing)


@gooey_on_empty_args(program_name=f"QC AIMMS Weather Data {__version__}",
                     program_description=f"Raw data validation for helicopter-mounted AIMMS probe.",
                     clear_before_run=True,
                     navigation="Tabbed",
                     tabbed_groups=True,
                     # body_bg_color="#4DD9FF",
                     header_bg_color="#4DD9FF",
                     footer_bg_color="#4DD9FF",
                     default_size=(900, 700),
                     ignore_gooey=(__name__ != "__main__"))
def get_args():
    """ Retrieve user arguments for raw solar data qc using gooey/argparse. """
    parser = GooeyParser(prog="QC AIMMS Weather Data",
                         epilog=f"v{__version__}")

    settings_group = parser.add_argument_group("QC Settings")

    smoothing_group = parser.add_argument_group("Sampling Settings")

    logging_group = parser.add_argument_group("Log Settings")

    settings_group.add_argument('--extraction_exe',
                        help="Specify an alternate weather probe extraction executable.",
                        default="ekf560A30.exe",
                        choices=["ekf560A30.exe", "ekf612A30.exe", "canextr4_ssii.exe"],
                        metavar="Extraction EXE")

    settings_group.add_argument("--in_path",
                                widget="FileChooser",
                                help="Input aimms file. (typically *.RAW or *.ÿÿÿ)",
                                metavar="Input File")

    settings_group.add_argument('--solar',
                        help='Corresponding solar probe data to check for temporal coverage and reasonable values',
                                metavar="Solar Data File")

    settings_group.add_argument('--mission_file',
                        help='Corresponding lidar mission csv file or lidar RPP file to check timestamp overlap',
                        metavar="Mission CSV or RPP")

    settings_group.add_argument("--out_dir",
                                widget="DirChooser",
                                help="Output directory for extracted statistics and plots. "
                                     "If blank, will output to input directory.",
                                metavar="Output Directory")

    settings_group.add_argument('--utc_offset',
                        type=float,
                        help='Input local to UTC time offset, default -7.0',
                        default=-7.0,
                        metavar="Solar Probe UTC Offset")

    settings_group.add_argument('--per_line_qc',
                        action='store_false',
                        help="Enable QC per line using rpp file timestamps.",
                        metavar="Per Swath QC")

    smoothing_group.add_argument("--wind_smoothing",
                                 default=20,
                                 type=int)

    smoothing_group.add_argument("--temp_smoothing",
                                 default=10,
                                 type=int)

    smoothing_group.add_argument("--pressure_smoothing",
                                 default=10,
                                 type=int)

    smoothing_group.add_argument("--relhumid_smoothing",
                                 default=10,
                                 type=int)

    smoothing_group.add_argument("--solar_smoothing",
                                 default=10,
                                 type=int)

    logging_group.add_argument("--log_level",
                                default="WARNING",
                                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                help="Specify the logging verbosity.",
                                metavar="Log Level")

    args = parser.parse_args()

    return args



def validate_args(args):
    return args


def main():
    args = get_args()
    args = validate_args(args)
    sys.exit(check_weather_data(args.in_path,
                                args.solar,
                                args.mission_file,
                                args.out_dir,
                                args.utc_offset,
                                args.per_line_qc,
                                args.extraction_exe,
                                args.wind_smoothing,
                                args.temp_smoothing,
                                args.relhumid_smoothing,
                                args.pressure_smoothing,
                                args.solar_smoothing))


if __name__ == '__main__':
    main()
