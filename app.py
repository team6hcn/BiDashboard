import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF


# Configure la page pour une mise en page large
st.set_page_config(page_title="Tableau de Bord", page_icon="📊", layout="wide")


# ---- Global Variables ----
template_file_name = "template_dashboard.xlsx"

# ---- Functions ----
def create_empty_template():
    """Create an empty Excel template for the user to download."""
    with pd.ExcelWriter(template_file_name) as writer:
        pd.DataFrame(columns=["Numéro Transaction", "Date", "Code Produit", "Nom Produit", 
                              "Quantité", "Prix total", "Client Code", "Nom Client"]).to_excel(writer, sheet_name="Transactions", index=False)
        pd.DataFrame(columns=["Code Produit", "Nom du produit", "Catégorie", "Prix de vente", 
                              "Quantité en stock"]).to_excel(writer, sheet_name="Produits et Stock", index=False)
        pd.DataFrame(columns=["Client Code", "Nom Client"]).to_excel(writer, sheet_name="Clients", index=False)

def load_data(file):
    """Load the uploaded Excel file."""
    try:
        transactions = pd.read_excel(file, sheet_name="Transactions")
        products = pd.read_excel(file, sheet_name="Produits et Stock")
        clients = pd.read_excel(file, sheet_name="Clients")
        return transactions, products, clients
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None, None, None

def calculate_kpis(filtered_transactions):
    """Calculate KPIs for the dashboard."""
    kpis = {}
    if not filtered_transactions.empty:
        kpis['Chiffre daffaires total'] = filtered_transactions['Prix total'].sum()
        kpis['Nombre total de transactions'] = len(filtered_transactions)
        kpis['Quantité totale vendue'] = filtered_transactions['Quantité'].sum()
        if 'Nom Produit' in filtered_transactions.columns:
            kpis['Top produit par ventes'] = filtered_transactions.groupby("Nom Produit")['Prix total'].sum().idxmax()
        if 'Nom Client' in filtered_transactions.columns:
            kpis['Top client par dépenses'] = filtered_transactions.groupby("Nom Client")['Prix total'].sum().idxmax()
    else:
        kpis = {key: "Aucune donnée" for key in [
            'Chiffre d\'affaires total', 'Nombre total de transactions', 
            'Quantité totale vendue', 'Top produit par ventes', 'Top client par dépenses']}
    return kpis

