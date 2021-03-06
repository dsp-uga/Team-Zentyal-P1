import re
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import col, split
from pyspark.ml.feature import RegexTokenizer, CountVectorizer
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.classification import RandomForestClassifier
from google.cloud import storage


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

    def __init__(self, sc):
        self.sparkContext = sc

    def train_preproecessing(self,content):

        ## Load files
        X_files = sc.textFile('gs://chatrath/files/X_train.txt')
        X_asm_files = X_files.map(lambda x: (("gs://chatrath/data/asm/" + x + ".asm")))
        X_asm_files = X_asm_files.reduce(lambda x, y: x + "," + y)
        X_asm = sc.wholeTextFiles(X_asm_files)
        X_train_asm = X_asm.mapValues(lambda x: re.sub("""[\t{Z}]""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[+{Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[-{Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[={Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[\r|{Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[;{Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: re.sub("""[\n{Z}]+""", "", x))
        X_train_asm = X_train_asm.mapValues(lambda x: x.split())


        ## Filter and Extract opcode
        X_train_asm = X_train_asm.mapValues(lambda x: list(filter(lambda y: y in content, x)))
        X_train_asm = X_train_asm.mapValues(lambda x: " ".join(map(str, x)))
        X_train_asm = X_train_asm.map(lambda x: (x[0].split("/")[-1].split(".")[0], x[1]))

        ## Create Dataframe
        asm_df = X_train_asm.map(lambda x: Row(filename=x[0], data=x[1])).toDF()

        ## Load lables
        rddy = sc.textFile("gs://chatrath/files/y_train.txt")

        ## Ensuring lables are in order
        X_files = X_files.zipWithIndex()
        rddy = rddy.zipWithIndex()
        dfy = rddy.map(lambda line: Row(label=line[0], id1=line[1]))  #(id,label)
        dfy = dfy.toDF()
        dfx = X_files.map(lambda line: Row(file=line[0], id=line[1])).toDF()  #(id,filename)
        resultantdf = dfx.alias('a').join(dfy.alias('b'), col('b.id1') == col('a.id')).drop('id').drop('id1')  #(filename,label)
        resultantdf = resultantdf.join(asm_df, asm_df.filename == resultantdf.file).drop('file').drop('filename')  #(data,label)

        ## Tokenizing data
        regexToken = RegexTokenizer(inputCol="data", outputCol="words", pattern="\\W")
        asm_df = regexToken.transform(resultantdf)
        asm_df = asm_df.drop('data')

        ## Using CountVectorizer to extract features
        countvector = CountVectorizer(inputCol="words", outputCol="features")
        cv = countvector.fit(asm_df)
        asm_df = cv.transform(asm_df)
        traindata = asm_df.withColumn('label', resultantdf['label'].cast('int'))

        return traindata, cv


class test_malware(object):

    def __init__(self, sc):
        self.sparkContext = sc

    def test_preprocessing(self,content,cv):

        ## Load file
        X_files = sc.textFile('gs://chatrath/files/X_test.txt')
        X_asm_files = X_files.map(lambda x: (("gs://chatrath/data/asm/" + x + ".asm")))
        X_asm_files = X_asm_files.reduce(lambda x, y: x + "," + y)
        X_asm = sc.wholeTextFiles(X_asm_files)
        X_test_asm = X_asm.mapValues(lambda x: re.sub("""[\t{Z}]""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[+{Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[-{Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[={Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[\r|{Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[;{Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: re.sub("""[\n{Z}]+""", "", x))
        X_test_asm = X_test_asm.mapValues(lambda x: x.split())

        ## Filter out opcodes
        X_test_asm = X_test_asm.mapValues(lambda x: list(filter(lambda y: y in content, x)))
        X_test_asm = X_test_asm.mapValues(lambda x: " ".join(map(str, x)))
        X_test_asm = X_test_asm.map(lambda x: (x[0].split("/")[-1].split(".")[0], x[1]))

        ## Create test dataframe
        testdata = X_test_asm.map(lambda x: Row(filename=x[0], data=x[1])).toDF()

        ## Tokenizing data
        regexToken = RegexTokenizer(inputCol="data", outputCol="words", pattern="\\W")
        asm_df = regexToken.transform(testdata)
        asm_df = asm_df.drop('data')

        ## Using CountVectorizer to extract features
        # countvector = CountVectorizer(inputCol="words", outputCol="features")
        # cv = countvector.fit(asm_df)
        testdata = cv.transform(asm_df)
        # traindata = asm_df.withColumn('label', resultantdf['label'].cast('int'))

        return testdata


class model_malware(object):

    def train_test_Model(self, trainData, testdata, spark):

        ## Using RandomForestClassifier to train the model
        rf = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=50, maxDepth=25, maxBins=32)
        rfmodel = rf.fit(trainData)
        predictions = rfmodel.transform(testdata)

        ## Select Prediction and Filename
        predictions = predictions.select('prediction', 'filename')

        ## Save it to Parquet file
        predictions.write.parquet("gs://chatrath/prediction.parquet")

    def __init__(self, sc):
        self.sparkContext = sc


if __name__ == '__main__':

    spark = SparkSession.builder.appName("Malware_Classification").getOrCreate()
    sc = spark.sparkContext

    # Load instruction set
    client = storage.Client()
    bucket = client.get_bucket('chatrath')
    blob = storage.Blob('files/instruction_set.txt', bucket)
    content = blob.download_as_string()
    content = content.decode("utf-8")
    content = content.split("\n")
    content = [x[:-1] for x in content]

    #creating testing object
    train= train_malware(sc)

    #creating testing object
    test= test_malware(sc)

    #creating model object
    model=model_malware(sc)

    #Create train data
    df_train, cv = train.train_preproecessing(content)

    #Create test data
    df_test = test.test_preprocessing(content, cv)

    #Running the model
    prediction = model.train_test_Model(df_train,df_test,spark)






