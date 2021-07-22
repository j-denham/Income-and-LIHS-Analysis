import pandas as pd
import numpy as np
import re


def bedroom_string_to_int(bedroom_string):
    str_to_int_dict = {
        'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6
    }
    split_string = str(bedroom_string).split()

    # Cheeky sanity checks to ensure minimal hair pulling
    assert(len(split_string) >= 2)
    assert(str_to_int_dict[split_string[0]])

    return str_to_int_dict[split_string[0]]


def rent_range_to_average(rent_range_string):
    bounds = re.findall("\\d+", rent_range_string)
    if len(bounds) == 1:
        # Sanity check as only rent entry that should trigger this is '950 and over'
        assert(int(bounds[0]) == 950)
        return bounds[0]
    assert(len(bounds) == 2)
    return (int(bounds[0]) + int(bounds[1])) / 2


def calculate_average_bedrooms_df():
    # Num Bedrooms per dwelling dataset
    dwelling_df = pd.read_csv('../Datasets/Dwelling-Structure-And-Number-Of-Bedrooms-By-SA2-2006-2011-2016.csv', encoding = 'ISO-8859-1')
    # Trim unneeded columns
    dwelling_df = dwelling_df.loc[
        :,
        ['Number of Bedrooms', 'Dwelling Structure', 'Region', 'Census year', 'Value']
    ].replace(
        ['Total', 'Not stated', 'None (includes bedsitters)'],
        np.nan
    ).dropna()

    dwelling_df['Number of Bedrooms'] = dwelling_df['Number of Bedrooms'].apply(bedroom_string_to_int)

    # Essentially the cleaned dwelling_df, but sorted for better viewing.
    # Probably better to use set_index... but the below set_index is
    # returning errors and I'm too lazy to fix it atm :)
    dwelling_df = dwelling_df.groupby(
        ['Region', 'Dwelling Structure', 'Census year', 'Number of Bedrooms']
    ).sum()

    # TEST: Run a diff, see if the csvs are still the same
    # dwelling_df.set_index(['Dwelling Structure', 'Region', 'Census year', 'Number of Bedrooms'], inplace=True)
    # dwelling_df.sort_values(by=['Dwelling Structure', 'Region', 'Census year', 'Number of Bedrooms'], inplace=True)

    # Total count of houses of each dwelling type
    dwelling_groups_totals_df = dwelling_df.groupby(
        ['Region', 'Dwelling Structure', 'Census year']
    ).sum().rename(columns={'Value': 'Total'})
    dwelling_groups_totals_df['Average Bedrooms'] = 0

    # This loop may take a while on your machine, give it a minute or two
    for index, row in dwelling_groups_totals_df.iterrows():
        # print('INDEX: ' + str(index))
        # print('ROW: ' + str(row))
        mean = 0
        # Avoid division by 0 errors in below loop
        if row['Total'] == 0:
            continue
        for i in range(1, 7):
            full_index = (index[0], index[1], index[2], i)
            # num houses of particular dwelling type and bedroom count * num bedrooms / total num of bedrooms of that dwelling type
            weighted_element = dwelling_df.loc[full_index].values[0] * i / row['Total']
            mean += weighted_element
        dwelling_groups_totals_df.loc[index, 'Average Bedrooms'] = mean


    # TEST: Just a cheeky save to peruse the results :D
    # dwelling_df.to_csv('../Datasets/dwelling-test.csv')
    # dwelling_groups_df.to_csv('../Datasets/dwelling-groups-sum-test.csv')
    # dwelling_groups_totals_df.to_csv('../Datasets/dwelling-groups-totals-test.csv')

    return dwelling_groups_totals_df


