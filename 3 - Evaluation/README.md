# Hello User!

My name is Lukas Timusk (lemtimus - 20992768)

In order to run my program, please follow these steps:

YOU NEED: Python3 installed, and to produce or have access the following files:

1. A 'qrels' file that outlines which documents are relevant and not relevant to each topic, in the form "topicID ignore docno judgment" seperated by whitespace, and be a text file. 
2. A 'results' file that has the results of your processing of the documents in your database, in my case the 'LA TIMES' documents. This file needs to be in the form "TopicID, 'QO', docid, rank, score, runtag". For example: "401 Q0 LA082690-0052 8 6 lemtimusAND"

Then you can run the code with the usage: python3 evaluationengine <qrelsfile path> <results file path>
