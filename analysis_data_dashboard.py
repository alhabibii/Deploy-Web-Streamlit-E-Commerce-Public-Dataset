import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Kode Anda untuk mengambil data dan memprosesnya
# Load data dari GitHub
data_paths = {
    'customers': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/customers_dataset.csv',
    'order_items': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/order_items_dataset.csv',
    'order_payments': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/order_payments_dataset.csv',
    'order_reviews': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/order_reviews_dataset.csv',
    'order_dataset': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/orders_dataset.csv',
    'product_category_name_translation': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/product_category_name_translation.csv',
    'product_dataset': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/products_dataset.csv',
    'seller_dataset': 'https://raw.githubusercontent.com/alhabibii/Dataset/main/E-Commerce%20Publik%20Dataset/sellers_dataset.csv'
}

dataframes = {key: pd.read_csv(path) for key, path in data_paths.items()}

customers =  dataframes['customers']
order_items =  dataframes['order_items']
order_payments =  dataframes['order_payments']
order_reviews =  dataframes['order_reviews']
order_dataset =  dataframes['order_dataset']
product_category =  dataframes['product_category_name_translation']
product_dataset =  dataframes['product_dataset']
seller_dataset =  dataframes['seller_dataset']

## product_dataset 
product_dataset['product_category_name'].fillna('uncategorized', inplace=True)

