import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from collections import deque
import heapq
import time

# Excel dosyasının adı
EXCEL_PATH = "PROLAB 3 - GÜNCEL DATASET (1).xlsx"

df = pd.read_excel(EXCEL_PATH)
df.columns = df.columns.str.strip()

# Sütun isimlerini kontrol et
print("Excel sütunları:", df.columns.tolist())
print(f"Toplam satır sayısı: {len(df)}")

# Veri kalitesi kontrolü
print("\nVeri kalitesi kontrolü:")
print(f"paper_title boş satırlar: {df['paper_title'].isna().sum()}")
print(f"coauthors boş satırlar: {df['coauthors'].isna().sum()}")
print(f"doi boş satırlar: {df['doi'].isna().sum()}")

# İlk birkaç satırı göster
print("\nİlk 3 satırın coauthors verileri:")
for i in range(min(3, len(df))):
    print(f"Satır {i}: {df.iloc[i]['coauthors']}")

title_col = 'paper_title'
coauthors_col = 'coauthors'
doi_col = 'doi'

# ORCID sütununu bul
orcid_col = None
for col in df.columns:
    if 'orcid' in col.lower():
        orcid_col = col
        break

if orcid_col:
    print(f"ORCID sütunu bulundu: {orcid_col}")
else:
    print("ORCID sütunu bulunamadı, yazar adları kullanılacak")

author_id_map = {}
author_orcid_map = {}  # ORCID'den yazar adına eşleme
G = nx.Graph()

# Her yazarın yazdığı makale sayısını tutmak için
author_paper_counts = {}

# Yazar adından ID'ye eşleme
author_name_to_id = {}
author_orcid_map = {}  # ORCID'den yazar adına eşleme

def normalize_author_name(name):
    """Yazar adını normalize et (büyük/küçük harf, boşluklar)"""
    return name.strip().lower()

def clean_author_name(name):
    """Yazar adını temizle ve standardize et"""
    # Boşlukları normalize et
    name = ' '.join(name.split())
    # Noktalama işaretlerini temizle
    name = name.replace('.', '').replace(',', '').replace(';', '').replace(':', '')
    # Fazla boşlukları kaldır
    name = ' '.join(name.split())
    return name.strip()

def find_similar_author(author_name, existing_authors):
    """Benzer yazar adı bul - daha sıkı kontrol"""
    normalized_name = normalize_author_name(author_name)
    
    # Tam eşleşme
    for existing_name in existing_authors:
        if normalize_author_name(existing_name) == normalized_name:
            return existing_name
    
    # Çok benzer eşleşme (sadece boşluk, noktalama farkı)
    for existing_name in existing_authors:
        existing_norm = normalize_author_name(existing_name)
        # Sadece boşluk ve noktalama farkı varsa
        if existing_norm.replace(' ', '') == normalized_name.replace(' ', ''):
            return existing_name
    
    return None

def parse_authors(authors_str):
    """Yazar string'ini ayrıştır ve temizle - TÜM YAZARLARI AL"""
    if pd.isna(authors_str):
        return []
    
    authors_str = str(authors_str).strip()
    if not authors_str or authors_str.lower() in ['nan', 'none', 'null', '']:
        return []
    
    authors = []
    
    # Önce farklı ayırıcıları dene
    separators = [';', '|', '\n', ' and ', ' & ', ',']
    raw_authors = [authors_str]
    
    for sep in separators:
        if any(sep in author for author in raw_authors):
            new_raw_authors = []
            for author in raw_authors:
                if sep in author:
                    new_raw_authors.extend(author.split(sep))
                else:
                    new_raw_authors.append(author)
            raw_authors = new_raw_authors
    
    # Her yazarı temizle ama daha esnek ol
    for author in raw_authors:
        author = author.strip()
        # Boş değerleri atla
        if not author or author.lower() in ['nan', 'none', 'null', '']:
            continue
        
        # Parantez içindeki bilgileri temizle ama yazar adını koru
        if '(' in author:
            # Parantez içindeki ORCID bilgilerini çıkar
            if 'orcid' in author.lower() or 'doi' in author.lower():
                author = author.split('(')[0].strip()
            # Diğer parantez içi bilgileri koru (üniversite, vb.)
        
        # Tırnak işaretlerini temizle
        author = author.strip('"\'')
        
        # Yazar adını temizle ve standardize et
        author = clean_author_name(author)
        
        # Sayısal değerleri atla (sadece tamamen sayısal olanları)
        if author.isdigit() and len(author) < 4:  # Kısa sayısal değerleri atla
            continue
            
        # En az 1 karakter olsun (2 yerine 1)
        if author and len(author) >= 1:
            authors.append(author)
    
    return authors

# Veri okuma ve işleme sürecini detaylandır
total_papers = 0
total_authors_found = 0
unique_authors = set()

