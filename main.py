import streamlit as st
import pandas as pd
import numpy as np
from src import module

st.title('Gamal Daily Sales Recap')

st.subheader('Langkah 1: Upload Data')

st.warning('Pastikan data hari ini belum masuk ke DB', icon="⚠️")
df_daily = st.file_uploader("Upload data harian hari ini disini")
df_db = st.file_uploader("Upload DB sampai dengan hari sebelumnya disini")


if (df_db is not None) and (df_daily is not None):

    # read files
    with st.spinner('Mohon tunggu, sedang mengupload...'):
        df_db = pd.read_excel(df_db)
        df_daily = pd.read_excel(df_daily)

        # assert than DB is before daily
        db_date= df_db['Tanggal'].max() - pd.Timedelta('1 minute')
        daily_date= df_daily['Tanggal'].max()
        if db_date > daily_date:
            st.error('Tanggal daily lebih awal daripada tanggal DB', icon="🚨")

    # do the calculation
    with st.spinner('Menghitung...'):
        df_daily_clean = module.clean_df_daily(df_daily, df_db)
        summary = module.get_summary_per_day(df_daily_clean)
    st.success('Perhitungan selesai!', icon="✅")
    
    # display result
    st.subheader('Langkah 2: Masukkan Rekap di Bawah ke KPI Ads')
    summary_st= st.dataframe(data= summary, width= 900)

    # download merged DB
    st.subheader('Langkah 3: Download Full Database')

    with st.spinner('Mempersiapkan database...'):
        cols= df_db.columns
        df_daily_clean= df_daily_clean[cols]
        df_merged= pd.concat([df_db, df_daily_clean], axis = 0)
        date= df_daily_clean['Tanggal'].max().strftime('%d %b %Y')
        filename= f'DB - {date}.xlsx'

        # write dataframe
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_merged.to_excel(writer, sheet_name='Sheet1', index=False)
            writer.close()

            st.success('Download siap!', icon="✅")
            
            # render download button
            st.download_button(
                label= "Click Untuk Mendownload Full DB",
                data= buffer,
                file_name= filename,
                mime= "application/vnd.ms-excel"
            )