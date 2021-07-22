import pdfplumber, tempfile, pathlib
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import re, os, sys, logging, xlwt, openpyxl, xlsxwriter, pytesseract
import pandas as pd

import django
from django.conf import settings

class DocTools:
    load_django_settings = False
    django_settings      = False


    defaults = dict(
        image_type  = "png",   # When changing these types, change the top 2 at once for consitency
        image_ext   = ".png",
        image_rgba  = "PNG",   # This is used for the final step for highlighting text coordinates
    )
    logging         = logging.getLogger('doctools')
    core_regex      = False
    extract_regex   = False
    use_django_paths= True    # Tells paths to ignore Django settings if False

    def __init__(self, **kwargs):

        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)

        self.set_logging()
        self.set_settings()
        self.set_regex()

    def set_logging(self):
        # Setup logging level
        self.logging.setLevel(logging.DEBUG)

        # Add streamhandling
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Config log formatting
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add handler
        self.logging.addHandler(handler)

    def set_settings(self):
        if self.django_settings:
            return
        # Temporarily settings up scrip to run from command-line
        sys.path.append("../../../")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
        django.setup()
        # print(settings.DRF_FILE_UPLOAD_PATH)
        self.django_settings = settings

    def set_regex(self):

        ## TBD:  add physical contingency to "dd"
        ## TBD:  add investigation period to "dd"
        dollar_amount               = """\$ {0,}[0-9]{1,3}(,[0-9]{3}){0,}"""
        first_dollaramt_insentence  = """([^.])+""" + dollar_amount
        numberswrittenout           = """((one|eleven|ten|two|twelve|twenty|three|thirteen|thirty|fourteen|forty|four|fifteen|fifty|five|sixteen|sixty|six|seventeen|seventy|seven|eighteen|eighty|eight|nineteen|ninety|nine|hundred|thousand|million|billion)[- ]{0,1})+"""
        time_period                 = """(""" + numberswrittenout +"""|\(?[0-9]{1,3}[) -])+((business|calendar)[ -])?(day|month|week|year)s?"""
        first_timeperiod_insentence = """([^.])+""" + time_period
        monthsofyear_regex          = """(january|jan\.{0,1}|february|feb\.{0,1}|march|mar\.{0,1}|april|apr\.{0,1}|may|june|jun\.{0,1}|july|jul\.{0,1}|august|aug\.{0,1}|september|sept\.{0,1}|october|oct\.{0,1}|november|nov\.{0,1}|december|dec\.{0,1})"""
        date_slashtype_regex        = """(\d{1,2}/\d{1,2}/\d{4})"""
        date_writtenout_regex       = """(""" + monthsofyear_regex + """ \d{1,2}, \d{4}""" + """)"""
        date_eithertype_regex       = """(""" + date_writtenout_regex + """|""" + date_slashtype_regex + """)"""
        first_date_or_timeperiod_insentence = """([^.])+""" + """(""" + time_period + """|""" +date_eithertype_regex + """)"""
        deposit_regex               = """((initial|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth) )?deposit"""
        price_regex                 = """((purchase) )?price"""
        dd_regex                    = """(dd|due diligence|feasibility|inspection|physical contingency|investigation)( period)?"""
        closing_regex               = """((closing)( (period|date))?|close of escrow)"""

        self.core_regex = dict(
            dollar_amount               =   dollar_amount,
            first_dollaramt_insentence  =   first_dollaramt_insentence,
            numberswrittenout           =   numberswrittenout,
            time_period                 =   time_period,
            first_timeperiod_insentence =   first_timeperiod_insentence,
            monthsofyear_regex          =   monthsofyear_regex,
            date_slashtype_regex        =   date_slashtype_regex,
            date_writtenout_regex       =   date_writtenout_regex,
            date_eithertype_regex       =   date_eithertype_regex,
            first_date_or_timeperiod_insentence =   first_date_or_timeperiod_insentence,
            deposit_regex               =   deposit_regex,
            price_regex                 =   price_regex,
            dd_regex                    =   dd_regex,
            closing_regex               =   closing_regex
        )

        self.extract_regex = dict(
            purchaseprice = dict(
                segment = price_regex + first_dollaramt_insentence,
                entity  = dollar_amount,
                entity_name = "purchase_price"
            ),
            dd = dict (
                segment = dd_regex + first_date_or_timeperiod_insentence,
                entity  = time_period,
                entity_name = "due_diligence"
            ),
            closing = dict(
                segment = closing_regex + first_date_or_timeperiod_insentence,
                entity  = time_period,
                entity_name = "closing"
            ),
            deposit = dict(
                segment = deposit_regex + first_dollaramt_insentence,
                entity  = dollar_amount,
                entity_name = "deposit"
            ),
            time_period = dict(
                segment = time_period,
                entity  = time_period,
                entity_name = "time_period"
            )
            # dateeither      =   date_eithertype_regex,
        )


    def process(self, source, destination):
        """
          Converted method, not currently in use.
        """
        try:
            img_path = self.pdftoimage(source, destination)

        except FileNotFoundError as e:
            self.logging.error(f"File not found {e}")


        # Make sure paths exists and are directories
        if srcpath.is_dir() == True and targetpath.is_dir() == True:
            # Process PDF files within source directory
            newfilepaths = []
            for xpath in srcpath.iterdir():         #iterate through filepaths in directory
                if xpath.suffix.upper() == ".PDF":  #use of upper() makes it case insensitive

                    print(xpath.resolve())          #print full path
                    #pdfdirecttotext(xpath, targetpath)
                    newimgpath = pdftoimage(xpath, targetpath)
                    newpdfpath = createsearchablepdf(newimgpath, targetpath)
                    newfilepaths.append({'newpdfpath': newpdfpath, 'newimagepath': newimgpath})

            for x in newfilepaths:
                #imagetotext(xpath, targetpath)
                highlights = self.pdf_to_text_coordinates(x['newpdfpath'])
                highlightpdfimage(highlights, x['newpdfpath'], x['newimagepath'])

        else:
            print('Source or target paths do not exist, or are not directories.')

        return

    def get_image_dimensions(self, source):
        source = f"{self.django_settings.DRF_FILE_UPLOAD_PATH}/{source}"
        return Image.open(source).size


    def pdf_to_image(self, source, targetpath):
        self.logging.info(f"Converting {source}")
        # save temp image files in temp dir, delete them after we are finished
        # Use django settings to prepend source path

        if self.use_django_paths:
            source      =   f"{self.django_settings.DRF_FILE_UPLOAD_PATH}/{source}"
            targetpath  =   f"{self.django_settings.DRF_FILE_UPLOAD_PATH}/{targetpath}"

        with tempfile.TemporaryDirectory(dir = targetpath) as temp_dir:
            # convert pdf to multiple image
            images = convert_from_path(source, output_folder=temp_dir)
            # save images to temporary directory
            temp_images = []
            for i in range(len(images)):
                image_path = f'{temp_dir}\{i}.jpg'
                images[i].save(image_path, 'JPEG')
                temp_images.append(image_path)
             #   image2searchablepdf(image_path)

            # read images into pillow.Image
            imgs = list(map(Image.open, temp_images))
            # find minimum width of images
            min_img_width = min(i.width for i in imgs)
            # find total height of all images
            total_height = 0
            for i, img in enumerate(imgs):
                total_height += imgs[i].height
            # create new image object with width and total height
            merged_image = Image.new(imgs[0].mode, (min_img_width, total_height))
            # paste images together one by one
            y = 0

            for img in imgs:
                merged_image.paste(img, (0, y))
                y += img.height

            # save merged image
            targetfile = source + self.defaults['image_ext']
            merged_image.save(targetfile, self.defaults['image_type'])
            self.logging.info(f"Saved {targetfile}")
            return targetfile

    def pdf_to_text_coordinates(self, filepath):
        """
            pdf_to_bow

            This method will take a converted text-based PDF file and concat a list of words
            and also build a dictionary of words with x and y coordinates.  Similar to 
            NLP bag of words task with the added coordinates of word vectors on document.
        """

        # use pdfplumber's page.extract_words() function to get a list of nested dictionaries
        # containing each word in a PDF and its location.  We perform regex searches on a string
        # composed of these words.  We will use the position of a match within the string to trace words back
        # the nested dictionaries from which they arose, which contain their position on the page, allowing us to highlight
        # them in the document image.

        with pdfplumber .open(filepath) as f:
            startindex = 0
            vocabulary = []
            for page in f.pages:
                for wd in page.extract_words():
                    wd['text']          = wd['text'] + ' ' #adds a space after each word
                    wd['pdfpage']       = page.page_number
                    wd['startindex']    = startindex #the starting point of this particular word in the fulltext string created later
                    
                    wordlength          = len(wd['text'])
                    wd['endindex']      = startindex + wordlength -1  #the end of this word within the fulltext string
                    vocabulary.append(wd) #appends words with their x,y coordinates from each page of the PDF
                    startindex = wd['endindex'] + 1

            #string together all the words, separating by spaces.
            fulltext = ''
            for w in vocabulary:
                fulltext += w['text']
                #print(w['startindex'], w['text'], w['x0'], w['bottom'], w['x1'], w['top'], w['startindex'], w['endindex'])

            return fulltext, vocabulary

    def image_to_pdf(self, srcpath):
        """
            image_to_pdf

            This method will convert an image to a PDF with text contents.  The PDF
            format is searchable / has consistent text formatting for future usability.
        """

        #srcpath = pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 PG 1 Searchable1.png')
        #targetpath = pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 PG 1 Searchable1.pdf')
        self.logging.info(f"Converting {srcpath} to searchable pdf")

        image = Image.open(srcpath)
        newpdf = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
        newpdffilepath = srcpath + '.processed.pdf'
        with open(newpdffilepath, 'w+b') as f:
            f.write(newpdf)  # pdf type is bytes by default
        #pytesseract.image_to_string(Image.open(imgpath.resolve())))
        #pytesseract.image_to_string(im)

        ## ocrmypdf.ocr()
        ## ocrmypdf.hocrtransform(srcpath.resolve(), targetpath.resolve())
        return newpdffilepath

    def img_to_text(self, imgpath):

        # Open the file in append mode so that
        # All contents of all images are added to the same file
        # target_filepath = pathlib.Path.joinpath(targetdirpath, imgpath + '.txt')
        target_filepath = imgpath + ".txt"
        self.logging.info(f"Opening {imgpath}.txt for conversion.")
        with open(target_filepath, "a") as f:

            # Recognize the text as string in image using pytesserct
            text = str(pytesseract.image_to_string(Image.open(imgpath)))
            # print(text.upper())
            text = text.replace('-\n', '')  #replaces hypens added at line endings

            # Finally, write the processed text to the file.
            f.write(text)
            self.logging.info(f"Saved {target_filepath}.")

        return target_filepath

    def get_entity_matches(self, fulltext, wordregistry):

        results = []  #load with information used to apply highlights to the document image
        match_id = 0
        for key, pattern in self.extract_regex.items():
            sequence = 0
            for match in re.finditer(pattern['segment'], fulltext, re.IGNORECASE):
                    match_id += 1
                    s = match.start()
                    e = match.end()

                    #cross reference s and e from fulltext string to positions on the pdf document
                    #NOTE THAT A MATCH MAY BE A SUBSET OF A WORD, IN WHICH CASE THE STARTING POINT OF THE MATCH
                    #WILL COME AFTER THE STARTING POINT OF THE WORD!  A MATCH MAY ALSO STRADDLE MULTIPLE WORDS

                    x0, y0, x1, y1 = 0, 0, 0, 0
                    for index, word in enumerate(wordregistry):
                        success = 0
                        #test if this word contains the beginning of a match
                        if match.start() >= word['startindex'] and match.start() <= word['endindex']:
                            #estimate starting position on document
                            x0 = word['x0']
                            y0 = word['bottom']
                            if match.end() <= word['endindex']:
                                x1 = word['x1']
                                y1 = word['top']
                            else:
                                x1 = word['x1']
                                y1 = word['top']
                            success=1

                        if match.start() < word['startindex'] and match.end() >= word['startindex']:
                            x0 = word['x0']
                            y0 = word['bottom']
                            if match.end() <= word['endindex']:
                                x1 = word['x1']
                                y1 = word['top']
                            else:
                                x1 = word['x1']
                                y1 = word['top']
                            success=1

                        if success == 1:
                            if len(word['text']) > 0:
                                extension = (x1 - x0) / len(word['text'])  ##since the edge of the last character is typically beyond x1, we need to extend the highlight slightly
                            else:
                                extension = 1

                        if success == 1:
                            results.append({
                                'pattern_name': key, 
                                'sequence':     sequence,
                                'start_index':  match.start(),
                                'end_index':    match.end(),
                                'word':         word['text'],
                                'word_id':      index, 
                                'match_id':     match_id, 
                                'matches_with': fulltext[s:e], 
                                'x0': x0, 
                                'y0': y0, 
                                'x1': x1 + extension,
                                'y1': y1
                            })
                            sequence += 1
        return results
    
    def clean_entity(self, entity = ""):

        replace_map = ["(", ")"]

        for char in replace_map:
            entity = entity.replace(char, "")

        entity = entity.strip()    ## Strip whitespace

        if entity[::-1][0] == ",": ## Remove trailing commas when possible
            entity = entity[:-1]

        return entity.strip() 

    def get_entity_coordinates(self, entity_name = False, entity_value = False, from_index = False, segment_length = 10, word_coords = False):
        # print("Searching for entity:", entity)
        # print("Segment_length:", segment_length)
        # print("From index + 20:", [r for r in word_coords[from_index:from_index+segment_length]])
        # print("----------------------------------")

        entity_length = len(entity_value.split())

        matches = False # in the event nothign is found, handle false

        for index, word_coord in enumerate(word_coords[from_index:from_index+segment_length]):

            if entity_length > 1:
                """ Multi-word matches """
                match = word_coord['text'].strip() == entity_value.split()[0]
                single_match = False
                # print(
                #     "1st word / word_coord iter / len / type:", 
                #     (entity.split()[0], word_coord['text']), 
                #     (len(entity.split()[0]), len(word_coord['text'])), 
                #     (type(entity.split()[0]), type(word_coord['text'])),
                #     match
                # )
            else:
                """ Single-word match """
                ## Totally a bad hack here but goign to add it until we come up with better pre-processing
                ## Added clean_entity_method to remove "(" type characters when trying to match coordinates 
                match = self.clean_entity(word_coord['text']) == entity_value.strip()
                single_match = True
            
            if match:

                found_match = dict(
                    index  = index,
                    entity_name = entity_name,
                    entity_value = entity_value,
                    x0     = word_coords[from_index + index]['x0'],
                    x1     = word_coords[from_index + index]['x1'],
                    y0     = word_coords[from_index + index]['bottom'],
                    y1     = word_coords[from_index + index]['top']
                )

                if single_match:
                    found_match['x1'] = word_coords[from_index + index]['x1']
                else:
                    found_match['x1'] = word_coords[from_index + index + entity_length - 1]['x1']

                matches = found_match

        return matches

    def map_entities(self, pdfpath, word_coords, doctext = False, vocabulary = False):
        """[summary]

        Args:
            pdfpath ([str]): [description]
            word_coords ([list[dict]]): List of words and positional attributes.  Sometimes this is called "vocabulary" in this file
                                        for the sake of future continuity and/or future code refactors, this is a better name for 
                                        this type of resource.

        Returns:
            [type]: [description]
        """

        highlights = []
        # fulltext, wordregistry = pdfexcavate(pdfpath)
        # myregexdict, searchthesepattersndict = regexdict()

        if not doctext and not vocabulary:
            doctext, vocabulary = self.pdf_to_text_coordinates(pdfpath)
        
        results = self.get_entity_matches(doctext, vocabulary)

        bidsummary = []
        # purchase price algorithm
        matches_found = dict()
        for row in results:
            for pattern_name, pattern in self.extract_regex.items():
      
                if row['pattern_name'] == pattern_name: # and row['sequence'] == 0: # attempt to match all
                  
                    if matches_found.get(pattern_name, False):
                        continue

                    matches = re.search(pattern['entity'], row['matches_with'])
                    
                    if matches:
                        # print("name:", pattern_name,"match:", matches.group(0))
                        # print("patter", row['pattern_name'], type(matches))
                        matched = self.get_entity_coordinates(
                            entity_name     = pattern['entity_name'],
                            entity_value    = matches.group(0),
                            from_index      = row['word_id'],
                            segment_length  = len(row['matches_with'].split(' ')),
                            word_coords     = word_coords
                        )
                        bidsummary.append(matched)
                        matches_found[pattern_name] = True

                        # bidsummary.append({
                        #     'pattern_name': row['pattern_name'],
                        #     'sequence':     row['sequence'], 
                        #     'matches_with': row['matches_with'],
                        #     'word':         row['word'],
                        #     'result':       matches.group(0),
                        #     'x0':           row['x0'],
                        #     'y0':           row['y0'],
                        #     'x1':           row['x1'],
                        #     'y1':           row['y1']
                        # })

            # if r['pattern_name']== 'purchaseprice' and r['sequence']==0:  #for now, we're using the first match in the pattern
            #     z = re.search(self.core_regex['dollar_amount'], r['matches_with'])
            #     if z:
            #         bidsummary.append({
            #             'pattern_name': r['pattern_name'],
            #             'sequence':     r['sequence'], 
            #             'matches_with': r['matches_with'], 
            #             'result':       z.group(0)
            #         })

            # # deposit algorithm
            # if r['pattern_name'] == 'deposit' and r['sequence']==0:
            #     z = re.search(self.core_regex['dollar_amount'], r['matches_with'])
            #     if z:
            #         bidsummary.append(
            #             {'pattern_name': r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})

            # # dd period algorithm
            # if r['pattern_name']== 'dd' and r['sequence']==0:
            #     z = re.search(self.core_regex['time_period'], r['matches_with'])
            #     if z:
            #         bidsummary.append({'pattern_name':r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})

            # # closing period algorithm
            # if r['pattern_name']== 'closing' and r['sequence']==0:
            #     z = re.search(self.core_regex['time_period'], r['matches_with'])
            #     if z:
            #         bidsummary.append({'pattern_name':r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})
        # print(bidsummary)
        # print("Writing CSV")
        # df = pd.DataFrame(bidsummary)
        # df.to_csv("test.csv")
        # print(bidsummarydf)

        # writer = pd.ExcelWriter(r"C:\Users\Brett\Desktop\bidsummary.xlsx", engine='xlsxwriter')
        # bidsummarydf.to_excel(writer, sheet_name='Sheet1')
        # writer.save()
            #highlightpdfimage(results, pdfpath, mirrorimagepath)
        return bidsummary

    def image_to_highlighted(self, highlights, pdfpath, mirrorimagepath):
        
        mirrorimagepath = f"{self.django_settings.DRF_FILE_UPLOAD_PATH}/{mirrorimagepath}"
        pdfpath         = f"{self.django_settings.DRF_FILE_UPLOAD_PATH}/{pdfpath}"

        base = Image.open(mirrorimagepath).convert('RGBA')
        overlay = Image.new('RGBA', base.size, (255, 255, 255, 0))
        with pdfplumber.open(pdfpath) as pdf:
            
            for page in pdf.pages:

                if page.width > 0:
                    scale = base.size[0]/page.width # I'm using this to translate pdf plumber coordinates to image coordinates
                else: 
                    scale = 1  #defaults to 1 in case there is no page width

                count =0
                for h in highlights:
                        shape = [(h['x0']*scale, h['y0']*scale), (h['x1']*scale, h['y1']*scale)]
                        d = ImageDraw.Draw(overlay)
                        if count%2==0:
                            d.rectangle(shape, fill=(255,0,0,32)) # last number in fill specifies opacity!
                        else:
                            d.rectangle(shape, fill=(0, 0, 255, 32))  # last number in fill specifies opacity!

                        d = ImageDraw.Draw(base, 'RGBA')
                        count += 1

                #font = ImageFont.truetype("arial.ttf", 270)
                # draw text, half opacity
                #d.text((10, 10), "Hello", font=font, fill=(255, 0, 0, 255))
                # draw text, full opacity
                #d.text((10, 60), "World", fill=(255, 0, 0, 255))
                out = Image.alpha_composite(base, overlay)
                #out.show()
                out.save(f"{mirrorimagepath}.highlighted{self.defaults['image_ext']}", self.defaults['image_rgba'])

        return highlights