for idx, row in df.iterrows():
    title = row[title_col]
    doi = row[doi_col]
    coauthors_raw = row[coauthors_col]
    orcid_raw = row[orcid_col] if orcid_col and orcid_col in df.columns else None
    
    if pd.isna(coauthors_raw):
        print(f"Satır {idx}: coauthors boş, atlanıyor")
        continue
    
    # Yeni parse_authors fonksiyonunu kullan
    coauthors = parse_authors(coauthors_raw)
    
    if not coauthors:
        print(f"Satır {idx}: Hiç yazar bulunamadı: '{coauthors_raw}'")
        continue
    
    total_papers += 1
    author_ids = []
    
    # Her yazarı işle
    for author in coauthors:
        unique_authors.add(author)
        total_authors_found += 1
        
        # ORCID varsa kullan, yoksa yazar adını kullan
        if orcid_raw and pd.notna(orcid_raw) and str(orcid_raw).strip():
            author_id = str(orcid_raw).strip()
            author_orcid_map[author_id] = author
        else:
            # Yazar adını temizle
            clean_author = clean_author_name(author)
            
            # Benzer yazar adı var mı kontrol et
            existing_authors = list(author_name_to_id.values())
            similar_author = find_similar_author(clean_author, existing_authors)
            
            if similar_author:
                # Benzer yazar bulundu, onun ID'sini kullan
                for aid, name in author_name_to_id.items():
                    if name == similar_author:
                        author_id = aid
                        break
            else:
                # Yeni yazar, yeni ID oluştur
                author_id = clean_author
        
        # Aynı ID'li yazarları birleştir
        if author_id not in author_name_to_id:
            author_name_to_id[author_id] = author
            G.add_node(author_id, name=author)
        
        author_ids.append(author_id)
        # Makale sayısını güncelle
        author_paper_counts[author] = author_paper_counts.get(author, 0) + 1
    
    # Kenarları oluştur - TÜM YAZARLAR ARASINDA
    for i in range(len(author_ids)):
        for j in range(i+1, len(author_ids)):
            if not G.has_edge(author_ids[i], author_ids[j]):
                G.add_edge(author_ids[i], author_ids[j], papers=[title], dois=[doi], weight=1)
            else:
                G[author_ids[i]][author_ids[j]]["papers"].append(title)
                G[author_ids[i]][author_ids[j]]["dois"].append(doi)
                G[author_ids[i]][author_ids[j]]["weight"] += 1
    
    # Her 100 makalede bir ilerleme raporu
    if total_papers % 100 == 0:
        print(f"İşlenen makale: {total_papers}, Bulunan yazar: {total_authors_found}, Benzersiz yazar: {len(unique_authors)}")

print(f"\n=== GRAF OLUŞTURMA İSTATİSTİKLERİ ===")
print(f"Toplam işlenen makale sayısı: {total_papers}")
print(f"Toplam bulunan yazar sayısı: {total_authors_found}")
print(f"Benzersiz yazar sayısı: {len(unique_authors)}")
print(f"Graf düğüm sayısı: {G.number_of_nodes()}")
print(f"Graf kenar sayısı: {G.number_of_edges()}")

# Yazar sayısı kontrolü
if len(unique_authors) != G.number_of_nodes():
    print(f"⚠️  UYARI: Benzersiz yazar sayısı ({len(unique_authors)}) ile graf düğüm sayısı ({G.number_of_nodes()}) farklı!")
    print("Bu, aynı yazarın farklı ID'lerle kaydedildiğini gösteriyor.")

# Yazar sayısını analiz et
print(f"\n=== YAZAR SAYISI ANALİZİ ===")
print(f"Excel'den okunan benzersiz yazar sayısı: {len(unique_authors)}")
print(f"Graf düğüm sayısı: {G.number_of_nodes()}")

# Benzer yazar adlarını bul
similar_groups = {}
for author in unique_authors:
    normalized = normalize_author_name(author)
    if normalized not in similar_groups:
        similar_groups[normalized] = []
    similar_groups[normalized].append(author)

# Birden fazla varyantı olan yazarları göster
duplicate_authors = {norm: authors for norm, authors in similar_groups.items() if len(authors) > 1}
if duplicate_authors:
    print(f"\n⚠️  Aynı yazarın farklı yazılışları bulundu ({len(duplicate_authors)} grup):")
    for norm, authors in list(duplicate_authors.items())[:5]:  # İlk 5 grubu göster
        print(f"  {norm}: {authors}")
    if len(duplicate_authors) > 5:
        print(f"  ... ve {len(duplicate_authors) - 5} grup daha")

# En çok makale yazan yazarları göster
top_authors = sorted(author_paper_counts.items(), key=lambda x: x[1], reverse=True)[:10]
print(f"\nEn çok makale yazan 10 yazar:")
for i, (author, count) in enumerate(top_authors, 1):
    print(f"{i:2d}. {author}: {count} makale")

# Yazar sayısını düzelt
print(f"\n=== DÜZELTİLMİŞ YAZAR SAYISI ===")
print(f"Temizlenmiş benzersiz yazar sayısı: {len(set(clean_author_name(a) for a in unique_authors))}")
print(f"Graf düğüm sayısı: {G.number_of_nodes()}")

