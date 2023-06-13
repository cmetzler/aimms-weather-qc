import os
import pandas as pd

# TODO: can we have wind speed, temp as attributes or even color the kml in segments based on the windspeed?


def aimms_to_kml(weather_df, kml_file):
    """ Writes the positional information from a weather data file to a kml. Useful for cross referencing against
    the sensor trajectory to identify potential areas of missed weather coverage.

    Required Parameters
    ----------
    weather_df : dataframe
        A weather data pandas dataframe with positional information.
    kml_file : str
        An output file to write the kml data to.

    """

    df_kml = weather_df.iloc[::10, :]

    kml_text = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
    <Style id="sn_ylw-pushpin">
        <LineStyle>
            <color>ffff0000</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>7f00ff00</color>
            <colorMode>random</colorMode>
        </PolyStyle>
    </Style>
    <StyleMap id="sn_ylw-pushpin0">
        <Pair>
            <key>normal</key>
            <styleUrl>#sn_ylw-pushpin1</styleUrl>
        </Pair>
        <Pair>
            <key>highlight</key>
            <styleUrl>#sn_ylw-pushpin</styleUrl>
        </Pair>
    </StyleMap>
    <Style id="sn_ylw-pushpin1">
        <LineStyle>
            <color>ffff0000</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>7f00ff00</color>
            <colorMode>random</colorMode>
        </PolyStyle>
    </Style>
    <Placemark>
        <name>AIMMS Trajectory</name>
        <description>Generated by weather_data_check.py</description>
        <styleUrl>#sn_ylw-pushpin0</styleUrl>
        <LineString>
            <tessellate>1</tessellate>
            <altitudeMode>absolute</altitudeMode>
            <coordinates>
'''
    # iterates through the subsampled dataframe and writes values to the kml coordinates
    for index, row in df_kml.iterrows():
        kml_text += '\t\t\t\t' + str(row['Long']) + ',' + str(row['Lat']) + ',' + str(row['Z']) + '\n'

    ## complete the kml footer
    kml_text += '''         </coordinates>
        </LineString>
    </Placemark>
</Document>
</kml>'''

    # create a kml file and dump the subsampled kml data to it
    with open(os.path.join(kml_file), 'w') as f:
        f.write(kml_text)