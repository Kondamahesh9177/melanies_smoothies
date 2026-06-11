import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Page Title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Customer Name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Snowflake Connection
cnx = st.connection("snowflake")
session = cnx.session()

# Read Fruit Data
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

# Convert to Pandas
pd_df = my_dataframe.to_pandas()

# Display table for debugging
# st.dataframe(pd_df)

# Fruit Selection
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

if ingredients_list:

    ingredients_string = ''

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + ' '

        try:
            search_on = pd_df.loc[
                pd_df['FRUIT_NAME'] == fruit_chosen,
                'SEARCH_ON'
            ].iloc[0]

            st.write(
                f"Fruit Selected: {fruit_chosen} | Search Value: {search_on}"
            )

            if pd.isna(search_on) or str(search_on).strip() == "":
                st.error(
                    f"SEARCH_ON value missing for {fruit_chosen} in FRUIT_OPTIONS table."
                )
                continue

            st.subheader(f"{fruit_chosen} Nutrition Information")

            api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on}"

            response = requests.get(api_url)

            if response.status_code == 200:

                fruit_data = response.json()

                # Check if API returned an error message
                if isinstance(fruit_data, dict) and "message" in fruit_data:
                    st.error(
                        f"API Error for {fruit_chosen}: {fruit_data['message']}"
                    )
                else:
                    st.dataframe(
                        pd.json_normalize(fruit_data),
                        use_container_width=True
                    )

            else:
                st.error(
                    f"API returned status code {response.status_code}"
                )

        except Exception as e:
            st.error(
                f"Error processing {fruit_chosen}: {str(e)}"
            )

    # Order Insert Statement
    my_insert_stmt = f"""
        INSERT INTO SMOOTHIES.PUBLIC.ORDERS
        (INGREDIENTS, NAME_ON_ORDER)
        VALUES
        ('{ingredients_string.strip()}','{name_on_order}')
    """

    time_to_insert = st.button('Submit Order')

    if time_to_insert:

        try:
            session.sql(my_insert_stmt).collect()

            st.success(
                f'Your Smoothie is ordered, {name_on_order}!',
                icon="✅"
            )

        except Exception as e:
            st.error(
                f"Failed to save order: {str(e)}"
            )
