import pandas as pd
import streamlit as st

pd.options.mode.copy_on_write = True

seed_df = pd.read_csv("seed_df_clean.csv")

town_dict = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}


def town_rank(rank):
    return town_dict[rank]


def budget(gold, min_seed_qty):
    pps = (gold+1)/min_seed_qty
    return pps


def gib_crops(date, rank, season, exclude_crops=[], pps=300, multi=True):
    rec_crops = []
    avail_days = 28 - date

    # setting up the df based on input parameters
    working_df = seed_df[seed_df["season"] == season]  # specific season
    query_df = working_df[
        working_df["town_rank"] >= rank
    ]  
    just_these_df = query_df.query('name not in @exclude_crops')
    # determines seed availability
    if multi == False:  # allows to remove multiharvest crops
        just_these_df = just_these_df[just_these_df["is_mult_har"] == False]
    just_these_df = (
        just_these_df[just_these_df["days"] <= avail_days]
        .sort_values("profit_per_day", ascending=False)
        .drop_duplicates("name", keep="first")
    )

    fastest = min(list(just_these_df["days"]))

    while avail_days >= fastest:
        plant_this = {}
        working_df = just_these_df.copy()
        working_df = working_df[working_df["seed_buy_price"] <= pps+1]
        working_df = working_df[working_df["days"] <= avail_days]
        working_df["rem_days"] = avail_days - working_df["days"]
        working_df["multiplant"] = working_df["rem_days"] >= fastest
        working_df.loc[working_df["multiplant"] == False, "profit_per_day"] = (
            working_df["sale_value"] - working_df["seed_buy_price"]
        ) / avail_days
        working_df.sort_values("profit_per_day", ascending=False, inplace=True)
        plant_this["seed"] = working_df["name"].iloc[0]
        plant_this["daily_profit"] = working_df["profit_per_day"].iloc[0]
        plant_this["season_rem_post_harvest"] = working_df["rem_days"].iloc[0]
        avail_days = avail_days - working_df["days"].iloc[0]
        rec_crops.append(plant_this)
        pps = 300
    return rec_crops

def avail_crop_list(rank, season):
    working_df = seed_df[seed_df["season"] == season]  # specific season
    query_df = working_df[working_df["town_rank"] >= rank]
    avails = list(set(query_df["name"]))
    return avails


st.title("Coral Island Crop Planner")
st.subheader("Input your constraints...")
st.subheader("...we will make you BANK")
st.write(
    "Fill in info about your farm and budget -- this calculates which crops will give the best profits for the remainder of the season"
)
st.text("(Disclaimer: This crop planner does not account for crops crossing between seasons)")

# What is the current date?
date = st.slider("Planting Date", min_value=1, max_value=28)

# What season are you working in?
season = st.selectbox(
    "Planting Season", ("Spring", "Summer", "Fall", "Winter")
).lower()

# What is your current town rank? (impacts seed availability)
town_level = st.select_slider(
    "Current Town Rank", options=["F", "E", "D", "C", "B", "A", "S"]
)
rank = town_rank(town_level)


st.write("The next two questions help to calculate your initial per-seed budget.")
# how much gold to spend on seeds?
gold = st.number_input("Max gold to spend:", min_value=15)

# minimum number of seeds to buy?
min_seeds = st.number_input("Minimum seeds to buy:", min_value=1)

st.write("Lastly, let us know if there are any crops you're not interested in planting:")

# Allow multi-harvest crops?
multi = st.toggle("Allow multi-harvest crops? (ie: hot pepper, sugarcane, artichoke)", value=True)

pps = budget(gold, min_seeds)

exclude_crops = []
if st.toggle("Exclude any specific crops?", value=False):
    st.text("(Grey = can be selected, Red = won't be selected)")
    avail_crops = avail_crop_list(rank, season)
    col1, col2 = st.columns(2)
    half = int(len(avail_crops)/2)
    with col1:
        for i in avail_crops[:half]:
            if st.toggle(i.title(), value=False, key=i):
                exclude_crops.append(i)
    with col2:
        for i in avail_crops[half:]:
            if st.toggle(i.title(), value=False, key=i):
                exclude_crops.append(i)

if st.button("Calculate Crops"):
    if pps <= 15:
        st.write("No seeds are available with your budget. :(")
    else:
        plant_these = gib_crops(date, rank, season, exclude_crops, pps, multi)
        for plant in plant_these:
            st.write(
                f"{plant['seed'].title()} ({round(plant['daily_profit'], 2)}g profit per day) "
            )
            if plant["season_rem_post_harvest"] == 1:
                st.text(
                    " . " * 3
                    + f"{plant['season_rem_post_harvest']} day remains after harvest"
                )
            else:
                st.text(
                    " . " * 3
                    + f"{plant['season_rem_post_harvest']} days remaining after harvest"
                )



if __name__ == "__main__":
    gib_crops(11, 4, "summer")
