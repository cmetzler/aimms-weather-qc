from os.path import dirname, realpath, basename, splitext, join, isdir
import sys
from colorama import init, Fore, Style
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors

from utils.read_weather_data_files import solar_to_df
from utils.gooey_wrapper import gooey_on_empty_args, GooeyParser
from utils.loggers import Logger
from utils.paths import get_filecount_and_size

# set plotting backend to avoid QT errors
matplotlib.use('TKAgg')

# initialize terminal text coloring
init()

__version__ = "0.0.1"


def solar_to_stats(solar_file, out_dir=None, utc_offset=7.0, start_time=None, end_time=None, smoothing=20):
    """ Compute statistics for collected solar data, warn the user of anomalous data, and plot the data.

    Illumination, also known as "irradiance", is sometimes measured in watts per square meter (W/m2).
    Another means of measuring light is photon flux. Photon flux is commonly measured in units of
    micromoles per square meter per second (micromoles/m2/s), where 1 mole of photons = 6.022 x 1023 photons.
    Some NV5 sensors measure in W/m2 and others in micromoles/m2/s. Care should be taken that the dataframe supplied
    to this function has irradiance values that have been converted to micromoles/m2/s.

    Note that our collected solar data does not have a spatial component by default, it would have to be
    matched to spatial data by timestamp.

    Required Parameters
    ----------
    solar_data_df : dataframe
        A pandas dataframe of the collected solar data.
        Expects columns ["Date", "LocalTime", "MicroMoles"].
    out_dir : str
        An path for the statistics and plots.

    Optional Parameters
    ----------
    utc_offset : float
        The local time offset from UTC in hours to allow for comparison to UTC collection time stamps.
        In general this will be the laptop time, not true local time. Default is 7.0 hours.
    start_time : str
        The expected start time of solar data collection. Typically this would be the first lidar timestamp in UTC.
        If not set, no QC is performed on time overlap.
    end_time : str
        The expected end time of solar data collection. Typically this would be the last lidar timestamp in UTC.
        If not set, no QC is performed on time overlap.
    smoothing : float
        Smooths the time series data using a Simple Moving Average. Helps to reduce false positives and information
        overload. Default is a 10 period SMA.
    """
    # read the raw data
    raw_solar_df, units = solar_to_df(solar_file,
                                      header_rows=1,
                                      delimiter=",",
                                      columns=None,
                                      time_column="LocalTime",
                                      time_format="%H:%M:%S")

    # setup the output files
    if out_dir:
        output_stats = join(out_dir, splitext(basename(solar_file))[0] + "_solar_stats.txt")
        timeseries_plot = join(out_dir, splitext(basename(solar_file))[0] + "_solar_timeseries_plot.png")
        # spatial_plot = join(splitext(basename(solar_file))[0] + "_spatial_plot.png")
    else:
        output_stats = splitext(solar_file)[0] + "_solar_stats.txt"
        timeseries_plot = splitext(solar_file)[0] + "_solar_timeseries_plot.png"
        # spatial_plot = splitext(solar_file)[0] + "_spatial_plot.png"

    # compute some statistics
    average_photon_flux = round(raw_solar_df["MicroMoles"].mean(), 1)
    median_photon_flux = round(raw_solar_df["MicroMoles"].median(), 1)
    max_photon_flux = round(raw_solar_df["MicroMoles"].max(), 1)
    min_photon_flux = round(raw_solar_df['MicroMoles'].min(), 1)
    stdev_photon_flux = round(raw_solar_df['MicroMoles'].std(), 1)

    # get local (laptop) and utc time stamps
    local_start_time = raw_solar_df['LocalTime'].iloc[0].time()
    local_end_time = raw_solar_df['LocalTime'].iloc[-1].time()
    utc_start_time = (raw_solar_df['LocalTime'].iloc[0] - pd.Timedelta(hours=utc_offset)).time()
    utc_end_time = (raw_solar_df['LocalTime'].iloc[-1] - pd.Timedelta(hours=utc_offset)).time()

    # estimate sample rate:
    sample_rate = raw_solar_df['LocalTime'].diff().median()

    # get number of records and time duration of the collection
    length = len(raw_solar_df['LocalTime'].index)
    estimated_seconds = round(length * sample_rate.total_seconds(), 1)
    duration = (raw_solar_df['LocalTime'].iloc[-1]) - (raw_solar_df['LocalTime'].iloc[0])
    duration_from_length = pd.Timedelta(seconds=estimated_seconds)

    # smooth the data
    smoothing_rate = int(smoothing / sample_rate.total_seconds())
    if smoothing_rate < 1:
        smoothing_rate = 1
    raw_solar_df["MicroMoles"] = raw_solar_df["MicroMoles"].rolling(window=smoothing_rate).mean()

    # check for critical errors

    # check against user given start and stop times
    if start_time:
        start_time = pd.to_datetime(start_time).time()
        if utc_start_time > start_time:
            start_time_warning = "WARNING! Solar data may start after lidar collection began."
    if end_time:
        end_time = pd.to_datetime(end_time).time()
        if utc_end_time < end_time:
            end_time_warning = "WARNING! Solar data may end before lidar collection ends."

    # are there way fewer records than we'd expect for the time duration?
    time_difference = duration - duration_from_length

    # are there zero values and if so how many?
    zero_value_df = raw_solar_df.loc[raw_solar_df['MicroMoles'] == 0]
    zero_value_records = len(zero_value_df['LocalTime'].index)

    # are there lots of low values and if so how many?
    low_value_df = raw_solar_df.loc[raw_solar_df['MicroMoles'] <= 300]
    low_value_records = len(low_value_df['LocalTime'].index)

    # are there lots of high values and if so how many?
    high_value_df = raw_solar_df.loc[raw_solar_df['MicroMoles'] >= 1500]
    high_value_records = len(high_value_df['LocalTime'].index)

    print(Fore.YELLOW + "\n\n### Solar Probe Statistics ###\n")
    print(Style.RESET_ALL + f"Data collected for {duration}.")
    print(f"Collected {length} records.\n")
    print(f"Records cover an estimated {duration_from_length} at {sample_rate.total_seconds()} sample rate.")
    print(f"Solar flux smoothed with a {smoothing} second moving average.\n")
    print(f"Survey UTC Start Time: {start_time}")
    print(f"Survey UTC End Time: {end_time}")
    print(f"Solar UTC Start Time: {utc_start_time}")
    print(f"Solar UTC End Time: {utc_end_time}")
    print(f"Solar Local Start Time: {local_start_time}")
    print(f"Solar Local End Time: {local_end_time}\n")
    print(f"Average photon flux: {average_photon_flux} micromoles")
    print(f"Photon flux StDev: {stdev_photon_flux} micromoles")
    print(f"Median photon flux: {median_photon_flux} micromoles")
    print(f"Minimum photon flux: {min_photon_flux} micromoles")
    print(f"Maximum photon flux: {max_photon_flux} micromoles\n")

    if time_difference >= pd.Timedelta(minutes=10):
        print(Fore.RED + f"WARNING! Potential data recording error"
              + Style.RESET_ALL + f" discrepancy of {time_difference} between record count and start/stop times.")
    if zero_value_records > 30:
        print(Fore.RED + f"WARNING! Potential data recording error"
              + Style.RESET_ALL + f" for {zero_value_records} records.")
    if low_value_records > 30:
        print(Fore.RED + f"WARNING! Low solar irradiance detected"
              + Style.RESET_ALL + f" for {low_value_records} records.")
    if high_value_records > 30:
        print(Fore.RED + "WARNING! High solar irradiance detected"
              + Style.RESET_ALL + f" for {high_value_records} records.")
    if start_time:
        print(Fore.RED + f"{start_time_warning}" + Style.RESET_ALL)
    if end_time:
        print(Fore.RED + f"{end_time_warning}"+ Style.RESET_ALL)

    with open(output_stats, mode='w') as f:
        # write out stats to a log file for future review
        f.writelines(f"### Solar Probe Statistics ###\n\n")
        f.writelines(f"Data collected for {duration}.\n")
        f.writelines(f"Collected {length} records.\n")
        f.writelines(f"Records cover an estimated {duration_from_length} at {sample_rate.total_seconds()} sample rate.\n\n")
        f.writelines(f"Solar flux smoothed with a {smoothing} second moving average.\n")
        f.writelines(f"Survey UTC Start Time: {start_time}\n")
        f.writelines(f"Survey UTC End Time: {end_time}\n")
        f.writelines(f"Solar UTC Start Time: {utc_start_time}\n")
        f.writelines(f"Solar UTC End Time: {utc_end_time}\n")
        f.writelines(f"Solar Local Start Time: {local_start_time}\n")
        f.writelines(f"Solar Local End Time: {local_end_time}\n\n")
        f.writelines(f"Average photon flux: {average_photon_flux} micromoles\n")
        f.writelines(f"Photon flux StDev: {stdev_photon_flux} micromoles\n")
        f.writelines(f"Median photon flux: {median_photon_flux} micromoles\n")
        f.writelines(f"Minimum photon flux: {min_photon_flux} micromoles\n")
        f.writelines(f"Maximum photon flux: {max_photon_flux} micromoles\n\n")

        if time_difference >= pd.Timedelta(minutes=10):
            f.writelines(Fore.RED + f"WARNING! Potential data recording error"
                  + Style.RESET_ALL + f" discrepancy of {time_difference} between record count and start/stop times.\n")
        if zero_value_records > 30:
            f.writelines(f"WARNING! Potential data recording error"
                         f" for {zero_value_records} records.\n")
        if low_value_records > 30:
            f.writelines(f"WARNING! Low solar irradiance detected"
                         f" for {low_value_records} records.\n")
        if high_value_records > 30:
            f.writelines("WARNING! High solar irradiance detected"
                         f" for {high_value_records} records.\n")
        if start_time:
            f.writelines(f"{start_time_warning}\n")
        if end_time:
            f.writelines(f"{end_time_warning}\n")

    # generate timeseries plot
    fig, ax = plt.subplots()
    raw_solar_df.plot(x="LocalTime", y="MicroMoles", title=basename(solar_file) + " Timeseries", ax=ax, figsize=(15,10))
    ax.set_xlabel("Local Time")
    ax.set_ylabel("Solar Irradiation")
    # reference line at 600 micromoles
    ax.axhline(y=600, xmin=0, xmax=1, linestyle='--', color='purple')
    plt.savefig(timeseries_plot, bbox_inches='tight', format='png', dpi=900)
    plt.close(fig)

    # TODO: fix the stats logging
    # move stats to log directory for future compilation and reference
    #try:
    #    log_report(output_stats, report_type="new_report")
    #except Exception as e:
    #    print(e)

    # TODO: add spatial plot (requires linking to trajectory data by timestamp)
    # TODO: add spatial kml (also requires linking to trajectory data)

    return duration, utc_start_time, utc_end_time, output_stats, timeseries_plot