# Eğer hala fazla yazar varsa, manuel kontrol öner
if len(set(clean_author_name(a) for a in unique_authors)) > 110:  # %10 tolerans
    print(f"\n⚠️  Yazar sayısı hala fazla görünüyor.")
    print("Excel dosyasını kontrol edin ve aynı yazarın farklı yazılışlarını düzeltin.")

# Eğer yazar sayısı beklenenden azsa, ek kontroller yap
if len(unique_authors) < 500:  # Beklenen minimum yazar sayısı
    print("\n⚠️  UYARI: Yazar sayısı beklenenden az!")
    print("Ek kontroller yapılıyor...")
    
    # Tüm coauthors sütununu tekrar kontrol et
    all_authors_sample = []
    for idx, row in df.iterrows():
        if not pd.isna(row[coauthors_col]):
            coauthors_str = str(row[coauthors_col])
            if coauthors_str and coauthors_str.lower() not in ['nan', 'none', '']:
                all_authors_sample.append(coauthors_str[:100])  # İlk 100 karakter
    
    print(f"Coauthors örnekleri (ilk 5):")
    for i, sample in enumerate(all_authors_sample[:5]):
        print(f"  {i+1}: {sample}")
    
    # Farklı ayırıcıları test et
    separator_test = {}
    for sample in all_authors_sample[:10]:  # İlk 10 örneği test et
        for sep in [',', ';', '|', '\n', ' and ', ' & ']:
            if sep in sample:
                separator_test[sep] = separator_test.get(sep, 0) + 1
    
    print(f"En çok kullanılan ayırıcılar: {separator_test}")

print(f"Toplam yazar sayısı: {G.number_of_nodes()}")
print(f"Toplam iş birliği (kenar) sayısı: {G.number_of_edges()}")

# Ortalama makale sayısı ve %20 sınırları
paper_counts = list(author_paper_counts.values())
avg_paper_count = sum(paper_counts) / len(paper_counts)
upper_limit = avg_paper_count * 1.2
lower_limit = avg_paper_count * 0.8

# Düğüm boyutu ve rengi belirleme - fotoğraftaki gibi
node_sizes = []
node_colors = []
for node in G.nodes():
    author = G.nodes[node]['name']
    count = author_paper_counts.get(author, 0)
    degree = G.degree(node)
    
    # Boyut: hem makale sayısı hem de bağlantı sayısına göre
    size = 200 + (count * 50) + (degree * 20)
    node_sizes.append(size)
    
    # Renk: dereceye göre (fotoğraftaki gibi yeşil tonları)
    if degree > 10:
        node_colors.append('#2E8B57')  # Sea Green
    elif degree > 5:
        node_colors.append('#3CB371')  # Medium Sea Green
    elif degree > 2:
        node_colors.append('#66CDAA')  # Medium Aquamarine
    else:
        node_colors.append('#98FB98')  # Pale Green

# Kenar kalınlıkları (ağırlık) - daha kalın kenarlar
edge_widths = [G[u][v]['weight'] for u, v in G.edges()]
max_weight = max(edge_widths) if edge_widths else 1
edge_widths = [1.0 + 3*(w-1)/max_weight for w in edge_widths]  # min 1.0, max 4.0

# Layout - daha kompakt ve merkezi yerleşim
pos = nx.spring_layout(G, seed=42, k=1, iterations=100)

fig, ax = plt.subplots(figsize=(16, 12))

# Önce kenarları çiz - daha kalın ve belirgin
nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color="#666666", ax=ax)

# Sonra düğümleri çiz (kenarların üstünde görünsün)
nx.draw_networkx_nodes(
    G, pos,
    node_color=node_colors,
    node_size=node_sizes,
    alpha=0.8,
    linewidths=2,
    edgecolors="#000000",
    ax=ax
)

# Daha fazla düğümü etiketle
labels = {}
for node in G.nodes():
    author = G.nodes[node]['name']
    count = author_paper_counts.get(author, 0)
    # Daha fazla yazarı etiketle
    if count > avg_paper_count * 0.5:  # Ortalama makale sayısının yarısından fazla olanları
        labels[node] = author

for node, (x, y) in pos.items():
    if node in labels:
        ax.text(
            x, y, labels[node],
            fontsize=9,
            fontweight='bold',
            color='#000',
            ha='center', va='center',
            zorder=3,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='none')
        )

ax.set_title("4. Graf Modeli", fontsize=16, fontweight='bold', loc='left')
ax.set_facecolor('white')
ax.axis('off')

# Görünüm alanını ayarla - daha kompakt
x_coords = [pos[node][0] for node in G.nodes()]
y_coords = [pos[node][1] for node in G.nodes()]

