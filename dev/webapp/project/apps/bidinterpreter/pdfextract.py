import pdfplumber
import tempfile
import pathlib
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from pdf2image import convert_from_path
import re
import os
import pandas as pd
import xlwt
import openpyxl
import xlsxwriter


def test():

    titanicdf = pd.read_csv(r"C:\Users\Brett\Desktop\titanic.csv")
    print(titanicdf[["Age", "Sex"]].head(20))
    return


def pdfdispatch():

    srcpath = pathlib.Path(r'C:\Users\Brett\Desktop\Final Offers')
    targetpath = pathlib.Path(r'C:\Users\Brett\Desktop\test')

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
            highlights = pdfexcavate(x['newpdfpath'])
            highlightpdfimage(highlights, x['newpdfpath'], x['newimagepath'])

    else:
        print('Source or target paths do not exist, or are not directories.')

    return

def createsearchablepdf(srcpath, targetpath):

    #srcpath = pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 PG 1 Searchable1.png')
    #targetpath = pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 PG 1 Searchable1.pdf')
    im = Image.open(srcpath.resolve())
    newpdf = pytesseract.image_to_pdf_or_hocr(im, extension='pdf')
    newpdffilepath = pathlib.Path.joinpath(targetpath, srcpath.stem + ' from_image.pdf')
    with open(newpdffilepath, 'w+b') as f:
        f.write(newpdf)  # pdf type is bytes by default
    #pytesseract.image_to_string(Image.open(imgpath.resolve())))
    #pytesseract.image_to_string(im)

    ## ocrmypdf.ocr()
    ## ocrmypdf.hocrtransform(srcpath.resolve(), targetpath.resolve())
    return newpdffilepath

def pdftoimage(xpath, targetpath):

    # save temp image files in temp dir, delete them after we are finished

    with tempfile.TemporaryDirectory(dir=targetpath) as temp_dir:
        # convert pdf to multiple image
        images = convert_from_path(xpath.resolve(), output_folder=temp_dir)
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
        targetfile = targetpath.joinpath(xpath.stem + '.jpg')
        merged_image.save(targetfile, 'JPEG')

        return targetfile

def imagetotext(imgpath, targetdirpath):

    # Open the file in append mode so that
    # All contents of all images are added to the same file
    targetfilepath = pathlib.Path.joinpath(targetdirpath, imgpath.stem + '.txt')
    f = open(targetfilepath, "a")

    # Recognize the text as string in image using pytesserct
    text = str(pytesseract.image_to_string(Image.open(imgpath.resolve())))
    print(text.upper())
    text = text.replace('-\n', '')  #replaces hypens added at line endings

    # Finally, write the processed text to the file.
    f.write(text)

    # Close the file after writing all the text.
    f.close()
    return

def pdfdirecttotext(pdfpath, targetdirpath):

    #this code pulls text directly from searchable pdf's; doesn't work with scanned pdfs
    # pdffile = open(r'C:\Users\Brett\Desktop\Final Offers\Anton 03.13.20.pdf', 'rb')
    # pdfname = r'C:\Users\Brett\Desktop\Final Offers\MBK 03.13.20.pdf'
    # outputfolder = r'C:\Users\Brett\Desktop\test'

    targetfilepath = pathlib.Path.joinpath(targetdirpath, pdfpath.stem + 'DIRECT.txt')
    f = open(targetfilepath, "a")

    with pdfplumber .open(pdfpath.resolve()) as pdf:
        for page in pdf.pages:
            f.write(str(page.extract_text()))

    f.close()
    # pdfread = p2.PdfFileReader(pdffile)
    # x = pdfread.getPage(2)
    # print(x.extractText())
    return