## Working example of API:
# dt = DocTools()
# source_path     =   f"{dt.django_settings.DRF_FILE_UPLOAD_PATH}/1"
# source          =   f"{source_path}/Griffis 2019.4.19 LOI Courtyards at 65th.pdf"
# img_filepath    =   dt.pdf_to_image(source, source_path)
# pdf_filepath    =   dt.img_to_pdf(img_filepath) # searchable pdf
# doctext, vocabulary = dt.pdf_to_text_coordinates(pdf_filepath)
# matches         = dt.get_entity_matches(doctext, vocabulary)

## Image to text
# text_filepath   =   dt.img_to_text(img_filepath)
# dt.map_entities(pdf_filepath)

## 
# dt = DocTools()  # this is the new class for general document handling which may be expanded to more than just "PDFs"

# source = "the document from Django request /bidinterpreter/[deal id]/import/[document id]"
# source_path = "the uploads directory/[deal id]/[doc id]"

# img_filepath        =   dt.pdf_to_image(source, source_path)        # 1. Converts initial PDF doc to image, returns image location
# pdf_filepath        =   dt.image_to_pdf(img_filepath)                 # 2. Converts image to "searchable pdf"
# doctext, vocabulary =   dt.pdf_to_text_coordinates(pdf_filepath)  # 3. Get document text from PDF, then get coordinates of each word
# matches             =   dt.get_entity_matches(doctext, vocabulary)    # 4. Extract matches /w coordinates
# dt.image_to_highlighted(matches, pdf_filepath, img_filepath)      # 5. Apply highlighting to document and save PNG