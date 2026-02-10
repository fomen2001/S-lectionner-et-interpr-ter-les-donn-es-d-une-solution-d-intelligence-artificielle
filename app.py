import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import io

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="NovaRetail - Pilotage Acquisition",
    page_icon="📊",
    layout="wide"
)

# --- 2. CHARGEMENT DES DONNÉES (Simulé pour portabilité) ---
@st.cache_data
def load_data():
    # Données Leads (Granulaires)
    csv_data = """lead_id,date,channel,device
    201,2025-10-02,Emailing,Desktop
    202,2025-10-03,Google Ads,Mobile
    203,2025-10-04,LinkedIn Ads,Desktop
    204,2025-10-05,Emailing,Mobile
    205,2025-10-06,Google Ads,Tablet
    206,2025-10-07,LinkedIn Ads,Desktop
    207,2025-10-08,Emailing,Mobile
    208,2025-10-09,Google Ads,Desktop
    209,2025-10-10,LinkedIn Ads,Mobile
    210,2025-10-11,Emailing,Desktop"""
    
    # Données Campagnes (Agrégées)
    json_data = """[
      {"campaign_id": "NR01", "channel": "Emailing", "cost": 1500, "impressions": 60000, "clicks": 1800, "conversions": 150},
      {"campaign_id": "NR02", "channel": "Google Ads", "cost": 4200, "impressions": 120000, "clicks": 3200, "conversions": 260},
      {"campaign_id": "NR03", "channel": "LinkedIn Ads", "cost": 3800, "impressions": 50000, "clicks": 1100, "conversions": 95}
    ]"""
    
    # Données CRM (Enrichissement)
    crm_data = {
        'lead_id': [201, 202, 203, 204, 205, 206, 207, 208, 209, 210],
        'company_size': ['1-10', '10-50', '50-100', '1-10', '100-500', '50-100', '10-50', '100-500', '50-100', '1-10'],
        'sector': ['SaaS', 'Industry', 'Finance', 'HealthTech', 'Retail', 'SaaS', 'Education', 'Industry', 'Finance', 'SaaS'],
        'region': ['Île-de-France', 'Hauts-de-France', 'PACA', 'Occitanie', 'Auvergne-Rhône-Alpes', 'Île-de-France', 'Nouvelle-Aquitaine', 'Grand Est', 'Île-de-France', 'Bretagne'],
        'status': ['MQL', 'SQL', 'Client', 'MQL', 'SQL', 'Client', 'MQL', 'SQL', 'Client', 'MQL']
    }

    # Création des DataFrames
    df_leads = pd.read_csv(io.StringIO(csv_data))
    df_leads['date'] = pd.to_datetime(df_leads['date'])
    
    df_campaigns = pd.DataFrame(json.loads(json_data))
    df_crm = pd.DataFrame(crm_data)
    
    # Fusion (Merge)
    df_merged = pd.merge(df_leads, df_crm, on='lead_id', how='left')
    
    # Calcul des KPI Campagnes
    df_campaigns['CTR'] = (df_campaigns['clicks'] / df_campaigns['impressions']) * 100
    df_campaigns['Conversion_Rate'] = (df_campaigns['conversions'] / df_campaigns['clicks']) * 100
    df_campaigns['CPL'] = df_campaigns['cost'] / df_campaigns['conversions']
    
    return df_campaigns, df_merged

# Chargement
df_camp, df_detail = load_data()

# --- 3. BARRE LATÉRALE (Filtres) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=50) # Logo placeholder
st.sidebar.header("🔍 Filtres")

# Filtre Canal
selected_channel = st.sidebar.multiselect(
    "Canal d'acquisition",
    options=df_camp['channel'].unique(),
    default=df_camp['channel'].unique()
)

# Filtre Date (Périmètre imposé : Octobre 2025)
st.sidebar.markdown("---")
st.sidebar.info("📅 **Périmètre :** Octobre 2025")

# Application des filtres
if not selected_channel:
    st.warning("Veuillez sélectionner au moins un canal.")
    st.stop()

df_camp_filtered = df_camp[df_camp['channel'].isin(selected_channel)]
df_detail_filtered = df_detail[df_detail['channel'].isin(selected_channel)]

# --- 4. KPI GLOBAUX (Haut de page) ---
st.title("🚀 NovaRetail - Performance Marketing by FOMENA")
st.markdown("Tableau de bord de suivi du ROI et de la Qualité des Leads.")

