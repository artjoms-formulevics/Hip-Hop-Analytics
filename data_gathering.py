#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 17:36:09 2020

@author: afo
"""

import pandas as pd
import os
import traceback
from os.path import abspath
from inspect import getsourcefile

from gathering_functions import load_album_names, get_album_list, load_album, write_album_files, write_df, add_data_folder, create_folders
import config

# Get the working dir
p = abspath(getsourcefile(lambda:0))
p = p.rsplit('/', 1)[0]
os.chdir(p)
print('Working Directory is: %s' % os.getcwd())

add_data_folder()  # add data folder if not existent

names_df = pd.read_csv(p+'/rapper_list.csv', engine='python')  # get rapper list to collect
names = names_df.loc[names_df['collected']==0]['names'].tolist()  # rapper name list
urls = names_df.loc[names_df['collected']==0]['url'].tolist()  # urls in case name is not working

output = []  # output list

# Genius token
token = config.token 


to_collect = 2 # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)

if to_collect == 0:
    collected = 'Albums'
elif to_collect == 1:
    collected = 'Albums + EPs'
else:
    collected = 'Albums + EPs + Mixtapes'
    
    
# Main loop for every rapper name
for name in range(0, len(names)):
    
    try:
        create_folders(names, name)  # create subfolderds for each artist, if does not exist
        df = get_album_list(urls, names, name, to_collect)  # call function to get all albums by rapper
        
        # Sub loop for all gathered albums
        for i in range(0, len(df)): 
            try:
                
                # Small adjustment for GZA, as his name in RYM has slash which translates to subfodler
                if df.iloc[0,0] == 'GZA/Genius':
                    df['Artist'] = 'GZA'
                    names[name] = 'GZA'
                
                data = load_album(df, i, token)  # function to load album from Genius and save as temp file
                # If file was downloaded, write it to storage
                if data != "album exists":
                    write_album_files(data, df, i, names, name)  # function to write album to json
            
            # The main error to be observed is attributeError, when album cannot be collected from Genius
            # In this case, it is skipped
            except AttributeError as aer:
                print('album: '+df.iloc[i,1]+' could not be collected. Going for next.')
                print(aer)
                print(traceback.format_exc())

        print("\n================")
        print("Collected artist: " + names[name])
        
        
        if len(df) == 0:  # if artist was found, but no albums were downloaded, mark it as status "2"
            names_df.iloc[name+len(names_df)-len(names),1] = 2
            names_df.to_csv(p+'/rapper_list.csv', index=False)
        else:  # if at least one album was gathered, mark as status "1"
            names_df.iloc[name+len(names_df)-len(names),1] = 1
            names_df.to_csv(p+'/rapper_list.csv', index=False)

            files = load_album_names(p, df, to_collect)  # load list of all files downloaded
            
            df['Album'].replace( { r'[^\w\s]' : '' }, inplace= True, regex = True)  # make clean album name to match file name (withou special characters)
            
            df.to_csv('data/'+names[name]+'/albums_all.csv', index=False)  # save list of all albums (incl. not downloaded)
            
            df = df[df['Album'].isin(files)]  # check & filters albums by files downloaded
            write_df(df, names, name)  # save final album list
            print(df)
            

    except Exception as e:
        print('error occured')
        print(e)
        print(traceback.format_exc())
        names_df.iloc[name+len(names_df)-len(names),1] = 0  # if error mark as status "0" and write back a rapper list
        names_df.to_csv(p+'/rapper_list.csv', index=False)
        print("\n================")
        print("Failed to collect: " + names[name])
        
                
