import pandas as pd
import os
import newspaper
import trafilatura
import argparse
import threading
from tqdm import tqdm
import math
from atpbar import atpbar, flushing
import time

def validate_input_file(input_file):
  if not os.path.exists(input_file):
    print(f"File {input_file} does not exist")
    return False
  return True

def validate_threads(threads):
  if threads:
    if threads < 1:
      print("Number of threads must be greater than 0")
      return False
    return True
  print("Taking default number of threads as 4")
  return True

def validate_data_frame(df):
  if df.empty:
    print("Input file is empty")
    return False
  required_input_columns = ["URL"]
  if not all(col in df.columns for col in required_input_columns):
    print("Input file does not have the correct structure")
    return False
  return True

def read_file(input_file_name):
  if input_file_name.endswith('.csv'):
    df = pd.read_csv(input_file_name)
  
  if input_file_name.endswith('.xlsx') | input_file_name.endswith('.xlsm') | input_file_name.endswith('.xls'):
    df = pd.read_excel(input_file_name)
  
  return df

def prepare_data_frame(df: pd.DataFrame):
  df = df.drop_duplicates(subset=['URL'])
  # Shuffle data
  df = df.sample(frac=1).reset_index(drop=True)
  return df

def scrape_data(df, start, end):
    for index in atpbar(range(start, end), name=f'Scraping articles: {start}/{end}'):
      try:
          newspaper_article = newspaper.article(df.loc[index, 'URL'])
          df.loc[index, 'STATUS'] = 'SUCCESS'
          df.loc[index, 'ARTICLE_TITLE'] = newspaper_article.title
          df.loc[index, 'TEXT'] = trafilatura.extract(newspaper_article.html)
      except:
          df.loc[index, 'STATUS'] = 'ERROR'
    
def scrape_data_threaded(df, num_threads=4):
  with flushing():
    threads = []
    chunk_size = math.ceil(len(df) / num_threads)
    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        thread = threading.Thread(target=scrape_data, args=(df, start, end))
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()
        

def clean_data(df):
  df = df.dropna(subset=['URL'])
  return df

def main():
  """MAS - Multi-threaded Article Scraper

    MAS reads an input file - CSV, XLS, XLSX, XLSM that contains a list of
    URLs. It then scrapes the articles from the URLs and writes the article
    title and text to an output file.

    Keyword Arguments:
        - input_file -- Input file containing URLs structured in the correct way. 
        Input file needs to have a column named "URL" containing the URLs.
        
        - threads -- Number of threads to use for scraping (default 4). 
        Optional, can be used with -t flag.
    """
  
  parser = argparse.ArgumentParser()
  parser.add_argument("input_file", help="Input file")
  parser.add_argument("-t", help="Number of threads", dest="threads", type=int, default=4, required=False)
  args = parser.parse_args()
  
  if not validate_input_file(args.input_file):
    return
  
  if not validate_threads(args.threads):
    return
  
  df = read_file(args.input_file)
  
  if not validate_data_frame(df):
    return None
  
  start_time = time.time()
  
  df = prepare_data_frame(df)
  
  scrape_data_threaded(df, args.threads)
  
  df = clean_data(df)
  
  output_file = args.input_file.split('.')[0] + "_output.xlsx"
  
  df.to_excel(output_file)
  
  end_time = time.time()
  
  print(f"Time taken: {round(end_time - start_time, 2)} seconds")
  
if __name__ == '__main__':
    main()