# Calculs agrégés
total_spend = df_camp_filtered['cost'].sum()
total_leads = df_camp_filtered['conversions'].sum()
global_cpl = total_spend / total_leads if total_leads > 0 else 0
global_conv_rate = (df_camp_filtered['conversions'].sum() / df_camp_filtered['clicks'].sum()) * 100

# Affichage en 4 colonnes
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("💰 Budget Dépensé", f"{total_spend:,.0f} €")
kpi2.metric("👥 Total Leads", f"{total_leads}")
kpi3.metric("📉 Coût par Lead (CPL)", f"{global_cpl:.2f} €")
kpi4.metric("⚡ Taux Conv. Global", f"{global_conv_rate:.2f} %")

st.markdown("---")

# --- 5. ANALYSE DE LA RENTABILITÉ (Milieu de page) ---
st.subheader("📊 Rentabilité & Efficacité par Canal")

col_left, col_right = st.columns(2)

with col_left:
    # GRAPHIQUE 1 : CPL par Canal (Rentabilité)
    fig_cpl = px.bar(
        df_camp_filtered, 
        x='channel', 
        y='CPL', 
        color='CPL',
        color_continuous_scale='Teal',
        title="<b>Coût par Lead (CPL)</b>",
        text_auto='.3s'
    )
    fig_cpl.update_layout(yaxis_title="Coût (€)", xaxis_title="", showlegend=False)
    fig_cpl.update_traces(textposition='outside', texttemplate='%{y:.1f}€')
    st.plotly_chart(fig_cpl, use_container_width=True)
    
    # INTERPRÉTATION 1
    st.info("💡 **Analyse CPL :** L'Emailing est le canal le plus économique (10€). LinkedIn est 4x plus cher, ce qui nécessite une surveillance du ROI.")

