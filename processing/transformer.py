import application
from datamodel.request import RossmannRequest
import pandas as pd


def transform_to_df(requests: list[RossmannRequest]):
    sam = [request.dict() for request in requests]
    df = pd.DataFrame(sam)

    df[['Promo', 'SchoolHoliday']] = df[['Promo', 'SchoolHoliday']].astype('object')
    df.drop(['Open'], axis=1, inplace=True)

    # New features
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df.Date.dt.year
    df['Month'] = df.Date.dt.month
    df['DayOfMonth'] = df.Date.dt.day
    df['WeekOfYear'] = df.Date.dt.isocalendar().week
    df.drop('Date', axis=1, inplace=True)

    # Merging
    df_merged = df.merge(application.store_data, how='inner', on='Store')
    df_merged['WeekOfYear'] = df_merged['WeekOfYear'].astype('int')

    # Again some features
    df_merged['Current-OpenComp'] = 12 * (df_merged['Year'] - df_merged['CompetitionOpenSinceYear']) \
                                    + (df_merged['Month'] - df_merged['CompetitionOpenSinceMonth'])
    df_merged['Current-OpenPromo'] = 12 * (df_merged['Year'] - df_merged['Promo2SinceYear']) \
                                     + (df_merged['Month'] - df_merged['Promo2SinceWeek'] * 12 / 52)

    # Encoding
    for i, col in enumerate(df_merged.loc[:, df_merged.dtypes == 'object']):
        df_merged[col].replace(application.maps[i], inplace=True)

    return df_merged
