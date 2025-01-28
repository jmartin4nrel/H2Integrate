"""
Plots prices of products generated from GreenHEART using ArcGIS
"""

import os
import numpy as np
import pandas as pd
import arcgis
import json
import pickle
import requests
import matplotlib.pyplot as plt

from arcgis.gis import GIS
from arcgis.geometry import Point, MultiPoint
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from pathlib import Path
from ipywidgets import *
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from greenheart.tools.keys import set_arcgis_key_dot_env
from hopp.tools.resource.resource_tools import get_country

# Set API key using .env file
set_arcgis_key_dot_env()
ARCGIS_API_KEY = os.getenv("ARCGIS_API_KEY")

# Compile prices
def compile_prices(folder, price_type:str = 'lcoh'):

    lats = []
    lons = []
    prices = []

    # Read price in differently depending on how it is stored
    if price_type == 'lcoe':
        folder = str(folder)+"_pre_iron/lcoe"
        label = 'Levelized\nCost of\nElectricity\n[$/kWh]'
        def read_price(price_struct): price = price_struct; return price
    if price_type == 'lcoh':
        folder = str(folder)+"_pre_iron/lcoh"
        label = 'Levelized\nCost of\nHydrogen\n[$/kg]'
        def read_price(price_struct): price = price_struct; return price
    elif price_type == 'lco_ore':
        folder = str(folder)+"_iron_out/iron_ore_finance"
        label = 'Levelized\nCost of\nIron Ore\nPellets\n[$/tonne]'
        def read_price(price_struct): price = price_struct.sol['price']; return price
    elif price_type == 'lcoi':
        folder = str(folder)+"_iron_out/iron_finance"
        label = 'Levelized\nCost of\nIron\n[$/tonne]'
        def read_price(price_struct): price = price_struct.sol['price']; return price
    else:
        NotImplementedError('Price type "{}" has not been implemented'.format(price_type))
    
    fns = os.listdir(folder)
    
    for fn in fns:
    
        # Get lat and lon from filename
        uscore1idx = fn.index('_')
        lat = np.float64(fn[:uscore1idx])
        uscore2idx = fn[(uscore1idx+1):].index('_') + uscore1idx+1
        lon = np.float64(fn[(uscore1idx+1):uscore2idx])

        # Read prices and append to array
        if uscore2idx > 0:
            reader = open(folder+'/'+fn,"rb")
            price_struct = pickle.load(reader)
            price = read_price(price_struct)
            lats.append(lat)
            lons.append(lon)

            prices.append(price)

    return lats, lons, prices, label


# Arrange prices into spatial data frame
def arrange_sdf(output_path, price_type):

    lats, lons, prices, label = compile_prices(output_path, price_type)
    geodata = requests.get(
        "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson").json()
    lats = np.array(lats,ndmin=2)
    lons = np.array(lons,ndmin=2)
    price_array = np.array(prices,ndmin=2)

    # Make lists of lats, lons, and data
    lat_list = []
    lon_list = []
    price_list = []
    shape_list = []
    x, y = np.shape(lats)
    for i in range(x):
        for j in range(y):
            # Filter out non-usa points
            country = get_country(lats[i,j], lons[i,j], geodata)
            if (country == 'United States of America'):
                lat_list.append(lats[i,j])
                lon_list.append(lons[i,j])
                price_list.append(price_array[i,j])
                if j == 0:
                    shape_list.append('s')
                else:
                    shape_list.append('o')

    # Rearrange to 1-D spatial dataframe
    coord_df = pd.DataFrame({'lat':lat_list, 'lon':lon_list})
    coord_df['price'] = price_list
    coord_sdf = pd.DataFrame.spatial.from_xy(coord_df,'lon','lat')

    return coord_sdf, label

# Mercator x/y conversion from gis.stackexchange.com/questions/156035
def merc_x(lon):
  r_major=6378137.000
  x = r_major*(lon*np.pi/180)
  return x
def merc_y(lat):
  if lat>89.5:lat=89.5
  if lat<-89.5:lat=-89.5
  r_major=6378137.000
  r_minor=6356752.3142
  temp=r_minor/r_major
  eccent=(1-temp**2)**.5
  phi=(lat*np.pi/180)
  sinphi=np.sin(phi)
  con=eccent*sinphi
  com=eccent/2
  con=((1.0-con)/(1.0+con))**com
  ts=np.tan((np.pi/2-phi)/2)/con
  y=0-r_major*np.log(ts)
  return y

