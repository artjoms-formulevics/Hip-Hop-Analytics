#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 22:53:56 2021

@author: afo
"""

import pandas as pd
import lyricsgenius
import json
import os
from os.path import isfile, join
from os import listdir
import re

from rym import rymscraper

# Function to get all the json file names in 3 subdirectories of given rapper - albums, eps, mixtapes
def load_album_names(p, df, to_collect=2):
    
    files_alb = []
    files_ep = []
    files_mix = []
    
    album_path = p + '/data/' + df.iloc[0,0] +'/albums'
    ep_path = p + '/data/' + df.iloc[0,0] +'/eps'
    mixtape_path = p + '/data/' + df.iloc[0,0] +'/mixtapes'
    if to_collect >= 0:
        # Get list of files from albums
        files_alb = [f for f in listdir(album_path) if isfile(join(album_path, f))]
        files_alb = [s.replace('.json', '') for s in files_alb]
        
        if to_collect >= 1:
            # Get list of files from eps
            files_ep = [f for f in listdir(ep_path) if isfile(join(ep_path, f))]
            files_ep = [s.replace('.json', '') for s in files_ep]
            
            if to_collect >= 2:
                # Get list of files from mixtapes
                files_mix = [f for f in listdir(mixtape_path) if isfile(join(mixtape_path, f))]
                files_mix = [s.replace('.json', '') for s in files_mix]
            
    files = files_alb + files_ep + files_mix  # make single list

    try :
        files.remove('.DS_Store')
    except ValueError:
        print()

    return files

# Function to get the discography from RYM and add to dataframe
def get_album_list(urls, names, name, to_collect=2):
    
    network = rymscraper.RymNetwork()  # main scraper object
    
    # If artist url is supplied, take it, otherwise take name     
    if len(str(urls[name])) > 2:
        discography_infos = network.get_discography_infos(url=urls[name], complementary_infos=False)
    else:
        discography_infos = network.get_discography_infos(name=names[name], complementary_infos=False)
    
    # don't forget to close and quit the browser (prevent memory leaks)
    network.browser.close()
    network.browser.quit()
    
    print("Discography for: " + names[name] + " gathered successfully!")
    
    # Placeholders for output lists
    artist_list = []
    album_list = []
    date_list = []
    type_list = []
    
    print(discography_infos[0]['Artist'])
    
    # If 0 - collect albums, if 1 - albums+eps, if 2 - albums+eps+mixtapes (all)
    if to_collect >= 0:
        # Loop to get the albums first
        for x in discography_infos:
            # Both these rappers have accent on "e" which breaks the check by name (as csv file with names in UTF-8)
            # So in case of them name is not checked, otherwise it gets checked to be sure it is not wrong artist
            # Same logic applies to all three loops
            if names[name] == 'Andre 3000' or names[name] == 'Red Cafe':  
                if x['Category'] == 'Album':
                    artist_list.append(names[name])
                    album_list.append(x['Name'])
                    date_list.append(x['Year'])
                    type_list.append(x['Category'])
            else:
                if x['Artist'] == names[name] and x['Category'] == 'Album':
                    artist_list.append(names[name])
                    album_list.append(x['Name'])
                    date_list.append(x['Year'])
                    type_list.append(x['Category'])
                    
        if to_collect >= 1:           
            # Loop to get the EPs second          
            for x in discography_infos:
                if names[name] == 'Andre 3000' or names[name] == 'Red Cafe':
                    if x['Category'] == 'EP':
                        artist_list.append(names[name])
                        album_list.append(x['Name'])
                        date_list.append(x['Year'])
                        type_list.append(x['Category'])
                else:
                    if x['Artist'] == names[name] and x['Category'] == 'EP':
                        artist_list.append(names[name])
                        album_list.append(x['Name'])
                        date_list.append(x['Year'])
                        type_list.append(x['Category'])
                        
            if to_collect >= 2:  
                 # Loop to get the mixtapes last
                for x in discography_infos:
                    if names[name] == 'Andre 3000' or names[name] == 'Red Cafe':
                        if x['Category'] == 'Mixtape':
                            artist_list.append(names[name])
                            album_list.append(x['Name'])
                            date_list.append(x['Year'])
                            type_list.append(x['Category'])
                    else:
                        if x['Artist'] == names[name] and x['Category'] == 'Mixtape':
                            artist_list.append(names[name])
                            album_list.append(x['Name'])
                            date_list.append(x['Year'])
                            type_list.append(x['Category'])
    
    # All the ouputs collected into df
    d = {'Artist': artist_list, 'Album':album_list, 'Year': date_list, 'Type': type_list}
    df = pd.DataFrame(d)
    df['Year'] = pd.to_numeric(df['Year'])
    df = df.sort_values(by=['Type', 'Year'])
    
    return df

    # Function to gather album with lyrics from Genius
def load_album(df, i, token):
    
    # Set the recommended parametrs in order collection not to fail
    token = token
    genius = lyricsgenius.Genius(token)
    genius.retries = 3
    genius.timeout = 10
    
    # Check all the paths, if the album was already gathered, if yes = do not download
    if os.path.exists('data/'+df.iloc[i,0]+'/albums/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json'):
        data = "album exists"
        print("Album: " + df.iloc[i,1] + " already stored!")
    elif os.path.exists('data/'+df.iloc[i,0]+'/eps/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json'):    
        data = "album exists"
        print("Album: " + df.iloc[i,1] + " already stored!")
    elif os.path.exists('data/'+df.iloc[i,0]+'/mixtapes/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json'):  
        data = "album exists"
        print("Album: " + df.iloc[i,1] + " already stored!")
   # if there is no album, look for it and download
    else: 
        # Get the album and save it as temp file
        album = genius.search_album(df.iloc[i,1], df.iloc[i,0])
        album.save_lyrics('album.json', overwrite=True)
    
        print("Album: " + df.iloc[i,1] + " gathered successfully!")
        
        with open('album.json') as f:
            data = json.load(f)
        
    return data

# Function to write collectred json albums to folders
def write_album_files(data, df, i, names, name):
    
    # Json files getting stored in respective folder (album, eps, mixtapes) based on the type
    if df.iloc[i,3] == 'Album':
        with open('data/'+names[name]+'/albums/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json', 'w') as fp:
            json.dump(data, fp)
            
    if df.iloc[i,3] == 'EP':
        with open('data/'+names[name]+'/eps/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json', 'w') as fp:
            json.dump(data, fp)
        
    if df.iloc[i,3] == 'Mixtape':
        with open('data/'+names[name]+'/mixtapes/'+re.sub(r'[^\w\s]','',df.iloc[i,1])+'.json', 'w') as fp:
            json.dump(data, fp)
        
        
    print('Album ' + data['name'] + ' written to json file!')

# Function to write rapper album list df to csv
def write_df(df, names, name):
    
    df.to_csv('data/'+names[name]+'/albums.csv', index=False)
    print('Discography for:  ' + df.iloc[0,0] + ' written to csv!')
    
def add_data_folder():
    # Folders are created if non existent
    if os.path.exists('data/') == False:
            os.makedirs('data')
    
def create_folders(names, name):     
    # Folders are created if non existent
    if os.path.exists('data/'+names[name]) == False:
            os.makedirs('data/'+names[name])
            
    if os.path.exists('data/'+names[name]+'/albums') == False:
            os.makedirs('data/'+names[name]+'/albums')
            
    if os.path.exists('data/'+names[name]+'/eps') == False:
            os.makedirs('data/'+names[name]+'/eps')
            
    if os.path.exists('data/'+names[name]+'/mixtapes') == False:
            os.makedirs('data/'+names[name]+'/mixtapes')