@gooey_on_empty_args(program_name=f"QC Solar Irradiance {__version__}",
                     program_description=f"Raw data validation for helicopter-mounted solar irradiance probe.",
                     clear_before_run=True,
                     navigation="Tabbed",
                     tabbed_groups=True,
                     # body_bg_color="#4DD9FF",
                     header_bg_color="#4DD9FF",
                     footer_bg_color="#4DD9FF",
                     default_size=(700, 700),
                     ignore_gooey=(__name__ != "__main__"))
def get_args():
    """ Retrieve user arguments for raw solar data qc using gooey/argparse. """
    parser = GooeyParser(prog="QC Solar Irradiance",
                         epilog=f"v{__version__}")

    settings_group = parser.add_argument_group("QC Settings")

    logging_group = parser.add_argument_group("Log Settings")

    settings_group.add_argument("--in_path",
                                widget="FileChooser",
                                help="Input raw solar data file (typically *.csv)",
                                metavar="Input File")

    settings_group.add_argument("--recursive",
                                action="store_false",
                                default=True,
                                help=" Search all subdirectories for file matches. "
                                     "Only applied if 'Input File' is a directory.",
                                metavar="Recursive")

    settings_group.add_argument("--out_dir",
                                widget="DirChooser",
                                help="Output directory for extracted statistics and plots. "
                                     "If blank, will output to input directory.",
                                metavar="Output Directory")

    settings_group.add_argument("--utc_offset",
                                help="Specify the offset in hours from UTC Time.",
                                default=-7.0,
                                type=float,
                                metavar="UTC Offset")

    settings_group.add_argument("--start_time",
                                help="Lidar survey start time to compare against. No comparison is made if left blank."
                                     " Ex: \"14:45:00\"",
                                metavar="Lidar Start Time")

    settings_group.add_argument("--end_time",
                                help="Lidar survey end time to compare against. No comparison is made if left blank."
                                     " Ex: \"20:30:00\"",
                                metavar="Lidar End Time")

    settings_group.add_argument("--smoothing",
                                help="Period over which to apply a moving average for data smoothing. Use 1 to analyze "
                                     "the raw data with no modifications. Measured in seconds, not records!",
                                metavar="Moving Average Period",
                                type=int,
                                default=20)

    logging_group.add_argument("--log_level",
                                default="WARNING",
                                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                help="Specify the logging verbosity.",
                                metavar="Log Level")

    logging_group.add_argument("--log_dir",
                               help="Specify an alternate directory for logging the statistics.",
                               metavar="Stats log dir")

    args = parser.parse_args()

    # flip booleans for gooeyparser limitation
    args.recursive = not args.recursive

    return args


