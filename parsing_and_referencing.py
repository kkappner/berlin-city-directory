# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 10:33:21 2021

Demonstration code for the Berlin city directory parsing and referencing process.
https://github.com/kkappner/berlin-city-directory

@author: kalle
"""

import os
import sys
import pandas as pd
import geopandas as gpd

path_wdir = os.getcwd()
path_data = os.path.join(path_wdir, 'referencing', 'data')
path_script = os.path.join(path_wdir, 'bcdextract')
path_training = os.path.join(path_script, 'training')
sys.path.append(path_script)         
from cd_datastructure import CDBook
from cd_entryparsing import Classifier
import cd_referencing

#Generate a city directory book instance
cdbook = CDBook()

#Parse PAGE XML files, iteratively adding them to the CDBook.
path_sample_book = os.path.join('bab_h_1880', 'results', '2021-11-26-13-33-50_xml', 'pages')
for filename in os.listdir(path_sample_book):
    infile_xml = os.path.join(path_sample_book, filename)
    cdbook.parse_from_pagexml(infile_xml)
   
#A CDBook is just a dataclass organizing the OCR output and allowing us to structure it.
cdbook
cdbook.pages[0].columns[0].lines[1]

#(Optionally) define a list of expected street names
street_list = ['Ackerſtraße', 'Adalbertſtraße', 'Adlerſtraße', 'Admiralſtraße', 'Adolfſtraße', 'Ahornſtraße', 'Albrechtſtraße', 'Alexanderſtraße', 'Kleine Alexanderſtraße', 'Alexander Ufer', 'Alexandrinenſtraße']
   
#Fine lines with street names, street numbers, and indention; consolidate.
for page in cdbook.pages:
    for col in page.columns:
        col.find_lines_with_street_names(inflate_std=3, street_list=street_list, difflib_cutoff=.75)
        col.find_lines_with_street_numbers()
        col.tag_indented_lines(inflate_std=.5, ignore_nonstd_lines=True)
        col.consolidate_indented_lines()

#We missed Albrechtſtraße; correct manually.
cdbook.list_streets()
cdbook.pages[6].columns[5].lines[30]
cdbook.pages[6].columns[5].lines[30].tag_as_street_name(street_list=street_list, difflib_cutoff=.5)
cdbook.pages[6].columns[5].lines[30].tag_as_street_name(name='Albrechtſtraße')

#Distribute street names and numbers to all other entries.
cdbook.distribute_addresses()
cdbook.pages[8].columns[2].list_entries()

#To parse the content within lines, we use an adjusted version of the "city-directory-entry-parser", written by Bert Spaan and Stephen Balogh
#See https://github.com/nypl-spacetime/city-directory-entry-parser
training_data_csv = os.path.join(path_training, 'training.csv')

#Create a classifier for entry parsing.
classifier = Classifier()
classifier.load_training(training_data_csv)
classifier.train()

#Parse all entries.
cdbook.parse_all_entries(classifier)

#Inspect a sample.
recognized_occupations = []
for line in cdbook.pages[8].columns[2].lines:
    occs = line.parsed_entry.categories['occupations']
    recognized_occupations.extend(occs)
recognized_occupations[:15]

#Convert occupations and addresses into a DataFrame
df = cdbook.occupations_to_dataframe(sanitize_strings=True)
df.fillna('', inplace=True)


#Geo-referencing
#Short-hand functions to map between unique addresses and the full set of addresses.
gatd = cd_referencing.generate_add_translation_dict
ratd = cd_referencing.read_from_add_translation_dict

#Get the list of addresses to geo-reference, and its subset of unique addresses
addresses = list(df['street'].fillna('') + ' ' + df['number'].fillna(''))
addresses_unique = list(dict.fromkeys(addresses))

#Fully-automatic geo-referencing via some geocoding API. 
xs, ys = cd_referencing.georef_automatic(addresses_unique, trail=', Berlin, Germany', verbose=True)
tdict = gatd(addresses_unique, xs, ys)
df[['x_1', 'y_1']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')

#Semi-automatic geo-referencing via a shapefile of street linestrings. 
#Note: We need to reproject the streets shapefile to WGS 84 (EPSG:4326).
path_streets = os.path.join(path_data, 'streets_1880.gpkg') #source file is in EPSG:3068 CRS, will be reprojected
xs, ys = cd_referencing.georef_semiautomatic(addresses_unique, path_streets, reproject=4326, verbose=True)
tdict = gatd(addresses_unique, xs, ys)
df[['x_2', 'y_2']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')

#Manual geo-referencing via a shapefile of lot polygons (alternatively, pass a points shapefile).
path_plots = os.path.join(path_data, 'lots_1880.gpkg')
xs, ys = cd_referencing.georef_manual(addresses_unique, path_plots, reproject=4326, polygons=True, verbose=True)   
tdict = gatd(addresses_unique, xs, ys)
df[['x_3', 'y_3']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')

#Status-referencing
#Short-hand functions to map between unique occupations and the full set of occupations.
gotd = cd_referencing.generate_occ_translation_dict
rotd = cd_referencing.read_from_occ_translation_dict

#Get the list of occupations to status-reference, and its subset of unique occupations
occupations = list(df['occupation'])
occupations_unique = list(dict.fromkeys(occupations))

#Fully-automatic status-referencing, searching for a close match within the current HISCO database.
#Note: We use a local csv table containing the scraped HISCO database; alternatively query the occupations online from the HISCO website using cd_referencing.statusref_online().
path_occs = os.path.join(path_data, 'occupations_hiscowebsite.csv')
unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.5, verbose=True)
#unique_hiscos = cd_referencing.statusref_online(occupations_unique, verbose=True)
tdict = gotd(occupations_unique, unique_hiscos)
df['hisco_1'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)

#Semi-automatic status-referencing, searching for a close match within the list of occupations published in the 1882 Prussian occupational census.
path_occs = os.path.join(path_data, 'occupations_census.csv')
unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.5, verbose=True)
tdict = gotd(occupations_unique, unique_hiscos)
df['hisco_2'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)

#Manual status-referencing, searching for a close match within a handcoded list of German occupations.
path_occs = os.path.join(path_data, 'occupations_handcoded.csv')
unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.5, verbose=True)
tdict = gotd(occupations_unique, unique_hiscos)
df['hisco_3'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)

#Map from HISCO to HISCAM.
path_hiscam = os.path.join(path_data, 'hiscam_u2.csv')
df_hiscam = pd.read_csv(path_hiscam, engine='python', sep=',')
dict_hiscam = pd.Series(df_hiscam['HISCAM'].values, index=df_hiscam['HISCO']).to_dict()
dict_hiscam = {str(key).zfill(5):val for key, val in dict_hiscam.items()}
def hiscos_to_hiscams(hiscos, dict_hiscam):
    hiscos = [str(hisco).replace('*', '') if hisco else hisco for hisco in hiscos] #HISCO website strings sometimes include a trailing asterisk.
    return [dict_hiscam.get(hisco) for hisco in hiscos]

for i in range(1,3+1):
    df[f'hiscam_{i}'] = hiscos_to_hiscams(df[f'hisco_{i}'], dict_hiscam)

df[['hiscam_1', 'hiscam_2', 'hiscam_3']]
df[['hiscam_1', 'hiscam_2', 'hiscam_3']].count()

#Match census tract IDs for the validation.
path_sbs = os.path.join(path_data, 'sb_1880.gpkg')
gdf_sbs = gpd.read_file(path_sbs).to_crs(epsg=4326)

for n in range(1,3+1):
    geometry=gpd.points_from_xy(df[f'x_{n}'], df[f'y_{n}'])
    gdf_points = gpd.GeoDataFrame(None, geometry=geometry)
    gdf_points.crs = 'EPSG:4326'
    gdf_points = gpd.sjoin(gdf_points, gdf_sbs, how='left', op='within')
    df[f'sb_{n}'] = gdf_points[~gdf_points.index.duplicated(keep='first')]['id']


#Export to Stata dta.
retain = ['hiscam_1', 'hiscam_2', 'hiscam_3', 'x_1', 'x_2', 'x_3', 'y_1', 'y_2', 'y_3', 'sb_1', 'sb_2', 'sb_3']
df[retain].to_stata(os.path.join(path_data, 'validation_ab.dta'))
