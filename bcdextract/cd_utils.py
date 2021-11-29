# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 14:30:51 2021

@author: kalle
"""
from __future__ import absolute_import
import os
import urllib

def download_berlin_cd_files(year, pages, out_folder):

    for page in pages:    
        image_id = f'{page}'.zfill(8)
        url = f'https://digital.zlb.de/viewer/api/v1/records/34115512_{year}/files/images/{image_id}.png/full/max/0/default.png'
        out_filename = os.path.join(out_folder, f'{image_id}.png')
        if not os.path.isdir(out_folder): os.mkdir(out_folder)
        urllib.request.urlretrieve(url, out_filename)
        
def convert_pagexml_to_tesseract():
    """
    Reads in OCR ground truthfiles in PAGEXML format, converts to line images and corresponding text for further use by Tesseract.

    Code adapted from the OCR-D project
    https://github.com/OCR-D/format-converters
    """
    import os
    from lxml import etree
    from PIL import Image

    #gen_dir = os.path.join('C:', os.sep, 'Users', 'kalle', 'Dropbox', '!Adress books and Census data', 'Data', 'Tesseract training data', 'AB1875')
    gen_dir = os.path.join('C:', os.sep, 'Users', 'kalle', 'Desktop', 'ocr with thilo', 'training')
    in_dir = os.path.join(gen_dir, 'AB1875')
    out_dir = os.path.join(gen_dir,'data', 'AB_frk', 'ground-truth')

    image_format = 'png'
    page_version= '2017-07-15'
    ns = {
         'pc': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/' + page_version,
         'xlink' : "http://www.w3.org/1999/xlink",
         're' : "http://exslt.org/regular-expressions",
         }
    PC = "{%s}" % ns['pc']
    xpath = ".//pc:TextLine"
        
    xml_files = [os.path.join(in_dir, file) for file in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, file)) & file.endswith('.xml')]
    png_files = [os.path.join(in_dir, file) for file in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, file)) & file.endswith('.nrm.png')]

    for (xml_file, png_file) in zip(xml_files, png_files):
        
        #read input xml
        page_elem = etree.parse(xml_file).getroot().find('./' + PC + 'Page')

        #open input png
        f = open(png_file, 'rb')
        pil_image = Image.open(f)

        #iterate over all structs
        for struct in page_elem.xpath(xpath, namespaces=ns):

            points = struct.find("./" + PC + "Coords").get("points")
            if not points:
                continue

            xys = [tuple([int(p) for p in pair.split(',')]) for pair in points.split(' ')]

            # generate PIL crop schema from struct points
            min_x = pil_image.width
            min_y = pil_image.height
            max_x = 0
            max_y = 0
            for xy in xys:
                if xy[0] < min_x:
                    min_x = xy[0]
                if xy[0] > max_x:
                    max_x = xy[0]
                if xy[1] < min_y:
                    min_y = xy[1]
                if xy[1] > max_y:
                    max_y = xy[1]

            # generate and save struct image
            pil_image_struct = pil_image.crop((min_x, min_y, max_x, max_y))
            pil_image_struct.save("%s/%s_%s.%s" % (out_dir, os.path.basename(png_file), struct.get("id"), image_format), dpi=(300, 300))

            # extract text
            unic = struct.find("./" + PC + "TextEquiv").find("./" + PC + "Unicode")
            if unic is not None and unic.text is not None:
                text_dest = open("%s/%s_%s.gt.txt" % (out_dir,os.path.basename(png_file),struct.get("id")), "w", encoding='utf-8')
                #fix ligatures etc
                unic.text= unic.text.replace('\ueedc', 'ß')
                text_dest.write(unic.text)
                text_dest.close()