with col_right:
    # GRAPHIQUE 2 : CTR vs Conversion (Efficacité - Double Axe)
    fig_dual = go.Figure()
    
    # Barres pour le CTR
    fig_dual.add_trace(go.Bar(
        x=df_camp_filtered['channel'],
        y=df_camp_filtered['CTR'],
        name='CTR (%)',
        marker_color='#636EFA',
        yaxis='y'
    ))
    
    # Ligne pour le Taux de Conversion
    fig_dual.add_trace(go.Scatter(
        x=df_camp_filtered['channel'],
        y=df_camp_filtered['Conversion_Rate'],
        name='Taux Conv (%)',
        marker=dict(size=10, color='#EF553B'),
        mode='lines+markers',
        yaxis='y2'
    ))
    
    fig_dual.update_layout(
        title="<b>CTR vs Taux de Transformation</b>",
        yaxis=dict(title="CTR (%)", side="left", showgrid=False),
        yaxis2=dict(title="Taux Conv (%)", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_dual, use_container_width=True)
    
    # INTERPRÉTATION 2
    st.info("💡 **Analyse Efficacité :** L'Emailing a le meilleur CTR (Attractivité), mais LinkedIn présente un excellent taux de conversion une fois le clic obtenu.")

# --- 6. ANALYSE QUALITATIVE ---
st.subheader("🎯 Qualité & Segmentation (Impact Business)")

col_qual1, col_qual2 = st.columns([2, 1])

with col_qual1:
    # GRAPHIQUE 3 : Statut des Leads par Canal
    df_status = df_detail_filtered.groupby(['channel', 'status']).size().reset_index(name='count')
    status_order = {'status': ['MQL', 'SQL', 'Client']}
    
    fig_status = px.bar(
        df_status, 
        x="channel", 
        y="count", 
        color="status", 
        title="<b>Qualité des Leads générés (MQL > SQL > Client)</b>",
        color_discrete_map={
            'MQL': '#FFA07A',   # Orange (Entrée de tunnel)
            'SQL': '#87CEFA',   # Bleu (Milieu de tunnel)
            'Client': '#90EE90' # Vert (Conversion finale)
        },
        category_orders=status_order,
        text_auto=True
    )
    fig_status.update_layout(yaxis_title="Nombre de Leads", xaxis_title="")
    st.plotly_chart(fig_status, use_container_width=True)
    
    # INTERPRÉTATION 3 (Critique)
    st.warning("⚠️ **Insight Majeur :** Seul LinkedIn génère des Clients signés immédiatement. L'Emailing ne produit que des MQL (bruit) et Google du SQL (volume).")

with col_qual2:
    # GRAPHIQUE 4 : Répartition Sectorielle
    fig_pie = px.pie(
        df_detail_filtered, 
        names='sector', 
        title="<b>Cibles par Secteur</b>",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textinfo='percent+label', showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # INTERPRÉTATION 4
    st.caption("ℹ️ **Cible :** Dominance des secteurs SaaS et Finance.")

# --- 7. ANALYSE DEMOGRAPHIQUE ---
st.subheader("🏢 Segmentation : Taille & Région")

col_dem1, col_dem2 = st.columns(2)

with col_dem1:
    # GRAPHIQUE 5 : Analyse par Taille d'Entreprise
    df_size = df_detail_filtered['company_size'].value_counts().reset_index()
    df_size.columns = ['Taille', 'Nombre']

    fig_size = px.bar(
        df_size, 
        x='Taille', 
        y='Nombre',
        title="<b>Répartition par Taille d'Entreprise</b>",
        color='Nombre',
        color_continuous_scale='Blues',
        template='plotly_white'
    )
    st.plotly_chart(fig_size, use_container_width=True)
    
    # INTERPRÉTATION 5
    st.caption("ℹ️ **Taille :** Les PME/ETI (50-500) sont bien représentées, validant le ciblage B2B.")

with col_dem2:
    # GRAPHIQUE 6 : Analyse par Région (Top 5)
    df_region = df_detail_filtered['region'].value_counts().nlargest(5).reset_index()
    df_region.columns = ['Région', 'Nombre']

    fig_region = px.bar(
        df_region, 
        x='Nombre', 
        y='Région', 
        orientation='h',
        title="<b>Top Régions des Leads</b>",
        color='Nombre',
        color_continuous_scale='Teal',
        template='plotly_white'
    )
    fig_region.update_layout(yaxis={'categoryorder':'total ascending'}) 
    st.plotly_chart(fig_region, use_container_width=True)
    
    # INTERPRÉTATION 6
    st.caption("ℹ️ **Géo :** Forte concentration en Île-de-France, suivie des pôles économiques majeurs.")


# --- 8. ANALYSE ET RECOMMANDATIONS (Mise à jour) ---
with st.expander("💡 Voir l'analyse stratégique et les recommandations"):
    
    # Partie 1 : Les questions auxquelles répond ce dashboard
    st.markdown("""
    ### 🧠 Problématiques Métier
    Ce tableau de bord a été conçu pour répondre à 5 questions stratégiques :
    
    1.  **Performance Marketing (CTR/Conv) :** *Notre tunnel d'acquisition est-il efficace ?* (Attractivité vs Transformation).
    2.  **Coût par Lead (CPL) :** *Où part notre argent ?* (Optimisation de l'Allocation Budgétaire).
    3.  **Qualité des Leads :** *Générons-nous du chiffre d'affaires ou du vent ?* (Arbitrage Quantité vs Qualité / ROI Réel).
    4.  **Secteurs & Taille :** *Qui sont nos vrais clients ?* (Validation du Product-Market Fit et adaptation de la force de vente).
    5.  **Régions :** *Où devons-nous prospecter ?* (Stratégie de Maillage Territorial).
    
    ---
    """)

    # Partie 2 : Les recommandations concrètes (Actionable Insights)
    st.markdown("""
    ### 📌 Recommandations Opérationnelles (Octobre 2025)
    
    1.  **NE PAS COUPER LINKEDIN ADS :** Bien que son CPL soit élevé (40€), c'est le **seul canal qui génère des signatures clients directes**. C'est le canal de la rentabilité réelle.
    2.  **RESTRUCTURER L'EMAILING :** Ce canal génère du volume à bas coût (10€) mais uniquement des prospects froids (MQL). **Action :** Mettre en place une boucle de *Nurturing* automatique avant de les envoyer aux commerciaux.
    3.  **CIBLAGE GÉOGRAPHIQUE :** Concentrer les budgets Google Ads sur l'**Île-de-France** (Cœur de cible) et tester une approche locale sur la région **Auvergne-Rhône-Alpes** (2ème vivier de leads).
    """)
    
    
    # Bouton de téléchargement
    csv_export = df_detail_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données consolidées (CSV)",
        data=csv_export,
        file_name='novaretail_data_oct2025.csv',
        mime='text/csv',
    )