def validate_args(args):
    """ Validate the user inputs prior to code execution. """
    return args


def main():
    """ Execute the solar statistics script. """

    # get args from gooey/argparse
    args = get_args()

    args.logger = Logger(__name__,
                         console_logger=True,
                         print_logger=False,
                         console_log_level=args.log_level,
                         print_log_level=args.log_level)

    args = validate_args(args)

    # if a directory was specified, loop through all solar data files
    if isdir(args.in_path):
        file_count, total_size, file_paths = get_filecount_and_size(args.in_path,
                                                                    extensions=[".csv"],
                                                                    exclude_folders=["ignore"],
                                                                    recursive=args.recursive,
                                                                    file_list=True)
        args.logger.info(f"\nProcessing {file_count} solar files totalling {round(total_size,2)} GB.")
        for file_path in file_paths:
            duration, utc_start_time, utc_end_time, output_stats, timeseries_plot = \
                solar_to_stats(file_path,
                               out_dir=args.out_dir,
                               utc_offset=args.utc_offset,
                               start_time=args.start_time,
                               end_time=args.end_time,
                               smoothing=args.smoothing)
    # else run the qc on the input file
    else:
        duration, utc_start_time, utc_end_time, output_stats, timeseries_plot = \
            solar_to_stats(args.in_path,
                           out_dir=args.out_dir,
                           utc_offset=args.utc_offset,
                           start_time=args.start_time,
                           end_time=args.end_time,
                           smoothing=args.smoothing)

    print("\nProcessing complete!")


if __name__ == '__main__':
    main()
