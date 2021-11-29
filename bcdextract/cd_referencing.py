# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 12:41:29 2021

@author: kalle
"""

def georef_automatic(addresses: list, lead: str = '', trail: str = '', verbose=False):
    """
    Converts a list of address strings into x, y coordinates via ArcGIS's geocoding API. 
    Returns two lists of x and y coordinates.
    """     
    import geocoder
    xs, ys =[], []
    
    def _geocode_address_(addstring):
        g = geocoder.arcgis(addstring)
        return g.x, g.y    
    
    N = len(addresses)
    for n, address in enumerate(addresses):
        if isinstance(address, str):
            x, y = _geocode_address_(f'{lead}{address}{trail}')
        else:
            x, y = None
        xs.append(x)
        ys.append(y)
        if verbose:
            if x and y: status = 'success'
            else: status = 'failure'
            print('Geocoded {address}: {status} ({n} / {N})'.format(address=address, n=n+1, N=N, status=status))
    
    return xs, ys

def georef_semiautomatic(addresses, path_streets, reproject=False, verbose=False):
    """
    Geo-referencing via interpolated addresses along street lines.
    Expects a certain format for the passed streets shapefile.
    """
    import geopandas as gpd
    import numpy as np
    import difflib
    gdf_streets = gpd.read_file(path_streets)
    for field in ('num_1', 'num_2', 'num_3', 'num_4'):
        gdf_streets[field].replace('.', None, inplace=True)
    if reproject:
        gdf_streets = gdf_streets.to_crs(epsg=reproject)
    
    def _generate_addresspoints_(row):
        """
        Generates the interpolated array of points for a street; returns a dictionary including the given start and end numbers
        """
        linestring = row['geometry']
        dict_points = {} #initialize empty points dictionary
        num_1 = row['num_1']
        num_2 = row['num_2']
        num_3 = row['num_3']
        num_4 = row['num_4']
        street = row['name']
        
        #return empty points dictionary if no linestring geometry is provided
        if not linestring:
            return dict_points
        
        #populate the points dictionary sequentially
        for numpair in ([num_1, num_2], [num_3, num_4]):
            a, b = numpair
            if a and b:
                nums = [int(a), int(b)]
                n_smaller, n_larger = np.min(nums), np.max(nums) #identify smaller and larger of the nums
                n_points = n_larger - n_smaller - 1 #find amount of integer house numbers to interpolate
                geos_points = [linestring.interpolate(i/float(n_points), normalized=True) for i in range(n_points)] #get the interpolated points
                temp_dict_points = {f'{street} {key}' : val for key, val in zip(range(n_smaller + 1, n_larger), geos_points)} #store in a dictionary
                dict_points = {**dict_points, **temp_dict_points}
                if linestring.boundary: #if passed geometry has a boundary, take the boundary (i.e. start and end) coordinates
                    dict_points[f'{street} {a}'] = linestring.boundary[0]
                    dict_points[f'{street} {b}'] = linestring.boundary[1]
                else: #if passed geometry has no boundary, just take the centroid coordinates
                    dict_points[f'{street} {a}'] = linestring.centroid
                    dict_points[f'{street} {b}'] = linestring.centroid
            
        return dict_points

    #attach a dictionary of interpolated point positions to each street in the shapefile
    gdf_streets['dict_points'] = gdf_streets.apply(lambda x : _generate_addresspoints_(x), axis=1)

    #construct a dictionary containing every point address
    matchlist = gdf_streets[['dict_points']].to_dict(orient='records')
    matchdict = {}
    for street in matchlist:
        tempdict = street['dict_points']
        matchdict = {**matchdict, **tempdict}
    matchkeys = list(matchdict.keys())
    matchvals = list(matchdict.values())
        
    #find the x, y coords from best guess matches against the interpolated addresses
    xs, ys = [], []
    
    def _geocode_address_(addstring, matchkeys, matchvals):
        matcheslist = difflib.get_close_matches(addstring, matchkeys, n=1, cutoff=0.5)
        if matcheslist: 
            match = matcheslist[0]
            idx = matchkeys.index(match)
            x, y = matchvals[idx].x, matchvals[idx].y
        else: x, y = None, None
        return x, y
        
    N = len(addresses)
    for n, address in enumerate(addresses):
        if isinstance(address, str):
            x, y = _geocode_address_(address, matchkeys, matchvals)
        else:
            x, y = None
        xs.append(x)
        ys.append(y)
        if verbose:
            if x and y: status = 'success'
            else: status = 'failure'
            print('Geocoded {address}: {status} ({n} / {N})'.format(address=address, n=n+1, N=N, status=status))
    
    return xs, ys

def georef_manual(addresses, path_plots, reproject=False, polygons=False, verbose=False):
    """
    Takes in a shapefile, matches passed adresses against best guess in polygon shapefile, retrieves point coords;
    Return lists of x and y coords
    This code basically replicates the preceeding function
    """
    import geopandas as gpd
    import difflib
    gdf_plots = gpd.read_file(path_plots)
    if reproject:
        gdf_plots = gdf_plots.to_crs(epsg=reproject)
    if polygons:
        gdf_plots['geometry'] = gdf_plots['geometry'].centroid
    
    matchlist = gdf_plots[['adress1', 'geometry']].rename(columns={'adress1':'adress'}).to_dict(orient='records') + gdf_plots[['adress2', 'geometry']].rename(columns={'adress2':'adress'}).to_dict(orient='records') + gdf_plots[['adress3', 'geometry']].rename(columns={'adress3':'adress'}).to_dict(orient='records')
    
    matchdict = {adress['adress'] : adress['geometry'] for adress in matchlist if adress['adress'] and adress['geometry']}
    matchkeys = list(matchdict.keys())
    matchvals = list(matchdict.values())

    #find the x, y coords from best guess matches against the interpolated addresses
    xs, ys = [], []
    
    def _geocode_address_(addstring, matchkeys, matchvals):
        matcheslist = difflib.get_close_matches(addstring, matchkeys, n=1, cutoff=0.5)
        if matcheslist: 
            match = matcheslist[0]
            idx = matchkeys.index(match)
            x, y = matchvals[idx].x, matchvals[idx].y
        else: x, y = None, None
        return x, y
        
    N = len(addresses)
    for n, address in enumerate(addresses):
        if isinstance(address, str):
            x, y = _geocode_address_(address, matchkeys, matchvals)
        else:
            x, y = None
        xs.append(x)
        ys.append(y)
        if verbose:
            if x and y: status = 'success'
            else: status = 'failure'
            print('Geocoded {address}: {status} ({n} / {N})'.format(address=address, n=n+1, N=N, status=status))
    
    return xs, ys

def statusref_offline(occupations, path_reference, difflib_cutoff=1, verbose=False):
    import pandas as pd
    import difflib
    
    df_reference = pd.read_csv(path_reference, dtype={'hisco':'object'})
    matchkeys = list(df_reference['occupation'])
    matchvals =list(df_reference['hisco'])

    #find the occs from best guess matches against the supplied list
    hiscos = []
    
    def _match_hisco_(occstring, matchkeys, matchvals):
        """Function retrieves the closest match"""
        matcheslist = difflib.get_close_matches(occstring, matchkeys, n=1, cutoff=difflib_cutoff)
        if matcheslist: 
            match = matcheslist[0]
            idx = matchkeys.index(match)
            hisco = matchvals[idx]
        else: hisco = None
        return hisco
        
    N = len(occupations)
    for n, occupation in enumerate(occupations):
        if isinstance(occupation, str):
            hisco = _match_hisco_(occupation, matchkeys, matchvals)
        else:
            hisco = None
        hiscos.append(hisco)
        if verbose:
            if hisco: status = 'success'
            else: status = 'failure'
            print('Statusreferenced {occupation}: {status} ({n} / {N})'.format(occupation=occupation, n=n+1, N=N, status=status))

    return hiscos

def statusref_online(occupations, verbose=False):
    """
    Status-referencing via the HISCO website.
    """

    import requests
    from bs4 import BeautifulSoup
    import re
    #need to transform a couple of characters for the query
    for pair in (['ü', '%fc'], ['ö', '%f6'], ['ä', '%e4'], ['ß', '%df'], [' ', '%20']):
        occupations = [el.replace(pair[0], pair[1]) for el in occupations]

    hiscos = []
    
    def _lookup_hisco_(occupation):
        url = 'https://historyofwork.iisg.nl/list_hiswi.php?ftsearch={occ}&modus=search&show_all=Y'.format(occ=occupation)
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "lxml")
        list_soup = soup.find_all('td', valign='top')
        list_soup_str = str(list_soup)
        list_soup_str_split = re.split('<|>', list_soup_str)
        hisco_codes = [tag for tag in list_soup_str_split if tag.isdigit() and len(tag) == 5] #Find all listed HISCO codes
        #If at least one HISCO code is found, take the most common HISCO code
        if hisco_codes:
            most_common = max(set(hisco_codes), key=hisco_codes.count) #find most common HISCO code; could be refined by accepting splits
            return most_common
        else:
        #If no HISCO code is found, return None
            return None

    N = len(occupations)
    for n, occupation in enumerate(occupations):
        if isinstance(occupation, str):
            hisco = _lookup_hisco_(occupation)
        else:
            hisco = None
        hiscos.append(hisco)
        if verbose:
            if hisco: status = 'success'
            else: status = 'failure'
            print('Statusreferenced {occupation}: {status} ({n} / {N})'.format(occupation=occupation, n=n+1, N=N, status=status))
    
    return hiscos

def generate_add_translation_dict(addresses, xs, ys):    
    translation_dict = {key : [x, y] for key, x, y in zip(addresses, xs, ys)}
    return translation_dict

def read_from_add_translation_dict(address, tdict):
    """map an original address to x, y coords using the dictionary of unique addresses"""
    x, y = tdict[address]
    return x, y

def generate_occ_translation_dict(occupations, hiscos):    
    translation_dict = {key : hisco for key, hisco in zip(occupations, hiscos)}
    return translation_dict

def read_from_occ_translation_dict(occupation, tdict):
    """map an original occupation to HISCO code using the dictionary of unique occupations"""
    hisco = tdict[occupation]
    return hisco