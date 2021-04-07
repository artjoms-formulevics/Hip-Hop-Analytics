#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 12:23:54 2020

@author: afo
"""

import pandas as pd
import os
import re
from num2words import num2words
import traceback
from os.path import abspath
from inspect import getsourcefile
from glob import glob
import pickle

from helper_functions import load_album_names, load_album, write_to_files, load_dataframe

# Get the working dir
p = abspath(getsourcefile(lambda:0))
p = p.rsplit('/', 1)[0]
os.chdir(p)
print('Working Directory is: %s' % os.getcwd())

# File paths for all rappers collected
paths = glob(p + '/data/' + "*/")

output = []  # output list

max_length = 35000  # how many words to collect

to_collect = 2 # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)

if to_collect == 0:
    collected = 'Albums'
elif to_collect == 1:
    collected = 'Albums + EPs'
else:
    collected = 'Albums + EPs + Mixtapes'

# Main loop for every rapper name
for i in range(0, len(paths)):
    
    try:
        df = load_dataframe(paths, i)  # get album list
        files = load_album_names(paths, i, to_collect)  # get all file names stored for this rapper
        
        lyric_length = 0  # placeholder for lyric length
        full_lyric = ''  # placeholder for lyric context
        
        # Loop for each album
        for file in range(0, len(files)):
            
            try:
                data = load_album(df, file, i, paths)  # load album from json file
                
                lyric_list = []  # list to contain lyrics
                df.iloc[file,5] = len(data['songs'])  # get the total number of songs in the album
        
                # Loop for each song
                for j in range(0, len(data['songs'])):
                    lyric_list.append(data['songs'][j]['lyrics'])  # add a song from lyric dict
                    lyric_list[j] = lyric_list[j].replace("'", "")  # remove apostrophes (I'm -> Im)
                    lyric_list[j] = lyric_list[j].lower()  # all to lowercase
                    lyric_list[j] = re.sub("[\(\[].*?[\)\]]", "", lyric_list[j])  # remove parenthesis () and brackets []
                    lyric_list[j] = re.sub('\W+',' ', lyric_list[j])  # remove all punctuation
                    lyric_list[j] = re.sub(r'\b\w{1,1}\b', '', lyric_list[j] )  # remove 1-letter words (a, I, etc.)
                    lyric_list[j] = re.sub(' +', ' ', lyric_list[j])  # remove exceed spaces
                    lyric_list[j] = lyric_list[j].rsplit()  # split song into a list
                    for z in range(0, len(lyric_list[j])):
                        if lyric_list[j][z].isnumeric() == True:
                            lyric_list[j][z] = num2words(lyric_list[j][z], lang='en')  # convert numbers to words
                    
                    full_lyric = full_lyric + ' ' + ' '.join(lyric_list[j])  # add to full lyric string
                    lyric_length = lyric_length + len(lyric_list[j])  # calculate length of lyrics gathered so far
                    
                    df.iloc[file,4] = j+1  # add how many songs from the album were used
                    if lyric_length >= max_length:  # if more than 35,000 already collected, end
                        break
                
                df.iloc[file,4] = j+1  # add how many songs from the album were used
                if lyric_length >= max_length:  # if more than 35,000 already collected, end
                    break    
        
            except AttributeError as aer:
                print('album: '+df.iloc[i,1]+' could not be processed. Going for next.')
                print(aer)
                print(traceback.format_exc())
              
                
        full_lyric = full_lyric.rsplit()  # split lyric string into words
        
        # If more than 35,000 words gathered, proceed
        if len(full_lyric) >= max_length:    
            full_lyric = full_lyric[0:max_length]  # leave exactly first 35,000
            joined_lyric = ' '.join(full_lyric)  # join back to str
            
            unique_lyric = len(set(full_lyric))  # calculate number of unique words
        
            # Append to output
            t = {'name': df.iloc[0,0], 'words': unique_lyric, 'albums': df, 'text': joined_lyric, 'collected': collected}
            output.append(t)  
            write_to_files(df, unique_lyric, joined_lyric)   # write output files
            
            print("\n================")
            print("Artist: " + df.iloc[0,0])
            print("Unique words: " + str(unique_lyric))
            print("\nMetadata:")
            print(df)
        
        # If lyric length = 0, fail message
        elif len(full_lyric) == 0:
            
            print("\n================")
            print("Failed to collect: " + df.iloc[0,0])
        
        # If lyric length between 0 and 35,000 - message that not enough lyrics
        else:
            
            print("\n================")
            print("Not enough lyrics for: " + df.iloc[0,0])
        
    except Exception as e:
        print('error occured')
        print(e)
        print(traceback.format_exc())

try:
    # Get final summary dataframe and write it               
    words=[d['words'] for d in output]
    rappers=[d['name'] for d in output]
    end_df = pd.DataFrame(list(zip(rappers, words)), columns=['Name', 'Words']).sort_values(by='Words', ascending=False)
    end_df['Collected'] = collected
    end_df.to_csv(p+'/end_result_words.csv', index=False)
    pickle.dump( output, open( "unique_words.pickle", "wb" ) )

except Exception:
    print("No lyrics were gathered!")

#output = pickle.load( open ("unique_words.pickle", "rb") )


