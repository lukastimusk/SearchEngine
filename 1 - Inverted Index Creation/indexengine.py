
import array
import zlib
import re
import gzip
import os
import sys
from datetime import datetime

def main():
    alldocs = []
    docnos = []
    offsets = array.array('I')  # unsigned long array for offsets
    internalid = 0  
 

    # Vars for zip parsing 
    inside_doc = False
    inside_headline = False


    # ******** INPUT ERROR CATCHING **********
    if len(sys.argv) == 1:
        print("You have entered no arguments for this progam. This program allows you to enter your input file of text, with an output directory in which the output will be stored.  Please enter your arguments in the following order: \n")
        print("Usage: python3 indexengine.py <inputfile> <outputdirectory>")
        sys.exit(1)
    elif len(sys.argv) != 3:
        print("Incorrect number of arguments.")
        print("Usage: python indexengine.py <inputfile> <outputdirectory>")
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

    # 3. Find Date -- MOVE THIS TO INDEXENGINE.PY

    def extract_date(docno):
        try:
            date_str = docno[2:8]
            date = datetime.strptime(date_str, "%m%d%y").date()
            return date.strftime("%B %d, %Y")
        except:
            print("Error: Could not parse date from DOCNO")
            return ""


    # ******** HELPER CLEANING FUNCITON *******

    def clean_tag(s):
        cleaned = re.sub(r'<[^>]+>', '', s)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    # ******** EXTRACT DATE HELPER ********

    try:
        with gzip.open(input_file_path, 'rt') as gz_file:


            # LOOP FOR EACH LINE IN GZ FILE
            for line in gz_file:

                if  '<DOC>' in line:  # see <DOC>, create new current doc []
                    inside_doc = True
                    current_doc = [line]
                    inside_headline = False
                    current_headline = ""
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
                
                elif inside_doc:
                
                    if '<DOCNO>' in line:
                        docno = clean_tag(line)
                        current_doc.append(line)
                        docnos.append(docno)


                    elif '<HEADLINE>' in line:
                        current_doc.append(line)
                        inside_headline = True

                        #CHECK IF ANY TEXT IN THE LINE 
                        headline_text = clean_tag(line)
                        if headline_text:
                            current_headline += headline_text + " "

                    
                    elif '</HEADLINE>' in line and inside_headline:
                        inside_headline = False
                        current_doc.append(line)

                        #CHECK IF ANY TEXT IN THE LINE 
                        headline_text = clean_tag(line)
                        if headline_text:
                            current_headline += headline_text + " "

                    
                    elif inside_headline:
                        current_doc.append(line)

                        headline_text = clean_tag(line.strip())
                        if headline_text:
                            current_headline += headline_text + " "


                    
                    else:
                        current_doc.append(line)

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
        

    # ********* PRINT SUCCESS *********
    print(f" {len(alldocs)} documents just processd.")
    print(f"Sending written to: {output_directory}")

if __name__ == "__main__":
    main()