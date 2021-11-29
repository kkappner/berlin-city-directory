# Replication files and code for Albers and Kappner (2021)

This repository contains replication files and code for Albers and Kappner (2021). In this example, we show how to use the extraction work flow described in the paper to convert the first 10 pages of the [1880 Berlin city directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/) into a dataset of geo- and status-referenced household heads. We also provide a Stata file of the fully referenced [1880 directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/) and the Stata code processing it for our validation exercises.

List of directories and their content:
- *bab_h_1880*: [OCR4all](https://github.com/OCR4all/OCR4all) processing and result files for the first 10 pages of the [1880 Berlin city directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/).
- *bcdextract*: Various Python scripts used in the structuring and referencing process.
- *ocr_model*: Our trained [Calamari](https://github.com/Calamari-OCR/calamari) OCR model.
- *referencing*: Various files used in the geo- and status-referencing process.
- *validation*: Stata code and files used in our validation excercise.

Note: The Python script relies on some widely used libraries, such as [geopandas](https://geopandas.org/), [shapely](https://shapely.readthedocs.io/en/stable/manual.html), [geocoder](https://github.com/DenisCarriere/geocoder) etc. To run the validation Stata code, you will also need to set up [gpinter](https://github.com/thomasblanchet/gpinter) and make sure that your Stata version can run it via [rsource](http://fmwww.bc.edu/RePEc/bocode/r/rsource.html).

## OCR via OCR4all

We use [OCR4all](https://github.com/OCR4all/OCR4all) to recognize household head entries listed in the [1880 Berlin city directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/). To reduce the amount of recognition errors, we train Calamari's [*Fraktur 19th century*](https://github.com/Calamari-OCR/calamari_models/tree/master/fraktur_19th_century) model on the first 50 pages of the [1875 directory](https://digital.zlb.de/viewer/image/34115512_1875/1066/). You find the resulting OCR model in the *ocr_model* directory.

## OCR output parsing

Our script takes in a collection of [PAGE XML](https://www.primaresearch.org/schema/PAGE/gts/pagecontent/2019-07-15/Simple%20PAGE%20XML%20Example.pdf) files generated by [OCR4all](https://github.com/OCR4all/OCR4all) (or any other OCR environment). The *bab_h_1880* directory contains the OCR4all processing and result files for the first 10 pages from the [1880 Berlin city directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/). The *parsing_and_referencing.py* script contains the full code for this section.

```python
>>> import os
>>> from cd_datastructure import CDBook

#Generate a city directory book instance
>>> cdbook = CDBook()

#Parse PAGE XML files, iteratively adding them to the CDBook.
>>> infolder = os.path.join('bab_h_1880', 'results', '2021-11-26-13-33-50_xml', 'pages')
>>> for filename in os.listdir(infolder):
>>>     infile_xml = os.path.join(infolder, filename)
>>>     cdbook.parse_from_pagexml(infile_xml)
```

A CDBook is just a dataclass organizing the OCR output and allowing us to structure it.

```python
>>> cdbook
CDBook [10 pages, 60 columns, 5869 lines]
>>> cdbook.pages[0].columns[0].lines[1]
1. a. d. Linienſtr.
```

To structure the OCR'd text content, we identify lines that announce street names and street numbers, and tag and consolidate indented lines. These operations are performed at the column level because the underlying functions exploit statistics computed over all bounding boxes within a given column. By optionally passing a list of expected street names, e.g. from [here](https://digital.zlb.de/viewer/image/34115512_1880/1840/LOG_0148/), we help our algorithm to identify lines announcing street names more reliably.

```python
>>> street_list = ['Ackerſtraße', 'Adalbertſtraße', 'Adlerſtraße', 'Admiralſtraße', 'Adolfſtraße', 'Ahornſtraße', 
                   'Albrechtſtraße', 'Alexanderſtraße', 'Kleine Alexanderſtraße', 'Alexander Ufer', 'Alexandrinenſtraße']
               
>>> for page in cdbook.pages:
>>>    for col in page.columns:
>>>        col.find_lines_with_street_names(inflate_std=3, street_list=street_list, difflib_cutoff=.75)
>>>        col.find_lines_with_street_numbers()
>>>        col.tag_indented_lines(inflate_std=.5, ignore_nonstd_lines=True)
>>>        col.consolidate_indented_lines()

>>> cdbook.list_streets()
Page | Column | Line | Street
0      0        0      Ackerſtraße
3      2        9      Adalbertſtraße
5      4        19     Adlerſtraße
5      5        40     Admiralſtraße
6      4        50     Adolfſtraße
6      5        28     Ahornſtraße
7      2        28     Alexanderſtraße
9      0        8      Kleine Alexanderſtraße
9      3        54     Alexander Ufer
9      3        57     Alexandrinenſtraße
```

The algorithm did a reasonable job, though it failed to identify [Albrechtſtraße](https://digital.zlb.de/viewer/image/34115512_1880/1147/). If needed, this can be corrected manually, either by passing the desired string or by searching for a close match with a lower threshold.

```python
>>> cdbook.pages[6].columns[5].lines[30]
Albrechtſtr. (NW)
>>> cdbook.pages[6].columns[5].lines[30].tag_as_street_name(street_list=street_list, difflib_cutoff=.5)
>>> cdbook.pages[6].columns[5].lines[30].tag_as_street_name(name='Albrechtſtraße')
```

Next, we distribute the recognized street names and house numbers to all other lines. The following example output from [the third column of page 9](https://digital.zlb.de/viewer/image/34115512_1880/1149/) also illustrates that a couple of distinct lines were accidentally consolidated.

```python
>>> cdbook.distribute_addresses()
>>> cdbook.pages[8].columns[2].list_entries()
List of entries in column
0 Alexanderſtraße 38a  Silberberg & Co., Gebr., Fbrk. 
1 Alexanderſtraße 39  E. Dietert, Ww, Rent Caro, Kfm. Färber, Seifenſieder. Hirſch, Kfm. 
2 Alexanderſtraße 39  Jacob, Fbrk. Köttner, Kim. 
3 Alexanderſtraße 39  Landgraf, Kfm. 
4 Alexanderſtraße 39  Steinauer & Co., Strumpfwrn. Geſch. 
5 Alexanderſtraße 39  Wuttke, Ger. Aktuar a. D. 
6 Alexanderſtraße 40  E. Quarg, Reſtaur. Feuermeldeſtelle. 
...
```

To structure the content *within* each text line, we use an adapted version of the [city-directory-entry-parser](https://github.com/nypl-spacetime/city-directory-entry-parser). This is based ond a conditional random fields algorithm trained with customized ground truth data.

```python
>>> from cd_entryparsing import Classifier

>>> training_data_csv = os.path.join(path_training, 'training_ab1873_p4u25v2.csv')

#Create a classifier for entry parsing.
>>> classifier = Classifier()
>>> classifier.load_training(training_data_csv)
>>> classifier.train()

#Parse all entries.
>>> cdbook.parse_all_entries(classifier)
```

The algorithm parses line content into names, occupations, proprietory status indicators, absentee addresses and other information. For the example output above, all occupations are correctly detected, though some non-occupation tokens are wrongly labeled as occupations:

```python
>>> recognized_occupations = []
>>> for line in cdbook.pages[8].columns[2].lines:
>>>     occs = line.parsed_entry.categories['occupations']
>>>     recognized_occupations.extend(occs)
>>> recognized_occupations[:15]
['Co', 'Gebr .', 'Fbrk .', 'Ww', 'Rent', 'Kfm .', 'Seifenſieder .', 'Kfm .', 'Fbrk .', 'Kim .', 'Kfm .', 'Co', 'Strumpfwrn . Geſch .', 'Ger. Aktuar a. D.', 'Reſtaur . Feuermeldeſtelle .']
```
To prepare the structured data, we convert it into a DataFrame, dropping all non-address and non-occupation information, and sanitizing the strings.

```python
>>> df = cdbook.occupations_to_dataframe(sanitize_strings=True)
>>> df
                  street number        occupation
0            Ackerſtraße                         
1            Ackerſtraße      1         Poſtbeamt
2            Ackerſtraße      1               Kfm
3            Ackerſtraße      1         Schneider
4            Ackerſtraße      1               Kfm
                 ...    ...               ...
5232  Alexandrinenſtraße    18a                Ww
5233  Alexandrinenſtraße    18a       Schneiderin
5234  Alexandrinenſtraße     19  Baugeſell⸗ſchaft
5235  Alexandrinenſtraße     19         Stadtſerg
5236  Alexandrinenſtraße     19         Schloſſer

[5237 rows x 3 columns]
```

## Geo- and status-referencing

The DataFrame produced above contains city directory entries with occupations and addresses. Next, we want to reference these entries in the [HISCO](https://iisg.amsterdam/en/data/data-websites/history-of-work) occupational classification scheme and translate address strings into latitude-longitude coordinates. The various files used in the geo- and status-referencing process are available in the *referencing* directory. The *parsing_and_referencing.py* script contains the full code for this section.

```python
>>> import cd_referencing

#To economize, we only reference unique addresses and occupations.
>>> addresses = list(df['street'].fillna('') + ' ' + df['number'].fillna(''))
>>> addresses_unique = list(dict.fromkeys(addresses))
>>> occupations = list(df['occupation'])
>>> occupations_unique = list(dict.fromkeys(occupations))

>>> len(addresses)
5237
>>> len(addresses_unique)
448

#Later, we use a couple of functions to map the coordinates and HISCO codes of unique addresses and occupations back the full set of observations.
>>> gatd = cd_referencing.generate_add_translation_dict
>>> ratd = cd_referencing.read_from_add_translation_dict
>>> gotd = cd_referencing.generate_occ_translation_dict
>>> rotd = cd_referencing.read_from_occ_translation_dict
```

Our three geo-referencing approaches:

```python
#Fully-automatic geo-referencing via some geocoding API. 
>>> xs, ys = cd_referencing.georef_automatic(addresses_unique, trail=', Berlin, Germany')
>>> tdict = gatd(addresses_unique, xs, ys)
>>> df[['x_1', 'y_1']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')

#Semi-automatic geo-referencing via a shapefile of street linestrings. 
#Note: We need to reproject the streets shapefile to WGS 84 (EPSG:4326).
>>> path_streets = os.path.join('referencing', 'streets_1880.shp')
>>> xs, ys = cd_referencing.georef_semiautomatic(addresses_unique, path_streets, reproject=4326)
>>> tdict = gatd(addresses_unique, xs, ys)
>>> df[['x_2', 'y_2']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')

#Manual geo-referencing via a shapefile of lot polygons (alternatively, pass a points shapefile).
>>> path_plots = os.path.join('referencing', 'lots_1880.gpkg')
>>> xs, ys = cd_referencing.georef_manual(addresses_unique, path_plots, reproject=4326, polygons=True)   
>>> tdict = gatd(addresses_unique, xs, ys)
>>> df[['x_3', 'y_3']] = df.apply(lambda x: ratd(f"{x['street']} {x['number']}", tdict), axis=1, result_type='expand')
```

Our three status-referencing approaches:

```python
#Fully-automatic status-referencing, searching for a close match within the current HISCO database.
#Note: We use a local csv table containing the scraped HISCO database; alternatively query the occupations online from the HISCO website using cd_referencing.statusref_online().
>>> path_occs = os.path.join('referencing', 'occupations_hiscowebsite.csv')
>>> unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.75, verbose=True)
>>> tdict = gotd(occupations_unique, unique_hiscos)
>>> df['hisco_1'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)

#Semi-automatic status-referencing, searching for a close match within the list of occupations published in the 1882 Prussian occupational census.
>>> path_occs = os.path.join('referencing', 'occupations_census.csv')
>>> unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.75, verbose=True)
>>> tdict = gotd(occupations_unique, unique_hiscos)
>>> df['hisco_2'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)

#Manual status-referencing, searching for a close match within a handcoded list of German occupations.
>>> path_occs = os.path.join('referencing', 'occupations_handcoded.csv')
>>> unique_hiscos = cd_referencing.statusref_offline(occupations_unique, path_occs, difflib_cutoff=.75, verbose=True)
>>> tdict = gotd(occupations_unique, unique_hiscos)
>>> df['hisco_3'] = df.apply(lambda x: rotd(x['occupation'], tdict), axis=1)
```

We still need to translate [HISCO](https://iisg.amsterdam/en/data/data-websites/history-of-work) codes to [HISCAM](http://www.hisma.org/HISMA/HISCAM.html) social status scale values.

```python
>>> path_hiscam = os.path.join('referencing', 'hiscam_u2.csv')
>>> df_hiscam = pd.read_csv(path_hiscam, engine='python', sep=',')
>>> dict_hiscam = pd.Series(df_hiscam['HISCAM'].values, index=df_hiscam['HISCO']).to_dict()
>>> dict_hiscam = {str(key).zfill(5):val for key, val in dict_hiscam.items()}
>>> def hiscos_to_hiscams(hiscos, dict_hiscam):
>>>    hiscos = [str(hisco).replace('*', '') if hisco else hisco for hisco in hiscos] #HISCO website strings sometimes include a trailing asterisk.
>>>    return [dict_hiscam.get(hisco) for hisco in hiscos]

>>> for i in range(1,4):
>>>     df[f'hiscam_{i}'] = hiscos_to_hiscams(df[f'hisco_{i}'], dict_hiscam)

>>> df[['hiscam_1', 'hiscam_2', 'hiscam_3']]
       hiscam_1  hiscam_2   hiscam_3
0           NaN       NaN        NaN
1     65.779999       NaN        NaN
2           NaN       NaN        NaN
3     50.820000     50.82  50.820000
4           NaN       NaN        NaN
        ...       ...        ...
5232        NaN       NaN        NaN
5233  50.820000     50.82  50.820000
5234        NaN       NaN  88.220001
5235        NaN       NaN        NaN
5236  56.930000       NaN        NaN

[5237 rows x 3 columns]
```

## Validation (Stata code)

The *validation/scripts* directory contains Stata code and files to reproduce the figures and estimates in our paper based on the fully referenced [1880 Berlin city directory](https://digital.zlb.de/viewer/image/34115512_1880/1141/).
