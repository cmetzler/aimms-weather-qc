import pandas as pd
import sys
import re


def solar_to_df(solar_file,
                header_rows=1,
                delimiter=",",
                columns=None,
                time_column="LocalTime",
                time_format="%H:%M:%S"):
    """Reads a solar probe csv file and returns a pandas dataframe.

    The csv file is generally three comma separated columns: Date, LocalTime,
    and MicroMoles of solar irradiation. Sometimes the irradiation is recored in watts per square meter.
    The units will be converted to micromoles in the dataframe.
    The typical csv file has a 1 row header
    that is ignored, but the user can specify any number of header rows
    (or to skip sensor tests and test-fires).An alternate delimiter may be specified
    with the keyword argument "delimiter". The user may specify a list of
    alternate column names with the "columns" keyword argument. If alternate columns
    are given, the user must either include "LocalTime" or specify the new time column name
    using the "time_column" keyword argument.

    Required Parameters
    ----------
    solar_file : str
        A path to a raw solar probe data csv file

    Optional Parameters
    ----------
    header_rows : int
        Number of rows containing header data that can be skipped. Defaults to 1.
    delimiter : str
        The delimiter used within the csv file. Defaults to ","
    columns : list
        The column names within the csv file. Defaults to ["Date", "LocalTime", "MicroMoles"]
    time_column : str
        Specify the name of the column containing time information. Default is "LocalTime".
    time_format : str
        Specify the format of the time string for conversion to a datetime object. Default is "%H:%M:%S".

    Returns
    -------
    dataframe
        Pandas dataframe of the solar probe timeseries data

    """
    # read the first line to determine the units
    with open(solar_file, "r") as f:
        first_line = f.readline()
        units = first_line.split(",")[2].strip()
        print(f"\n\nDiscovered {units} units for solar irradiance.")

    # set the columns of the dataframe
    columns = columns or ["Date", "LocalTime", "MicroMoles"]

    # read the data into a dataframe
    raw_solar_df = pd.read_csv(solar_file, skiprows=header_rows, delimiter=delimiter, names=columns)

    # format the time column, this is generally local time (computer time)
    raw_solar_df[time_column] = raw_solar_df[time_column].str.lstrip()
    raw_solar_df[time_column] = pd.to_datetime(raw_solar_df[time_column], format=time_format)

    # convert the units if needed.
    if units == "watts/m2" or units == "W/m2":
        raw_solar_df["MicroMoles"] = raw_solar_df["MicroMoles"] * 4.57
        print("Converting W/m2 to MicroMoles")
    elif units == "Î¼moles":
        print("No unit conversion applied.")
    else:
        print("Warning! Units not recognized, no conversion applied!")

    return raw_solar_df, units