def regexprocessing(pdfpath, mirrorimagepath):
    highlights = []
    fulltext, wordregistry = pdfexcavate(pdfpath)
    myregexdict, searchthesepattersndict = regexdict()

    results = pattern_search(searchthesepattersndict, fulltext, wordregistry)

    bidsummary = []
    # purchase price algorithm

    for r in results:

        if r['pattern_name']== 'purchaseprice' and r['sequence']==0:  #for now, we're using the first match in the pattern
            z = re.search(myregexdict['dollar_amount']['regex'], r['matches_with'])
            if z:
                bidsummary.append({
                    'pattern_name':r['pattern_name'],
                    'sequence': r['sequence'], 
                    'matches_with': r['matches_with'], 
                    'result': z.group(0)
                })
                print("found purhcase price:", z.group(0))
                print(myregexdict['dollar_amount']['regex'], r['matches_with'])

        # deposit algorithm
        if r['pattern_name'] == 'deposit' and r['sequence']==0:
            z = re.search(myregexdict['dollar_amount']['regex'], r['matches_with'])
            if z:
                bidsummary.append(
                    {'pattern_name': r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})

        # dd period algorithm
        if r['pattern_name']== 'dd' and r['sequence']==0:
            z = re.search(myregexdict['time_period']['regex'], r['matches_with'])
            if z:
                bidsummary.append({'pattern_name':r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})

        # closing period algorithm
        if r['pattern_name']== 'closing' and r['sequence']==0:
            z = re.search(myregexdict['time_period']['regex'], r['matches_with'])
            if z:
                bidsummary.append({'pattern_name':r['pattern_name'], 'sequence': r['sequence'], 'matches_with': r['matches_with'], 'result': z.group(0)})

    bidsummarydf = pd.DataFrame(bidsummary)

    print(bidsummarydf)

    # writer = pd.ExcelWriter(r"C:\Users\Brett\Desktop\bidsummary.xlsx", engine='xlsxwriter')
    # bidsummarydf.to_excel(writer, sheet_name='Sheet1')
    # writer.save()


        #highlightpdfimage(results, pdfpath, mirrorimagepath)
    return



def regexdict():
    #predefined regex code:

    dollar_amount  = """\$ {0,}[0-9]{1,3}(,[0-9]{3}){0,}"""
    first_dollaramt_insentence = """([^.])+""" + dollar_amount
    numberswrittenout = """((one|eleven|ten|two|twelve|twenty|three|thirteen|thirty|fourteen|forty|four|fifteen|fifty|five|sixteen|sixty|six|seventeen|seventy|seven|eighteen|eighty|eight|nineteen|ninety|nine|hundred|thousand|million|billion)[- ]{0,1})+"""
    time_period = """(""" + numberswrittenout +"""|\(?[0-9]{1,3}[) -])+((business|calendar)[ -])?(day|month|week|year)s?"""
    first_timeperiod_insentence = """([^.])+""" + time_period
    monthsofyear_regex = """(january|jan\.{0,1}|february|feb\.{0,1}|march|mar\.{0,1}|april|apr\.{0,1}|may|june|jun\.{0,1}|july|jul\.{0,1}|august|aug\.{0,1}|september|sept\.{0,1}|october|oct\.{0,1}|november|nov\.{0,1}|december|dec\.{0,1})"""
    date_slashtype_regex = """(\d{1,2}/\d{1,2}/\d{4})"""
    date_writtenout_regex = """(""" + monthsofyear_regex + """ \d{1,2}, \d{4}""" + """)"""
    date_eithertype_regex = """(""" + date_writtenout_regex + """|""" + date_slashtype_regex + """)"""
    first_date_or_timeperiod_insentence = """([^.])+""" + """(""" + time_period + """|""" +date_eithertype_regex + """)"""
    deposit_regex = """((initial|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth) )?deposit"""
    price_regex = """((purchase) )?price""" #################################
    dd_regex = """(dd|due diligence|feasibility|inspection)( period)?"""
    closing_regex = """((closing)( (period|date))?|close of escrow)"""

    myregexdict = dict(
        dollar_amount = {'regex': dollar_amount},
        first_dollaramt_insentence = {'regex': first_dollaramt_insentence}, #############################################
        numberswrittenout = {'regex': numberswrittenout},
        time_period = {'regex': time_period},
        first_timeperiod_insentence = {'regex': first_timeperiod_insentence},
        monthsofyear_regex = {'regex': monthsofyear_regex},
        date_slashtype_regex = {'regex': date_slashtype_regex},
        date_writtenout_regex = {'regex': date_writtenout_regex},
        date_eithertype_regex = {'regex': date_eithertype_regex},
        first_date_or_timeperiod_insentence = {'regex': first_date_or_timeperiod_insentence},
        deposit_regex = {'regex': deposit_regex},
        price_regex = {'regex': price_regex},
        dd_regex = {'regex': dd_regex},
        closing_regex = {'regex': closing_regex}
    )

    searchthesepatternsdict = dict(
        purchaseprice = {'regex': price_regex + first_dollaramt_insentence},
        dateeither={'regex': date_eithertype_regex},
        dd = {'regex': dd_regex + first_date_or_timeperiod_insentence},
        closing = {'regex': closing_regex + first_date_or_timeperiod_insentence},
        deposit = {'regex': deposit_regex + first_dollaramt_insentence},
 #       writtendates = {'regex': date_writtenout_regex}
 #       financingcontingency = {'regex': 'price'},
 #       alldollaramounts = {'regex': dollar_amount},
  #      dd ={'regex': 'due diligence |feasibility|inspection period'},
   #     longhand_numbers = {'regex': numberswrittenout},
        time_period = {'regex': time_period}
        )

    return myregexdict, searchthesepatternsdict


