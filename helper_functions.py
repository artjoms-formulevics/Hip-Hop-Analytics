#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 22:36:21 2021

@author: afo
"""

import pandas as pd
import json
from os.path import isfile, join
from os import listdir

# Function to get all the json file names in 3 subdirectories of given rapper - albums, eps, mixtapes
def load_album_names(paths, i, to_collect=2):
    
    # Placeholer lists
    files_alb = []
    files_ep = []
    files_mix = []
    
    # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)
    if to_collect >= 0:
        
        # Get list of files from albums
        files_alb = [f for f in listdir(paths[i]+'albums/') if isfile(join(paths[i]+'/albums', f))]
        try :
            files_alb.remove('.DS_Store')
        except ValueError:
            print()
        
        files_alb = [k for k in files_alb if '.json' in k]
        
        if to_collect >= 1:
            
            # Get list of files from eps
            files_ep = [f for f in listdir(paths[i]+'eps/') if isfile(join(paths[i]+'/eps', f))]
            try :
                files_ep.remove('.DS_Store')
            except ValueError:
                print()
            
            files_ep = [k for k in files_ep if '.json' in k]
            
            if to_collect >= 2:
                    
                # Get list of files from mixtapes
                files_mix = [f for f in listdir(paths[i]+'mixtapes/') if isfile(join(paths[i]+'/mixtapes', f))]
                try :
                    files_mix.remove('.DS_Store')
                except ValueError:
                    print()
                
                files_mix = [k for k in files_mix if '.json' in k]
    
    files = files_alb + files_ep + files_mix # make single list
    
    return files

# Function to load the json album. Path is based on type from the dataframe
def load_album(df, file, i, paths):

    # Determine the folder
    if df.iloc[file, 3] == 'Album':
        filepath = paths[i]+'albums/'+df.iloc[file,1]+'.json'
    elif df.iloc[file, 3] == 'EP':
        filepath = paths[i]+'eps/'+df.iloc[file,1]+'.json'
    else:
        filepath = paths[i]+'mixtapes/'+df.iloc[file,1]+'.json'
    
    # Load file
    with open(filepath) as f:
        data = json.load(f)
    
    return data

# Function to write files for the word_count script. Writes album list, unique word count and full used lyric to files
def write_to_files(df, unique_lyric, joined_lyric):
          
    df.to_csv('data/'+df.iloc[0,0]+"/albums.csv", index=False)
        
    with open('data/'+df.iloc[0,0]+'/unque.txt', 'w') as the_file:
        the_file.write(str(unique_lyric))
            
    with open('data/'+df.iloc[0,0]+'/full.txt', 'w') as the_file:
        the_file.write(joined_lyric)
    
    print('Data is written to files!')

# Function to load the saved artist album dataframe    
def load_dataframe(paths, i):
    
    df = pd.read_csv(paths[i]+'/albums.csv')
    df['Year'] = pd.to_numeric(df['Year'])
    df = df.sort_values(by=['Type', 'Year'])  # sort by year and type to make sure old albums go first, then EPs, then Mixtapes
    df['used'] = 0  # counter of used songs from album for word count
    df['total songs'] = 0  # counter of total songs in album for word count
    #df = df[df['Type'] == 'Album']

    return df