# Tüm grafiği göster, biraz daha kompakt
ax.set_xlim(min(x_coords) - 0.05, max(x_coords) + 0.05)
ax.set_ylim(min(y_coords) - 0.05, max(y_coords) + 0.05)

fig.tight_layout(pad=2)

# BST Node sınıfı
class BSTNode:
    def __init__(self, author_id, author_name, paper_count):
        self.author_id = author_id
        self.author_name = author_name
        self.paper_count = paper_count
        self.left = None
        self.right = None

class BST:
    def __init__(self):
        self.root = None
    
    def insert(self, author_id, author_name, paper_count):
        if not self.root:
            self.root = BSTNode(author_id, author_name, paper_count)
        else:
            self._insert_recursive(self.root, author_id, author_name, paper_count)
    
    def _insert_recursive(self, node, author_id, author_name, paper_count):
        if paper_count < node.paper_count:
            if node.left is None:
                node.left = BSTNode(author_id, author_name, paper_count)
            else:
                self._insert_recursive(node.left, author_id, author_name, paper_count)
        else:
            if node.right is None:
                node.right = BSTNode(author_id, author_name, paper_count)
            else:
                self._insert_recursive(node.right, author_id, author_name, paper_count)
    
    def delete(self, author_id):
        self.root = self._delete_recursive(self.root, author_id)
    
    def _delete_recursive(self, node, author_id):
        if node is None:
            return node
        
        # Yazarı bul
        if author_id < node.author_id:
            node.left = self._delete_recursive(node.left, author_id)
        elif author_id > node.author_id:
            node.right = self._delete_recursive(node.right, author_id)
        else:
            # Yazar bulundu, silme işlemi
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            
            # İki çocuğu varsa, en küçük sağ alt ağacı bul
            temp = self._min_value_node(node.right)
            node.author_id = temp.author_id
            node.author_name = temp.author_name
            node.paper_count = temp.paper_count
            node.right = self._delete_recursive(node.right, temp.author_id)
        
        return node
    
    def _min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current
    
    def inorder_traversal(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append((node.author_id, node.author_name, node.paper_count))
            self._inorder_recursive(node.right, result)

# Global değişkenler
current_path = []
current_queue = deque()
current_bst = BST()
highlighted_nodes = set()
highlighted_edges = set()

def find_author_id(author_input):
    """Yazar ID'sini bul"""
    author_input = author_input.strip()
    
    # Önce tam eşleşme ara
    for node_id in G.nodes():
        if str(node_id) == author_input or G.nodes[node_id]['name'] == author_input:
            return node_id
    
    # ORCID eşleşmesi ara
    for orcid, author_name in author_orcid_map.items():
        if orcid == author_input or author_name == author_input:
            return author_name
    
    # Kısmi eşleşme ara
    matches = []
    for node_id in G.nodes():
        author_name = G.nodes[node_id]['name']
        if author_input.lower() in author_name.lower():
            matches.append((node_id, author_name))
    
    # Eğer tek eşleşme varsa onu döndür
    if len(matches) == 1:
        return matches[0][0]
    
    # Eğer birden fazla eşleşme varsa kullanıcıya seçim sun
    if len(matches) > 1:
        match_text = f"'{author_input}' için {len(matches)} eşleşme bulundu:\n\n"
        for i, (node_id, author_name) in enumerate(matches[:10]):  # İlk 10 eşleşmeyi göster
            paper_count = author_paper_counts.get(author_name, 0)
            match_text += f"{i+1}. {author_name} - {paper_count} makale\n"
        
        if len(matches) > 10:
            match_text += f"... ve {len(matches) - 10} eşleşme daha\n"
        
        match_text += "\nLütfen tam yazar adını girin."
        messagebox.showinfo("Çoklu Eşleşme", match_text)
        return None
    
    return None

def show_author_info(node_id):
    author = G.nodes[node_id]['name']
    # Kenarlardan makale isimlerini topla
    paper_set = set()
    for neighbor in G.neighbors(node_id):
        edge_data = G.get_edge_data(node_id, neighbor)
        if edge_data and 'papers' in edge_data:
            paper_set.update(edge_data['papers'])
    paper_list = list(paper_set)
    info = f"Yazar: {author}\n\nMakaleler:\n" + "\n".join(paper_list)
    messagebox.showinfo("Yazar Bilgisi", info)

def on_click(event):
    if event.inaxes is None:
        return
    x_click, y_click = event.xdata, event.ydata
    min_dist = float('inf')
    closest_node = None
    for node, (x, y) in pos.items():
        dist = (x - x_click) ** 2 + (y - y_click) ** 2
        if dist < min_dist:
            min_dist = dist
            closest_node = node
    node_radius = max(node_sizes) / 20000
    if min_dist < node_radius ** 2:
        show_author_info(closest_node)

def on_scroll(event):
    """Mouse wheel ile zoom yapma"""
    if event.inaxes is None:
        return
    
    # Zoom faktörü
    zoom_factor = 1.1 if event.button == 'up' else 0.9
    
    # Mevcut görünüm sınırlarını al
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    
    # Mouse pozisyonunu al
    x_mouse, y_mouse = event.xdata, event.ydata
    
    # Yeni görünüm sınırlarını hesapla
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    new_x_range = x_range / zoom_factor
    new_y_range = y_range / zoom_factor
    
    # Mouse pozisyonunu merkez alarak zoom yap
    new_x_min = x_mouse - (x_mouse - x_min) / zoom_factor
    new_x_max = x_mouse + (x_max - x_mouse) / zoom_factor
    new_y_min = y_mouse - (y_mouse - y_min) / zoom_factor
    new_y_max = y_mouse + (y_max - y_mouse) / zoom_factor
    
    # Görünüm sınırlarını güncelle
    ax.set_xlim(new_x_min, new_x_max)
    ax.set_ylim(new_y_min, new_y_max)
    
    # Grafiği yenile
    canvas.draw()

def update_graph_display():
    """Grafiği güncelle"""
    ax.clear()
    
    # Kenarları çiz
    edge_colors = []
    edge_widths_updated = []
    for u, v in G.edges():
        if (u, v) in highlighted_edges or (v, u) in highlighted_edges:
            edge_colors.append('#FF0000')  # Kırmızı
            edge_widths_updated.append(3.0)
        else:
            edge_colors.append('#333333')
            edge_widths_updated.append(edge_widths[list(G.edges()).index((u, v))])
    
    nx.draw_networkx_edges(G, pos, width=edge_widths_updated, alpha=0.4, 
                          edge_color=edge_colors, ax=ax)
    
    # Düğümleri çiz
    node_colors_updated = []
    node_sizes_updated = []
    for i, node in enumerate(G.nodes()):
        if node in highlighted_nodes:
            node_colors_updated.append('#FF0000')  # Kırmızı
            node_sizes_updated.append(node_sizes[i] * 1.5)
        else:
            node_colors_updated.append(node_colors[i])
            node_sizes_updated.append(node_sizes[i])
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors_updated,
                          node_size=node_sizes_updated, alpha=0.9,
                          linewidths=1, edgecolors="#333333", ax=ax)
    
    # Etiketleri çiz
    for node, (x, y) in pos.items():
        if node in labels:
            ax.text(x, y, labels[node], fontsize=8, fontweight='normal',
                   color='#333', ha='center', va='center', zorder=3)
    
    ax.set_title("4. Graf Modeli", fontsize=16, fontweight='bold', loc='left')
    ax.set_facecolor('white')
    ax.axis('off')
    ax.set_xlim(min(x_coords) - 0.1, max(x_coords) + 0.1)
    ax.set_ylim(min(y_coords) - 0.1, max(y_coords) + 0.1)
    
    canvas.draw()

