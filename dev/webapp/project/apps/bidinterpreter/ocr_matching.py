import pandas as pd, numpy as np
import time, os, glob, re, sys, time
from datetime import datetime
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models._models_py3 import ReadOperationResult
# sys.path.append("..")

## nlp libraries
import spacy
nlp = spacy.load("en_core_web_sm") # default model -- we will make a better one later

class AzureVisionService:
    
    client      = False
    credentials = False
    result      = False
    last_duration = False
    collection_results = False
    
    def __init__(self, **opts):
        for attribute, value in opts.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)
        self.set_client()
                
    def set_client(self):
        '''
        Authenticate
        Authenticates Azure credentials and creates a client.
        '''
        if self.credentials and self.credentials.get('subscription_key', False):
            # Init client
            credentials  = CognitiveServicesCredentials(self.credentials.get('subscription_key'))
            self.client  = ComputerVisionClient(self.credentials.get('endpoint'), credentials)
    
    def set_ocr_tokens(self, words):
        _

    def get_ocr(self, filepath):
        '''
        Read and extract from an image -- note that only S1 tier service will return results for PDFs > 2 pages.
        '''
        try:
            # Images PDF with text
            fp = open(filepath,'rb')
        except Exception as error:
            raise Exception(f"Problem opening file {filepath}:  {error}")
    
        # Images PDF with text
        fp = open(filepath,'rb')

        # Async SDK call that "reads" the image
        response = self.client.read_in_stream(fp, raw=True)
        # Don't forget to close the file
        fp.close()

        # Get ID from returned headers
        operation_location = response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        # SDK call that gets what is read
        start = datetime.now() # profile time
        while True:
            result = self.client.get_read_result(operation_id) # get_read_operation_result(operation_id)
            if result.status not in [OperationStatusCodes.not_started, OperationStatusCodes.running]:
                break
            time.sleep(.5)
        end = datetime.now()
        self.last_duration = (end -  start).total_seconds()
        return result
    
    def get_result_stats(self, result):
        assert type(result) is ReadOperationResult, f"{result} is not a ReadOperationResult."
        stats = dict(
            status   = result.status,
            n_pages  = len(result.analyze_result.read_results),
            duration = self.last_duration,
            pages    = []

        )
        for page in result.analyze_result.read_results:
            stats['pages'].append(
                dict(
                    angle  = page.angle,
                    width  = page.width,
                    height = page.height,
                    unit   = page.unit,
                )
            )
        return stats
    
    def get_entities(self, result):
        assert type(result) is ReadOperationResult, f"{result} is not a ReadOperationResult."
        # print("Result stats....", result.as_dict()['analyze_result']['read_results'])
        entities = []
        word_n   = 0
        for page_n, page in enumerate(result.as_dict()['analyze_result']['read_results']):
            for line_n, line in enumerate(page['lines']):
                for entity in line['words']:
                    entities.append({
                        "index": word_n,
                        "page":  page_n,
                        "line":  line_n,
                        "text":  entity['text'],
                        "coord": entity['bounding_box'],
                    })
                    word_n += 1
        return entities
    

    
    
    def get_fulltext(self, result, linebreaks = True):
        assert type(result) is ReadOperationResult, f"{result} is not a ReadOperationResult."
        text = ""
        for page in result.as_dict()['analyze_result']['read_results']:
            for line in page['lines']:
                if linebreaks:
                    text += "\n"
                for word in line['words']:
                    text += f"{word['text']} "
        return text
    
    def get_token_punctuation(self, tokens):
        """ get_token_punctuation
        
        Transforms original tokens to a dictionary with new offsets mapped to their orignal token index for
        easy reverse lookup later (mainly for NER models).
        
        Parameters
        ----------
        tokens : list[dict]
        
        Returns
        ----------
        dict[int:dict] 
            List of new offsets with punctuation mapped to original token index.
        
        """
        
        new_tokens = []
        added_token_count = 0
        for original_index, token in enumerate(tokens):
            punctuation_split = re.split('(\W+)', token['text'])
            money_split = token['text'].split("$")
            if len(money_split) > 1:
                for money_index, money_item in enumerate(money_split):
                    money_item = "$" if money_index == 0 else money_item
                    new_tokens.append(
                        dict(
                            original_index    = original_index,
                            punctuation_index = original_index + added_token_count,
                            text              = money_item,
                            page              = token['page'],
                            bounding_box      = token['bounding_box']
                        )
                    )
                    added_token_count += 1
            elif token['text'].count(",") > 1 or len(punctuation_split) == 1:
                new_tokens.append(
                    dict(
                        original_index    = original_index,
                        punctuation_index = original_index + added_token_count,
                        text              = token['text'],
                        page              = token['page'],
                        bounding_box      = token['bounding_box']
                    )
                )
            else:
                for split_item in punctuation_split:
                    if split_item == '':
                        continue
                    new_tokens.append(
                        dict(
                            original_index    = original_index,
                            punctuation_index = original_index + added_token_count,
                            text              = split_item,
                            page              = token['page'],
                            bounding_box      = token['bounding_box']
                        )
                    )
                    added_token_count += 1
        return new_tokens
        
    
    def get_tokens(self, result, by_offset = True):
        """ get_tokens
        
        Gets and prints the spreadsheet's header columns

        Parameters
        ----------
        result : ReadOperationResult (Azure response), required
            The file location of the spreadsheet

        by_offset : bool, optional
            Totally forgetting why this was added.. will remove if not needed after 1st release.

        Returns
        -------
        list[dict] (no punction) or dict[int:dict] (keys are original tokens)
            List of tokens with the original coordinates / bounding boxes
        """
        assert type(result) is ReadOperationResult, f"{result} is not a ReadOperationResult."
        tokens = {} if by_offset else []
        words  = 0
        for page in result.as_dict()['analyze_result']['read_results']:
            for line in page['lines']:
                for word in line['words']:
                    if by_offset:
                        # TBD
                        tokens
                    else:
                        tokens.append(
                            dict(
                                text = word['text'],
                                page = page['page'],
                                bounding_box = word['bounding_box'],
                                confidence = word['confidence']
                            )
                        )
                    words += 1
        return tokens