def pdfexcavate(pdfpath):

    # use pdfplumber's page.extract_words() function to get a list of nested dictionaries
    # containing each word in a PDF and its location.  We perform regex searches on a string
    # composed of these words.  We will use the position of a match within the string to trace words back
    # the nested dictionaries from which they arose, which contain their position on the page, allowing us to highlight
    # them in the document image.

    with pdfplumber .open(pdfpath.resolve()) as pdf:
        startindex = 0
        wordregistry = []
        for page in pdf.pages:
            for wd in page.extract_words():
                wd['text'] = wd['text'] + ' ' #adds a space after each word
                wd['pdfpage'] = page.page_number
                wd['startindex'] = startindex #the starting point of this particular word in the fulltext string created later
                wordlength = len(wd['text'])
                wd['endindex'] = startindex + wordlength -1  #the end of this word within the fulltext string
                wordregistry.append(wd) #appends words with their x,y coordinates from each page of the PDF
                startindex = wd['endindex'] + 1

        #string together all the words, separating by spaces.
        fulltext=''
        for w in wordregistry:
            fulltext = fulltext + w['text']
            #print(w['startindex'], w['text'], w['x0'], w['bottom'], w['x1'], w['top'], w['startindex'], w['endindex'])

        return fulltext, wordregistry

def pattern_search(patterns, fulltext, wordregistry):

    results = []  #load with information used to apply highlights to the document image
    match_id = 0
    for p in patterns:
        sequence = 0
        for match in re.finditer(patterns[p]['regex'], fulltext, re.IGNORECASE):
                match_id+=1
                s = match.start()
                e = match.end()

                #cross reference s and e from fulltext string to positions on the pdf document
                #NOTE THAT A MATCH MAY BE A SUBSET OF A WORD, IN WHICH CASE THE STARTING POINT OF THE MATCH
                #WILL COME AFTER THE STARTING POINT OF THE WORD!  A MATCH MAY ALSO STRADDLE MULTIPLE WORDS

                x0, y0, x1, y1 = 0, 0, 0, 0
                for word in wordregistry:
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
                            'pattern_name': p, 
                            'sequence': sequence, 
                            'match_id': match_id, 
                            'matches_with': fulltext[s:e],
                            'x0': x0, 'y0': y0, 
                            'x1': x1 + extension,'y1': y1
                        })
                        sequence+=1
    return results

def highlightpdfimage(highlights, pdfpath, mirrorimagepath):


    base = Image.open(mirrorimagepath.resolve()).convert('RGBA')
    overlay = Image.new('RGBA', base.size, (255, 255, 255, 0))
    with pdfplumber.open(pdfpath.resolve()) as pdf:
        for page in pdf.pages:
            if page.width > 0:
                scale = base.size[0]/page.width # I'm using this to translate pdf plumber coordinates to image coordinates
            else: scale = 1  #defaults to 1 in case there is no page width

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
            out.save(pathlib.Path.joinpath(mirrorimagepath.parent, mirrorimagepath.stem + ' highlighted.png'), 'PNG')

    return

## testing to run on-demmand to compare results

#bidinterpreter.pdfextract.createsearchablepdf()
#bidinterpreter.pdfextract.pdfdispatch()
#bidinterpreter.pdfextract.imagetotext()
#------
# upload_path = "/home/dave/projects/bidinterpreter/uploads/1"
# target_pdf = f"{upload_path}/Griffis 2019.4.19 LOI Courtyards at 65th.pdf.png.processed.pdf"
# target_img = f"{upload_path}/Griffis 2019.4.19 LOI Courtyards at 65th.pdf.png"

# highlights = regexprocessing(pathlib.Path(target_pdf), pathlib.Path(target_img))
#-----
# highlightpdfimage(highlights, pathlib.Path(target_pdf), pathlib.Path(target_img))



#bidinterpreter.pdfextract.regexdict()
#bidinterpreter.pdfextract.test()

