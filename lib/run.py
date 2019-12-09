# coding: utf-8

import pandas as pd
import numpy as np
import sys
import os
import zipfile
import re
import string
import pickle

from find_borders import find_borders
from morph_funcs import lemmatize, preprocessing_all_method

INPUT_FILE_PATH = '/task-for-hiring-data/test_data.csv'
OUTPUT_FILE_PATH = '/task-for-hiring-data/target_prediction.csv'
OUTPUT_WITH_STAR_FILE_PATH = '/task-for-hiring-data/mask_prediction.csv'


def load_pickle(filepath):

    with open(filepath, 'rb') as handle:
        b = pickle.load(handle)

    return b


def get_categories(df_):

    category_dumm = pd.DataFrame(index=df_.index)

    for category in categories:
        category_dumm[f'category_{category}_dumm'] = df_['category'] == category

    category_dumm = category_dumm.astype(float)

    return category_dumm


def get_tf_features(df_):

    tf_features_lemm = tfidf_lemm.transform(df_['lemm_description'])

    tfidf_df_lemm = pd.DataFrame(
        tf_features_lemm.todense(),
        columns=tfidf_lemm.get_feature_names()
    )

    top_400_lems_df = tfidf_df_lemm[top_400_feat_full_tfidf]
    top_400_lems_df.columns = [f'lemm_{col}' for col in top_400_lems_df]

    return top_400_lems_df


def get_phone_mask_features(df_):

    contain_masks = ['9\d{9}[^\d]', '89\d{9}[^\d]', '79\d{9}[^\d]', '\+79\d{9}[^\d]',
                     '\+7', '9\d{2}', '89', '79', '\+79']

    phone_mask_features = pd.DataFrame(index=df_.index)

    for ix, mask in enumerate(contain_masks):
        phone_mask_features[f'cm_{ix}'] = df_['description'].str.contains(mask)
        phone_mask_features[f'cm_on_{ix}'] = df_['only_num_descr'].str.contains(mask)

    phone_mask_features = phone_mask_features.astype(float)

    return phone_mask_features


def input_preproccessing(input_file):

    df_ = pd.read_csv(INPUT_FILE_PATH)
    df_['prep_description'] = df_['description']. \
        apply(lambda x: preprocessing_all_method(x, stopwords, eng=False, numbers=True))
    df_['lemm_description'] = df_['prep_description'].str.split().apply(lemmatize)
    df_['lemm_description'] = df_['lemm_description'].fillna('')

    df_['datetime_submitted'] = pd.to_datetime(df_['datetime_submitted'])
    df_['hour_of_day'] = df_['datetime_submitted'].dt.hour
    df_['day_of_week'] = df_['datetime_submitted'].dt.day

    df_['region_filt'] = np.where(df_['region'].isin(region_mapper['region_filt']), df_['region'], 'other')
    df_['city_filt'] = np.where(df_['city'].isin(city_mapper['city_filt']), df_['city'], 'other')

    df_['subcategory'] = \
        np.where(df_['subcategory'].isin(avg_target_subcategory['subcategory']), df_['subcategory'], 'other')
    df_['category'] = \
        np.where(df_['category'].isin(avg_target_category['category']), df_['category'], 'other')

    df_['only_num_descr'] = df_['description'].replace('[^0-9\+]', '', regex=True)

    return df_


def find_borders_safe(string_):

    try:
        return find_borders(string_)
    except:
        return None


def transform_pr_star(pr_ser, train_conc):

    pr_star = pr_ser.copy()
    pr_star['description'] = train_conc['description']
    pr_star['borders'] = pr_star['description'].apply(find_borders_safe)
    pr_star['start'] = pr_star['borders'].str[0]
    pr_star['end'] = pr_star['borders'].str[1]
    pr_star.loc[pr_star['prediction'] < .3, ['start', 'end']] = np.nan
    pr_star = pr_star[['index', 'start', 'end']]
    pr_star = pr_star.fillna(-1).replace({-1: 'None'})

    return pr_star

if __name__ == '__main__':

    ## READING DATA

    with open('dicts/russian_stopwords.txt', 'r') as f:
        stopwords = f.readline()
        stopwords = set(stopwords.split(', '))

    with open('dicts/categories_list.txt', 'r') as f:
        categories = [x.strip() for x in f.readlines()]

    with open('dicts/top_400_lemmas.txt', 'r') as f:
        top_400_feat_full_tfidf = [x.strip() for x in f.readlines()]

    region_mapper = pd.read_csv('dicts/region_mapper.csv')
    city_mapper = pd.read_csv('dicts/city_mapper.csv')

    avg_target_subcategory = pd.read_csv('dicts/avg_target_subcategory.csv')
    avg_target_category = pd.read_csv('dicts/avg_target_category.csv')

    sub_price_medians = pd.read_csv('dicts/sub_price_medians.csv')

    with zipfile.ZipFile('models/tfidf.pickle.zip', 'r') as zip_ref:
        zip_ref.extractall('models/')
    
    tfidf_lemm = load_pickle('models/tfidf.pickle')    
    os.remove('models/tfidf.pickle')
    
    model_columns = load_pickle('models/model_columns.pickle')
    ss = load_pickle('models/scaller.pickle')
    cat_lrs = load_pickle('models/cat_lrs.pickle')

    ## PREPROCCESSING

    df_ = input_preproccessing(INPUT_FILE_PATH)
    category_dumm = get_categories(df_)
    top_400_lems_df = get_tf_features(df_)
    phone_mask_features = get_phone_mask_features(df_)

    df_ = df_.reset_index().merge(city_mapper).merge(region_mapper) \
        .merge(avg_target_subcategory).merge(avg_target_category).merge(sub_price_medians).set_index(
        'index').sort_index()

    df_['price'] = df_['price'].fillna(df_['price_sub_median'])

    drop_columns = ['title', 'description', 'subcategory', 'category', 'region',
                    'city', 'datetime_submitted', 'is_bad', 'prep_description',
                    'only_num_descr', 'lemm_description', 'region_filt', 'city_filt', 'price_sub_median']

    train_conc = pd.concat([df_, category_dumm, phone_mask_features, top_400_lems_df], axis=1)

    ## SEPARATE FOR EVERY CATEGORY
    cat_ixs = {}

    for category in train_conc['category'].unique():
        filt_ix = train_conc['category'] == category
        cat_ixs[category] = list((train_conc['category'][filt_ix]).index)

    X_ss = ss.transform(train_conc[model_columns].astype(float))

    ## APPLY MODELS AND CONCAT RESULTS
    pr_ser = pd.Series()

    for cat in cat_ixs:
        X_cat = X_ss[cat_ixs[cat]]
        pr = cat_lrs[cat].predict_proba(X_cat)[:, 1]
        pr_ser_cat = pd.Series(pr, index=cat_ixs[cat])
        pr_ser = pd.concat([pr_ser, pr_ser_cat])

    pr_ser = pr_ser.sort_index()
    pr_ser = pr_ser.rename('prediction').reset_index()
    pr_ser.to_csv(OUTPUT_FILE_PATH, index=False)

    ## TASK WITH STAR

    pr_star = transform_pr_star(pr_ser, train_conc)
    pr_star['start'] = pr_star['start'].apply(str).apply(lambda x: x.split('.')[0])
    pr_star['end'] = pr_star['end'].apply(str).apply(lambda x: x.split('.')[0])
    pr_star.to_csv(OUTPUT_WITH_STAR_FILE_PATH, index=False)
    