def download_as_pdf(kpis, filtered_data):
    """Generate and download the dashboard as a PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Tableau de Bord : Vue d'ensemble", ln=True, align='C')
    pdf.ln(10)
    
    for key, value in kpis.items():
        pdf.cell(200, 10, txt=f"{key} : {value}", ln=True)
    
    #pdf.ln(10)
    #pdf.cell(200, 10, txt="Données Filtrées : Transactions", ln=True)
    #pdf.ln(10)
    
    #for _, row in filtered_data.iterrows():
    #    pdf.cell(200, 10, txt=str(row.values), ln=True)
    
    pdf_content = pdf.output(dest='S').encode('latin1')  # Convertir en binaire pour le téléchargement
    return pdf_content

def plot_sales_over_time(transactions):
    """Plot sales over time as a line chart."""
    transactions['Date'] = pd.to_datetime(transactions['Date'])
    sales_over_time = transactions.groupby(transactions['Date'].dt.to_period("M"))['Prix total'].sum()
    sales_over_time.index = sales_over_time.index.astype(str)  # Convert PeriodIndex to strings for plotting
    
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(sales_over_time.index, sales_over_time.values, marker='o', color="blue")
    ax.set_title("Évolution des ventes (par mois)", fontsize=14)
    ax.set_xlabel("Mois", fontsize=12)
    ax.set_ylabel("Chiffre d'affaires (DZD)", fontsize=12)
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)  # Incline les étiquettes de l'axe des x
    st.pyplot(fig)

def plot_sales_by_category(transactions, products):
    """Plot sales by category as a pie chart."""
    merged = pd.merge(transactions, products, on="Code Produit", how="inner")
    sales_by_category = merged.groupby("Catégorie")['Prix total'].sum()
    
    fig, ax = plt.subplots(figsize=(6, 4))
    sales_by_category.plot(kind='pie', autopct='%1.1f%%', startangle=90, ax=ax, legend=False, cmap="Set3")
    ax.set_title("Répartition des ventes par catégorie", fontsize=14)
    ax.set_ylabel("")  # Remove default ylabel
    st.pyplot(fig)

def display_top_products(transactions):
    """Display a table of top-selling products."""
    top_products = transactions.groupby("Nom Produit").agg(
        Quantité_Totale=("Quantité", "sum"),
        Revenus_Totaux=("Prix total", "sum")
    ).sort_values("Revenus_Totaux", ascending=False).reset_index()
    st.write("### Meilleurs produits (par ventes)")
    st.dataframe(top_products, use_container_width=True)
















# ---- Streamlit App ----
st.title("Tableau de Bord - Gestion des Ventes")

# Step 1: Template Download
st.header("Téléchargez le modèle Excel que vous devez remplir pour afficher votre tableau de bord.")
if st.button("Cliquez pour générer le modèle Excel."):
    create_empty_template()
    with open(template_file_name, "rb") as file:
        st.download_button(label="Le modèle a été généré avec succès. Cliquez pour le télécharger.", data=file, file_name=template_file_name)

# Step 2: Upload the Excel File
st.header("Uploader le fichier Excel")
uploaded_file = st.file_uploader("Choisissez un fichier Excel rempli", type=["xlsx"])

if uploaded_file:
    transactions, products, clients = load_data(uploaded_file)
    
    if transactions is not None:
        # Step 3: Global Filters
        st.header("Filtres globaux")
        categories = ["Toutes les catégories"] + products['Catégorie'].dropna().unique().tolist()
        selected_category = st.selectbox("Sélectionnez une catégorie", categories)
        
        # Apply filters
        if selected_category and selected_category != "Toutes les catégories":
            filtered_transactions = transactions[transactions['Nom Produit'].isin(
                products[products['Catégorie'] == selected_category]['Nom du produit'])]
        else:
            filtered_transactions = transactions
        
        # Step 4: Display KPIs
        st.header("Vue d'ensemble (KPIs)")
        kpis = calculate_kpis(filtered_transactions)

        # Organiser les KPIs en colonnes
        col1, col2, col3 = st.columns(3)

        with col1:
            value = f"{kpis['Chiffre daffaires total']} DZD"
            st.metric(label="Chiffre d'affaires total", value=value)

        with col2:
            value = kpis['Nombre total de transactions']
            st.metric(label="Nombre total de transactions", value=value)

        with col3:
            value = kpis['Quantité totale vendue']
            st.metric(label="Quantité totale vendue", value=value)

        col4, col5 = st.columns(2)
        with col4:
            value = kpis['Top produit par ventes']
            st.metric(label="Top produit par ventes", value=value)

        with col5:
            value = kpis['Top client par dépenses']
            st.metric(label="Top client par dépenses", value=value)

        
        # Display filtered transactions
        st.header("Données Filtrées")
        st.dataframe(filtered_transactions, use_container_width=True)



        # Step 5: Sales Analysis
        st.header("Analyse des ventes")

        col6, col7 = st.columns(2)
        with col6:
            # a. Ventes dans le temps
            st.subheader("Ventes dans le temps")
            plot_sales_over_time(filtered_transactions)
        with col7:
            # b. Répartition des ventes par catégorie
            st.subheader("Répartition des ventes par catégorie")
            plot_sales_by_category(filtered_transactions, products)

        # c. Meilleurs produits
        st.subheader("Meilleurs produits")
        display_top_products(filtered_transactions)



        # Step 5: Download Dashboard as PDF
        st.header("Télécharger le tableau de bord")
        pdf_buffer = download_as_pdf(kpis, filtered_transactions)
        st.download_button(label="Télécharger le tableau de bord en PDF", data=pdf_buffer, file_name="dashboard.pdf", mime="application/pdf")