#EDA 
## product_dataset
product_dataset_trans = pd.merge(product_dataset,product_category, on='product_category_name')
product_dataset_trans = product_dataset_trans.drop(columns=['product_category_name'])
product_dataset_trans = product_dataset_trans[['product_id', 'product_category_name_english', 'product_name_lenght', 'product_description_lenght', 'product_photos_qty', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']]
product_dataset = product_dataset_trans
## order_items
order_items_new = pd.merge(order_items, product_dataset, on='product_id')
order_items_new = order_items_new[['order_id', 'order_item_id', 'product_id', 'product_category_name_english', 'price', 'freight_value', 'seller_id', 'shipping_limit_date']]
most_ordered = order_items_new['product_category_name_english'].value_counts()

#1 
order_dataset_delivered = order_dataset[['order_id', 'order_status', 'order_purchase_timestamp', 'customer_id']]
order_dataset_delivered = order_dataset_delivered[order_dataset_delivered['order_status']=='delivered']
order_dataset_delivered['order_purchase_timestamp'] = pd.to_datetime(order_dataset_delivered['order_purchase_timestamp'])
order_dataset_delivered['order_purchase_timestamp'] = order_dataset_delivered['order_purchase_timestamp'].dt.date
order_items_new = order_items_new[['order_id', 'product_id', 'product_category_name_english']]
merged_order = pd.merge(order_dataset_delivered, order_items_new[['order_id', 'product_id', 'product_category_name_english']], on='order_id', how='inner')
merged_order = merged_order[['order_id', 'product_id', 'product_category_name_english', 'customer_id', 'order_purchase_timestamp', 'order_status']]
merged_order = merged_order.sort_values(by='order_purchase_timestamp', ascending=False)
latest_date = merged_order['order_purchase_timestamp'].max()
one_year_ago = latest_date - pd.DateOffset(years=1)
one_year_ago_filtered = merged_order[merged_order['order_purchase_timestamp']>= one_year_ago]
category_order = one_year_ago_filtered.groupby('product_category_name_english')['order_id'].count().reset_index()
category_order = category_order.sort_values(by='order_id', ascending=False)
daily_sales = one_year_ago_filtered.groupby(one_year_ago_filtered['order_purchase_timestamp'])['order_id'].count()

#2
customer_one_year = pd.merge(one_year_ago_filtered, customers, on='customer_id')
customer_one_year_grouped = customer_one_year['customer_state'].value_counts()

#3
merged_review = pd.merge(one_year_ago_filtered, order_reviews, on='order_id')
average_scores = merged_review.groupby('product_category_name_english')['review_score'].mean()
highly_rated_products = average_scores[average_scores > 4]
highly_rated_products = highly_rated_products.sort_values(ascending=True)

#4
lowest_rated_products = average_scores[average_scores < 4]
lowest_rated_products = lowest_rated_products.sort_values(ascending=True)

#5
order_dataset_rfm = order_dataset.copy()
order_dataset_rfm.set_index('order_id', inplace=True)
order_payments_rfm = order_payments.copy()
order_payments_rfm.set_index('order_id', inplace=True)
db_rfm = order_dataset_rfm.merge(order_payments_rfm, left_index=True, right_index=True, how='outer')
db_rfm.dropna(inplace=True)
db_rfm[['order_purchase_timestamp',
       'order_approved_at',
       'order_delivered_carrier_date',
       'order_delivered_customer_date',
       'order_estimated_delivery_date']] = db_rfm[['order_purchase_timestamp',
       'order_approved_at',
       'order_delivered_carrier_date',
       'order_delivered_customer_date',
       'order_estimated_delivery_date']].astype('datetime64[ns]')

db_rfm[['payment_sequential', 'payment_installments']] = db_rfm[['payment_sequential', 'payment_installments']].astype('int64')
rfm = db_rfm[['customer_id', 'order_purchase_timestamp', 'payment_value']].reset_index()
#recency
today = rfm['order_purchase_timestamp'].max() + pd.to_timedelta(1, 'D')
recency = pd.DataFrame(rfm.groupby(by='customer_id', as_index=False)['order_purchase_timestamp'].max())
recency.rename(columns={'order_purchase_timestamp': 'Last Purchase Date'}, inplace=True)
recency['Recency'] = recency['Last Purchase Date'].apply(lambda x: (today - x).days)
#frequency
frequency = pd.DataFrame(rfm.groupby(by='customer_id', as_index=False)['order_id'].count())
frequency.rename(columns={'order_id': 'Frequency'}, inplace=True)
#monetary
monetary = pd.DataFrame(rfm.groupby(by='customer_id', as_index=False)['payment_value'].sum())
monetary.columns = ['customer_id', 'Monetary']
df_rf = recency.merge(frequency, on='customer_id')
df_rfm = df_rf.merge(monetary, on='customer_id')
df_rfm.drop(columns='Last Purchase Date', inplace=True)
def f_score(x):
    if x == 1:
        return 1
    elif x == 2:
        return 2
    elif x == 3:
        return 3
    elif x == 4:
        return 4
    else:
        return 5

def m_score(x):
    if x < 50:
        return 1
    elif x < 100:
        return 2
    elif x < 150:
        return 3
    elif x < 200:
        return 4
    else:
        return 5

df_rfm['R Score'] = pd.qcut(x=df_rfm['Recency'], q=5, labels=[5, 4, 3, 2, 1])
df_rfm['F Score'] = df_rfm['Frequency'].apply(f_score )
df_rfm['M Score'] = x=df_rfm['Monetary'].apply(m_score)

df_rfm = df_rfm[['customer_id', 'Recency', 'R Score', 'Frequency', 'F Score', 'Monetary', 'M Score']]
r = df_rfm['Recency']
r_score = df_rfm['R Score']

m = df_rfm['Monetary']
m_score = df_rfm['M Score']

df_rfm['R Score'] = df_rfm['R Score'].astype('int64')
df_rfm['RFM Score'] = df_rfm['R Score'].astype(str) + df_rfm['F Score'].astype(str) + df_rfm['M Score'].astype(str)
df_rfm['Segment'] = df_rfm['R Score'].astype(str) + df_rfm['F Score'].astype(str)

segt_map = {
    r'[1-2][1-2]': 'Hibernating',
    r'[1-2][3-4]': 'At Risk',
    r'[1-2]5': 'Cannot Loose',
    r'3[1-2]': 'About To Sleep',
    r'33': 'Need Attention',
    r'[3-4][4-5]': 'Loyal Customers',
    r'41': 'Promising',
    r'51': 'New Customers',
    r'[4-5][2-3]': 'Potential Loyalists',
    r'5[4-5]': 'Champions'
}

df_rfm['Segment'] = df_rfm['Segment'].replace(segt_map, regex=True)
df_rfm.reset_index(inplace=True)

rfm_final = df_rfm[['customer_id', 'Recency', 'Frequency', 'Monetary', 'Segment']]
df_segt = rfm_final[['customer_id','Segment']].groupby('Segment').agg('count').reset_index()
df_segt.rename(columns={'customer_id': 'Customer Counts'}, inplace=True)

segment = df_segt['Segment']
customer_counts = df_segt['Customer Counts']

##SIDEBAR KANAN*****************************************

st.sidebar.title("Profil Pengguna")

# Menambahkan foto profil di sidebar
st.sidebar.image('https://github.com/alhabibii/My-GitHub-Profile-Introduction/raw/main/20220803_065605_0000.jpg')
st.sidebar.write("Nama : Adil Latif Habibi")
st.sidebar.write("Email: adillatif845@gmail.com")

# Sidebar untuk memilih pertanyaan
st.sidebar.title("Menu")
selected_question = st.sidebar.selectbox("Pilih Info:", ["Order Terbanyak", "Sebaran Pelanggan", "Rating Produk > 4", "Rating Produk < 4", "RFM Analysis"])
selected_date = st.sidebar.date_input("Pilih Tanggal", order_dataset_delivered['order_purchase_timestamp'].max())

# Main content
st.title("Aplikasi Dashboard E Commerce Public Dataset")

# Menampilkan grafik berdasarkan pertanyaan yang dipilih
if selected_question == "Order Terbanyak":
    st.header("Kategori Produk Paling Banyak Diorder 1 Tahun Terakhir")
    
    # Membuat grafik Pertanyaan 1
    fig1a, ax1a = plt.subplots(figsize=(12, 6))
    bars1a = ax1a.bar(category_order['product_category_name_english'][:10], category_order['order_id'][:10])
    ax1a.set_xlabel("Kategori Produk")
    ax1a.set_ylabel('Jumlah Order yang Delivered')
    ax1a.set_title('10 Kategori Produk Terbanyak Diorder dalam 1 Tahun Terakhir')
    ax1a.set_xticklabels(category_order['product_category_name_english'][:10], rotation=45)

    for bar in bars1a:
        height = bar.get_height()
        ax1a.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # Jarak label dari bar
                    textcoords="offset points",
                    ha='center', va='bottom')

    # Menampilkan grafik Pertanyaan 1 di Streamlit
    st.pyplot(fig1a)

    # Grafik tren harian penjualan dalam 1 tahun terakhir
    st.header("Tren Order Harian 1 Tahun Terakhir")
    fig1b, ax1b = plt.subplots(figsize=(16, 8))
    ax1b.plot(daily_sales.index, daily_sales.values, marker='o', markersize=1, linestyle='-')
    ax1b.set_xlabel('Tanggal')
    ax1b.set_ylabel('Jumlah Order')
    ax1b.set_title('Tren Penjualan dalam 1 Tahun terakhir')
    ax1b.set_xticklabels(daily_sales.index, rotation=45)
    
    label_points = [0, 60, 120, 180, 240, 300, 360]
    for i in label_points:
        ax1b.annotate(f'{daily_sales.values[i]}',
                    (daily_sales.index[i], daily_sales.values[i]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center', va='bottom')

    # Menampilkan grafik tren penjualan di Streamlit
    st.pyplot(fig1b)


elif selected_question == "Sebaran Pelanggan":
    st.header("Total Jumlah Pelanggan di Semua Negara Bagian")
    
    # Membuat grafik Pertanyaan 2
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.bar(customer_one_year_grouped.index, customer_one_year_grouped)
    ax2.set_title('Jumlah Pelanggan Berdasarkan State')
    ax2.set_xlabel('State')
    ax2.set_ylabel('Jumlah Pelanggan')
    ax2.set_xticklabels(customer_one_year_grouped.index, rotation=45)
    
    for i, v in enumerate(customer_one_year_grouped):
        ax2.text(i, v + 10, str(v), ha='center', va='bottom')
    
    # Menampilkan grafik Pertanyaan 2 di Streamlit
    st.pyplot(fig2)

# ...

elif selected_question == "Rating Produk > 4":
    st.header("Daftar Kategori Produk dengan Rating Score > 4")
    
    # Membuat grafik Pertanyaan 3
    fig3, ax3 = plt.subplots(figsize=(8, 13))
    ax3.barh(highly_rated_products.index, highly_rated_products)
    ax3.set_title('Produk dengan Rata-Rata Penilaian > 4')
    ax3.set_xlabel('Rata-Rata Review Score')
    ax3.set_ylabel('Product ID')
    ax3.set_xlim(4, max(highly_rated_products))
    
    for i, v in enumerate(highly_rated_products):
        ax3.text(v + 0.1, i, f'{v:.2f}', color='black', va='center', fontsize=10)
    
    # Menampilkan grafik Pertanyaan 3 di Streamlit
    st.pyplot(fig3)

# ...

elif selected_question == "Rating Produk < 4":
    st.header("Daftar Kategori Produk dengan Rating Score < 4")
    
    # Membuat grafik Pertanyaan 4
    fig4, ax4 = plt.subplots(figsize=(9, 6))
    ax4.barh(lowest_rated_products.index, lowest_rated_products)
    ax4.set_title('Produk dengan Rata-Rata Penilaian < 4')
    ax4.set_xlabel('Rata-Rata Review Score')
    ax4.set_ylabel('Product ID')
    ax4.set_xlim(0, 5)
    
    for i, v in enumerate(lowest_rated_products):
        ax4.text(v + 0.1, i, f'{v:.2f}', color='black', va='center', fontsize=10)
    
    # Menampilkan grafik Pertanyaan 4 di Streamlit
    st.pyplot(fig4)

# ...

elif selected_question == "RFM Analysis":
    st.header("Distribusi dan Segmentasi Loyalitas Pelanggan")
    
    # Membuat grafik Pertanyaan 5 (Recency Score Distribution)
    fig5a, ax5a = plt.subplots(figsize=(12, 6))
    ax5a.scatter(r, r_score, s=100, c=r_score)
    ax5a.set_title('Recency Score Distribution')
    ax5a.set_xlabel('Recency')
    ax5a.set_ylabel('Recency Score')
    
    # Menampilkan grafik Pertanyaan 5 (Recency Score Distribution) 
    st.pyplot(fig5a)

    # Membuat grafik Pertanyaan 5 (Monetary Score Distribution)
    fig5b, ax5b = plt.subplots(figsize=(12, 6))
    ax5b.scatter(m, m_score, s=100, c=m_score)
    ax5b.set_title('Monetary Score Distribution')
    ax5b.set_xlabel('Monetary')
    ax5b.set_ylabel('Monetary')
    
    # Menampilkan grafik Pertanyaan 5 (Monetary Score Distribution)
    st.pyplot(fig5b)

    # Membuat grafik Pertanyaan 5 (Segmentasi)
    st.header("Distribusi Pelanggan dan Segmentasi Loyalitas Pelanggan")
    
    # Membuat grafik Pertanyaan 5
    fig5c, ax5c = plt.subplots(figsize=(15, 6))
    scatter = ax5c.scatter(segment, customer_counts, s=customer_counts, c=customer_counts)
    cbar = plt.colorbar(scatter)
    cbar.set_label('Customer Counts')
    ax5c.set_title('Customer Counts By RFM Segmentation')
    ax5c.set_ylabel('Customer Counts')
    ax5c.set_xticklabels(segment, rotation=45)
    
    # Menampilkan grafik Pertanyaan 5 di Streamlit
    st.pyplot(fig5c)

    st.header("Distribusi Pelanggan dan Segmentasi Loyalitas Pelanggan")
    # Membuat grafik Pertanyaan 5
    df_segt_sorted = df_segt.sort_values(by='Customer Counts', ascending=True)
    fig5d, ax5d = plt.subplots(figsize=(15, 6))
    bars5d = ax5d.barh(segment, customer_counts, color='skyblue')
    ax5d.set_title('Customer Counts By RFM Segmentation')
    ax5d.set_xlabel('Customer Counts')
    ax5d.set_ylabel('Segment')

    for bar in bars5d:
        width = bar.get_width()
        ax5d.text(width, bar.get_y() + bar.get_height() / 2, f'{int(width)}', va='center')

    # Menampilkan grafik Pertanyaan 5 di Streamlit
    st.pyplot(fig5d)

# Menampilkan grafik penjualan berdasarkan tanggal yang dipilih
if selected_date:
    st.header(f"Grafik Penjualan untuk {selected_date}")
    
    # Gabungkan data dari order_items_new dengan order_dataset_delivered berdasarkan order_id
    data_selected_date = order_dataset_delivered[order_dataset_delivered['order_purchase_timestamp'] == selected_date]
    data_selected_date = data_selected_date.merge(order_items_new, on='order_id', how='inner')
    
    if not data_selected_date.empty:
        # Menghitung total order_id untuk setiap kategori produk
        total_orders = data_selected_date.groupby('product_category_name_english')['order_id'].count()

        # Membuat grafik
        fig, ax = plt.subplots(figsize=(15, 8))
        bars = ax.bar(total_orders.index, total_orders.values)
        ax.set_xlabel("Kategori Produk")
        ax.set_ylabel('Jumlah Order yang Diorder')
        ax.set_title('Grafik Penjualan Produk untuk Tanggal Tertentu')

        # Menambahkan angka-angka di atas batang grafik
        for bar, total in zip(bars, total_orders.values):
            height = bar.get_height()
            ax.annotate(f'{total}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3),
                        textcoords="offset points", ha='center', va='bottom')

        # Memutar label x agar terlihat lebih baik
        ax.set_xticklabels(total_orders.index, rotation=45, ha='right')

        # Menampilkan grafik di Streamlit
        st.pyplot(fig)
    else:
        st.write("Tidak ada data yang tersedia untuk tanggal yang dipilih.")


