
# AKNOWLEDGEMENTS:
# Most of my processing logic for the index, query terms and results is adapted from my homework 2 - Boolean AND Retrieval
# The BM25 scoring logic is completely new



import sys 
import array
import os
import math
from nltk.stem import PorterStemmer  # pip install nltk



def main():

    inv_index = []
    query_terms = []
    query_map = {}
    query_id_map = {}
    results = []
    docnos = []
    doc_lengths = []

    # Tuning Params:
    k1 = 1.2
    b = 0.75

    #Stemmer 
    stemmer = PorterStemmer()
    stemmer.mode = PorterStemmer.ORIGINAL_ALGORITHM



    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) != 4:
        print("Incorrect number of arguments.")
        print("Usage: python3 bm25.py <index path> <queries file path> <results output path>")
        sys.exit(1)



    # Arugment paths

    index_path = sys.argv[1]
    queries_file_path = sys.argv[2]
    results_output_path = sys.argv[3]

    lexicon_path = os.path.join(index_path, 'lexicon.txt')
    inv_index_path = os.path.join(index_path, 'inv_index.bin')
    offset_path = os.path.join(index_path, 'inv_index_offsets.bin')
    docnos_path = os.path.join(index_path, 'docnos.txt')
    doclengths_path = os.path.join(index_path, 'doc_lengths.txt')


    # ********************* READ IN FILES *********************

    # TURN LINES INTO DICT 
    with open(queries_file_path, 'r') as queries:
        lines = [line.strip() for line in queries if len(line) != 0]

        for i in range(0, len(lines)-1, 2):
            topic_num = int(lines[i])
            topic_query = lines[i+1]
            query_map[topic_num] = topic_query

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
        for string in strings:
            Tokenize( string, tokens )

    

    # **************************** MAIN LOGIC ******************************

    #Most of this is from my homework 2 - Boolean AND Retrieval

    # let query_terms be a list of unique query terms ordered from shortest to longest postings:
    # tokenize query terms, and look up IDs

    current_query_tokens = []
    all_results = []

    with open(inv_index_path, 'rb') as inv_index_file:
            

        for topic_num, topic_query in query_map.items():
            tokens = []
            TokenizeStrings([topic_query], tokens)
            current_query_tokens = tokens

            # NOW TOKENS -> IDS
                
            current_query_token_ids = []
            for token in current_query_tokens:
                if token in query_id_map:
                    token_id = query_id_map[token]
                    current_query_token_ids.append(token_id)
                else:
                    print(f"Error: count not find {token} in any of the documents. Omitting from the search")
                    continue

            # CHECK IF ANY VALID QUERY TERMS FOUND 

            if len(current_query_token_ids) == 0:
                print(f"Error: No valid query terms found for topic {topic_num}. Skipping this topic.")
                continue

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
            
            
            # CHECK IF I RETRIEVED ANY POSTINGS 

            if len(postings) == 0:
                print(f"Error: No documents found for {topic_query}. Skipping this topic.")
                continue
            




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
            
            # Now sort and take top 1000
            sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
            top_1000 = sorted_docs[:1000]

            for rank, (doc_id, score) in enumerate(top_1000, start=1):
                docno = docnos[doc_id]
                current_result = f"{topic_num} Q0 {docno} {rank} {score:.4f} lemtimusBM25"
                all_results.append((topic_num, score, current_result))
    
    # WRITE ALL RESULTS TO FILE
    all_results.sort(key=lambda x: (x[0], -x[1]))  # Sort by topic_num, then by score descending

    try: 
        with open(results_output_path, 'w') as results_file:
            for topic_num_, score, result_line in all_results:
                results_file.write(result_line + '\n')
            print("GREAT SUCCESS: Results written to", results_output_path)
    except Exception as e:
        print(f"Error: Couldn't write to file: '{results_output_path}': {e}")
        sys.exit(1)




if __name__ == "__main__":
    main()






            






                                
                                





