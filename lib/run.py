# coding: utf-8

import pandas as pd

if __name__ == '__main__':
    test = pd.read_csv('/task-for-hiring-data/test_data.csv')

    target_prediction = pd.DataFrame()
    target_prediction['index'] = range(test.shape[0])
    target_prediction['prediction'] = 0

    mask_prediction = pd.DataFrame()
    mask_prediction['index'] = range(test.shape[0])
    mask_prediction['start'] = None
    mask_prediction['end'] = None

    target_prediction.to_csv('/task-for-hiring-data/target_prediction.csv', index=False)
    mask_prediction.to_csv('/task-for-hiring-data/mask_prediction.csv', index=False)
