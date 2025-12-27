
# AKNOWLEDGEMENTS:
# Most of my processing logic for the index, query terms and results is adapted from my homework 4 - BM25 search retrieval



import sys 
import array
import os
import math
from datetime import datetime
import zlib
import time
import re


def main():

    print("INITIATING MAIN")

    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) != 2:
        print("Incorrect number of arguments.")
        print("Usage: python3 bm25-adapted.py <index path>")
        sys.exit(1)


    # Arugment paths

    index_path = sys.argv[1]

    # READ IN ALL FILES 
    tag_collection = set(["<SECTION>", "</SECTION>", "<LENGTH>", "</LENGTH>", "<HEADLINE>", "</HEADLINE>", "<BYLINE>", "</BYLINE>",
                        "<DOC>", "</DOC>", "<DOCNO>", "</DOCNO>", "<TEXT>", "</TEXT>","<DOCID>", "</DOCID>", "<DATE>", "</DATE>",
                          "<br>", "<br/>", "</br>", "<P>", "</P>", "<div>", "</div>", "<html>", "</html>", "<body>", "</body>"])

    punctuation_collection = set(['.', "!", "?"])

    inv_index = []
    query_id_map = {}
    docnos = []
    doc_lengths = []


    # Tuning Params:
    k1 = 1.2
    b = 0.75



    lexicon_path = os.path.join(index_path, 'lexicon.txt')
    inv_index_path = os.path.join(index_path, 'inv_index.bin')
    offset_path = os.path.join(index_path, 'inv_index_offsets.bin')
    docnos_path = os.path.join(index_path, 'docnos.txt')
    doclengths_path = os.path.join(index_path, 'doc_lengths.txt')
    docs_path = os.path.join(index_path, 'docs.bin')
    offsets_path = os.path.join(index_path, 'offsets.bin')


    # ********************* READ IN FILES *********************


    # TURN LEXICON TO DICT FOR O(1) LOOKUP - MAP TERM TO ID 

    try:
        with open(lexicon_path, 'r') as lexicon:
            for line in lexicon:
                both = line.strip().split('\t') #NOW ITS A LIST [id, token]

                if len(both) != 2:
                    print(f"Error: Lexicon file line malformed: at '{line.strip()}'")
                    continue

                token_id = int(both[0])
                token = both[1]
                query_id_map[token] = token_id
    except Exception as e:
        print(f"Error: Couldn't read lexicon file at '{lexicon_path}': {e}")
        print(f"Line is at {line} with token being {both[0]}")
        exit(1)
        #Format: {term: term_id}
        
    # INVERTED INDEX 

    inv_index_offsets = array.array("I")
    with open(offset_path, 'rb') as offset_file:

        offset_path_size = os.path.getsize(offset_path)

        inv_index_offsets.fromfile(offset_file, offset_path_size // 4) # I KNOW ITS ALL 4 BYTE INTS :) now I got number of ints in file

        #Format: array of offsets 
    
    
    # DOC NOS 

    with open(docnos_path, 'r') as docnos_file:
        for line in docnos_file:
            docnos.append(line.strip())

    
    # DOC LENGTHS 

    with open(doclengths_path, 'r') as doclengths_file:
        for line in doclengths_file:
            doc_lengths.append(int(line.strip()))
    
    # AVERAGE DOC LENGTH
    total_length = sum(doc_lengths)
    avg_doc_length = total_length / len(doc_lengths)

    
    # Get Offsets 

    with open(offsets_path, 'rb') as offsets_file:

        offsets_path_size = os.path.getsize(offsets_path)

        doc_offsets = array.array("I")
        doc_offsets.fromfile(offsets_file, offsets_path_size // 4) # I KNOW ITS ALL 4 BYTE INTS :) now I got number of ints in file



    # ********************** INTERACTIVE LOOP ************************

    print("Welcome to Lukas's interactive query engine!")

    while True: 
        user_query = input("Enter your query for awesome retrieval or type 'q' to quit: ")

        if user_query.lower() == 'q':
            print("Now exiting the interactive query engine.")
            print("Goodbye!")
            break
        
        if not user_query.strip():
            print("Error: you gotta type something homie")
            continue

        start_time = time.time()

        query_results = bm25(user_query, inv_index_offsets, docnos, query_id_map, doc_lengths, avg_doc_length, docs_path, doc_offsets, inv_index_path, k1=1.2, b=0.75)


        #Catch no results 
        if not query_results:
            print("No results found for this query.\n")
            continue

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Text retrieval processed in {elapsed_time:.2f} seconds.\n")


        while True:
            user_input = input("Enter rank to view document, 'n' for new query, or 'q' to quit: ").strip().lower()

            if user_input == 'q':
                print("Exiting the interactive query engine.")
                print("Goodbye!")
                sys.exit(0)
            
            elif user_input == 'n':
                break #Back to query prompt

            else: # Hopfully a number

                try:
                    rank = int(user_input)
                    if rank < 1 or rank > len(query_results):
                        print(f"Error: Rank must be between 1 and 10")
                        continue
                    
                    # Display raw doc 
                    print(f"\n--- Full Document for Rank {rank} ---")
                    selected_result = query_results[rank - 1]

                    print(selected_result['full_doc'])

                    # Third loop for back option 

                    while True:
                        doc_input = input("Enter rank to view document,'b' to go back, 'n' for new query, or 'q' to quit: ").strip().lower()

                        if doc_input == 'q':
                            print("Exiting the interactive query engine.")
                            print("Goodbye!")
                            sys.exit(0)
                        
                        elif doc_input == 'b':

                            for result in query_results:
                                print(f"{result['rank']}. {result['headline']} ({result['date']}) \n {result['snippet']} ({result['docno']})\n")
                            break
                        
                        elif doc_input == 'n':
                            break # New query
                        else:
                            print("Error: Invalid input. Please enter 'b' to go back, 'n' for new query, or 'q' to quit.")






                except ValueError:
                    print("Error: Invalid input. Please enter a rank number, 'n' for new")
                    


            





def bm25(user_query, inv_index_offsets, docnos, query_id_map, doc_lengths, avg_doc_length, docs_path, doc_offsets, inv_index_path, k1, b):
    

    # ********************************** TOKENIZER ******************************

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

                    tokens.append( token )
                    
                start = i + 1

            i = i + 1

        if start != i :
            tokens.append(text[start:i])

    def TokenizeStrings( strings, tokens ):
        for string in strings:
            Tokenize( string, tokens )

    
    # **** Headline Extractor 3000 ****

    def extract_headline_from_doc(documentz):
        lines = documentz.split('\n')

        # find the headline & remooooove
        for line in lines:
            if line.lower().startswith("headline: "):
                headline = line[10:].strip()
                return headline
        return "No Headline Found"
    
    # **** Date extractor 3000 **** 

    def extract_date(docno):
        try:
            date_str = docno[2:8]
            date = datetime.strptime(date_str, "%m%d%y").date()
            return date.strftime("%B %d, %Y")
        except:
            print("Error: Could not parse date from DOCNO")
            return ""

    
    # *************************** QUERY BIASED SUMMARY *************************

    def split_into_sentences(text):


        #Edit: I tried this without regex and was having a tough go 
        # I decided just to use regex to split on punctuation followed by space

        #Also extract tags

        # STRIP TAGS AND CLEAN WHITESPACE
        text_without_tags = re.sub(r'<[^>]+>', '', text)
        text_cleaned = re.sub(r'\s+', ' ', text_without_tags).strip()

        #Now split on punctuation followed by a space -> 'hello.com' not split, 'hello. com' Is split
        sentences = re.split(r'([.!?])\s+', text_cleaned)

        reconstructed_sentences = []

        # Sentences come out split on punctuation, need to reconstruct -> odd indexes are punctuation
        for i in range(0, len(sentences)-1, 2):
            if i + 1 < len(sentences):
                reconstructed_sentences.append(sentences[i] + sentences[i + 1])

        # Check for any last sentence without punctuation
        if len(sentences) % 2 != 0:
            reconstructed_sentences.append(sentences[-1].strip())
    
        
        # KEEP TRACK OF TOKENS AND ORIGINAL TEXT
        sentence_and_tokens = []

        for sentence in reconstructed_sentences:
            tokens_in_sentence = []
            Tokenize(sentence, tokens_in_sentence)

            sentence_and_tokens.append({'text':sentence, 'tokens': tokens_in_sentence})

        return sentence_and_tokens

    def query_biased_summary(current_doc, current_query_tokens):
        
        #Steps:
        # 1. Get document from docs.bin and headline for h
        # 2. Break document into sentences
        # 3. Score sentences based on query term presence
        # 4. Return top scoring sentence (maybe 1 or 2???) as snippet

        # Map sentence to score 
        scores = {}

        headline = extract_headline_from_doc(current_doc)
        headline_ls = headline.lower().strip()

        # From our index engine, I store metadata, I only want the text body
        parts = current_doc.split("raw document:\n", 1)
        if len(parts) == 2:
            raw_content = parts[1]
        else:
            raw_content = current_doc


        sentences_and_tokens = split_into_sentences(raw_content)

        # CATCH NO CONTENT
        if not sentences_and_tokens:
            return "ERROR: NO CONTENT FOUND"
        

        # FOR O(1) Lookup
        query_set = set(current_query_tokens)

        for indx, data in enumerate(sentences_and_tokens):

            c, d, k, h, l = 0, 0, 0, 0, 0

            sentence_tokens = data['tokens']
            if not sentence_tokens:
                continue

            plaintext_sentence = data['text']

            # if sentence is header, h = 1 
            # if sentence is the first sentence in the doc, l =2, if its the second l=1 else l=0
            # c is the number of words in the sentence that are query terms including repetitions
            # d is the number of distinct occurences of query terms in the sentence
            # k is the length of the longest sequence of query terms in the sentence

            distinct_terms = []
            current_seq_len = 0

            for token in sentence_tokens:
                if token in query_set:
                    c += 1
                    distinct_terms.append(token)
                    current_seq_len += 1
                    k = max(k, current_seq_len)
                else:
                    current_seq_len = 0

            d = len(set(distinct_terms))

            if indx == 0:
                l = 2
            elif indx == 1:
                l = 1
            else:
                l = 0

            sentence_lower = plaintext_sentence.lower().strip()
            if sentence_lower == headline_ls:
                h = 1
            
            sentence_score = c+d+h+k+l
            
            scores[plaintext_sentence] = sentence_score
        
        # Get highest scoring sentence
        best_sentence = max(scores, key=scores.get)

        return best_sentence
           









    # **************************** MAIN LOGIC ******************************

    #Most of this is from my homework 2 - Boolean AND Retrieval

    # let query_terms be a list of unique query terms ordered from shortest to longest postings:
    # tokenize query terms, and look up IDs

    current_query_tokens = []


    with open(inv_index_path, 'rb') as inv_index_file:
            

        tokens = []
        TokenizeStrings([user_query], tokens)
        current_query_tokens = tokens

        # NOW TOKENS -> IDS
            
        current_query_token_ids = []
        for token in current_query_tokens:
            if token in query_id_map:
                token_id = query_id_map[token]
                current_query_token_ids.append(token_id)


        # CHECK IF ANY VALID QUERY TERMS FOUND 

        if len(current_query_token_ids) == 0:
            print(f"Error: No valid query terms found for this query")
            return []

        # retieve all postings 
        # (go into offsets)

        postings = {}
        # Need num of docs containing each term
        doc_frequencies = {}

        for id in current_query_token_ids:

            if id >= len(inv_index_offsets) - 1:
                print(f"WARNING: term ID {id} is out of bounds in the offsets file.")
                continue
        
            start_offset = inv_index_offsets[id]
            end_offset = inv_index_offsets[id + 1]

            byte_length = end_offset - start_offset
            # Find number of postings, gonna be length / 8 bc theyre all 4
            num_postings = byte_length // 8 

            inv_index_file.seek(start_offset)

            #CHECK FILE IS SEEKABLE
            if inv_index_file.tell() != start_offset:
                print(f"Error: Could not seek to correct spot: {id}.")
                continue

            postings_list = []

            # GENERATE ALL POSTINGS
            for i in range(num_postings):
                docno = int.from_bytes(inv_index_file.read(4), byteorder='little')
                count = int.from_bytes(inv_index_file.read(4), byteorder='little')

                #Changed this to appending tuple instead, just easier to manage
                postings_list.append((docno, count))

            
            postings[id] = postings_list

            #CAPTURE NUMBER OF DOCS CONTANING TERM I FOR IDF L8R
            doc_frequencies[id] = num_postings
        




        # *************** BM25 RETRIEVAL **************

        #Number of docs N:
        N = len(docnos)
        
        document_scores = {}

        for term_id in postings:
            docs_containing_term = doc_frequencies[term_id]

            # IDF LOGIC 
            idf = math.log((N - docs_containing_term + 0.5) / (docs_containing_term + 0.5))

            # TERM FREQ LOGIC 
            
            for doc_id, term_freq in postings[term_id]:
                if doc_id not in document_scores:
                    document_scores[doc_id] = 0.0
                
                
                doc_length = doc_lengths[doc_id]

                k = k1 * ((1 - b) + b * (doc_length / avg_doc_length))


                tf = term_freq / (term_freq + k)

                # Score applies to all terms. If multiple terms in doc, they add up
                document_scores[doc_id] += idf * tf
        
        # Now sort and take top 10
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
        top_10 = sorted_docs[:10]

        results_list = []

        # Read my old docs file to extract headlines and dates
        with open(docs_path, 'rb') as docs_file:
            rank = 1

            for doc_id, score in top_10:
                

                docno = docnos[doc_id]

                #Read document 
                start_offset = doc_offsets[doc_id]
                end_offset = doc_offsets[doc_id + 1]

                #start at the top
                docs_file.seek(start_offset)
                bin_current_doc = docs_file.read(end_offset - start_offset)

                # Get headline and date
                current_doc = zlib.decompress(bin_current_doc).decode('utf-8')

                current_doc_headline = extract_headline_from_doc(current_doc)
                current_doc_date = extract_date(docno)

                # *** CALL QUERY BIASED SUMMARY *** 
                snippet = query_biased_summary(current_doc, current_query_tokens)

                # ***** OUTPUT *****

                results_list.append({'rank': rank,'headline': current_doc_headline,'date': current_doc_date, 'snippet': snippet, 'docno': docno, 'full_doc': current_doc})

                # ***** OUTPUT *****
                print(f"{rank}. {current_doc_headline} ({current_doc_date}) \n {snippet} ({docno})\n")


                rank += 1

    return results_list





if __name__ == "__main__":
    main()