def function1_shortest_path():
    """1. A ile B yazarı arasındaki en kısa yolun bulunması"""
    global current_path, highlighted_nodes, highlighted_edges
    
    # Yazar ID'lerini al (ORCID veya yazar adı)
    author_a_input = simpledialog.askstring("Yazar A", "A yazarının ORCID'sini veya adını girin:")
    if author_a_input is None or author_a_input.strip() == "":
        return
    
    author_b_input = simpledialog.askstring("Yazar B", "B yazarının ORCID'sini veya adını girin:")
    if author_b_input is None or author_b_input.strip() == "":
        return
    
    # ID'leri bul
    author_a_id = find_author_id(author_a_input)
    author_b_id = find_author_id(author_b_input)
    
    if author_a_id is None:
        messagebox.showerror("Hata", f"A yazarı bulunamadı: {author_a_input}")
        return
    
    if author_b_id is None:
        messagebox.showerror("Hata", f"B yazarı bulunamadı: {author_b_input}")
        return
    
    # Yolların varlığını kontrol et
    if not nx.has_path(G, author_a_id, author_b_id):
        messagebox.showwarning("Uyarı", "Bu iki yazar arasında bağlantı bulunamadı!")
        return
    
    # En kısa yolu hesapla
    try:
        shortest_path = nx.shortest_path(G, author_a_id, author_b_id, weight='weight')
        current_path = shortest_path
        
        # Yolu vurgula
        highlighted_nodes = set(shortest_path)
        highlighted_edges = set()
        for i in range(len(shortest_path) - 1):
            highlighted_edges.add((shortest_path[i], shortest_path[i + 1]))
        
        # Yolu göster
        path_text = " -> ".join([G.nodes[node]['name'] for node in shortest_path])
        messagebox.showinfo("En Kısa Yol", f"Yol: {path_text}\nUzunluk: {len(shortest_path) - 1}")
        
        update_graph_display()
        
    except nx.NetworkXNoPath:
        messagebox.showwarning("Uyarı", "Bu iki yazar arasında yol bulunamadı!")

