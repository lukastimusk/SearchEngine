import sys 
import os 
import math

'''

#STEPS:
1. Process qrels file - turn into dictionary for use
2. process results file - turn into dictionary for use
3. Call calculaiton functions

'''



# *************** STATISTICS CALCULATIONS *****************

def calculate_average_precision(query_id, results_list, qrels_dict, relevant_docs):
    

    # Handle when no relevant docs for query
    # Handle when query_id not in relevant_docs 


    if query_id not in relevant_docs or relevant_docs[query_id] == 0:
        return 0.0  

    num_relevant_retrieved = 0
    sum_precision = 0.0

    for rank, doc_id in enumerate(results_list, start=1):
        
        #return empty dict if no results for query
        relevant = qrels_dict.get(query_id, {}).get(doc_id, 0)

        if relevant > 0:
            num_relevant_retrieved += 1
            p_at_k = num_relevant_retrieved / rank 
            sum_precision += p_at_k
        
    return sum_precision / relevant_docs[query_id]

def calculate_precision_at_k(query_id, results_list, qrels_dict, k):

    if len(results_list) == 0:
        return 0.0
    
    num_relevant_retrieved = 0 

    # STOP AT K
    for doc_id in results_list[:k]:

        #return empty dict if no results for query
        #We getting the value of the mapped docno, which is inside the dict of the query_id:
        # qrels_dict = {query_id: {doc_id: relevance, doc_id2: relevance2, ...}, ...}

        # IF WE CANT FIND IT IN QRELS, RELEVANCE IS 0
        relevance = qrels_dict.get(query_id, {}).get(doc_id, 0)
        if relevance > 0:
            num_relevant_retrieved += 1
        
    # Either divide by k or len(results_list) if less than k
    return num_relevant_retrieved / k




# TO GET NDCG: We need the ideal and then the actual DCG


def calculate_dcg_at_k(query_id, results_list, qrels_dict, k):

    # WE USE GAIN EITHER 0 OR 1 
    total_dcg = 0.0

    # STOP AT K AGAIN
    for rank, doc_id in enumerate(results_list[:k], start=1):
        relevance = qrels_dict.get(query_id, {}).get(doc_id, 0)

        if relevance > 0:
            gain = 1  # Binary relevance
            total_dcg += (gain / math.log2(rank + 1))
    

    return total_dcg
        

def calculate_ideal_dcg_at_k(query_id, results_list, qrels_dict, k):

    # GET ALL RELEVANT DOCS FOR QUERY
    relevant_docs = []

    if query_id in qrels_dict: 

        for doc_id, relevance in qrels_dict[query_id].items():
            if relevance > 0:
                relevant_docs.append(relevance)
    
    # SORT FOR ALL 1s AT START
    relevant_docs.sort(reverse=True)

    total_idcg = 0.0

    for rank, relevance in enumerate(relevant_docs[:k], start =1):
        gain = 1
        total_idcg += (gain / math.log2(rank + 1))
    
    return total_idcg

def calculate_ndcg_at_k(query_id, results_list, qrels_dict, k):

    dcg = calculate_dcg_at_k(query_id, results_list, qrels_dict, k)
    idcg = calculate_ideal_dcg_at_k(query_id, results_list, qrels_dict, k)

    # HANDLE WHEN idcg IS 0 SO NO ERROR
    if idcg == 0:
        return 0.0
    else:
        return dcg / idcg





# *************** MAIN FUNCTION *****************

