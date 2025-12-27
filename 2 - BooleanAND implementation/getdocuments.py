

#They pass in index path, (ID or DOCNO), (020391 or LA-193891)
import array
import zlib
import gzip
import os
import sys
import csv
from datetime import datetime

def main():
    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) != 4:
        print("Incorrect number of arguments.")
        print("Usage: python getdocuments.py <index path> <docno|id> <value>")
        sys.exit(1)


    user_path = sys.argv[1]
    id_type = sys.argv[2].lower()
    id_entered = sys.argv[3]

    if id_type not in ["docno", "id"]:
        print("Error: Second argument must be either 'docno' or 'id'.")
        sys.exit(1)

    # ****** METADATA VARS ********
    docno = ""
    internal_id = -1
    date = ""
    headline = ""
    raw_doc = ""


    # **** PATHS ****
    metadata_path = os.path.join(user_path, "metadata.tsv")
    offsets_path = os.path.join(user_path, "offsets.bin")
    docs_path = os.path.join(user_path, "docs.bin")
    docnos_path = os.path.join(user_path, "docnos.txt")


    # 2. Convert ID to a docno - use offset

    id_to_docno = {}
    docno_to_id = {}


    # **** CREATE DICTIONARY TRANSLATIONS **** 

    #with open(metadata_path, 'r', encoding='utf-8') as meta_file:
    #   reader = csv.reader(meta_file, delimiter='\t')

    try:
        with open(docnos_path, 'r', encoding='utf-8') as docnos_file:

            for line_num, line in enumerate(docnos_file):
                docno_entry = line.strip()

                if docno_entry:
                    docno_to_id[docno_entry] = line_num
                    id_to_docno[line_num] = docno_entry

    except Exception as e:
        print(f"Error: Couldn't read file: '{docnos_path}': {e}")
        sys.exit(1)


    # ** From dictionaries, set internal_id and docno translate our docnos to index and vice versa**

    try:
        if id_type == "id":
            internal_id = int(id_entered)

            if internal_id not in id_to_docno:
                print(f"Error: ID '{internal_id}' not found in index.")
                sys.exit(1)

            docno = id_to_docno[internal_id]

        else:
            docno = id_entered

            if docno not in docno_to_id:
                print(f"Error: ID '{docno}' not found in keys.")
                sys.exit(1)

            internal_id = docno_to_id[docno]

    except ValueError:
        print("Error: Invalid ID format - must be an integer")
        sys.exit(1)
    except:
        print("Error: Invalid ID format")
        sys.exit(1)



    # 4. Use ID to find offset, then read from docs.bin

    offsets = array.array('I')
    with open(offsets_path, 'rb') as offsets_file:
        num_offsets = os.path.getsize(offsets_path) // offsets.itemsize              
        offsets.fromfile(offsets_file, num_offsets)

        num_docs = num_offsets - 1

        if internal_id >= num_docs:
            print(f"Error: ID '{internal_id}' is out of the range, with max ID being {num_docs - 1}.")
            sys.exit(1)
        
        else:
            with open(docs_path, "rb") as f:
                beginning_byte = offsets[internal_id]
                num_bytes = offsets[internal_id + 1] - beginning_byte
                f.seek(beginning_byte)
                zipped_doc = f.read(num_bytes)
                raw_doc = zlib.decompress(zipped_doc).decode()


    # **** OUTPUT ****

    print(raw_doc)

if __name__ == "__main__":
    main()