def function2_queue_by_weight():
    """2. A yazarı ve işbirliği yaptığı yazarlar için düğüm ağırlıklarına göre kuyruk oluşturma"""
    global current_queue
    
    # Yazar ID'sini al (ORCID veya yazar adı)
    author_input = simpledialog.askstring("Yazar", "A yazarının ORCID'sini veya adını girin:")
    if author_input is None or author_input.strip() == "":
        return
    
    # ID'yi bul
    author_id = find_author_id(author_input)
    
    if author_id is None:
        messagebox.showerror("Hata", f"Yazar bulunamadı: {author_input}")
        return
    
    # İşbirliği yaptığı yazarları bul
    collaborators = list(G.neighbors(author_id))
    
    # Kuyruk oluştur (makale sayısına göre sırala)
    current_queue = deque()
    for collab in collaborators:
        paper_count = author_paper_counts.get(G.nodes[collab]['name'], 0)
        current_queue.append((collab, G.nodes[collab]['name'], paper_count))
    
    # Makale sayısına göre sırala (en yüksekten en düşüğe)
    current_queue = deque(sorted(current_queue, key=lambda x: x[2], reverse=True))
    
    # Kuyruğu göster
    queue_text = "Kuyruk (makale sayısına göre sıralı):\n\n"
    for i, (node_id, name, count) in enumerate(current_queue):
        queue_text += f"{i+1}. {name} (ID: {node_id}) - {count} makale\n"
    
    messagebox.showinfo("Kuyruk Oluşturuldu", queue_text)

def function3_bst_creation():
    """3. Kuyruktaki yazarlardan bir BST oluşturma"""
    global current_bst
    
    if not current_queue:
        messagebox.showwarning("Uyarı", "Önce kuyruk oluşturun (Fonksiyon 2)!")
        return
    
    # BST'yi temizle ve yeniden oluştur
    current_bst = BST()
    
    # Kuyruktaki yazarları BST'ye ekle
    for node_id, name, paper_count in current_queue:
        current_bst.insert(node_id, name, paper_count)
    
    # BST'yi göster
    bst_nodes = current_bst.inorder_traversal()
    bst_text = "BST (Inorder traversal):\n\n"
    for node_id, name, paper_count in bst_nodes:
        bst_text += f"{name} (ID: {node_id}) - {paper_count} makale\n"
    
    messagebox.showinfo("BST Oluşturuldu", bst_text)

def function4_bst_delete():
    """BST'den yazar silme"""
    if not current_bst.root:
        messagebox.showwarning("Uyarı", "Önce BST oluşturun (Fonksiyon 3)!")
        return
    
    # Silinecek yazar ID'sini al (ORCID veya yazar adı)
    author_input = simpledialog.askstring("Yazar", "Silinecek yazarın ORCID'sini veya adını girin:")
    if author_input is None or author_input.strip() == "":
        return
    
    # ID'yi bul
    author_id = find_author_id(author_input)
    
    if author_id is None:
        messagebox.showerror("Hata", f"Yazar bulunamadı: {author_input}")
        return
    
    # Yazarı sil
    current_bst.delete(author_id)
    
    # Güncellenmiş BST'yi göster
    bst_nodes = current_bst.inorder_traversal()
    bst_text = "Güncellenmiş BST (Inorder traversal):\n\n"
    for node_id, name, paper_count in bst_nodes:
        bst_text += f"{name} (ID: {node_id}) - {paper_count} makale\n"
    
    messagebox.showinfo("Yazar Silindi", bst_text)

def function5_shortest_paths_from_a():
    """4. A yazarı ve işbirlikçi yazarlar arasında kısa yolların hesaplanması"""
    # Yazar ID'sini al (ORCID veya yazar adı)
    author_input = simpledialog.askstring("Yazar", "A yazarının ORCID'sini veya adını girin:")
    if author_input is None or author_input.strip() == "":
        return
    
    # ID'yi bul
    author_id = find_author_id(author_input)
    
    if author_id is None:
        messagebox.showerror("Hata", f"Yazar bulunamadı: {author_input}")
        return
    
    # İşbirliği yaptığı yazarları bul
    collaborators = list(G.neighbors(author_id))
    
    # Alt grafik oluştur
    subgraph_nodes = {author_id}
    for collab in collaborators:
        subgraph_nodes.add(collab)
        # İşbirlikçilerin işbirlikçilerini de ekle
        for sub_collab in G.neighbors(collab):
            subgraph_nodes.add(sub_collab)
    
    subgraph = G.subgraph(subgraph_nodes)
    
    # En kısa yolları hesapla
    shortest_paths = nx.single_source_dijkstra_path(subgraph, author_id, weight='weight')
    
    # Sonuçları göster
    result_text = f"A yazarı ({G.nodes[author_id]['name']}) için en kısa yollar:\n\n"
    for target, path in shortest_paths.items():
        if target != author_id:
            target_name = G.nodes[target]['name']
            path_names = [G.nodes[node]['name'] for node in path]
            result_text += f"{target_name}: {' -> '.join(path_names)}\n"
    
    messagebox.showinfo("En Kısa Yollar", result_text)

