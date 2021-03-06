
import pyspark
from operator import add
from pyspark.ml.feature import NGram
from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import Row
from pyspark.sql.functions import concat, col, lit
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, CountVectorizer
from pyspark.ml import Pipeline
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.sql.types import IntegerType
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.classification import RandomForestClassifier,LogisticRegression
from pyspark.sql import functions as F
from pyspark.ml.feature import PCA
from pyspark.ml.linalg import Vectors
from pyspark.sql import SparkSession
from pyspark.sql.functions import split
import numpy as np


class train_malware(object):
    
    '''
    This class was used to format, preprocessing, feature extraction, training an testing of data.
   
    methods:
    dataformation: Reading data from X_small_train file and using it to pull data from GCP bucket
                    and the using dataframe/rdd to form the required dataframe
    preprocesisng: Using regular expression to remove line number as required. Then using in built packages
                    such as regexeTokenizer, CountVectorizer, ngrams , creating pipeline.
    train_test_model: using Random forest to train the model.using testing data to check the result.
    '''
    
    
    def dataformation(self,sc):
        #initializing the pathname
        pathname="gs://uga-dsp/project1/files/"
        #"gs://uga-dsp/project1/files/"

        extension=".bytes"
        
        #reading X_train file data into small_rdd 
        small_rdd=self.sparkContext.textFile(pathname+"X_train.txt")
        
        #creating the bytes_text_files to read the file in the data folder in GCP Buket
        filename_rdd=small_rdd.map(lambda x: (("gs://uga-dsp/project1/data/bytes/"+x+extension)))
        bytes_text_files = filename_rdd.reduce(lambda x, y: x + "," + y)
        
        #reading data of all the file mentioned in the X_small_train.txt
        rdd=self.sparkContext.wholeTextFiles(bytes_text_files)
        rdd = rdd.map(lambda x: (x[0].split("/")[-1].split(".")[0],x[1]))
        
        #reading label from Y_train.txt and storing in the rdd
        rddy=self.sparkContext.textFile(pathname+"y_train.txt")
        
        #reading filename from  X_train.txt
        rddx=self.sparkContext.textFile(pathname+"X_train.txt")
        
        # adding the index value to the both rdd and rddy
        rdd=rdd.zipWithIndex()
        rddx=rddx.zipWithIndex()
        rddy=rddy.zipWithIndex()
        
        #creating dataframe for both the rdd with column name
        df2=rddy.map(lambda line: Row(label=line[0],id=line[1])).toDF() #(id,label)
        df1 =rdd.map(lambda line: Row(data=line[0][1],id=line[1],file=line[0][0])).toDF() #(id,filename,data)
        dfx=rddx.map(lambda line: Row(filename=line[0], id=line[1])).toDF() #(id,filename)
        
        #creating resultant dataframe by joining above two dataframe 
        resultantdf=dfx.alias('a').join(df2.alias('b'),col('b.id') == col('a.id')).drop('id') #(filename,label)
        resultantdf=resultantdf.join(df1,resultantdf.filename == df1.file).drop('filename').drop('id') #(data,filename,label)
        
        return resultantdf
    
    def preprocessing(self,resultantdf):
        
        #removal of linenumber from each file data using regural expression
        resultantdf=resultantdf.withColumn('data', F.regexp_replace('data', '\\b\\w{3,}\\s',''))
        
        #using inbuilt regexTokenizer  api to tokenize the data
        regexTokenizer = RegexTokenizer(inputCol="data", outputCol="words", pattern="\\W")
        resultantdf=regexTokenizer.transform(resultantdf)
        resultantdf=resultantdf.drop('data') 
        resultantdf.show()
        
        # bag of words count usinf count vectorizer
        countVectors = CountVectorizer(inputCol="words", outputCol="features")
        cv=countVectors.fit(resultantdf)
        resultantdf1=cv.transform(resultantdf)
        resultantdf1=resultantdf1.withColumn('label',resultantdf1['label'].cast('int'))
        
        return(resultantdf1,cv)
      
    def __init__(self, sc): 
        self.sparkContext = sc 
        
        
        
