# mse-541-f25-hw2-lukastimusk
mse-541-f25-hw2-lukastimusk created by GitHub Classroom


# Hello User!

My name is Lukas Timusk (lemtimus - 20992768) 


In order to run my program, please follow these steps:

YOU NEED: Python3 installed, access to latimes.gz or my testing set - testing_documents.gz, your file of queries.txt in the correct format

FIRST -> You need to create your Index folder by processing your gz file through my indexengine.py

1. Ensure you have no folder called index in your current directory
2. Please download either my testing file called testingdocs.gz or latimes.gz into your current directory
3. Call my index engine program first, with the following usage: python indexengine.py <inputfile> <outputdirectory>
4. Call my getdocuments program with either a docno or id in mind to retrieve with the following usage: python getdocuments.py <index path> <docno|id> <value>


SECOND -> 

1. Ensure your query file is in the form of a txt file, in the repository - if you want to use mine for the LATimes.gz file, it's called queries.txt and it's in the root of the repository, at /Desktop/mse-541-f25-hw2-lukastimusk/queries.txt
2. To get your retrieval results, call the queryengine with the following usage: python3 queryengine.py <IndexFolderPath> <QueryFilePath> <OutputFilePath>
3. Access your results in the output file

I hope you enjoy!



PS:
Correct format for query file is:
topic number
query 
topic number 
query 

ex:
400 
doctor help
401
gatorade bottles
...