# Create map
def price_map(coord_sdfs, map_prefs: dict = {'latlon_lims': [42,50,-98,-82],
                                            'save_to_web': False,
                                            'url': '',
                                            'username':'',
                                            'pwd':'',
                                            'zoomlevel':7,
                                            'center':[46,-90],
                                            'colorbar_pos':(.5,.5,1,1),
                                            'colorbar_size':[.03,.50],
                                            'colorbar_label_pos':[],
                                            'colormap':'turbo',
                                            'marker_size':5,
                                            'dpi':100,
                                            'inches_per_deg':1,
                                            'price_types':['lcoe'],
                                            'snippet':'',
                                            'tags':'',
                                            'labels':[],
                                            'skip_webcall':False,
                                            'output_path':''}): 
    
    [lat_min,lat_max,lon_min,lon_max] = map_prefs['latlon_lims']

    # Determine map size
    min_x = merc_x(lon_min)
    max_x = merc_x(lon_max)
    min_y = merc_y(lat_min)
    max_y = merc_y(lat_max)
   
    pix_width = map_prefs['inches_per_deg']*(lon_max-lon_min)*map_prefs['dpi']
    vert_dist = (1/np.cos(np.pi*lat_min/180)+1/np.cos(np.pi*lat_max/180))/2
    pix_height = map_prefs['inches_per_deg']*(lat_max-lat_min)*map_prefs['dpi']*vert_dist
        
    
    # Create map and set up display
    if not map_prefs['skip_webcall']:
        gis = GIS()
        if map_prefs['save_to_web']:
            gis = GIS(url=map_prefs['url'],
                        username=map_prefs['username'],
                        password=map_prefs['pwd'])
        map = gis.map("USA", zoomlevel=map_prefs['zoomlevel'])
        map.center = map_prefs['center']
        
        # 3587 is the wkid for Web Mercator projection
        map.extent = {'spatialReference':{'wkid':3857},
                                            'xmin':min_x,
                                            'ymin':min_y,
                                            'xmax':max_x,
                                            'ymax':max_y}
        
        # # Set up point renderer with color mapping
        # rend = arcgis.mapping.renderer.generate_classbreaks(coord_sdf,
        #                                                     'Point',
        #                                                     colors=colormap,
        #                                                     field='price',
        #                                                     class_count=255, 
        #                                                     marker_size=map_prefs['marker_size'],
        #                                                     line_width=1,
        #                                                     outline_color=[0,0,0,255])
        # max_vals = [np.min(coord_sdf['price'].values)]
        # max_vals.extend([i['classMaxValue'] for i in rend['classBreakInfos']])
        # colors = [i['symbol']['color'] for i in rend['classBreakInfos']]

        # # Plot the colored points
        # coord_sdf.spatial.plot(map,renderer=rend)
        map
        if map_prefs['save_to_web']:
            map.save({'title':map_prefs['price_types'][0],
                    'snippet':map_prefs['snippet'],
                    'tags':map_prefs['tags'],
                    'extent':{'spatialReference':{'wkid':3857},
                                    'xmin':min_x,
                                    'ymin':min_y,
                                    'xmax':max_x,
                                    'ymax':max_y}})
            
    # Download rendered map from ArcGIS
    fn = 'web_map.png'
    map_path = map_prefs['output_path']
    if not map_prefs['skip_webcall']:
        map_url = map.webmap.print('PNG32',dpi=map_prefs['dpi'],
                                extent={'spatialReference':{'wkid':3857},
                                        'xmin':min_x,
                                        'ymin':min_y,
                                        'xmax':max_x,
                                        'ymax':max_y},
                                    output_dimensions=(pix_width,pix_height))
        with requests.get(map_url) as resp:
            with open(map_path+'/'+fn, 'wb') as file_handle:
                file_handle.write(resp.content)
    
    dpi = map_prefs['dpi']

    fig = plt.gcf()
    
    image = plt.imread(map_path+'/'+fn)
    
    fig.set_figwidth(pix_width/dpi)
    fig.set_figheight(pix_height/dpi)

    plt.imshow(image, extent=[0, pix_width, pix_height, 0])
    plt.xticks([])
    plt.yticks([])
    plt.rcParams['font.size'] = 48
    plt.rcParams['xtick.major.size'] = 10

    ax = plt.gca()

    markers = ['o','s']

    # Associate colors with colormap
    for price_idx, price_type in enumerate(map_prefs['price_types']):
        coord_sdf = coord_sdfs[price_idx]
        prices = coord_sdf.loc[:,'price'].values
        max_vals = np.linspace(min(prices),max(prices),256)
        im = plt.imshow(np.reshape(max_vals,(16,16)))
        im.set_visible(False)
        im.set_cmap(map_prefs['colormap'][price_idx])
        price_colors = []
        for price in prices:
            price_dists = np.abs(price-max_vals)
            color_idx = np.argmin(price_dists)
            price_colors.append(im.cmap.colors[color_idx])

        for row_idx in range(coord_sdf.shape[0]):
            row = coord_sdf.iloc[row_idx,:]
        
            lon = row['lon']
            lat = row['lat']
            map_x = (lon-lon_min)/(lon_max-lon_min)
            map_y = (lat_max-lat)/(lat_max-lat_min)
            ax.plot(map_x*pix_width,map_y*pix_height,markers[price_idx],
                    color=price_colors[row_idx],markeredgecolor='k')
        
        cbaxes = inset_axes(ax,
                            width='{:.2f}%'.format(map_prefs['colorbar_size'][price_idx][0]*100),
                            height='{:.2f}%'.format(map_prefs['colorbar_size'][price_idx][1]*100),
                            loc='lower left',
                            bbox_to_anchor=map_prefs['colorbar_pos'][price_idx],  # position of the colorbar
                            bbox_transform=ax.transAxes,  # coordinate system for the colorbar
                            borderpad=0,  # padding around the colorbar
                            )
        plt.colorbar(im, cax=cbaxes, ticklocation='left')
        cbaxes.tick_params(direction='inout',labelsize=8)
        label_pos = map_prefs['colorbar_label_pos'][price_idx]
        ax.text(pix_width*label_pos[0],pix_height*(1-label_pos[1]),map_prefs['labels'][price_idx],
                horizontalalignment='center',
                verticalalignment='center',fontsize=8)

    plt.show()