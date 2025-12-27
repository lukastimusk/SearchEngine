
import sys 
import array
import os



def main():

    inv_index = []
    query_terms = []
    query_map = {}
    query_id_map = {}
    results = []
    docnos = []


    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) != 4:
        print("Incorrect number of arguments.")
        print("Usage: python3 queryengine.py <index path> <queries file path> <results output path>")
        sys.exit(1)



    # Arugment paths

    index_path = sys.argv[1]
    queries_file_path = sys.argv[2]
    results_output_path = sys.argv[3]

    lexicon_path = os.path.join(index_path, 'lexicon.txt')
    inv_index_path = os.path.join(index_path, 'inv_index.bin')
    offset_path = os.path.join(index_path, 'inv_index_offsets.bin')
    docnos_path = os.path.join(index_path, 'docnos.txt')


    # **** READ IN FILES *****

    # TURN LINES INTO DICT 
    with open(queries_file_path, 'r') as queries:
        lines = [line.strip() for line in queries if len(line) != 0]

        for i in range(0, len(lines)-1, 2):
            topic_num = int(lines[i])
            topic_query = lines[i+1]
            query_map[topic_num] = topic_query

    # TURN LEXICON TO DICT FOR O(1) LOOKUP - MAP TERM TO ID 

    with open(lexicon_path, 'r') as lexicon:
        for line in lexicon:
            both = line.strip().split('\t') #NOW ITS A LIST [id, token]
            token_id = int(both[0])
            token = both[1]
            query_id_map[token] = token_id
    # INVERTED INDEX 

    inv_index_offsets = array.array("I")
    with open(offset_path, 'rb') as offset_file:

        offset_path_size = os.path.getsize(offset_path)

        inv_index_offsets.fromfile(offset_file, offset_path_size // 4) # I KNOW ITS ALL 4 BYTE INTS :) now I got number of ints in file

    
    # DOC NOS 

    with open(docnos_path, 'r') as docnos_file:
        for line in docnos_file:
            docnos.append(line.strip())


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
                    tokens.append( token )
                    
                start = i + 1

            i = i + 1

        if start != i :
            tokens.append(text[start:i])

    def TokenizeStrings( strings, tokens ):
        for string in strings:
            Tokenize( string, tokens )



    # *************** MAIN LOGIC **************


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
                    postings_list.append(docno)
                    postings_list.append(count)
                
                postings[id] = postings_list
            
            
            # CHECK IF I RETRIEVED ANY POSTINGS 

            if len(postings) == 0:
                print(f"Error: No documents found for {topic_query}. Skipping this topic.")
                continue
            




            # *************** BOOLEAN-AND RETRIEVAL **************


            # NOTE: I was getting a key error for so long here, finally 
            # realized it was because I was not checking if the term existed in postings before trying to access it.


            # FILTER OUT TERMS NOT IN POSTINGS
            valid_terms = [term for term in current_query_token_ids if term in postings]

            # SORT TERMS ACCORDING TO POSTINGS LENGTH 
            sorted_query_terms = sorted(valid_terms, key=lambda term_id: len(postings[term_id])//2)


            #CHECK IF WE HAVE ANY SORTED QUERY TERMS 
            if len(sorted_query_terms) == 0:
                print(f"Error: No valid postings found for topic {topic_num}, Skipping this topic.")
                continue

            # ******* FROM LECTURE *******
            results_set = []

            #start with shortest postings for initialization
            shortest = postings[sorted_query_terms[0]]
            i = 0 
            while i < len(shortest):
                results_set.append(shortest[i])
                i += 2
            
            # NOW RUN INTERSECTION 
            t = 1

            while t != len(sorted_query_terms):
                term_id = sorted_query_terms[t]
                current_postings = postings[term_id]
            
                new_results = []
                i = 0 
                j = 0 

                while i < len(results_set) and j < len(current_postings):
                    if results_set[i] == current_postings[j]:
                        new_results.append(results_set[i])
                        i += 1
                        j += 2
                    elif results_set[i] < current_postings[j]:
                        i += 1
                    else:
                        j += 2

                results_set = new_results
                t += 1

            # Now I have results_set, need create our output arrays 

            document_docnos = []
            ranks = []
            current_rank = 0
            run_tag = 'lemtimusAND'
            num_results = len(results_set)

            # ALL RESULTS FORMAT -> (topicID, Q0, docno, rank, score, runTag)


            # Enumerate for rank, score is inverse rank (from maybe 1000?, maybe len(results_set)?)
            for rank, doc_id in enumerate(results_set):


                score = num_results - rank - 1
                docno = docnos[doc_id]

                current_result = f"{topic_num} Q0 {docno} {rank + 1} {score} {run_tag}"


                # NEED EXTRA topic_num, score, TO SORT BY LATER
                all_results.append((topic_num, score, current_result))
    

    # SORT ALL RESULTS BY TOPIC NUM, THEN SCORE
    all_results.sort(key=lambda x: (x[0], -x[1])) 

    try: 
        with open(results_output_path, 'w') as results_file:
            for topic_num, score, result_line in all_results:
                results_file.write(result_line + '\n')
            print(f"SUCCESS: Results written to '{results_output_path}'")
    except Exception as e:
        print(f"Error: Couldn't write to file: '{results_output_path}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()






            






                                
                                