def function6_collaborator_count():
    """5. A yazarının işbirliği yaptığı yazar sayısının hesaplanması"""
    # Yazar ID'sini al (ORCID veya yazar adı)
    author_input = simpledialog.askstring("Yazar", "A yazarının ORCID'sini veya adını girin:")
    if author_input is None or author_input.strip() == "":
        return
    
    # ID'yi bul
    author_id = find_author_id(author_input)
    
    if author_id is None:
        messagebox.showerror("Hata", f"Yazar bulunamadı: {author_input}")
        return
    
    # İşbirliği yaptığı yazarları say
    collaborators = list(G.neighbors(author_id))
    collaborator_count = len(collaborators)
    
    # İşbirlikçilerin listesini oluştur
    collaborator_names = [G.nodes[collab]['name'] for collab in collaborators]
    
    result_text = f"Yazar: {G.nodes[author_id]['name']}\n"
    result_text += f"İşbirliği yaptığı yazar sayısı: {collaborator_count}\n\n"
    result_text += "İşbirlikçiler:\n"
    for i, name in enumerate(collaborator_names, 1):
        result_text += f"{i}. {name}\n"
    
    messagebox.showinfo("İşbirlikçi Sayısı", result_text)

def function7_most_collaborative():
    """6. En çok işbirliği yapan yazarın belirlenmesi"""
    # En yüksek dereceye sahip düğümü bul
    max_degree = 0
    most_collaborative_author = None
    
    for node in G.nodes():
        degree = G.degree(node)
        if degree > max_degree:
            max_degree = degree
            most_collaborative_author = node
    
    if most_collaborative_author:
        author_name = G.nodes[most_collaborative_author]['name']
        paper_count = author_paper_counts.get(author_name, 0)
        
        result_text = f"En çok işbirliği yapan yazar:\n\n"
        result_text += f"İsim: {author_name}\n"
        result_text += f"ID: {most_collaborative_author}\n"
        result_text += f"İşbirliği sayısı: {max_degree}\n"
        result_text += f"Makale sayısı: {paper_count}"
        
        messagebox.showinfo("En Çok İşbirliği Yapan Yazar", result_text)

def function8_longest_path():
    """7. Kullanıcıdan alınan yazar ID'sinden gidebileceği en uzun yolun bulunması"""
    # Yazar ID'sini al (ORCID veya yazar adı)
    author_input = simpledialog.askstring("Yazar", "Başlangıç yazarının ORCID'sini veya adını girin:")
    if author_input is None or author_input.strip() == "":
        return
    
    # ID'yi bul
    author_id = find_author_id(author_input)
    
    if author_id is None:
        messagebox.showerror("Hata", f"Yazar bulunamadı: {author_input}")
        return
    
    # DFS ile en uzun yolu bul
    def dfs_longest_path(node, visited, path):
        visited.add(node)
        path.append(node)
        
        max_path = path[:]
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                new_path = dfs_longest_path(neighbor, visited, path[:])
                if len(new_path) > len(max_path):
                    max_path = new_path
        
        return max_path
    
    # En uzun yolu bul
    longest_path = dfs_longest_path(author_id, set(), [])
    
    # Yolu göster
    path_names = [G.nodes[node]['name'] for node in longest_path]
    path_text = " -> ".join(path_names)
    
    result_text = f"En uzun yol:\n\n"
    result_text += f"Yol: {path_text}\n"
    result_text += f"Uzunluk: {len(longest_path) - 1} adım\n"
    result_text += f"Ziyaret edilen düğüm sayısı: {len(longest_path)}"
    
    messagebox.showinfo("En Uzun Yol", result_text)

def show_available_authors():
    """Mevcut yazarları göster"""
    # Tüm yazarları makale sayısına göre sırala
    sorted_authors = []
    for node_id in G.nodes():
        author_name = G.nodes[node_id]['name']
        paper_count = author_paper_counts.get(author_name, 0)
        degree = G.degree(node_id)
        sorted_authors.append((author_name, node_id, paper_count, degree))
    
    # Makale sayısına göre azalan sırada sırala
    sorted_authors.sort(key=lambda x: x[2], reverse=True)
    
    authors_text = f"Toplam {len(sorted_authors)} Yazar:\n\n"
    authors_text += "Sıra | Yazar Adı | Makale Sayısı | Bağlantı Sayısı | ID/ORCID\n"
    authors_text += "-" * 80 + "\n"
    
    for i, (author_name, node_id, paper_count, degree) in enumerate(sorted_authors):
        # ORCID varsa göster
        if node_id in author_orcid_map.values():
            orcid = [k for k, v in author_orcid_map.items() if v == node_id][0]
            id_info = f"ORCID: {orcid}"
        else:
            id_info = f"ID: {node_id}"
        
        authors_text += f"{i+1:3d} | {author_name:<25} | {paper_count:3d} | {degree:3d} | {id_info}\n"
    
    # Eğer çok uzunsa, dosyaya kaydet seçeneği sun
    if len(authors_text) > 10000:  # Çok uzun liste
        # Dosyaya kaydet
        with open("yazar_listesi.txt", "w", encoding="utf-8") as f:
            f.write(authors_text)
        
        messagebox.showinfo("Yazar Listesi", 
                          f"Toplam {len(sorted_authors)} yazar bulundu!\n\n"
                          f"Liste çok uzun olduğu için 'yazar_listesi.txt' dosyasına kaydedildi.\n\n"
                          f"İlk 10 yazar:\n" + 
                          "\n".join([f"{i+1}. {author[0]} - {author[2]} makale" 
                                    for i, author in enumerate(sorted_authors[:10])]))
    else:
        messagebox.showinfo("Mevcut Yazarlar", authors_text)

