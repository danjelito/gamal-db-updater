import pandas as pd
import numpy as np


def clean_telepon_col(df, telepon_column):
    """
    Clean telepon column.
    """

    data = (
        df[telepon_column]
        .astype(str)
        .str.replace("+", "", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
    )
    conditions = [
        data.str.startswith("6208"),
        data.str.startswith("8"),
        data.str.startswith("08"),
        True,
    ]
    choices = [
        data.str.replace("^6208", "628", regex=True),
        data.str.replace("^8", "628", regex=True),
        data.str.replace("^08", "628", regex=True),
        data,
    ]
    return np.select(conditions, choices)


def clean_platform(df, platform_column):
    """
    Clean platform column.
    """

    data = df[platform_column].str.replace("_", " ").str.title().str.strip()
    conditions = [
        data == "Shopee",
        data == "Tokopedia",
        data == "Tiktok",
        data == "Lazada",
        data.isin(["Webstore", "Website", "Web", "Tada", "Internal"]),  # Website
        data.isin(["Social Media", "Wa"]),  # WA
        data.isin(["Reseller"]),  # Reseller
    ]
    choices = [
        "Shopee",
        "Tokopedia",
        "Tiktok",
        "Lazada",
        "Website",
        "WA",
        "Reseller",
    ]
    return np.select(conditions, choices, default=data)


def get_nc_ro_boolean(df, df_db, telepon_column, flag):
    """
    Function that checks if the telepon has appared in main DB.
    Create a new column in a DF.
    """

    list_telepon = df_db["Telepon"].unique()

    ro = df[telepon_column].isin(list_telepon)
    if flag == "RO":
        return ro
    elif flag == "NC":
        return ro == False
    else:
        raise Exception("flag unrecognized")


def clean_df_daily(df_daily, df_db):
    """
    Clean DF daily.
    """

    df_daily_cleaned = (
        df_daily
        # exclude Bikinganteng_id
        .loc[~(df_daily["Nama toko"].isin(["Bikinganteng_id", "bikinganteng_id"]))]
        # exclude status pending
        .loc[lambda df_: ~(df_["Status MP"].isin(["Pending"]))]
        # make the column name the same with the column in db
        .rename(columns={"Kota/Kabupaten": "KOTA", "No. Telepon": "Telepon"})
        .assign(
            # clean telepon
            Telepon=lambda df_: clean_telepon_col(df_, "Telepon"),
            # clean platform
            Platform=lambda df_: clean_platform(df_, "Platform"),
        )
        .assign(
            # if telepon isna, replace that with no.pesanan
            Telepon_placeholder=lambda df_: np.where(
                df_["Telepon"] == "nan", df_["No. Pesanan"], df_["Telepon"]),
            # get nc ro
            is_nc=lambda df_: get_nc_ro_boolean(df_, df_db, "Telepon_placeholder", "NC"),
            is_ro=lambda df_: get_nc_ro_boolean(df_, df_db, "Telepon_placeholder", "RO"),
        )
    )
    return df_daily_cleaned


def get_num_order_per_plaform(df, no_pesanan_column, platform_column, platform):
    """
    Get number of order per platform.
    """
    return df.loc[(df[platform_column] == platform), no_pesanan_column].nunique()


def get_customer_by_platform(df, platform_col, platform, telepon_col, nc_col, nc=True):
    """
    Get the number of customer by platform.
    """
    if nc:
        return df.loc[
            ((df[platform_col] == platform) & (df[nc_col] == True)), telepon_col
        ].nunique()
    else:
        return df.loc[(df[platform_col] == platform), telepon_col].nunique()


def get_summary_per_day(df):
    """
    Get summary DF.
    """

    paket_basic_sku = ["Gamalpackage05"]

    # number of order by platform
    num_reseller = get_num_order_per_plaform(df, "No. Pesanan", "Platform", "Reseller")
    num_tiktok = get_num_order_per_plaform(df, "No. Pesanan", "Platform", "Tiktok")
    num_tokopedia = get_num_order_per_plaform(
        df, "No. Pesanan", "Platform", "Tokopedia"
    )
    num_shopee = get_num_order_per_plaform(df, "No. Pesanan", "Platform", "Shopee")
    num_wa = get_num_order_per_plaform(df, "No. Pesanan", "Platform", "Wa")
    num_lazada = get_num_order_per_plaform(df, "No. Pesanan", "Platform", "Lazada")

    # number of order from nc and ro
    num_order_from_nc = df.loc[(df["is_nc"] == True), "No. Pesanan"].nunique()
    num_order_from_ro = df.loc[(df["is_ro"] == True), "No. Pesanan"].nunique()
    total_order = num_order_from_ro + num_order_from_nc

    # omzet
    total_setelah_diskon_nc = df.loc[(df["is_nc"] == True), "Jumlah"].sum()
    total_setelah_diskon_ro = df.loc[(df["is_ro"] == True), "Jumlah"].sum()
    total_setelah_diskon = total_setelah_diskon_nc + total_setelah_diskon_ro

    # new customer
    nc_tiktok = get_customer_by_platform(
        df, "Platform", "Tiktok", "Telepon_placeholder", "is_nc", nc=True
    )
    nc_shopee = get_customer_by_platform(
        df, "Platform", "Shopee", "Telepon_placeholder", "is_nc", nc=True
    )
    nc_tokopedia = get_customer_by_platform(
        df, "Platform", "Tokopedia", "Telepon_placeholder", "is_nc", nc=True
    )
    nc_lazada = get_customer_by_platform(
        df, "Platform", "Lazada", "Telepon_placeholder", "is_nc", nc=True
    )

    # num paket basic
    num_basic = df.loc[
        df["SKU Induk"].isin(paket_basic_sku), "Telepon_placeholder"
    ].nunique()
    num_basic_nc = df.loc[
        (df["SKU Induk"].isin(paket_basic_sku) & df["is_nc"] == True),
        "Telepon_placeholder",
    ].nunique()

    # num product sold
    num_prod_sold_reg = df.loc[
        df["Platform"] != "Reseller", "Jumlah Produk di Pesan"
    ].sum()
    num_prod_sold_reseller = df.loc[
        df["Platform"] == "Reseller", "Jumlah Produk di Pesan"
    ].sum()

    data = {
        "ORDER PER PLATFORM": "",
        "Order Reseller": num_reseller,
        "Order Tiktok": num_tiktok,
        "Order Tokopedia": num_tokopedia,
        "Order Shopee": num_shopee,
        "Order WA": num_wa,
        "Order Lazada": num_lazada,
        "ORDER PER BUYER": "",
        "Order NC": num_order_from_nc,
        "Omzet NC": total_setelah_diskon_nc,
        "Order RO": num_order_from_ro,
        "Omzet RO": total_setelah_diskon_ro,
        "TOTAL ORDER AND OMZET": "",
        "Total Order": total_order,
        "Total Omzet": total_setelah_diskon,
        "NC PER PLATFORM": "",
        "NC Tiktok": nc_tiktok,
        "NC Shopee": nc_shopee,
        "NC Tokopedia": nc_tokopedia,
        "NC Lazada": nc_lazada,
        "PAKET BASIC": "",
        "NC Paket Basic": num_basic_nc,
        "Total Customer Paket Basic": num_basic,
        "JUMLAH PRODUK TERJUAL": "",
        "Regular": num_prod_sold_reg,
        "Reseller": num_prod_sold_reseller,
    }

    df_result = pd.DataFrame(index=data.keys(), data=data.values(), columns=["value"])
    return df_result
