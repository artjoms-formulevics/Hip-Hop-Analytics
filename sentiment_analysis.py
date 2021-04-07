#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 12:15:43 2020

@author: afo
"""

import pandas as pd
import os
import re
import traceback
from os.path import abspath
from inspect import getsourcefile
from nltk.corpus import stopwords
from glob import glob
import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pickle

from helper_functions import load_album_names, load_album, load_dataframe

# Using NLTK Vader analyzer
sid = SentimentIntensityAnalyzer()

# Get the working dir
p = abspath(getsourcefile(lambda:0))
p = p.rsplit('/', 1)[0]
os.chdir(p)
print('Working Directory is: %s' % os.getcwd())

# File paths for all rappers collected
paths = glob(p + '/data/' + "*/")

# Getting NLTK stopwords and adding own
stop_words = set(stopwords.words('english'))
additional_stopwords = ['im', 'ive', 'aint', 'dont', 'got', 'cant']
stop_words.update(additional_stopwords)


output = []  # output list

to_collect = 0 # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)

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
        
        # Placeholders for all album sentiment results, album names and realease years
        album_pos = []
        album_neg = []
        album_neu = []
        album_comp = []
        album_name = []
        album_years = []
        
        # Loop for each album
        for file in range(0, len(files)):

            data = load_album(df, file, i, paths)   # load album from json file
    
            lyric_list = []  # list to store song lyrics
            lst = []  # placeholder to store each line of the song
            
            # Loop for each song
            for j in range(0, len(data['songs'])):
                lyric_list.append(data['songs'][j]['lyrics'])  # add a song from lyric dict
                lyric_list[j] = re.sub("[\(\[].*?[\)\]]", "", lyric_list[j])  # remove parenthesis () and brackets []
                lst.append(lyric_list[j].splitlines())  # split song by lines and append to lst
                lst[j] = list(filter(None, lst[j]))  # remove empty tokens
         
            clean_album_name = re.sub(r'[^\w\s]','',data['name'])  # get clean album name to be the same as in files/list
            # Get the album year, if possible
            try:
                album_year = data['release_date_components']['year']
            except TypeError:
                album_year = "unknown"
        
            # Placeholders for all song sentiment results
            pos_song = []
            neg_song = []
            neu_song = []
            comp_song = []
            
            # Loop for each song
            for j in range(0, len(lst)):
                
                # Placeholders for all line sentiment results
                pos_lst = []
                neg_lst = []
                neu_lst = []
                comp_lst = []
                
                # Loop for each line of the song
                for l in range(0, len(lst[j])):
                    analysis = sid.polarity_scores(lst[j][l])  # get sentiment of the line
                    
                    # Append results to line placeholders
                    pos_lst.append(analysis['pos'])
                    neg_lst.append(analysis['neg'])
                    neu_lst.append(analysis['neu'])
                    comp_lst.append(analysis['compound'])
               
                # Get song sentiment by averaging line sentiments. If error - get default (e.g. no sentiment)
                try:
                    pos_song.append(sum(pos_lst) / len(pos_lst))
                except ZeroDivisionError:
                    pos_song.append(1/3)
                try:
                    neg_song.append(sum(neg_lst) / len(neg_lst))
                except ZeroDivisionError:
                    neg_song.append(1/3)
                try:
                    neu_song.append(sum(neu_lst) / len(neu_lst))
                except ZeroDivisionError:
                    neu_song.append(1/3)
                try:
                    comp_song.append(sum(comp_lst) / len(comp_lst))
                except ZeroDivisionError:
                    comp_song.append(0)
            
            # Get album sentiment by averaging song sentiments
            try:
                p_pos = sum(pos_song) / len(pos_song)  
                p_neg = sum(neg_song) / len(neg_song)
                p_neu = sum(neu_song) / len(neu_song)
                p_comp = sum(comp_song) / len(comp_song)
                
                # Get dominating sentiment and album result
                end_sent = np.argmax([p_pos, p_neg, p_neu])  
                if end_sent == 0:
                    sent = "Positive"
                    final_sent = p_pos
                elif end_sent == 1:
                    sent = "Negative"
                    final_sent = p_neg
                else:
                    sent = "Neutral"
                    final_sent = p_neu            
                
                # Print album info
                print("\n=============") 
                print("Album: " + data['full_title'] + ' (' + str(album_year) + '):')
                print("Positive sentiment:" + str(p_pos))
                print("Negative sentiment:" + str(p_neg))
                print("Neutral sentiment:" + str(p_neu))
                print("Album Sentiment: " + sent + " with weight of: " + str(final_sent))
                print("Average Compound Score: " + str(p_comp))
                
                # Append results to album placeholders
                album_pos.append(p_pos)
                album_neg.append(p_neg)
                album_neu.append(p_neu)
                album_comp.append(p_comp)
                
                # Append corresponding album name and release year
                album_name.append(data['full_title'])
                album_years.append(album_year)
            
            # If whole album has no lyrics - make default sentiment
            except ZeroDivisionError:
                print("No valid lyrics for this album!")
                album_pos.append(1/3)
                album_neg.append(1/3)
                album_neg.append(1/3)
                album_comp.append(0)
                
                album_name.append(data['full_title'])
                album_years.append(album_year)
        
        # Get rapper sentiment by averaging album sentiments
        try:
            final_pos = sum(album_pos) / len(album_pos)  
            final_neg = sum(album_neg) / len(album_neg)
            final_neu = sum(album_neu) / len(album_neu)
            final_comp = sum(album_comp) / len(album_comp)
            
            # Get dominating sentiment and final result
            end_sent = np.argmax([album_pos, album_neg, album_neu])
            if end_sent == 0:
                sent = "Positive"
                final_sent = final_pos
            elif end_sent == 1:
                sent = "Negative"
                final_sent = final_neg
            else:
                sent = "Neutral"
                final_sent = final_neu     
            
            # Print the results
            print("\n=============") 
            print("Artist: " + df.iloc[0,0] + ':')
            print("Positive sentiment:" + str(final_pos))
            print("Negative sentiment:" + str(final_neg))
            print("Neutral sentiment:" + str(final_neu))
            print("Album Sentiment: " + sent + " with weight of: " + str(final_sent))
            print("Average Compound Score: " + str(final_comp))
        except ZeroDivisionError:  # if error - no lyrics for the artist at all
            print("No valid lyrics for this album!")
        
        # Append to output
        t = {'name': df.iloc[0,0], 'positive_albums': album_pos, 'negative_albums': album_neg, 'neutral_albums': album_neu, 'compunds_albums': album_comp, 'albums': df, 'final_pos': final_pos, 'final_neg': final_neg, 'final_neu': final_neu, 'final_comp': final_comp, 'album_names': album_name, 'album_years': album_years, 'collected': collected}
        output.append(t)  
        
    except Exception as e:
        print('error occured')
        print(e)
        print(traceback.format_exc())

try:    
    # Create final output df with sentiments of all rappers and save to file 
    words=[d['final_comp'] for d in output]
    rappers=[d['name'] for d in output]
    end_df = pd.DataFrame(list(zip(rappers, words)), columns=['Name', 'Sentiment']).sort_values(by='Sentiment', ascending=False)
    end_df['Collected'] = collected
    end_df.to_csv(p+'/end_result_sentiment.csv', index=False)
    pickle.dump( output, open( "sentiment.pickle", "wb" ) )
    
except Exception:
    print("No lyrics were gathered!")
    
#output = pickle.load( open ("sentiment.pickle", "rb") )
