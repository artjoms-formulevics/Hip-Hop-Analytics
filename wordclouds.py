#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 12:15:43 2020

@author: afo
"""

import pandas as pd
import os
import re
from os.path import abspath
from inspect import getsourcefile
from nltk.tokenize import WhitespaceTokenizer
from nltk.corpus import stopwords
from glob import glob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import traceback
import pickle

from helper_functions import load_album_names, load_album, load_dataframe

# Get the working dir
p = abspath(getsourcefile(lambda:0))
p = p.rsplit('/', 1)[0]
os.chdir(p)
print('Working Directory is: %s' % os.getcwd())

# File paths for all rappers collected
paths = glob(p + '/data/' + "*/")

# Getting NLTK stopwords and adding own
stop_words = set(stopwords.words('english'))
additional_stopwords = ['im', 'ive', 'aint', 'dont', 'got', 'cant', 'em', 'yea', 'oh', 'yeah', 'ya', 'us', 'yo', 'yall','thats']
stop_words.update(additional_stopwords)

# Will be using whitespace tokenizer
tk = WhitespaceTokenizer() 

output = []  # output list

max_length = 25000  # how many words to collect

exit_on_max_length = False  # boolean to collect only songs of max length or all the albums completely

to_collect = 1 # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)

album_clouds = False  # if true, get clouds for each album separately, if false - only for artist in whole

if to_collect == 0:
    collected = 'Albums'
elif to_collect == 1:
    collected = 'Albums + EPs'
else:
    collected = 'Albums + EPs + Mixtapes'
    
# Main loop for each rapper
for i in range(0, len(paths)):
    
    try:     
        df = load_dataframe(paths, i)  # get album list
        files = load_album_names(paths, i, to_collect)  # get all file names stored for this rapper
        
        artist_lyric = ''  # placeholder for full artist lyric
        full_lyric = ''  # placeholder for full album lyrics text
        lyric_length = 0  # placeholder for lyric length
            
        try:

            # Loop for each album
            for file in range(0, len(files)):
    
                data = load_album(df, file, i, paths)   # load album from json file
                
                lyric_list = []  # list to store song lyrics
                df.iloc[file,5] = len(data['songs'])  # get the total number of songs in the album
                
                # Loop for each song
                for j in range(0, len(data['songs'])):
                    lyric_list.append(data['songs'][j]['lyrics'])  # add a song from lyric dict
                    lyric_list[j] = lyric_list[j].lower()  # all to lowercase
                    lyric_list[j] = re.sub("[\(\[].*?[\)\]]", "", lyric_list[j])  # remove parenthesis () and brackets []
                    lyric_list[j] = tk.tokenize(lyric_list[j])  # tokenizing with whitespace tokenizer
                    lyric_list[j] = [w.replace("'", "") for w in lyric_list[j]] # remove apostrophes (I'm -> Im)
                    lyric_list[j] = [re.sub(r'[^\w\d\s\-]+','', w) for w in lyric_list[j]] # remove all punctuation except hyphen
                    lyric_list[j] = [item for item in lyric_list[j] if not item.isdigit()]  # remove tokens that are digits that are not part of string
                    lyric_list[j] = [w for w in lyric_list[j] if re.search(r'\w+', w)]  # remove non-word tokens, if exists (e.g. single hyphen token)
                    lyric_list[j] = list(filter(None, lyric_list[j]))  # remove empty tokens
                    lyric_list[j] = [re.sub(r'\b\w{1,1}\b', '', w ) for w in lyric_list[j]]  # remove 1-letter words (a, I, etc.)
                    lyric_list[j] = [word for word in lyric_list[j] if not word in stop_words]  # remove stopwords
                
                # Same loop once again (idf why it does not work if add these lines in the first loop)
                for j in range(0, len(data['songs'])):
                    lyric_list[j] = list(filter(None, lyric_list[j]))  # remove empty tokens
        
                    full_lyric = full_lyric + ' ' + ' '.join(lyric_list[j])  # add song to full album lyric str
                    lyric_length = lyric_length + len(lyric_list[j])  # calculate length of lyrics gathered so far
                    
                artist_lyric = artist_lyric + ' ' + full_lyric  # add full album lyric to full artist lyric
                
                clean_album_name = re.sub(r'[^\w\s]','',data['name'])  # get clean album name to be the same as in files/list
                # Get the album year, if possible
                try:
                    album_year = data['release_date_components']['year']
                except TypeError:
                    album_year = "unknown"
                
                # Draw album clounds only if true
                if album_clouds == True:
                    # Create and generate a word cloud image for album:
                    wordcloud_album = WordCloud(max_words=100, background_color="white", stopwords='').generate(full_lyric)
                    
                    # Display the generated image:
                    plt.imshow(wordcloud_album, interpolation='bilinear')
                    plt.axis("off")
                    plt.title('Wordcloud for: ' + data['full_title'] + ' (' + str(album_year) + ')')
                    plt.show()
                
                df.iloc[file,4] = j+1  # add how many songs from the album were used
                if lyric_length >= max_length and exit_on_max_length == True:  # if more than 35,000 already collected & boolean is true, end
                    break
            
            # boolean to proceed or not after check on word count
            proceed = 1
            
            # if word limit is true, limit it
            if exit_on_max_length == True:
                artist_lyric = artist_lyric.rsplit()  # split lyric string into words
                artist_lyric = artist_lyric[0:max_length]  # leave exactly first 35,000
                artist_lyric = ' '.join(artist_lyric)  # join back to str
                
                # If not enough lyrics, skip this artist
                if len(artist_lyric.rsplit()) < max_length:
                    print("\n================")
                    print("Not enough lyrics for: " + df.iloc[0,0])
                    proceed = 0
            
            # proceed only if not forbidden by lack of words
            if proceed == 1:
                # Create and generate a word cloud image for rapper:
                wordcloud_artist = WordCloud(max_words=200, background_color="white", stopwords='').generate(artist_lyric)
                
                # Display the generated image:
                plt.imshow(wordcloud_artist, interpolation='bilinear')
                plt.axis("off")
                plt.title('Wordcloud for artist: ' + data['full_title'].rsplit('by ')[-1])
                plt.show()
        
                # Count the top 20 words of the rapper, get % of total and write to df
                word_count = Counter(artist_lyric.split()).most_common()
                words_df = pd.DataFrame(word_count, columns=['Name', 'Top_Words'])
                words_df['Percentage'] = words_df['Top_Words'] / len(artist_lyric.split())
                words_df['Artist'] = df.iloc[0,0]
                words_df['Collected'] = collected
                
                total_word_count = len(artist_lyric.split())  # get the total word count
                
                # Print words
                print("\n=============")
                print("Top 20 words by: " + df.iloc[0,0] + ":")
                for w in range(0,20):
                    print (word_count[w])
                
                # if there is limit on length, do not write to output, if it is not long enough
                if exit_on_max_length == True and len(artist_lyric.rsplit()) >= max_length:
                    # add artist to final output list and write artist words to file
                    t = {'name': df.iloc[0,0], 'albums': df, 'top_words': words_df, 'all_words':artist_lyric, 'word_count': total_word_count, 'collected': collected}
                    output.append(t) 
                    
                # If there is no limit, add anyway to output    
                if exit_on_max_length == False:
                    # add artist to final output list and write artist words to file
                    t = {'name': df.iloc[0,0], 'albums': df, 'top_words': words_df, 'all_words':artist_lyric, 'word_count': total_word_count, 'collected': collected}
                    output.append(t) 
                    
                # Write to df anyway    
                words_df.to_csv(paths[i] + "artist_top_words.csv", index=False)
                
        except Exception as e:
            print('error occured')
            print(e)
            print('Cannot collect album: ' + df.iloc[file,1] + ' by ' + df.iloc[file,0] + '. Going for next.')
        
    except Exception as e:
        print('error occured')
        print(e)
        print(traceback.format_exc())

# Placeholder for all the dfs
final_word_list = []

try:    
    # Get top words df for all rappers in a list
    for z in range(0, len(output)):
        final_word_list.append(output[z]['top_words'])
      
    # Concat and group them by words
    dfs = pd.concat(final_word_list)
    total_words = dfs.groupby(['Name'])['Top_Words'].sum()
    total_words = total_words.to_frame()
    total_words['Percentage'] = total_words['Top_Words'] / total_words['Top_Words'].sum()
    total_words = total_words.sort_values(by='Top_Words', ascending=False)
    total_words['Collected'] = collected
    total_words.to_csv(p+'/end_result_top_words.csv')
    pickle.dump( output, open( "frequent_words.pickle", "wb" ) )

except Exception:
    print("No lyrics were gathered!")

#output = pickle.load( open ("frequent_words.pickle", "rb") )