class test_malware(object):
    
    '''
    This class was used to format, preprocessing, feature extraction, training an testing of data.
   
    methods:
    dataformation: Reading data from X_small_test file and using it to pull data from GCP bucket
                    and the using dataframe/rdd to form the required dataframe
    preprocesisng: Using regular expression to remove line number as required. Then using in built packages
                    such as regexeTokenizer, CountVectorizer, ngrams , creating pipeline.
    train_test_model: using Random forest to train the model.using testing data to check the result.
    '''
    
    
    def dataformation(self,sc):
        #initializing the pathname and extension
        pathname="gs://uga-dsp/project1/files/"        
        extension=".bytes"
        
        #reading X_small_train file data into small_rdd 
        large_rdd=self.sparkContext.textFile(pathname+"X_test.txt")
        
        #creating the bytes_text_files to read the file in the data folder in GCP Buket
        filename_rdd=large_rdd.map(lambda x: ("gs://uga-dsp/project1/data/bytes/"+x+extension))
        bytes_text_files = filename_rdd.reduce(lambda x, y: x + "," + y);
        
        #reading data of all the file mentioned in the X_small_train.txt
        rdd=self.sparkContext.wholeTextFiles(bytes_text_files)
        rdd = rdd.map(lambda x: (x[0].split("/")[-1].split(".")[0],x[1]))

        #creating dataframe for both the rdd with column name
        resultantdf =rdd.map(lambda line: Row(data=line[1],file=line[0])).toDF() #(id,filename,data)
        
        return resultantdf
    
    def preprocessing(self,resultantdf,cv):
        
        #removal of linenumber from each file data using regural expression
        resultantdf=resultantdf.withColumn('data', F.regexp_replace('data', '\\b\\w{3,}\\s',''))
        
        #using inbuilt regexTokenizer  api to tokenize the data
        regexTokenizer = RegexTokenizer(inputCol="data", outputCol="words", pattern="\\W")
        resultantdf=regexTokenizer.transform(resultantdf)
        resultantdf=resultantdf.drop('data') #not required column dropped
        
        
        # bag of words count usinf count vectorizer
        resultantdf=cv.transform(resultantdf)
        
        return(resultantdf)
    
    
    def __init__(self, sc): 
            
        self.sparkContext = sc 
        
        
    
class model_malware(object):
    
    def train_test_Model(self,trainingData,testdata,spark):
        
        # Using RandomForestClassifier to train the model
        rf = RandomForestClassifier(labelCol="label",featuresCol="features",numTrees = 50,maxDepth = 25,maxBins = 32)
       
        # Train model with Training Data
        rfModel = rf.fit(trainingData)
        
        # using the testdata to for prediction/accuracy
        predictions = rfModel.transform(testdata)
        
        #selecting prediction and filename from prediction dataframe
        predictions=predictions.select('prediction','file')
        
        return(predictions)
    
    
    def __init__(self, sc): 
        self.sparkContext = sc 
        
    
        
    
if __name__=='__main__' :
        
    #creating spark sesson
    spark = SparkSession.builder.appName("Malware_Classification").getOrCreate()       
    sc=spark.sparkContext
    
    #creating training object     
    train=train_malware(sc)
    
    #creating testing object
    test=test_malware(sc)
    
    #creating model object
    model=model_malware(sc)
    
    #processing training data
    df_train=train.dataformation(sc)
    df_preprocessed_train,cv=train.preprocessing(df_train)
    df_preprocessed_train.show()
    
    #processing testing data
    df_test=test.dataformation(sc)
    df_test.show()
    df_preprocessed_test=test.preprocessing(df_test,cv)
    df_preprocessed_test.show()
    
    #calculating accuracy
    prediction=model.train_test_Model(df_preprocessed_train,df_preprocessed_test,spark)
    prediction.write.parquet("gs://dataproc-5c1f0658-b1b3-431f-b2f6-323ed0f2006e-us-east1/predictions_final1.parquet")





