
import array
import zlib
import re
import gzip
import os
import sys
from datetime import datetime
from nltk.stem import PorterStemmer  # pip install nltk



def main():
    alldocs = []
    docnos = []
    offsets = array.array('I')  # offsets for docs.bin
    inv_index_offsets = array.array('I') # offsets for inv_index
    internalid = 0  
    lexicon = {}
    inv_index = {}
    doc_lengths = []
 

    # Vars for zip parsing 
    inside_doc = False
    inside_headline = False

    # Create the stemmer
    stemmer = PorterStemmer()
    stemmer.mode = PorterStemmer.ORIGINAL_ALGORITHM


    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) == 1:
        print("You have entered no arguments for this progam. This program allows you to enter your input file of text, with an output directory in which the output will be stored.  Please enter your arguments in the following order: \n")
        print("Usage: python3 porter_indexengine.py <inputfile> <outputdirectory>")
        sys.exit(1)
    elif len(sys.argv) != 3:
        print("Incorrect number of arguments.")
        print("Usage: python porter_indexengine.py <inputfile> <outputdirectory>")
        sys.exit(1)


    # ***** Establish path variables and Error Catching *****
    input_file_path = sys.argv[1]
    output_directory = sys.argv[2]


    if not os.path.exists(input_file_path):
        print(f"Error: We couldn't find: '{input_file_path}' as a path.")
        sys.exit(1)


    if os.path.exists(output_directory):
        print(f"Error: the directory '{output_directory}' already exists .")
        sys.exit(1)

    try:
        os.makedirs(output_directory)
    except OSError as e:
        print(f"Error: Unable to create directory '{output_directory}': {e}")
        sys.exit(1)

    #  ************************** HELPER FUNCTIONS ***************************

    def extract_date(docno):
        try:
            date_str = docno[2:8]
            date = datetime.strptime(date_str, "%m%d%y").date()
            return date.strftime("%B %d, %Y")
        except:
            print("Error: Could not parse date from DOCNO")
            return ""
    

    # ************* TOKENIZER *********

    # This function takes a string and breaks it up into "words".  
    # It returns an array of these words.
    # text is the string to tokenize and tokens is a list to which tokens will be appended
    def Tokenize(text, tokens):
        text = text.lower() 

        start = 0 
        i = 0

        for currChar in text:
            if not currChar.isdigit() and not currChar.isalpha() :
                if start != i :
                    token = text[start:i]

                    # STEMING NOW HERE
                    token_stemmed = stemmer.stem(token)

                    tokens.append( token_stemmed )
                    
                start = i + 1

            i = i + 1

        if start != i :
            # STEM LAST TOKEN
            stemmed_last_token = stemmer.stem(text[start:i])
            tokens.append(stemmed_last_token)

    def TokenizeStrings( strings, tokens ):


        for s2 in strings:
            Tokenize( s2, tokens )

   
    # ************* convert tokens to ids *********
    
    def convert_tokens_to_ids(tokens, lexicon):
        token_ids = []
        for token in tokens:
            if token in lexicon:
                token_ids.append(lexicon[token])
            else:
                id = len(lexicon)
                lexicon[token] = id
                token_ids.append(id)  
        return token_ids

    # ************* count words *********

    def count_words(token_ids):
        word_count = {}
        for id in token_ids:
            if id in word_count:
                word_count[id] += 1
            else:
                word_count[id] = 1
        return word_count


    # ************ add to postings *********
    
    def add_to_postings(word_count, doc_id, inv_index):
        for token_id in word_count:
            count = word_count[token_id] 

            if token_id not in inv_index:
                inv_index[token_id] = []
            inv_index[token_id].append((doc_id, count))

    # ******** HELPER CLEANING FUNCITON *******

    def clean_tag(s):
        cleaned = re.sub(r'<[^>]+>', '', s)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()