def aimms_to_df(aimms_file, format=None):
    """Reads weather data from an aimms probe.

    The probe data can vary a bit between probes. There are at least 3 formats with subtle differences.
    This function will try to determine which format based on the first few rows of data and extract accordingly.

    Required Parameters
    ----------
    aimms_file : str
        A path to an extracted weather data file from an AIMMS probe.
    format: str
        The format of the data records. If left as None, the function will try to automatically detect the format.

    Returns
    -------
    dataframe
        Pandas dataframe of the weather probe timeseries data

    References
    ----------
    Aventech AIMMS 20 : https://aventech.com/products/aimms20.html
    Aventech AIMMS 30 : https://aventech.com/products/aimms30.html

    Format for Geo1 older-style aimms probe:
        Row 2 has:
    Time,Temp.,RH,P_stat,Uw,Vw,Lat.,Long.,Z,Ui,Vi,Wi,Roll,Pitch,Heading,TAS,Ww,AoS,P_beta,P_alpha,C_p,W_spd,W_dir

    Format for geo1 newer-style aimms probe:
        Row 2 has:
    Time,Temp.,RH,P_stat,Uw,Vw,Lat.,Long.,Z,Ui,Vi,Wi,Roll,Pitch,Heading,TAS,Ww,AoS,P_beta,P_alpha,W_spd,W_dir,Turb,LoadF.

    Format for QSI CLASS 2.0 style aimms probe:
       No header row! Fields are:
    Time,Temp.,RH,P_stat,Uw,Vw,Lat.,Long.,Z,Ui,Vi,Wi,Roll,Pitch,Heading,TAS,Ww,Dim_AoS,AoA,AoS,Wind_Status

    """

    # read the 2nd line to determine the format
    if format is None:
        with open(aimms_file) as f:
            line = f.readlines()[1]  # the second line should be indicative of the format
            line = re.sub("\s+", ",", line.strip())  # the whitespace may not be consistent so replace with commas
            if "AoS,P_beta,P_alpha,W_spd,W_dir,Turb,LoadF." in line:
                format = "geo1_new"
            elif "AoS,P_beta,P_alpha,C_p,W_spd,W_dir" in line:
                format = "geo1_old"
            else:  # the nv5 format has no header
                format = "nv5"

    if format == "geo1_old":
        aimms_df = pd.read_csv(aimms_file, skiprows=3, delimiter=r'\s+', skipinitialspace=True,
                               names=['Time', 'Temp', 'RH', 'P_stat', 'Uw', 'Vw', 'Lat', 'Long', 'Z', 'Ui', 'Vi', 'Wi',
                                      'Roll', 'Pitch', 'Heading', 'TAS', 'Ww', 'AoS', 'P_beta', 'P_alpha', 'C_p',
                                      'W_spd', 'W_dir'])
        # drop the final columns which are inconsistent between formats and not necessary for QC
        aimms_df = aimms_df.drop(columns=['AoS', 'P_beta', 'P_alpha', 'C_p', 'W_spd', 'W_dir'])

    elif format == "geo1_new":
        aimms_df = pd.read_csv(aimms_file, skiprows=3, delimiter=r'\s+', skipinitialspace=True,
                               names=['Time', 'Temp', 'RH', 'P_stat', 'Uw', 'Vw', 'Lat', 'Long', 'Z', 'Ui', 'Vi', 'Wi',
                                      'Roll', 'Pitch', 'Heading', 'TAS', 'Ww', 'AoS', 'P_beta', 'P_alpha', 'W_spd',
                                      'W_dir', 'Turb', "LoadF"])
        # drop the final columns which are inconsistent between formats and not necessary for QC
        aimms_df = aimms_df.drop(columns=['AoS', 'P_beta', 'P_alpha', 'W_spd', 'W_dir', 'Turb', "LoadF"])

    elif format == "nv5":
        aimms_df = pd.read_csv(aimms_file, skiprows=3, delimiter=r'\s+', skipinitialspace=True,
                               names=['Time', 'Temp', 'RH', 'P_stat', 'Uw', 'Vw', 'Lat', 'Long', 'Z', 'Ui', 'Vi', 'Wi',
                                      'Roll', 'Pitch', 'Heading', 'TAS', 'Ww', 'DimAoS', "AoA", "AoS", "Wind_Status"])
        # drop the final columns which are inconsistent between formats and not necessary for QC
        aimms_df = aimms_df.drop(columns=['DimAoS', "AoA", "AoS", "Wind_Status"])

    else:
        sys.exit(f"Weather format {format} not recognized!")

    # TODO: fix utc midnight rollover
    aimms_df['Time'] = aimms_df['Time'].apply(decimal_hours_to_hh_mm_ss)
    aimms_df['Time'] = pd.to_datetime(aimms_df['Time'], format='%H:%M:%S.%f')

    return aimms_df


def decimal_hours_to_hh_mm_ss(time):
    """ Convert a decimal hour to an hh:mm:ss format.

    Required Parameters
    ----------
    timestamp : float
        Time stamp in decimal hour format.

    Returns
    -------
    timestamp
        Time stamp in hh:mm:ss format
    """
    # force the clock to roll over at utc midnight
    time = time % 24

    hours = int(time)
    minutes = (time*60) % 60.
    seconds = (time*3600) % 60

    time = "%02d:%02d:%.2f" % (hours, minutes, seconds)

    return time