def calculate_average_rent(average_bedrooms_df):
    weekly_rent_df = pd.read_csv('../Datasets/Rent-Weekly-By-SA2-Melbourne-2006-2011-2016.csv')
    # Trim unneeded columns and entries
    weekly_rent_df = weekly_rent_df.loc[
        :,
        ['Dwelling Structure', 'Rent (weekly)', 'Region', 'Census year', 'Value']
    ].replace(
        ['Total', 'Not stated', 'Nil payments'],
        np.nan
    ).dropna()

    weekly_rent_df['Rent (weekly)'] = weekly_rent_df['Rent (weekly)'].apply(rent_range_to_average)
    weekly_rent_df.set_index(
        ['Region', 'Dwelling Structure', 'Census year', 'Rent (weekly)'],
        inplace=True
    )
    weekly_rent_df.sort_values(
        by=['Region', 'Dwelling Structure', 'Census year'],
        inplace=True
    )

    # Sum the totals for later use in weighted mean
    weekly_rent_dwelling_totals_df = weekly_rent_df.groupby(
        ['Region', 'Dwelling Structure', 'Census year']
    ).sum().rename(columns={'Value': 'Total'})
    weekly_rent_region_totals_df = weekly_rent_dwelling_totals_df.groupby(
        ['Region', 'Census year']
    ).sum().rename(columns={'Value': 'Total'})

    idx = pd.IndexSlice
    # UNCOMMENT THIS LOOP IF CALCULATING FROM SCRATCH
#     weekly_rent_dwelling_totals_df['Mean rent per dwelling'] = 0
#     for index, row in weekly_rent_dwelling_totals_df.iterrows():
#         mean = 0
#         average_bedrooms_per_dwelling = average_bedrooms_df.loc[index, 'Average Bedrooms']
#         if row['Total'] == 0 or average_bedrooms_per_dwelling == 0:
#             continue
#         weekly_rent_slice_df = weekly_rent_df.loc[idx[index[0], index[1], index[2], :], :]
#         for index0, row0 in weekly_rent_slice_df.iterrows():
#             weekly_rent_count = int(row0[0])
#             rent_range = int(index0[3])
#             # print('Weekly rent count for the dwelling type: ' + str(weekly_rent_count))
#             # print('This should be rent range: ' + str(index0[3]))
#             mean += rent_range * weekly_rent_count / row['Total']
#         mean = mean / average_bedrooms_per_dwelling
#         weekly_rent_dwelling_totals_df.loc[index, 'Mean rent per dwelling'] = mean

    # TEST: These are to avoid running the above loop. Comment out later
    # for full functionality
    weekly_rent_dwelling_totals_df = pd.read_csv('../Datasets/weekly-rent-dwelling-totals-test.csv')
    weekly_rent_dwelling_totals_df.set_index(
        ['Region', 'Dwelling Structure', 'Census year'],
        inplace=True
    )

    weekly_rent_region_totals_df['Mean rent per person'] = 0
    for index, row in weekly_rent_region_totals_df.iterrows():
        mean = 0
        total_rental_properties = row['Total']
        if total_rental_properties == 0:
            continue
        weekly_rent_per_dwelling_slice = weekly_rent_dwelling_totals_df.loc[
            idx[index[0], :, index[1]],
            :
        ]
        for index0, row0 in weekly_rent_per_dwelling_slice.iterrows():
            total_dwelling_count = int(row0['Total'])
            mean_dwelling_rent = int(row0['Mean rent per dwelling'])
            mean += mean_dwelling_rent * total_dwelling_count / total_rental_properties
        weekly_rent_region_totals_df.loc[index, 'Mean rent per person'] = mean

    # TEST: Have a looksie, see if everything is all good
    # weekly_rent_df.to_csv('../Datasets/weekly-rent-test.csv')
    # weekly_rent_dwelling_totals_df.to_csv('../Datasets/weekly-rent-dwelling-totals-test.csv')
    # weekly_rent_region_totals_df.to_csv('../Datasets/weekly-rent-region-totals-test.csv')

    return weekly_rent_region_totals_df


def calculate_cost_proportion(average_rent_per_person_srs, cost_of_living, centrelink_weekly_income):
    # Need to find data for weekly centrlink income for 2006, 2011
    cost_of_living_proportion_srs = average_rent_per_person_srs.apply(
        lambda x: (x + cost_of_living) / centrelink_weekly_income
    )