class EntityRegexMatch:
    
    regex  = False
    tokens = False # list of tokens /w coordinates from Azure service
    
    def __init__(self, **opts):
        for attribute, value in opts.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)
        self.set_patterns()
                
    def set_patterns(self):
        
        fillerallowed               = """.{0,100}"""
        
        dollar_amount               =  "\$ {0,}[0-9]{1,3}(,[0-9]{3}){0,}"
        first_dollaramt_insentence  =  f"([^.])+{dollar_amount}"
        numberswrittenout           =  """((one|eleven|ten|two|twelve|twenty|three|thirteen|thirty|fourteen|forty|four|fifteen|fifty|five|sixteen|sixty|six|seventeen|seventy|seven|eighteen|eighty|eight|nineteen|ninety|nine|hundred|thousand|million|billion)[- ]{0,1})+"""
        time_period                 =  "(" + numberswrittenout + """|\(?[0-9]{1,3}[) -])+((business|calendar)[ -])?(day|month|week|year)s?"""
        first_timeperiod_insentence =  """([^.])+""" + time_period
        
        monthsofyear_regex          =  """(january|jan\.{0,1}|february|feb\.{0,1}|march|mar\.{0,1}|april|apr\.{0,1}|may|june|jun\.{0,1}|july|jul\.{0,1}|august|aug\.{0,1}|september|sept\.{0,1}|october|oct\.{0,1}|november|nov\.{0,1}|december|dec\.{0,1})"""
        date_slashtype_regex        =  """(\d{1,2}/\d{1,2}/\d{4})"""
        date_writtenout_regex       =  """(""" + monthsofyear_regex + """ \d{1,2}, \d{4}""" + """)"""
        date_eithertype_regex       =  """(""" + date_writtenout_regex + """|""" + date_slashtype_regex + """)"""
        first_date_or_timeperiod_insentence = """([^.])+""" + """(""" + time_period + """|""" +date_eithertype_regex + """)"""
        
        deposit_regex               =  """((initial|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth) )?deposit"""
        price_regex                 =  """((purchase) )?price"""
        # dd_regex                    =  """(dd|due diligence|feasibility|inspection|physical contingency|investigation)( period)?"""
        dd_regex                    =  """(\bdd\b|due diligence|feasibility|inspection|study|physical|contingency)( period)?"""
        closing_regex               =  """((closing)( (period|date))?|close of escrow)"""
        purchase_segment            =  """.{0,50}(?=purchase)([^.])+""" + dollar_amount + """|([^.])+""" + dollar_amount + """.{0,50}(?=purchase)"""
        diligence_segment           =  """.{0,150}(?=diligence)([^.])+""" + time_period + """|([^.])+""" + time_period + """.{0,150}(?=diligence)"""

        ## This may not be needed..
        self.regex = dict(
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
        
        
        ## Legacy patterns
        self.extract_regex = dict(
            purchaseprice = dict(
                # segment = price_regex + first_dollaramt_insentence,
                segment = purchase_segment,
                entity  = dollar_amount,
                entity_name = "purchase_price"
            ),
            dd = dict(
                segment = dd_regex + fillerallowed + first_date_or_timeperiod_insentence,
                # segment = diligence_segment, # my new regex was a dud
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
            # time_period = dict(
            #     segment = time_period,
            #     entity  = time_period,
            #     entity_name = "time_period"
            # )
            # dateeither      =   date_eithertype_regex,
        )
        
        ## New segment patterns strategy
        self.extract_segments_regex = dict(
            purchaseprice = dict(
                segment = purchase_segment,
                entity_name = "purchase_price"
            ),
            dd = dict (
                segment = dd_regex,
                entity_name = "due_diligence"
            ),
            closing = dict(
                segment = closing_regex,
                entity_name = "closing"
            ),
            deposit = dict(
                segment = deposit_regex,
                entity_name = "deposit"
            ),
        )
    
    def get_document_token_pipeline(self, tokens = False):
        """
            get_document_token_pipeline
            
            Takes list of tokens (ie: generated from Azure OCR results), then runs the standard Spacy pipeline against it using a basic model.
        """
        
        if not tokens:
            tokens = self.tokens
        
        ## format token object from list[dict] format to list[str] format
        if type(tokens) == list:
            # print("Tokens are list.")
            tokens_only = [t['text'] for t in tokens]
        elif type(tokens) == dict:
            # print("Tokens are dict.")
            tokens_only = [t['text'] for i, t in tokens]
        else:
            return False
        
        doc = spacy.tokens.doc.Doc(nlp.vocab, words=tokens_only,)
        for name, proc in nlp.pipeline:
            doc = proc(doc)
        return doc
        
    
    def get_ent_stats(self, doc):
        stats = []
        for ent in doc.ents:
            stats.append(
                dict(
                    entity_text  = ent.text, 
                    entity_label = ent.label_
                )
            )
        return stats
    
    def get_nearest_span(self, doc, start, end, steps=3):
        """ get_nearest_span
        
        Finds valid span object withint ~steps offset within doc.  Sometimes tokens are padded with space or punctuation 
        and return "None".  This method seeks a valid span object by searching by steps +/-{i} within the string segment.

        Parameters
        ----------
        doc : Spacy.doc, required
            Spacy document object
        start: int, required
            String offset based on original text.
        end: int, required
            String offset based on original text.
        steps: int, optional
            Steps to search +/i within doc by offset.

        Returns
        -------
        Spacy.span
            Valid span (if found)
        """
        found_span = None
        for start_offset in range(start-steps, start+steps):
            if found_span is not None:
                continue
            for end_offset in range(end-steps, end+steps):
                span_search = doc.char_span(start_offset, end_offset)
                if span_search is not None:
                    # print(f"span was found!!!!!!!!! @ {start_offset} {end_offset}", span_search)
                    found_span = span_search
        return found_span
        
    
    def update_sequence_entities_to_matches(self, doc, matches):
        
        for index, match in enumerate(matches):
            # print("matchid",index, "start", match['segment_offset_start'], "end", match['segment_offset_end'])
            # span = doc.char_span(match['segment_offset_start'], match['segment_offset_end'])   
            ## Trying updated span finding method
            span = self.get_nearest_span(doc, match['segment_offset_start'], match['segment_offset_end'])
            
            # print("match index:", match['entity_name'], "type of span is:", type(span), "span text:", span)
      
            if span == None:
                continue
            # print("Span Entities:", span.ents)
            entities = []
            for entity_sequence in span.ents:
                # print(entity_sequence, entity_sequence.label_, len(entity_sequence), dir(entity_sequence))
                tokens = []
                for token in entity_sequence:
                    # print("doo doo", token.pos_, token.pos, token.text, token.lefts, doc[token.i])
                    tokens.append(
                        dict(
                            text        = token.text,
                            token_index = token.i,
                            pos         = token.pos,
                            pos_        = token.pos_
                        )
                    )

                entities.append(
                    dict(
                        label       = entity_sequence.label_,
                        text        = entity_sequence.text,
                        start_char  = entity_sequence.start_char,
                        end_char    = entity_sequence.end_char,
                        tokens      = tokens
                    )
                )
            matches[index]['entities'] = entities

        return matches
    
    def get_token_id_from_span(self, doc, offset_start, offset_end):
        _
        
    def find_token_from_span(self, doc, segment_offset_start, segment_offset_end, entity_offset_start, entity_offset_end):
        
        start = segment_offset_start + entity_offset_start
        end   = segment_offset_start + entity_offset_end

        token = False
        
        # Iteratively test for token.  Because matching sometimes gets trailing 0's in "$3,000.00", we check a range + 3
        for offset in range(end, end + 4):
            result = doc.char_span(start, offset)
            if type(result) != type(None):
                # print('Token found:', result)
                token = result
        
        return token
    
    def get_entity_matches(self, text):
        match_id = 0
        matches  = []
        for key, pattern in self.extract_regex.items():
            sequence = 0
            # print(key, pattern, pattern['entity'])
            for segment_match in re.finditer(pattern['segment'], text, flags = re.IGNORECASE):
                match_id += 1
                segment_offset_start, segment_offset_end = segment_match.start(), segment_match.end()
                segment_text = segment_match.group()
#                 matches = re.search(pattern['entity'], match)
#                 print("the matches", matches)
                entity_matches = re.search(pattern['entity'], segment_text, flags = re.IGNORECASE)
                entity_offset_start, entity_offset_end = entity_matches.span()
                # print(key, segment_text, entity_matches, dir(entity_matches))
                matches.append(
                    dict(
                        match_id             = match_id,
                        entity_name          = key,
                        segment_text         = segment_text,
                        segment_offset_start = segment_offset_start,
                        segment_offset_end   = segment_offset_end,
                        entity_match         = entity_matches.group(),
                        entity_offset_start  = entity_offset_start,
                        entity_offset_end    = entity_offset_end
                    )
                )
        return matches
    
    def get_segment_matches(self, text):
        match_id = 0
        matches  = []
        for key, pattern in self.extract_segments_regex.items():
            sequence = 0
            for segment_match in re.finditer(pattern['segment'], text, re.MULTILINE | re.IGNORECASE):
                # print("doodoo:", type(segment_match), segment_match)
                match_id += 1
                segment_offset_start, segment_offset_end = segment_match.start(), segment_match.end()
                segment_text = segment_match.group()
                matches.append(
                    dict(
                        match_id             = match_id,
                        entity_name          = key,
                        segment_text         = segment_text,
                        segment_offset_start = segment_offset_start,
                        segment_offset_end   = segment_offset_end,
                    )
                )
        return matches

    def get_best_entity(self, entities, strategy = "first"):
        """ get_best_entity
        
        Finds best match given a strategy.

        Parameters
        ----------
        match : dict, required
            Mixed match results found via  model + regex.
        strategy : str[first|money|date|company], required
            Rule stragegy to use for the entity list returned from the NER.

            first    - Select first entity found
            MONEY    - Select first money result found
            CARDINAL - Select first cardinal result found
            DATE     - Select first date result found
            ORG      - Select most common company name found (special case TBD)

        Returns
        -------
        int : index of best match in entities matches
        """
        
        if strategy not in [e['label'] for e in entities]:
            # if label doesn't exist in current match, safe to skip
            return False
        else:
            for index, entity in enumerate(entities):
                if entity['label'] == strategy:
                    return index # there is a more efficient way to do this with and arg-array function but these entity lists won't be super big

        # if all else fails, return false -- defensive pattern
        return False