def search_author():
    """Yazar arama fonksiyonu"""
    search_term = simpledialog.askstring("Yazar Ara", "Aranacak yazar adını girin:")
    if not search_term or search_term.strip() == "":
        return
    
    search_term = search_term.strip().lower()
    matches = []
    
    for node_id in G.nodes():
        author_name = G.nodes[node_id]['name']
        if search_term in author_name.lower():
            paper_count = author_paper_counts.get(author_name, 0)
            degree = G.degree(node_id)
            matches.append((author_name, node_id, paper_count, degree))
    
    if not matches:
        messagebox.showinfo("Arama Sonucu", f"'{search_term}' için sonuç bulunamadı.")
        return
    
    # Sonuçları makale sayısına göre sırala
    matches.sort(key=lambda x: x[2], reverse=True)
    
    result_text = f"'{search_term}' için {len(matches)} sonuç bulundu:\n\n"
    result_text += "Yazar Adı | Makale Sayısı | Bağlantı Sayısı | ID/ORCID\n"
    result_text += "-" * 70 + "\n"
    
    for author_name, node_id, paper_count, degree in matches[:20]:  # İlk 20 sonucu göster
        if node_id in author_orcid_map.values():
            orcid = [k for k, v in author_orcid_map.items() if v == node_id][0]
            id_info = f"ORCID: {orcid}"
        else:
            id_info = f"ID: {node_id}"
        
        result_text += f"{author_name:<20} | {paper_count:3d} | {degree:3d} | {id_info}\n"
    
    if len(matches) > 20:
        result_text += f"\n... ve {len(matches) - 20} sonuç daha"
    
    messagebox.showinfo("Arama Sonucu", result_text)

# Tkinter penceresi oluştur ve matplotlib grafiğini göm
root = tk.Tk()
root.title("Yazarlar Arası İş Birliği Grafı - Analiz Sistemi")
root.geometry("1400x900")

# Sol panel - Butonlar
left_frame = tk.Frame(root, width=300, bg='#f0f0f0')
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

# Başlık
title_label = tk.Label(left_frame, text="Analiz Fonksiyonları", font=("Arial", 14, "bold"), bg='#f0f0f0')
title_label.pack(pady=10)

# Butonlar
buttons = [
    ("1. En Kısa Yol Bul", function1_shortest_path),
    ("2. Kuyruk Oluştur", function2_queue_by_weight),
    ("3. BST Oluştur", function3_bst_creation),
    ("4. BST'den Yazar Sil", function4_bst_delete),
    ("5. Kısa Yollar Hesapla", function5_shortest_paths_from_a),
    ("6. İşbirlikçi Sayısı", function6_collaborator_count),
    ("7. En Çok İşbirliği", function7_most_collaborative),
    ("8. En Uzun Yol", function8_longest_path),
    ("9. Yazarları Listele", show_available_authors),
    ("10. Yazar Ara", search_author)
]

for text, command in buttons:
    btn = tk.Button(left_frame, text=text, command=command, 
                   width=25, height=2, font=("Arial", 10),
                   bg='#4CAF50', fg='white', relief=tk.RAISED)
    btn.pack(pady=5)

# Sağ panel - Grafik
right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Navigation toolbar ekle
toolbar = NavigationToolbar2Tk(canvas, right_frame)
toolbar.update()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Tıklama ve scroll olaylarını canvas'a bağla
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('scroll_event', on_scroll)

print("Grafikte zoom ve pan için:")
print("- Fare tekerleği ile zoom yapabilirsiniz (scroll up: büyüt, scroll down: küçült)")
print("- Fare ile sürükleyerek grafiği kaydırabilirsiniz")
print("- Toolbar'daki büyüteç ve el ikonlarını kullanabilirsiniz")
print("- Düğümlere tıklayarak yazar bilgilerini görebilirsiniz")
print("\nÖNEMLİ: Artık yazar ID'leri yerine ORCID'leri veya yazar adlarını kullanabilirsiniz!")
print("Yazarları görmek için '9. Yazarları Listele' butonunu kullanın.")
print("Arama yaparken yazar adının bir kısmını da yazabilirsiniz (kısmi eşleşme).")

root.mainloop() 