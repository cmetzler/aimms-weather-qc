from os.path import basename
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors
import cartopy.io.img_tiles as cimgt
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter


def plot_windspeed_errors(aimms_df, output_file):
    """ Plot the windspeed and potential wind speed errors. Overlays the plot on a basemap for spatial context.

    Required Parameters
    ----------
    aimms_df : dataframe
        The aimms probe data in a pandas dataframe
    output_file : str
        The output plot file.

    """
    # plot positions
    sbet_df = aimms_df.iloc[::5, :]  # thin data a bit
    #sbet_df = aimms_df
    #sbet_df.loc[:, "Lat"] = sbet_df.Long.map(np.degrees)
    #sbet_df.loc[:, "Long"] = sbet_df.Lat.map(np.degrees)
    x_min = round(sbet_df["Long"].min(), 3)
    x_max = round(sbet_df["Long"].max(), 3)
    y_min = round(sbet_df["Lat"].min(), 3)
    y_max = round(sbet_df["Lat"].max(), 3)
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_border = x_range * 0.2
    y_border = y_range * 0.2
    x_min = round(x_min - x_border / 2, 3)
    x_max = round(x_max + x_border / 2, 3)
    y_min = round(y_min - y_border / 2, 3)
    y_max = round(y_max + y_border / 2, 3)
    print(f"Trajectory plot boundaries: {x_min}, {x_max}, {y_min}, {y_max}")

    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())

    # plot basemap
    # imagery = OSM()
    stamen_terrain = cimgt.Stamen(style="terrain")

    # estimate an appropriate scale
    scale = np.ceil(-np.sqrt(2) * np.log(np.divide((x_max - x_min) / 2.0, 350.0))) + 1
    scale = (scale < 20) and scale or 19  # scale cannot be larger than 19
    # logger.info(f"Set map scale to {scale}.")

    ax.add_image(stamen_terrain, int(scale))
    # ax.add_image(imagery, int(scale))

    # format the plot area
    ax.set_extent((x_min, x_max, y_min, y_max), crs=ccrs.PlateCarree())
    ax.set_xticks(np.linspace(x_min, x_max, 7), minor=False)  # set longitude indicators
    ax.set_yticks(np.linspace(y_min, y_max, 7)[1:], minor=False)  # set latitude indicators
    lon_formatter = LongitudeFormatter(number_format='0.3f', degree_symbol='',
                                       dateline_direction_label=True)  # format lons
    lat_formatter = LatitudeFormatter(number_format='0.3f', degree_symbol='')  # format lats
    ax.xaxis.set_major_formatter(lon_formatter)  # set lons
    ax.yaxis.set_major_formatter(lat_formatter)  # set lats
    ax.xaxis.set_tick_params(labelsize=7)
    ax.yaxis.set_tick_params(labelsize=7)
    # gl = ax.gridlines(draw_labels=True, dms=False, x_inline=False, y_inline=False)
    # gl.xlabel_style = {"size": 5, "color": "black"}
    # gl.ylabel_style = {"size": 5, "color": "black"}

    # setup the color map
    cmap = matplotlib.colors.ListedColormap(['blue', 'cyan', 'red'])
    boundaries = [0, 1, 27, 999]
    norm = matplotlib.colors.BoundaryNorm(boundaries, cmap.N, clip=True)

    # plot the trajectory coordinates
    sbet_df.plot.scatter(x="Long", y="Lat", c='Computed_WS',  s=0.5, colormap=cmap, norm=norm, ax=ax, figsize=(15, 10))
    # plt.show()
    # save and close
    plt.title(f"Windspeed Errors for {basename(output_file)}", fontsize=10)
    plt.savefig(output_file,
                bbox_inches="tight", format="png", dpi=900)
    plt.close(fig)