def main():

    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) != 3:
        print("Incorrect number of arguments.")
        print("Usage: python3 evaluationengine <qrelsfile path> <results file path>")
        sys.exit(1)



    # Arugment paths

    qrels_file_path = sys.argv[1]
    results_file_path = sys.argv[2]


    # Maybe need this
    #qrels_file_path = os.path.join(qrels_file_path, 'qrels.txt')
    #results_file_path = os.path.join(results_file_path, 'results.txt')

    # Check if index path exists
    if not os.path.exists(qrels_file_path):
        print(f"Error: Index path '{qrels_file_path}' does not exist.")
        sys.exit(1)
    
    # Check if queries file exists
    if not os.path.exists(results_file_path):
        print(f"Error: Queries file '{results_file_path}' does not exist.")
        sys.exit(1)


    
    # **** LISTS AND DICTIONARIES TO KEEP TRACK OF ****
    qrels_dict = {}
    topics_found = []
    relevant_docs = {}
    results_dict = {}

    


    # ***** PROCESS QUERY FILE *****

    with open(qrels_file_path, 'r') as qrels_file:

        for line in qrels_file:

            parts = line.strip().split()
            if len(parts) != 4:
                # Skip bad lines 
                continue  

            query_id, ignoreme, doc_id, relevance = parts

            # MAP {TOPIC ID: {doc_id: relevance}, {doc_id: relevance}, ...}

            if query_id not in qrels_dict:
                qrels_dict[query_id] = {}

            # We dont need irrelevant docs 
            if int(relevance) > 0:
                qrels_dict[query_id][doc_id] = int(relevance)

            # List of topics found in QRELS

            if int(relevance) > 0:
                if query_id not in topics_found:
                    topics_found.append(query_id)   
                
                # Map query_id to number of relevant documents
                if query_id not in relevant_docs:
                    relevant_docs[query_id] = 1
                else:
                    relevant_docs[query_id] += 1
                
            
    # ***** PROCESS RESULTS FILE *****

    with open(results_file_path, 'r') as results_file:

        for line in results_file:
            
            parts = line.strip().split()

            # CHECK FOR LENGTH OF PARTS - DOC FORMAT
            if len(parts) != 6:
                print("Results file has incorrect structure")
                print("Aborting program")
                sys.exit(1)


            query_id, ignoreme, doc_id, rank, score, run_id = parts


            # CHECK query_id NUMERIC 

            try:
                int(query_id)
            except ValueError:
                print("Query ID in results file is not an integer.")
                print(f"Query ID found as : {query_id}")
                sys.exit(1)
            
            # CHECK FOR rank NUMERIC 

            try:
                rank = int(rank)
            except ValueError:
                print("Rank in results file is not an integer.")
                print(f"Rank found as : {rank}")

                sys.exit(1)

            # CHECK FOR score DECIMAL 

            try:
                score = float(score)
            except ValueError:
                print("Score in results file is non numeric.")
                print(f"Score found as : {score}")
                sys.exit(1)


    


            # MAP {TOPIC ID: [doc_id1, doc_id2, ...]}

            if query_id not in results_dict:
                results_dict[query_id] = []
            results_dict[query_id].append((doc_id, float(score)))


    # ***** SORT RESULTS *****

    '''
    INSTRUCTIONS: sort each topic's results by the score (descending).
    You should ignore the rank. Break ties in ranking using the docno (in descending lexicographical order)
    '''

    for query_id in results_dict:

        # Sort by score 
        results_dict[query_id].sort(key=lambda x: (x[1], x[0]), reverse=True) 
    

    # ***** OUTPUT ******
    print("GREAT SUCCESS! Evaluation metrics calculated:")


    print("query_id,AP,P@10,NDCG@10,NDCG@1000")


    for query_id in sorted(qrels_dict.keys()):

        results_list_plus_score = results_dict.get(query_id, [])
        results_list = [doc_id for doc_id, score in results_list_plus_score]

        ap = round(calculate_average_precision(query_id, results_list, qrels_dict, relevant_docs),3)
        p_at_10 = round(calculate_precision_at_k(query_id, results_list, qrels_dict, 10),3)
        ndcg_at_10 = round(calculate_ndcg_at_k(query_id, results_list, qrels_dict, 10),3)
        ndcg_at_1000 = round(calculate_ndcg_at_k(query_id, results_list, qrels_dict, 1000),3)


        '''
        Orgiginally, I was producing a file for each output, but I found this was not necessary
        Instead, I print to console in the required format
        '''

        print(f"{query_id}, {ap}, {p_at_10}, {ndcg_at_10}, {ndcg_at_1000}")









            



            


            






if __name__ == '__main__':
    main()
