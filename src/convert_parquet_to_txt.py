import numpy as np
import pyarrow.parquet as pq
import pandas as pd

if __name__ == '__main__':

    #reading the parquet file
    data=pq.read_table("/home/anant/Desktop/Prediciton/")
    #converting parquet file to pandas df
    dfn=data.to_pandas()
    #reading the X_test.txt into dataframe
    df23 = pd.read_csv('/home/anant/data_science_practicum/Malware Classification/dataset/small_data/X_test.txt',header=None)
    #renaming of the column
    df23.columns=['file']
    #reodering the result with proper file label
    result = pd.merge(dfnew,df23, how='left',on=['file'])
    #droping unwanted column
    result=result.drop(columns=['file'])
    #saving the the result in the file using numpy
    np.savetxt("/home/anant/data_science_practicum/Malware Classification/priyamk.txt",result.values,fmt="%d")