#     cost_of_living_df = average_rent_per_person_df.reindex(
#         columns=['Region', 'Census year', 'Mean rent per person', 'Cost of living proportion']
#     )

    return cost_of_living_proportion_srs


# Run the below if the dfs needs to be reconstructed, otherwise
# save your poor computer the trouble and load them instead!
# average_bedrooms_df = calculate_average_bedrooms_df()
# average_bedrooms_df.to_csv('../Datasets/Average-Number-of-Bedrooms-Per-Dwelling-Structure-2006-2011-2016-test.csv')
# average_rent_per_person_df = calculate_average_rent(average_bedrooms_df)

# Otherwise save your poor compute the trouble and load them insted!
average_bedrooms_df = pd.read_csv('../Datasets/Average-Number-of-Bedrooms-Per-Dwelling-Structure-2006-2011-2016.csv', encoding = 'ISO-8859-1')
average_bedrooms_df.set_index(['Region', 'Dwelling Structure', 'Census year'], inplace=True)
average_rent_per_person_df = pd.read_csv('../Datasets/Average-Weekly-Rent-Per-Person-2006-2011-2016.csv')

average_rent_per_person_2011_df = average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2011,
    :
]

average_rent_per_person_2016_df = average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2016,
    :
]
# 2011 Cost of living = 75 [Weekly groceries] + 35 [Misc costs like bills, transport etc.]
# 2011 Youth Allowance/Austudy [388.70 + 79.60 = 468.3 a fortnight]
cost_of_living_proportion_2011_youth_srs = calculate_cost_proportion(average_rent_per_person_2011_df['Mean rent per person'], 110, 234.15)
# 2011 Newstart [486.60 + 79.60 = 566.2 a fortnight]
cost_of_living_proportion_2011_newstart_srs = calculate_cost_proportion(average_rent_per_person_2011_df['Mean rent per person'], 110, 283.1)
# 2016 Cost of living = 87.5 [Weekly groceries] + 42.5 [Misc costs like bills, transport etc.]
# 2016 Youth Allowance/Austudy/Newstart under 22 [433.20 + 87.07 = 520.27 a fortnight]
cost_of_living_proportion_2016_youth_srs = calculate_cost_proportion(average_rent_per_person_2016_df['Mean rent per person'], 130, 260.135)
# 2016 Newstart/Jobseeker over 22 [528.70 + 87.07 = 615.77]
cost_of_living_proportion_2016_newstart_srs = calculate_cost_proportion(average_rent_per_person_2016_df['Mean rent per person'], 130, 307.89)


average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2011,
    ['Cost of living proportion (Youth Allowance)']
] = cost_of_living_proportion_2011_youth_srs
average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2011,
    ['Cost of living proportion (Newstart)']
] = cost_of_living_proportion_2011_newstart_srs

average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2016,
    ['Cost of living proportion (Youth Allowance)']
] = cost_of_living_proportion_2016_youth_srs
average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] == 2016,
    ['Cost of living proportion (Newstart)']
] = cost_of_living_proportion_2016_newstart_srs

# cost_of_living_df = average_rent_per_person_2011_df.append(average_rent_per_person_2016_df, ignore_index=True)
average_rent_per_person_df = average_rent_per_person_df.loc[
    average_rent_per_person_df['Census year'] != 2006,
    :
]
cost_of_living_df = average_rent_per_person_df.reindex(
    columns=['Region', 'Census year', 'Mean rent per person', 'Cost of living proportion (Youth Allowance)', 'Cost of living proportion (Newstart)']
)
cost_of_living_df.sort_values(by=['Region', 'Census year'], inplace=True)

cost_of_living_df.to_csv('../Datasets/Cost-of-Living-By-SA2-Year-2006-2011-2016.csv')
# cost_of_living_proportion_df.to_csv('../Datasets/Adjusted-Cost-of-Living-By-SA2-Year-2006-2011-2016.csv')
