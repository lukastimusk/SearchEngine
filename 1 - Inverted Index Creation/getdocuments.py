

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