# ************************ MAIN DOCUMENT PARSE ***********************

    try:
        with gzip.open(input_file_path, 'rt') as gz_file:


            # LOOP FOR EACH LINE IN GZ FILE
            for line in gz_file:

                if  '<DOC>' in line:  # see <DOC>, create new current doc []
                    inside_doc = True
                    current_doc = [line]
                    inside_headline = False
                    inside_text = False
                    inside_graphic = False
                    current_headline = ""
                    headline_parts = []
                    text_parts = []
                    graphic_parts = []

                    docno = ""
                    date = ""


                elif '</DOC>' in line and inside_doc:  # see close </DOC>, append to alldocs
                    current_doc.append(line)

                    if docno:
                        date = extract_date(docno)
                    
                    metadata_string = "docno: " + docno + "\ninternal_id: " + str(internalid) + "\ndate: " + date + "\nheadline: " + current_headline + "\nraw document:\n"
                    inside_doc = False
                    alldocs.append(metadata_string + "".join(current_doc))
                    internalid += 1



                    # **** TOKENIZATION AND PROCESSING 
                    text_cleaned = " ".join(text_parts).strip()
                    graphic_cleaned = " ".join(graphic_parts).strip()
                    headline_cleaned = " ".join(headline_parts).strip()


                    tokens = []

                    

                    TokenizeStrings([text_cleaned, graphic_cleaned, headline_cleaned], tokens)

                    doc_length = len(tokens)
                    doc_lengths.append(doc_length)

                    # ADD HERE:

                    # token_ids = toker_to_ids(tokens, lexicon)
                    token_ids = convert_tokens_to_ids(tokens, lexicon)

                    # word count = count_words(token_ids)
                    word_count = count_words(token_ids)

                    # add_to_postings(word_count, doc_id, inv_index -> dict {tokenid:posting}
                    add_to_postings(word_count, internalid-1, inv_index)


                    

                    




                
                elif inside_doc:
                    # Append every line for raw doc
                    current_doc.append(line)

                
                    if '<DOCNO>' in line:
                        docno = clean_tag(line)
                        docnos.append(docno)

                    # *** HEADLINE ###

                    if '<HEADLINE>' in line:
                        inside_headline = True

                        #CHECK IF ANY TEXT IN THE LINE 
                        if '</HEADLINE>' in line:
                            headline_text = clean_tag(line)
                            if headline_text:
                                current_headline += headline_text + " "
                            inside_headline = False
                            headline_parts.append(headline_text)

                        else:
                            headline_text = clean_tag(line)
                            if headline_text:
                                current_headline += headline_text + " "
                                headline_parts.append(headline_text)


                    elif '</HEADLINE>' in line and inside_headline:
                        inside_headline = False

                        #CHECK IF ANY TEXT IN THE LINE 
                        headline_text = clean_tag(line)
                        if headline_text:
                            current_headline += headline_text + " "
                            headline_parts.append(headline_text)

                    
                    elif inside_headline:

                        headline_text = clean_tag(line.strip())
                        if headline_text:
                            current_headline += headline_text + " "
                            headline_parts.append(headline_text)
                    

                    #*** TEXT ***

                    if '<TEXT>' in line:
                        if '</TEXT>' in line:
                            cleaned_text = clean_tag(line)
                            if len(cleaned_text) != 0:
                                text_parts.append(cleaned_text)
                        else:
                            inside_text = True 
                            cleaned_text = clean_tag(line)
                            if len(cleaned_text) != 0:
                                text_parts.append(cleaned_text)
                    
                    elif '</TEXT>' in line and inside_text == True:
                        cleaned_text = clean_tag(line)
                        if len(cleaned_text) != 0:
                            text_parts.append(cleaned_text)
                        inside_text = False 
                    
                    elif inside_text == True:
                        cleaned_text = clean_tag(line)
                        if len(cleaned_text) != 0:
                            text_parts.append(cleaned_text)

                     # *** GRAPHIC ***

                    if '<GRAPHIC>' in line:
                        if '</GRAPHIC>' in line:
                            cleaned_graphic = clean_tag(line)
                            if len(cleaned_graphic) != 0:
                                graphic_parts.append(cleaned_graphic)
                        else:
                            inside_graphic = True 
                            cleaned_graphic = clean_tag(line)
                            if len(cleaned_graphic) != 0:
                                graphic_parts.append(cleaned_graphic)
                    
                    elif '</GRAPHIC>' in line and inside_graphic == True:
                        cleaned_graphic = clean_tag(line)
                        if len(cleaned_graphic) != 0:
                            graphic_parts.append(cleaned_graphic)
                        inside_graphic = False 
                    
                    elif inside_graphic == True:
                        cleaned_graphic = clean_tag(line)
                        if len(cleaned_graphic) != 0:
                            graphic_parts.append(cleaned_graphic)
                    
    except gzip.BadGzipFile:
        print(f"Error: The file '{input_file_path}' is not a valid gzip file.")
        print("Please ensure you are providing a properly compressed .gz file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Couldn't read file: '{input_file_path}': {e}")
        sys.exit(1)





    # ********* ENCODE AND WRITE TO BINARY FILES ************

    assert offsets.itemsize >= 4

    try:
        with open(os.path.join(output_directory, "docs.bin"), 'wb') as doc_file:
            offset = 0 

            for d in alldocs:
                zipped_d = zlib.compress( d.encode() )
                doc_file.write(zipped_d)
                offsets.append(offset)
                offset += len(zipped_d)
            
            offsets.append(offset) 


        with open(os.path.join(output_directory,"offsets.bin"), 'wb') as offsets_out:
            offsets.tofile(offsets_out)

        with open(os.path.join(output_directory,"docnos.txt"), 'w', encoding='utf-8') as docnos_out:
            for docno in docnos:
                docnos_out.write(f"{docno}\n")


    except IOError as e:
            print(f"Error: Unable to write output files: {e}")
            sys.exit(1)



    try: 
        with open(os.path.join(output_directory, "doc_lengths.txt"), 'w') as lengths_out:
            for length in doc_lengths:
                lengths_out.write(f"{length}\n")



        # I probablu dont need the term_id, because its just the line number -1
        with open(os.path.join(output_directory, "lexicon.txt"), 'w', encoding='utf-8') as lexicon_out:
                for term, term_id in sorted(lexicon.items(), key=lambda x:x[1]):
                    #        lex_out.write(f"{term_id}\t{term}\n")
                    lexicon_out.write(f"{term_id}\t{term}\n")

        with open(os.path.join(output_directory, "inv_index.bin"), 'wb') as inv_index_out:
            offset = 0
            for term_id in sorted(inv_index.keys()):
                postings = inv_index[term_id]

                # Keep track of offset for invindex
                inv_index_offsets.append(offset)
                


                for doc_id, count in postings:
                    inv_index_out.write(doc_id.to_bytes(4, byteorder='little'))
                    inv_index_out.write(count.to_bytes(4, byteorder='little'))
                    offset += 8
                
            # FINAL OFFSET
            inv_index_offsets.append(offset)
        
        with open(os.path.join(output_directory, "inv_index_offsets.bin"), 'wb') as inv_index_offsets_out:
            inv_index_offsets.tofile(inv_index_offsets_out)


    except IOError as e:
        print(f"Error: Unable to write index files: {e}")
        sys.exit(1)
        

    # ********* PRINT SUCCESS *********
    print(f" {len(alldocs)} documents just processd.")
    print(f"Sending written to: {output_directory}")


if __name__ == "__main__":
    main()