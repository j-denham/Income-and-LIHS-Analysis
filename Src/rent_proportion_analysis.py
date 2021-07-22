import pandas as pd
import matplotlib.pyplot as plt
from rent_proportion_processor import calculate_cost_proportion


def count_cost_of_living(cost_of_living_df):
    cost_of_living_by_year_groups = cost_of_living_df.groupby(['Census year'])

    for name, group in cost_of_living_by_year_groups:
        youth_total = len(group['Cost of living proportion (Youth Allowance)'].values)
        newstart_total = len(group['Cost of living proportion (Newstart)'].values)
        youth_amount_over_1 = sum([1 for x in group['Cost of living proportion (Youth Allowance)'].values if x >= 1])
        newstart_amount_over_1 = sum([1 for x in group['Cost of living proportion (Newstart)'].values if x >= 1])
#         print('YEAR: ' + str(name))
#         print('NUMBER OVER 1: ' + str(amount_over_1))
#         print('TOTAL: ' + str(total))
        youth_proportion = youth_amount_over_1 / youth_total
        newstart_proportion = newstart_amount_over_1 / newstart_total
#         print('PROPORTION ' + str(proportion))
        plot_cost_of_living(group, name, youth_proportion, newstart_proportion)


def plot_cost_of_living(cost_of_living_df, year, youth_proportion, newstart_proportion):
#     plt.scatter(
#         cost_of_living_df['Region'], cost_of_living_df['Cost of living proportion'], color='green', s=5
#     )
#     print('PLOT TOTAL: ' + str(len(cost_of_living_df['Cost of living proportion'].values)))
#     plt.title('Actual Cost of Living Proportion by Suburb for {}'.format(year))
#     #plt.title('Adjusted Cost of Living Proportion by Suburb for {}'.format(year))
#     plt.plot(markersize=0.3)
#     plt.xscale('linear')
#     plt.yscale('linear')
#     plt.tick_params(bottom=False, labelbottom=False)
#     plt.xlabel('Percentage > 1 = {:.2f}%'.format(proportion * 100))
#     plt.ylabel('Cost of Living Proportion')
#     plt.grid(True)
#     plt.savefig(fname='../Plots/cost_of_living_scatter_{}.png'.format(year))
#     #plt.savefig(fname='../Plots/adjusted-cost_of_living_scatter_{}.png'.format(year))
    fig, ax = plt.subplots()
    ax.scatter(
        cost_of_living_df['Region'], cost_of_living_df['Cost of living proportion (Youth Allowance)'], color='green', s=5, label='Youth Allowance'
    )
    ax.scatter(
        cost_of_living_df['Region'], cost_of_living_df['Cost of living proportion (Newstart)'], color='red', s=5, label='Newstart'
    )
    ax.legend()
    ax.plot(markersize=0.3)
    if year == 2021:
        plt.title('Predicted Cost of Living Proportion by Suburb for {}'.format(year))
    else:
        plt.title('Actual Cost of Living Proportion by Suburb for {}'.format(year))
        #plt.savefig(fname='../Plots/adjusted-cost_of_living_scatter_{}.png'.format(year))
    plt.xscale('linear')
    plt.yscale('linear')
    plt.tick_params(bottom=False, labelbottom=False)
    plt.xlabel('Youth Allowance Percentage > 1 = {:.2f}%\nNewstart Percentage > 1 = {:.2f}%'.format(youth_proportion * 100, newstart_proportion * 100))
    plt.ylabel('Cost of Living Proportion')
    ax.grid(True)
    plt.savefig(fname='../Plots/cost_of_living_scatter_{}.png'.format(year))


def plot_average_rent_over_years(cost_of_living_df):
    rent_groups = cost_of_living_df.loc[
        :,
        ['Region', 'Census year', 'Mean rent per person']
    ].groupby(['Census year']).mean()

    # print(rent_groups)


# Regression not appropriate as it'll be extrapolating beyond observed range
# Therefore, use CPI to estimate the increase in rent prices from average
# rent in 2016, then calculate cost of living from this value
def predict_rent_2021(cost_of_living_df):
    # Remove index column
    cost_of_living_df = cost_of_living_df.loc[
        :,
        ['Region', 'Census year', 'Mean rent per person', 'Cost of living proportion (Youth Allowance)', 'Cost of living proportion (Newstart)']
    ]
    rent_cpi_df = pd.read_csv('../Datasets/CPI-Housing-Since-2016.csv')
    rent_cpi_quarterly_increase = rent_cpi_df['Percentage increase'].values
    cost_of_living_df_2016 = cost_of_living_df.loc[
        cost_of_living_df['Census year'] == 2016,
        ['Region', 'Census year', 'Mean rent per person']
    ]

    print(cost_of_living_df_2016)
    cost_of_living_2021_df = pd.DataFrame(
        columns=['Region', 'Census year', 'Mean rent per person']
    )
    for index, row in cost_of_living_df_2016.iterrows():
        rent_2021 = row['Mean rent per person']
        for i in rent_cpi_quarterly_increase:
            rent_2021 = rent_2021 * (1 + (i / 100))
        row_2021 = {
            'Region': row['Region'],
            'Census year': 2021,
            'Mean rent per person': rent_2021
        }
        cost_of_living_2021_df = cost_of_living_2021_df.append(row_2021, ignore_index=True)

    # Cost of living = 100 [Groceries] + 50 [Transport, bills etc.]
    # Youth Allowance/Austudy/Jobseeker under 22 [512.50 + 93.87 = 606.37 fornightly]
    cost_of_living_2021_df['Cost of living proportion (Youth Allowance)'] = calculate_cost_proportion(cost_of_living_2021_df['Mean rent per person'], 150, 303.185)
    # Jobseeker over 22 [620.80 + 93.87 = 714.67 fornightly]
    cost_of_living_2021_df['Cost of living proportion (Newstart)'] = calculate_cost_proportion(cost_of_living_2021_df['Mean rent per person'], 150, 357.335)

    predicted_cost_of_living_df = cost_of_living_df.append(cost_of_living_2021_df, ignore_index=True)
    predicted_cost_of_living_df.sort_values(by=['Region', 'Census year'], inplace=True)

    return predicted_cost_of_living_df




cost_of_living_df = pd.read_csv('../Datasets/Cost-of-Living-By-SA2-Year-2006-2011-2016.csv')
#cost_of_living_df = pd.read_csv('../Datasets/Adjusted-Cost-of-Living-By-SA2-Year-2006-2011-2016.csv')
#count_cost_of_living(cost_of_living_df)
#plot_average_rent_over_years(cost_of_living_df)
predicted_cost_of_living_df = predict_rent_2021(cost_of_living_df)
predicted_cost_of_living_df.to_csv('../Datasets/Predicted-Cost-of-Living-By-SA2-Year.csv')
count_cost_of_living(predicted_cost_of_living_df)

