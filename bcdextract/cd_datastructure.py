# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 10:40:22 2021

@author: kalle
"""

from enum import Enum, auto
import csv
import numpy as np
from shapely.geometry import Polygon, Point
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import re
from cd_entryparsing import LabeledEntry

class LineType(Enum):
    ENTRY = auto()
    INDENTED_ENTRY = auto()
    ENTRY_WITH_STREETNUMBER = auto()
    STREETNAME = auto()

@dataclass
class CDLine():
    content: str = ''
    coordsstring: str = ''
    bbox: Polygon = Polygon()
    number: str = ''
    street: str = ''
    linetype: LineType = LineType.ENTRY
    parsed_entry: LabeledEntry = LabeledEntry()
    
    def convert_coordstring_to_bbox(self):
        pts = self.coordsstring.split(' ')
        xcoords = [int(pt.split(',')[0]) for pt in pts]
        ycoords = [int(pt.split(',')[1]) for pt in pts]
        self.bbox = Polygon(zip(xcoords, ycoords))
        
    def compute_minrotatedbbox_sides(self): 
        """returns a width and length measure for a bounding box"""
        #https://gis.stackexchange.com/a/359025
        rotbox = self.bbox.minimum_rotated_rectangle
        x, y = rotbox.exterior.coords.xy
        edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
        width = min(edge_length)
        length = max(edge_length)
        return width, length
    
    def extract_leading_streetnum(self):
        """extracts leading street number fronm string, including standard number delimiters, and directly attached characters"""
        extracted_num = ''
        lastchar = ''
        for char in self.content:
            if char.isdigit() or (char in (' ', '.', ',', ';', '—', '-')) or (char.isalpha() and lastchar.isdigit()):
                extracted_num = extracted_num + char
                lastchar = extracted_num[-1]
            else:
                break
        if any(i.isdigit() for i in extracted_num): #if at least one number was extracted, take the extracted string out of the content and return it
            return extracted_num
    
    def identify_street_name(self, criterium, difflib_cutoff=.75, street_list=None):
        """automatically tags streetname lines"""
        if street_list: import difflib
        extracted_name = ''
        if self.compute_minrotatedbbox_sides()[0] > criterium: #large bounding box is prerequisite of street name
            extracted_name = self.content
            if street_list: #if a streetlist to match with is provided, find a match. If non is found, reset street name to ''.
                matches = difflib.get_close_matches(extracted_name, street_list, n=1, cutoff=difflib_cutoff)
                if matches:
                    extracted_name = matches[0]
                else:
                    extracted_name = ''        
        return extracted_name
    
    def tag_as_street_name(self, name=None, difflib_cutoff=.75, street_list=None):
        """manually tags streetname lines"""
        if street_list: import difflib
        if name: extracted_name = name
        else: extracted_name = self.content
        if street_list:
            matches = difflib.get_close_matches(extracted_name, street_list, n=1, cutoff=difflib_cutoff)
            if matches:
                extracted_name = matches[0]
        self.street = extracted_name
        self.linetype = LineType.STREETNAME
    
    def parse_entry(self, classifier):
        entry = LabeledEntry(self.content)
        classifier.label(entry)
        self.parsed_entry = entry
        
    def __repr__(self):
        return self.content
    
@dataclass
class CDColumn():
    lines: list[CDLine] = field(default_factory=list)
    
    def tag_indented_lines(self, inflate_std=1, ignore_nonstd_lines=False):        
        if ignore_nonstd_lines:
            list_of_lines = [line for line in self.lines if line.linetype.name not in ('ENTRY_WITH_STREETNUMBER', 'STREETNAME')]
        else:
            list_of_lines = self.lines
        leftbounds = [line.bbox.bounds[0] for line in list_of_lines]
        
        #leftboundsx, leftboundsy = zip(*[(line.bbox.bounds[0], line.bbox.bounds[1]) for line in list_of_lines])
        #b, cons = np.polyfit(leftboundsx, leftboundsy, 1)
        #leftboundsx_normalized = [(1 / b) * (leftbound - cons) for leftbound in leftboundsx]
        #leftbound_std = np.std(leftboundsx_normalized)
        #leftboundsx, leftboundsy = zip(*[(line.bbox.bounds[0], line.bbox.bounds[1]) for line in list_of_lines])
        #b, cons = np.polyfit(leftboundsx, leftboundsy, 1)
        #b2, b1, cons = np.polyfit(leftboundsx, leftboundsy, 2)
        
        leftbound_med = np.median(leftbounds)
        leftbound_std = np.std(leftbounds)
        #[print(idx, line.content) for (idx, line) in enumerate(col.lines) if line.bbox.bounds[0] > (1 / b) * (line.bbox.bounds[1] - cons) + 15]
        criterium = leftbound_med + leftbound_std * inflate_std
            
        for line in list_of_lines:
            if line.linetype.name in ('ENTRY', 'ENTRY_WITH_STREETNUMBER'): #find indentions for ENTRY lines
                #if line.bbox.bounds[0] > (1 / b) * (line.bbox.bounds[1] - cons) + leftbound_std * inflate_std:
                if line.bbox.bounds[0] > criterium:
                    line.linetype = LineType.INDENTED_ENTRY
            if line.linetype.name == 'STREETNAME':
                pass
                #may need to implement a function that fuses two street name lines

    def consolidate_indented_lines(self):
        #just set the first line's bbox as overall bbox for now
        consolidated_lines = [] #initialize an empty new column
        addline_content = '' #initialize temporary vars
        for line in reversed(self.lines): #loop reversed through old column
            if line.content: #if indented line has no content, drop it, else continue
                if line.linetype.name == 'INDENTED_ENTRY':
                    #accumulate content and bbox of indented line, but do not add to new column
                    if line.content.endswith(('⸗', '-')):
                        addline_content = line.content + addline_content
                    else:
                        addline_content = line.content + ' ' + addline_content
                else:
                    #add non-indented lines to new column, merge any accumulated addline content from indented lines
                    if line.content.endswith(('⸗', '-')):
                        consolidated_content = line.content + addline_content
                    else:
                        consolidated_content = line.content + ' ' + addline_content
                    newline = CDLine(consolidated_content, bbox=line.bbox, linetype=line.linetype, number=line.number, street=line.street)
                    consolidated_lines.append(newline)                
                    addline_content = '' #re-initialize
        self.lines = list(reversed(consolidated_lines))
    
    def find_lines_with_street_names(self, inflate_std=3, difflib_cutoff=.5, street_list=None):
        bboxheights = [line.compute_minrotatedbbox_sides()[0] for line in self.lines]
        bboxheight_mean = np.mean(bboxheights)
        bboxheight_std = np.std(bboxheights)
        criterium = bboxheight_mean + bboxheight_std * inflate_std
        for line in self.lines:
            extract = line.identify_street_name(criterium, difflib_cutoff, street_list)
            if extract:
                line.linetype = LineType.STREETNAME
                line.street = extract
    
    def find_lines_with_street_numbers(self):
        #tag lines with leading street numbers
        #wasteful, as we recompute the extract lateron
        for line in self.lines:
            extract = line.extract_leading_streetnum()
            if extract:
                line.linetype = LineType.ENTRY_WITH_STREETNUMBER
                line.number = extract
                line.content = line.content.replace(extract, '')
                    
    def list_entries(self):
        print_string = 'List of entries in column\n'
        for idx, line in enumerate(self.lines):
            if line.linetype.name == 'INDENTED_ENTRY': indention = '   '
            else: indention = ''
            print_string = print_string + str(idx) + ' ' + line.street + ' ' + line.number + ' ' + indention + line.content + '\n'
        print(print_string)

    def __len__(self):
        return len(self.lines)
                
@dataclass
class CDPage():
    columns: list[CDColumn] = field(default_factory=list)
    pagenum: int = None
                 
    def __repr__(self):
        return 'CDPage [{} columns, {} lines]'.format(len(self), np.sum([len(col) for col in self.columns]))
    
    def __len__(self):
        return len(self.columns)

@dataclass
class CDBook():
    pages: list[CDPage] = field(default_factory=list)
    
    def add_page(self, in_page):
        self.pages.append(in_page)

    
    def parse_from_pagexml(self, infile_xml, return_page=False):
        """
        transforms a PageXML file from OCR4all into a useful data structure; adds it to the CDBook instance;
        may instead return the parsed page as CDPage instance
        """
        
        with open(infile_xml, 'r', encoding='utf-8') as file:
            content = file.readlines()
            content = ''.join(content)
            bs_content = BeautifulSoup(content, 'lxml')
    
        colorder = [int(textregion.attrs['regionref'][1:])-1 for textregion in bs_content.find_all('regionrefindexed')]
        colorder = [sorted(colorder).index(x) for x in colorder] #correct for non-text regions being listed in the rank order
            
        parsed_page = CDPage() #initialize new page
        for col in [bs_content.find_all('textregion')[i] for i in colorder]:
            currentcolumn = CDColumn()
            for line in col.find_all('textline'):
                content = line.find_all('textequiv', index="0") #corrected is in index="0"
                if not content: content = line.find_all('textequiv', index="1") #if empty list returned, use content in index="1" (recognized)
                if not content: content = line.find_all('textequiv') #if list still empty, take first result among all textequivs
                content = content[0].find('unicode').string #extract actual text string
                if not content: content = '' #if no text string, pass empty string
                coordsstring  = line.find('coords').attrs['points']
                currentline = CDLine(content, coordsstring=coordsstring)
                currentline.convert_coordstring_to_bbox()
                currentcolumn.lines.append(currentline)
            parsed_page.columns.append(currentcolumn)    
        
        if not return_page: self.add_page(parsed_page)
        else: return parsed_page
        
    def distribute_addresses(self):
        #every column starts with a house number. Distribute recognized street numbers to all other in-between lines column-wise, extract numbers from line content
        #but street names are not repeated every column (nor every page), thus we need to distribute across pages
        currentnum = ''
        currentname = ''
        for page in self.pages:
            for col in page.columns:
                #currentnum = '' #reinitialize for every columns
                idx_numlines = [idx for idx, line in enumerate(col.lines) if line.linetype.name == 'ENTRY_WITH_STREETNUMBER']
                idx_namelines = [idx for idx, line in enumerate(col.lines) if line.linetype.name =='STREETNAME']
                for idx, line in enumerate(col.lines):
                    if idx in idx_numlines:
                        currentnum = line.number
                    else: #assign current running number to all lines that do not start with a house number, expcept those with a street name
                        if not (line.linetype.name == 'STREETNAME'): #expect for lines that define street names
                            line.number = currentnum
                    if idx in idx_namelines:
                        currentname = line.street
                    else:
                        line.street = currentname
    
    def parse_all_entries(self, classifier):
        for page in self.pages:
            for col in page.columns:
                for line in col.lines:
                    line.parse_entry(classifier)

    def generate_groundtruth_file(self, page_idx, out_csv):
        """
        Generate a ground truth csv file for manual labelling.
        """
        page = self.pages[page_idx]
        contents = []
        for colidx in range(len(page.columns)):
            lines = [line.content for line in page.columns[colidx].lines]
            contents.extend(lines)
        with open(out_csv, 'w', newline='', encoding='utf-8') as myfile:
             writer = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
             for idx, line in enumerate(contents):
                 writer.writerow([idx+1,'START','START']) #write START row
                 delimiters = ' ', ',', '.'
                 regexPattern = '(' + '|'.join(map(re.escape, delimiters)) + ')'
                 strings = re.split(regexPattern, line)
                 strings = [x.strip() for x in strings if x not in ('', ' ')]
                 for string in strings:
                     row = [idx+1, string]
                     writer.writerow(row)
                 writer.writerow([idx+1,'END','END']) #write START row

    def occupations_to_dataframe(self, sanitize_strings=False):
        import pandas as pd
        entries = []
        for page in self.pages:
            for col in page.columns:
                for line in col.lines:
                    street = line.street
                    number = line.number
                    entries.extend([[street, number, occ] for occ in line.parsed_entry.categories['occupations']])
        df = pd.DataFrame(entries, columns=['street', 'number', 'occupation'])
        if sanitize_strings:
            def sanitize(string):
                return string.rstrip('.').strip()
        df = df.applymap(sanitize)
        return df
                 
    def list_streets(self):
        streets = [(idxp, idxc, idxl, line.street) for (idxp, page) in enumerate(self.pages) for (idxc, col) in enumerate(page.columns) for (idxl, line) in enumerate(col.lines) if line.linetype.name =='STREETNAME']
        
        output_string = 'Page | Column | Line | Street\n'
        for (page, col, line, street) in streets:
            add_string = f'{page:<6} {col:<8} {line:<6} {street}\n'
            output_string += add_string
        print(output_string)
        
    def __repr__(self):
        return 'CDBook [{} pages, {} columns, {} lines]'.format(len(self.pages), np.sum([len(page) for page in self.pages]), np.sum([len(col) for page in self.pages for col in page.columns]))
    
    def __len__(self):
        return len(self.pages)