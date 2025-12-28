"""
PROJET BUSINESS INTELLIGENCE - TECHSTORE
Membre 3: Database Architect
Version FINALE strictement conforme aux exigences du TP

Cette version utilise:
- 1 seule table de faits: Fact_Sales (comme demandé dans le TP section 6)
- 4 tables dimensions: Dim_Date, Dim_Product, Dim_Store, Dim_Customer
- Tous les attributs nécessaires pour les KPIs demandés dans la section 7
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

# ====================================================
# FONCTIONS UTILITAIRES POUR LES CHEMINS
# ====================================================
def get_erp_path(filename):
    """Retourne le chemin complet vers un fichier ERP"""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, 'erp_tables', filename)

def get_data_path(filename):
    """Retourne le chemin complet vers un fichier data"""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, 'data', filename)

def get_db_path():
    """Retourne le chemin complet vers la base de données"""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, 'techstore_dw.db')

def create_database_tables():
    """
    ÉTAPE 1: Crée la base de données SQLite et toutes les tables
    selon le schéma en étoile strict du TP
    """
    print("=" * 60)
    print("🛠️  CRÉATION DE LA BASE DE DONNÉES TECHSTORE_DW")
    print("=" * 60)
    
    # ==========================================================
    # CORRECTION: Créer la base dans le même dossier que le script
    # ==========================================================
    db_path = get_db_path()
    
    print(f"📁 Emplacement de la base: {db_path}")
    
    # Supprimer l'ancienne base si elle existe (optionnel)
    if os.path.exists(db_path):
        print("⚠️  Suppression de l'ancienne base de données...")
        os.remove(db_path)
    
    # Créer la connexion à la base SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # =================================================================
    # DIMENSION: DATE (Dim_Date)
    # Pour l'analyse temporelle - Section 6: "While this dimension is 
    # technically optional, it is strongly recommended"
    # =================================================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dim_Date (
        date_key INTEGER PRIMARY KEY,      -- Format: YYYYMMDD (ex: 20240115)
        full_date DATE,                    -- Date complète pour jointures
        year INTEGER,                      -- Pour analyse par année
        month INTEGER,                     -- Pour analyse mensuelle
        quarter INTEGER,                   -- Pour analyse trimestrielle
        month_name TEXT,                   -- Pour les rapports (ex: "January")
        day_of_week TEXT                   -- Pour analyse par jour (ex: "Monday")
    )
    ''')
    print("📅 Dim_Date: Table de dimension temporelle créée")
    
    # =================================================================
    # DIMENSION: PRODUIT (Dim_Product)
    # Section 6: "Dim_Product: Flattened hierarchy, including 
    # Sentiment Score and Competitor Price"
    # =================================================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dim_Product (
        product_id TEXT PRIMARY KEY,       -- Identifiant unique produit (P100, P101...)
        product_name TEXT,                 -- Nom du produit
        category_id INTEGER,               -- ID catégorie (pour jointures)
        category_name TEXT,                -- Nom catégorie (Computers, Smartphones...)
        subcategory_id INTEGER,            -- ID sous-catégorie
        subcategory_name TEXT,             -- Nom sous-catégorie
        unit_price REAL,                   -- Prix de vente unitaire (ERP)
        unit_cost REAL,                    -- Coût unitaire de fabrication (ERP)
        competitor_price REAL,             -- Prix compétiteur (Source 3: Web Scraping)
        avg_sentiment_score REAL,          -- Score de sentiment moyen (Section 5: Sentiment Analysis)
        review_count INTEGER,              -- Nombre d'avis (pour contexte)
        avg_rating REAL,                   -- Note moyenne (1-5 étoiles)
        profit_margin_percent REAL         -- Marge bénéficiaire en % (calculée)
    )
    ''')
    print("📦 Dim_Product: Table des produits créée")
    
    # =================================================================
    # DIMENSION: MAGASIN (Dim_Store)
    # Section 6: "Dim_Store: Links stores to regions and includes Sales Targets"
    # =================================================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dim_Store (
        store_id INTEGER PRIMARY KEY,      -- Identifiant unique magasin (1, 2, 3...)
        store_name TEXT,                   -- Nom du magasin
        city_id INTEGER,                   -- ID ville (pour jointures)
        city_name TEXT,                    -- Nom ville (Alger, Oran...)
        region TEXT,                       -- Région (North, South, East, West, Center)
        manager_name TEXT,                 -- Nom du manager (de monthly_targets)
        target_revenue REAL                -- Objectif de revenu (pour KPI Target Achievement)
    )
    ''')
    print("🏪 Dim_Store: Table des magasins créée")
    
    # =================================================================
    # DIMENSION: CLIENT (Dim_Customer)
    # Section 6: "Dim_Customer: Tracking who is buying and their location"
    # =================================================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dim_Customer (
        customer_id TEXT PRIMARY KEY,      -- Identifiant unique client (C0001, C0002...)
        full_name TEXT,                    -- Nom complet du client
        city_id INTEGER,                   -- ID ville
        city_name TEXT,                    -- Ville de résidence
        region TEXT                        -- Région de résidence
    )
    ''')
    print("👤 Dim_Customer: Table des clients créée")
    
    # =================================================================
    # TABLE DE FAITS: VENTES (Fact_Sales)
    # Section 6: "The Fact Table (Fact_Sales): A central table containing 
    # all sales transactions from both the ERP and legacy archives"
    # =================================================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Fact_Sales (
        transaction_id INTEGER PRIMARY KEY,  -- ID transaction unique
        date_key INTEGER,                    -- Référence à Dim_Date (pour analyse temporelle)
        store_id INTEGER,                    -- Référence à Dim_Store
        product_id TEXT,                     -- Référence à Dim_Product
        customer_id TEXT,                    -- Référence à Dim_Customer
        
        -- MESURES NUMÉRIQUES (Section 6: "Includes numerical measures")
        quantity INTEGER,                    -- Quantité vendue
        total_revenue REAL,                  -- Chiffre d'affaires total
        unit_cost REAL,                      -- Coût unitaire (pour calculs)
        product_cost_total REAL,             -- Coût total des produits
        shipping_cost REAL,                  -- Frais de livraison (Section 4: Logistics)
        marketing_cost_per_sale REAL,        -- Coût marketing (Section 4: Marketing Data)
        net_profit REAL,                     -- Profit net (Section 5: "Net Profit" Calculation)
        profit_margin_percent REAL,          -- Marge en % (calculée)
        
        -- ATTRIBUTS DE DÉNORMALISATION (pour faciliter les requêtes)
        category_name TEXT,                  -- Catégorie produit (pour filtrage)
        region TEXT,                         -- Région (pour analyse géographique)
        
        -- CONTRAINTES DE CLÉ ÉTRANGÈRE
        FOREIGN KEY (date_key) REFERENCES Dim_Date(date_key),
        FOREIGN KEY (store_id) REFERENCES Dim_Store(store_id),
        FOREIGN KEY (product_id) REFERENCES Dim_Product(product_id),
        FOREIGN KEY (customer_id) REFERENCES Dim_Customer(customer_id)
    )
    ''')
    print("💰 Fact_Sales: Table de faits des ventes créée")
    print("✅ Toutes les tables ont été créées avec succès!")
    
    conn.commit()
    return conn

def load_dim_date(conn):
    """
    ÉTAPE 2: Charge la dimension Date
    Génère toutes les dates de 2023 à 2025 (période du projet)
    """
    print("\n" + "=" * 60)
    print("📅 CHARGEMENT DE Dim_Date")
    print("=" * 60)
    
    # Générer toutes les dates du 2023-01-01 au 2025-12-31
    dates = pd.date_range(start='2023-01-01', end='2025-12-31', freq='D')
    df_date = pd.DataFrame({'full_date': dates})
    
    # Créer la clé de substitution (meilleure performance)
    df_date['date_key'] = df_date['full_date'].dt.strftime('%Y%m%d').astype(int)
    
    # Extraire les composants de date
    df_date['year'] = df_date['full_date'].dt.year
    df_date['month'] = df_date['full_date'].dt.month
    df_date['quarter'] = df_date['full_date'].dt.quarter
    df_date['month_name'] = df_date['full_date'].dt.strftime('%B')  # Nom complet mois
    df_date['day_of_week'] = df_date['full_date'].dt.strftime('%A') # Nom jour semaine
    
    # Charger dans la base
    df_date.to_sql('Dim_Date', conn, if_exists='replace', index=False)
    print(f"✅ {len(df_date)} dates chargées (du {df_date['full_date'].min()} au {df_date['full_date'].max()})")
    
    return df_date

def load_dim_product(conn):
    """
    ÉTAPE 3: Charge la dimension Produit
    Fusionne les données de:
    1. ERP (produits, catégories, sous-catégories)
    2. Sentiment analysis (NLP)
    3. Prix compétiteurs (web scraping)
    4. Profit margin (calculé)
    """
    print("\n" + "=" * 60)
    print("📦 CHARGEMENT DE Dim_Product")
    print("=" * 60)
    
    try:
        # 1. Charger les données ERP 
        print("📥 Chargement des données ERP...")
        products = pd.read_excel(get_erp_path('table_products_cleaned.xlsx'))
        categories = pd.read_excel(get_erp_path('table_categories_cleaned.xlsx'))
        subcategories = pd.read_excel(get_erp_path('table_subcategories_cleaned.xlsx'))
        
        # 2. Fusionner la hiérarchie produit
        print("🔄 Fusion des données produit...")
        df_product = pd.merge(products, subcategories, on='SubCat_ID', how='left')
        df_product = pd.merge(df_product, categories, on='Category_ID', how='left')
        
        # 3. Ajouter le sentiment (Section 5: Sentiment Analysis)
        print("😊 Ajout des scores de sentiment...")
        sentiment = pd.read_excel(get_data_path('product_sentiment_scores.xlsx'))
        df_product = pd.merge(df_product, sentiment, on='Product_ID', how='left')
        
        # 4. Ajouter les prix compétiteurs (Section 4: Competitor Pricing)
        print("🏷️  Ajout des prix compétiteurs...")
        competitors = pd.read_excel(get_data_path('competitor_prices_cleaned.xlsx'))
        
        # Nettoyer le format du prix (enlever " DZD")
        if 'Competitor_Price_Raw' in competitors.columns:
            competitors['Competitor_Price_Raw'] = competitors['Competitor_Price_Raw'].str.replace(' DZD', '').astype(float)
        
        # Jointure sur le nom du produit
        df_product = pd.merge(df_product, 
                             competitors[['Competitor_Product_Name', 'Competitor_Price_Raw']], 
                             left_on='Product_Name', 
                             right_on='Competitor_Product_Name', 
                             how='left')
        
        # 5. Ajouter la marge bénéficiaire dans la table product
        print("💰 Ajout des marges bénéficiaires...")
        profit_summary = pd.read_excel(get_data_path('product_profit_summary.xlsx'))
        df_product = pd.merge(df_product, 
                             profit_summary[['Product_ID', 'Profit_Margin_%']], 
                             on='Product_ID', 
                             how='left')
        
        # 6. Renommer les colonnes pour correspondre à Dim_Product
        print("✏️  Renommage des colonnes...")
        df_product.rename(columns={
            'Product_ID': 'product_id',
            'Product_Name': 'product_name',
            'Category_ID': 'category_id',
            'Category_Name': 'category_name',
            'SubCat_ID': 'subcategory_id',
            'SubCat_Name': 'subcategory_name',
            'Unit_Price': 'unit_price',
            'Unit_Cost': 'unit_cost',
            'Competitor_Price_Raw': 'competitor_price',
            'Avg_Sentiment_Score': 'avg_sentiment_score',
            'Review_Count': 'review_count',
            'Avg_Rating': 'avg_rating',
            'Profit_Margin_%': 'profit_margin_percent'
        }, inplace=True)
        
        # 7. Charger dans la base
        df_product.to_sql('Dim_Product', conn, if_exists='replace', index=False)
        print(f"✅ {len(df_product)} produits chargés")
        print(f"   Exemple: {df_product['product_name'].iloc[0]} (ID: {df_product['product_id'].iloc[0]})")
        
        return df_product
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        print(f"📁 Vérifiez que vos fichiers sont dans:")
        print(f"   - {get_erp_path('')}")
        print(f"   - {get_data_path('')}")
        raise

def load_dim_store(conn):
    """
    ÉTAPE 4: Charge la dimension Magasin
    Fusionne les données de:
    1. ERP (magasins, villes)
    2. Objectifs mensuels (HR targets)
    """
    print("\n" + "=" * 60)
    print("🏪 CHARGEMENT DE Dim_Store")
    print("=" * 60)
    
    try:
        # 1. Charger les données ERP
        print("📥 Chargement des données magasins...")
        stores = pd.read_excel(get_erp_path('table_stores_cleaned.xlsx'))
        cities = pd.read_excel(get_erp_path('table_cities_cleaned.xlsx'))
        
        # 2. Fusionner magasins avec villes
        df_store = pd.merge(stores, cities, on='City_ID', how='left')
        
        # 3. Ajouter les managers et objectifs (Section 4: HR & Targets)
        print("🎯 Ajout des objectifs et managers...")
        targets = pd.read_excel(get_data_path('monthly_targets_cleaned.xlsx'))
        
        # Pour chaque magasin, prendre le dernier manager connu
        latest_targets = targets.sort_values('Month').drop_duplicates('Store_ID', keep='last')
        
        # Ajouter manager_name et target_revenue à Dim_Store
        df_store = pd.merge(df_store, 
                           latest_targets[['Store_ID', 'Manager_Name', 'Target_Revenue']], 
                           left_on='Store_ID', 
                           right_on='Store_ID', 
                           how='left')
        
        # 4. Renommer les colonnes
        df_store.rename(columns={
            'Store_ID': 'store_id',
            'Store_Name': 'store_name',
            'City_ID': 'city_id',
            'City_Name': 'city_name',
            'Region': 'region',
            'Manager_Name': 'manager_name',
            'Target_Revenue': 'target_revenue'
        }, inplace=True)
        
        # 5. Charger dans la base
        df_store.to_sql('Dim_Store', conn, if_exists='replace', index=False)
        print(f"✅ {len(df_store)} magasins chargés")
        print(f"   Régions couvertes: {df_store['region'].unique().tolist()}")
        
        return df_store
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        raise

def load_dim_customer(conn):
    """
    ÉTAPE 5: Charge la dimension Client
    Fusionne les données clients avec les villes
    """
    print("\n" + "=" * 60)
    print("👤 CHARGEMENT DE Dim_Customer")
    print("=" * 60)
    
    try:
        # 1. Charger les données
        customers = pd.read_excel(get_erp_path('table_customers_cleaned.xlsx'))
        cities = pd.read_excel(get_erp_path('table_cities_cleaned.xlsx'))
        
        # 2. Fusionner clients avec villes
        df_customer = pd.merge(customers, cities, on='City_ID', how='left')
        
        # 3. Renommer les colonnes
        df_customer.rename(columns={
            'Customer_ID': 'customer_id',
            'Full_Name': 'full_name',
            'City_ID': 'city_id',
            'City_Name': 'city_name',
            'Region': 'region'
        }, inplace=True)
        
        # 4. Charger dans la base
        df_customer.to_sql('Dim_Customer', conn, if_exists='replace', index=False)
        print(f"✅ {len(df_customer)} clients chargés")
        
        return df_customer
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        raise

def load_fact_sales(conn):
    """
    ÉTAPE 6: Charge la table de faits Fact_Sales
    Section 6: "The Fact Table (Fact_Sales): A central table containing 
    all sales transactions from both the ERP and legacy archives"
    """
    print("\n" + "=" * 60)
    print("💰 CHARGEMENT DE Fact_Sales")
    print("=" * 60)
    
    try:
        # 1. Charger les transactions avec profit net
        print("📥 Chargement des transactions...")
        transactions = pd.read_excel(get_data_path('transactions_with_net_profit.xlsx'))
        
        # Vérifier les colonnes disponibles
        print(f"📋 Colonnes disponibles: {transactions.columns.tolist()}")
        
        # 2. Convertir et nettoyer les données
        print("🔄 Conversion des dates et nettoyage...")
        
        # Convertir la date en datetime
        transactions['Date'] = pd.to_datetime(transactions['Date'])
        
        # Créer la date_key (format YYYYMMDD)
        transactions['date_key'] = transactions['Date'].dt.strftime('%Y%m%d').astype(int)
        
        # Nettoyer les nombres (remplacer virgules par points)
        numeric_columns = ['Net_Profit', 'Total_Revenue', 'Unit_Cost', 'Product_Cost_Total', 
                          'Shipping_Cost', 'Marketing_Cost_Per_Sale']
        
        for col in numeric_columns:
            if col in transactions.columns:
                transactions[col] = transactions[col].astype(str).str.replace(',', '.').astype(float)
        
        # 3. Calculer Profit_Margin_% s'il n'existe pas
        if 'Profit_Margin_%' not in transactions.columns:
            print("📊 Calcul de la marge bénéficiaire...")
            transactions['Profit_Margin_%'] = (transactions['Net_Profit'] / transactions['Total_Revenue']) * 100
        
        # 4. Préparer le DataFrame pour Fact_Sales
        print("✏️  Préparation de Fact_Sales...")
        
        # Sélectionner et renommer les colonnes nécessaires
        fact_sales = transactions[[
            'Trans_ID', 'date_key', 'Store_ID', 'Product_ID', 
            'Customer_ID', 'Quantity', 'Total_Revenue', 'Unit_Cost',
            'Product_Cost_Total', 'Shipping_Cost', 'Marketing_Cost_Per_Sale',
            'Net_Profit', 'Profit_Margin_%', 'Category_Name', 'Region'
        ]].copy()
        
        # Renommer les colonnes
        fact_sales.rename(columns={
            'Trans_ID': 'transaction_id',
            'Store_ID': 'store_id',
            'Product_ID': 'product_id',
            'Customer_ID': 'customer_id',
            'Quantity': 'quantity',
            'Total_Revenue': 'total_revenue',
            'Unit_Cost': 'unit_cost',
            'Product_Cost_Total': 'product_cost_total',
            'Shipping_Cost': 'shipping_cost',
            'Marketing_Cost_Per_Sale': 'marketing_cost_per_sale',
            'Net_Profit': 'net_profit',
            'Profit_Margin_%': 'profit_margin_percent',
            'Category_Name': 'category_name',
            'Region': 'region'
        }, inplace=True)
        
        # 5. Vérifier l'intégrité des clés étrangères
        print("🔍 Vérification des clés étrangères...")
        
        # Vérifier que tous les product_id existent dans Dim_Product
        dim_products = pd.read_sql("SELECT product_id FROM Dim_Product", conn)
        missing_products = set(fact_sales['product_id']) - set(dim_products['product_id'])
        
        if missing_products:
            print(f"⚠️  Attention: {len(missing_products)} produits manquants dans Dim_Product")
        
        # Vérifier que tous les store_id existent dans Dim_Store
        dim_stores = pd.read_sql("SELECT store_id FROM Dim_Store", conn)
        missing_stores = set(fact_sales['store_id']) - set(dim_stores['store_id'])
        
        if missing_stores:
            print(f"⚠️  Attention: {len(missing_stores)} magasins manquants dans Dim_Store")
        
        # 6. Charger dans la base
        fact_sales.to_sql('Fact_Sales', conn, if_exists='replace', index=False)
        
        print(f"✅ {len(fact_sales)} transactions chargées dans Fact_Sales")
        print(f"📅 Période: {transactions['Date'].min()} au {transactions['Date'].max()}")
        print(f"💰 Profit net total: {fact_sales['net_profit'].sum():,.2f} DZD")
        
        return fact_sales
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        raise

def verify_database(conn):
    """
    ÉTAPE 7: Vérifie l'intégrité et les statistiques de la base
    """
    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    stats = []
    
    # Compter les enregistrements dans chaque table
    tables = ['Dim_Date', 'Dim_Product', 'Dim_Store', 'Dim_Customer', 'Fact_Sales']
    
    for table in tables:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
            stats.append((table, count))
        except Exception as e:
            stats.append((table, f"ERREUR: {e}"))
    
    # Afficher les statistiques
    print("\n📊 STATISTIQUES DE LA BASE:")
    print("-" * 40)
    for table, count in stats:
        print(f"  {table:20} → {count:>10} enregistrements")
    
    # Vérifier les KPIs de base
    print("\n🎯 KPIs DE BASE:")
    print("-" * 40)
    
    try:
        # Total Revenue
        total_revenue = pd.read_sql(
            "SELECT SUM(total_revenue) as total FROM Fact_Sales", 
            conn
        ).iloc[0]['total']
        print(f"  Total Revenue: {total_revenue:,.2f} DZD")
        
        # Net Profit
        net_profit = pd.read_sql(
            "SELECT SUM(net_profit) as total FROM Fact_Sales", 
            conn
        ).iloc[0]['total']
        print(f"  Net Profit: {net_profit:,.2f} DZD")
        
        # Average Profit Margin
        avg_margin = pd.read_sql(
            "SELECT AVG(profit_margin_percent) as avg FROM Fact_Sales", 
            conn
        ).iloc[0]['avg']
        print(f"  Average Margin: {avg_margin:.2f}%")
        
        # Number of unique customers
        unique_customers = pd.read_sql(
            "SELECT COUNT(DISTINCT customer_id) as count FROM Fact_Sales", 
            conn
        ).iloc[0]['count']
        print(f"  Unique Customers: {unique_customers}")
        
    except Exception as e:
        print(f"  Erreur calcul KPIs: {e}")
    
    return stats

def main():
    """
    FONCTION PRINCIPALE
    Exécute toutes les étapes dans l'ordre
    """
    print("=" * 60)
    print("🚀 DÉMARRAGE DU SCRIPT DE CRÉATION DE BASE DE DONNÉES")
    print("=" * 60)
    
    # Afficher le répertoire courant pour diagnostic
    print(f"📁 Répertoire de travail: {os.getcwd()}")
    print(f"📁 Emplacement du script: {os.path.dirname(__file__)}")
    print(f"📁 Emplacement prévu de la base: {get_db_path()}")
    
    # Vérifier que les dossiers existent
    required_folders = ['data', 'erp_tables']
    for folder in required_folders:
        folder_path = os.path.join(os.path.dirname(__file__), folder)
        if not os.path.exists(folder_path):
            print(f"❌ Dossier manquant: {folder_path}")
            print("   Structure attendue:")
            print("   data/ → Contient les fichiers Excel nettoyés")
            print("   erp_tables/ → Contient les fichiers Excel ERP")
            
            # Afficher ce qui existe
            print(f"\n📂 Contenu de {os.path.dirname(__file__)}:")
            for item in os.listdir(os.path.dirname(__file__)):
                print(f"   - {item}")
            return
        else:
            print(f"✅ Dossier trouvé: {folder_path}")
            # Afficher quelques fichiers pour vérification
            files = os.listdir(folder_path)
            print(f"   {len(files)} fichiers trouvés")
    
    try:
        # ÉTAPE 1: Créer les tables
        conn = create_database_tables()
        
        # ÉTAPE 2: Charger les dimensions
        load_dim_date(conn)
        load_dim_product(conn)
        load_dim_store(conn)
        load_dim_customer(conn)
        
        # ÉTAPE 3: Charger la table de faits
        load_fact_sales(conn)
        
        # ÉTAPE 4: Vérifier la base
        verify_database(conn)
        
        # SUCCÈS
        print("\n" + "=" * 60)
        print("🎉 BASE DE DONNÉES CRÉÉE AVEC SUCCÈS!")
        print("=" * 60)
        print(f"\n📁 Fichier généré: {get_db_path()}")
        print("📊 Prêt pour le dashboard Streamlit!")
        print("\n✅ Tâches accomplies par le Membre 3 (Database Architect):")
        print("   1. Conception du schéma en étoile ✓")
        print("   2. Création des tables SQLite ✓")
        print("   3. Chargement des données ✓")
        print("   4. Vérification de l'intégrité ✓")
        
        # Vérifier la taille du fichier
        db_size = os.path.getsize(get_db_path())
        print(f"\n📊 Taille de la base: {db_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Fermer la connexion
        if 'conn' in locals():
            conn.close()
            print("\n🔒 Connexion à la base fermée")

if __name__ == "__main__":
    main()