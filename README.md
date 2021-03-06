# Team-Zentyal-P1

This repository contains classification of documents, to classify documents into one out of several possible malware families, using Google Cloud Platform, PySpark, Jupyter notebook. This project is done for CSCI8360: Data Science Practicum at The University of Georgia.

In this project, data was taken from the Microsoft Malware Classification Challenge. The uncompressed data is nearly about half terabyte. The data can be found from follwing Google Storage Path. gs://uga-dsp/project1/files Here, We are trying to classify this data into one of the several possible malware families. There are 9 classes of malware, and each instance of malware has only of the following categories. 

1. Ramnit
2. Lollipop
3. Kelihos_ver3
4. Vundo
5. Simda
6. Tracur
7. Kelihos_ver1
8. Obfuscator.ACY
9. Gatak

# Built With

- Python 3.6
- Apache Spark
- Google Cloud Platform
- PySpark- Python API for Apache Spark 
- Jupyter Notebook 

# Dependencies 

### For Google Storage Cloud Library

!pip install --upgrade google-cloud-storage\
!pip install -U requests

### To use PySpark components
!pip install pyspark

# Approach 

We are using Google Cloud Platform for computation. 

### First Approach 

we used the unigram analysis with random forest on binaryHex files available in the training data. For preprocessing, we removed the line numbers and other characters like "?" using Regex Tokenizer available in PySpark.ml.feature. 
Next, we extracted the hexadecimal bytes and performed the unigram analysis. Using count vectorizer we extracted the feature vectors. Then, we used Random Forest to train our model on small dataset (number of trees =20 and depth=8) with the accuracy of 89.49.

![alt text](https://github.com/dsp-uga/Team-Zentyal-P1/blob/master/images/Random_Forest_Bytes_small.jpeg)

Then we trained our model on large dataset, this time we changed the number of trees to 50 and depth to 25. We got the accuracy of 98.01.

### Second approach:

For the second approach, we used the opcode n-gram analysis. For preprocessing, all the spaces and unrequired characters were removed using regex expressions. Next, we filtered out opcodes to get a list of opcode instruction set from each file. CountVectorizer was applied to extract features. These features were passed through a Random Forest model with number of trees 20 and depth 8. The accuracy obtained for the small dataset was 92.97. 

![alt text](https://github.com/dsp-uga/Team-Zentyal-P1/blob/master/images/Random_Forest_asm_small.jpeg)

On the large dataset the model was changed to have number of trees as 50 and depth 25.  We got accuracy of 98.45


# Contributing 

There are no specific guidlines for contibuting. If you see something that could be improved, send a pull request! If you think something should be done differently (or is just-plain-broken), please create an issue.

# Authors 

Abhishek Chatrath\
Anant Tripathi\
Denish Khetan

# References 

https://towardsdatascience.com/multi-class-text-classification-with-pyspark-7d78d022ed35

https://spark.apache.org/docs/2.1.0/ml-features.html

https://www.cse.iitk.ac.in/users/cs365/2015/_submissions/karanb/report.pdf

# License

This Project is under the GNU General Public License v3.0. For more details visit License file here: https://github.com/dsp-uga/Team-Zentyal-P1
