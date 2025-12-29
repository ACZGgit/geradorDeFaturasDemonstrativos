import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# --- Configurações ---
random.seed(42)
np.random.seed(42)

provider_name = "HOSPITAL BOM ATENDIMENTO"

# Banco de dados de Itens (Código, Descrição, Faixa de Preço)
items_db = [
    (10101012, "CONSULTA EM PRONTO SOCORRO", (50.0, 150.0)),
    (40304361, "HEMOGRAMA COMPLETO", (15.0, 30.0)),
    (40301011, "GLICOSE", (5.0, 15.0)),
    (40805011, "RX TORAX", (40.0, 80.0)),
    (40901123, "ULTRASSONOGRAFIA ABDOME TOTAL", (100.0, 200.0)),
    (90000010, "DIPIRONA SODICA 1G", (2.0, 10.0)),
    (90000020, "SORO FISIOLOGICO 0.9% 500ML", (5.0, 20.0)),
    (90000030, "KETOPROFENO 100MG", (8.0, 25.0)),
    (60000001, "TAXA DE SALA", (50.0, 100.0)),
    (60000002, "TAXA DE MATERIAIS DESCARTAVEIS", (20.0, 50.0)),
    (20104040, "TERAPIA INTENSIVA", (500.0, 1200.0)),
    (30906060, "RESSONANCIA MAGNETICA", (300.0, 800.0)),
    (40302020, "COLESTEROL TOTAL", (10.0, 25.0)),
    (90010010, "AMOXICILINA 500MG", (15.0, 40.0)),
    (90020020, "IBUPROFENO 600MG", (10.0, 30.0))
]

# Banco de dados de Beneficiários (Expandido)
beneficiaries_db = [
    # Naruto
    ("NARUTO UZUMAKI", "KONOHA001"), ("SASUKE UCHIHA", "KONOHA002"), ("SAKURA HARUNO", "KONOHA003"), ("KAKASHI HATAKE", "KONOHA004"),
    ("HINATA HYUGA", "KONOHA005"), ("SHIKAMARU NARA", "KONOHA006"), ("TSUNADE SENJU", "KONOHA007"), ("JIRAIYA", "KONOHA008"),
    # Dr. Stone
    ("SENKU ISHIGAMI", "STONE001"), ("TAIJU OKI", "STONE002"), ("YUZURIHA OGAWA", "STONE003"), ("TSUKASA SHISHIO", "STONE004"),
    ("CHROME", "STONE005"), ("KOHAKU", "STONE006"), ("GEN ASAGIRI", "STONE007"),
    # Shingeki no Kyojin
    ("EREN YEAGER", "TITAN001"), ("MIKASA ACKERMAN", "TITAN002"), ("ARMIN ARLERT", "TITAN003"), ("LEVI ACKERMAN", "TITAN004"),
    ("ERWIN SMITH", "TITAN005"), ("HISTORIA REISS", "TITAN006"), ("REINER BRAUN", "TITAN007"),
    # One Punch Man
    ("SAITAMA", "HERO001"), ("GENOS", "HERO002"), ("TATSUMAKI", "HERO003"), ("BANG", "HERO004"),
    ("MUMEN RIDER", "HERO005"), ("FUBUKI", "HERO006"), ("KING", "HERO007"),
    # Invincible
    ("MARK GRAYSON", "VILTRUM001"), ("NOLAN GRAYSON", "VILTRUM002"), ("SAMANTHA EVE WILKINS", "VILTRUM003"), ("DEBBIE GRAYSON", "VILTRUM004"),
    ("REX SLOAN", "VILTRUM005"), ("DUPLI-KATE", "VILTRUM006"), ("WILLIAM CLOCKWELL", "VILTRUM007")
]

def generate_large_dataset(num_remessas=1, start_date=datetime(2023, 10, 1), target_rows=300):
    data = []
    rows_generated = 0
    remessa_id = random.randint(10000, 99999)
    billing_date = start_date + timedelta(days=random.randint(20, 30))
    billing_date_str = billing_date.strftime("%Y-%m-%d 00:00:00.000000")

    while rows_generated < target_rows:
        name, matricula = random.choice(beneficiaries_db)
        guia_id = random.randint(1000000000, 9999999999)
        senha = random.randint(10000, 99999)
        service_date = start_date + timedelta(days=random.randint(0, 15))
        service_date_str = service_date.strftime("%d/%m/%y")

        num_items = random.randint(3, 8)
        guide_items = random.choices(items_db, k=num_items)

        for code, desc, price_range in guide_items:
            price = round(random.uniform(*price_range), 2)
            price_str = f"{price:.2f}".replace('.', ',')

            row = {
                "prestador": provider_name,
                "data_faturamento": billing_date_str,
                "numero_remessa": remessa_id,
                "matricula": matricula,
                "nome": name,
                "numero_guia": guia_id,
                "senha": senha,
                "codigo": code,
                "descricao": desc,
                "valor_cobrado": price_str,
                "data_atendimento": service_date_str
            }
            data.append(row)
            rows_generated += 1
            if rows_generated >= target_rows:
                break
    return pd.DataFrame(data)

def process_statement_data(df):
    statement_rows = []
    billing_date_str = df['data_faturamento'].iloc[0]
    billing_date = datetime.strptime(billing_date_str, "%Y-%m-%d 00:00:00.000000")
    payment_date = billing_date + timedelta(days=30)
    payment_date_str = payment_date.strftime("%d/%m/%Y")

    total_declared = 0.0
    total_paid = 0.0
    total_glosa = 0.0

    for _, row in df.iterrows():
        val_str = row['valor_cobrado'].replace(',', '.')
        val_declared = float(val_str)
        is_glosa = random.random() < 0.15
        val_glosa = 0.0
        cod_glosa = ""

        if is_glosa:
            glosa_percent = random.uniform(0.1, 1.0)
            val_glosa = round(val_declared * glosa_percent, 2)
            cod_glosa = random.choice(["1001", "1002", "2005", "5001"])

        val_paid = val_declared - val_glosa
        total_declared += val_declared
        total_paid += val_paid
        total_glosa += val_glosa

        statement_rows.append({
            "guia": row['numero_guia'],
            "senha": row['senha'],
            "beneficiario": row['nome'],
            "matricula": row['matricula'],
            "data_atendimento": row['data_atendimento'],
            "codigo": row['codigo'],
            "descricao": row['descricao'],
            "valor_declarado": f"{val_declared:.2f}".replace('.', ','),
            "valor_glosa": f"{val_glosa:.2f}".replace('.', ',') if val_glosa > 0 else "0,00",
            "codigo_glosa": cod_glosa if val_glosa > 0 else "-",
            "valor_pago": f"{val_paid:.2f}".replace('.', ',')
        })

    summary = {
        "prestador": df['prestador'].iloc[0],
        "remessa": df['numero_remessa'].iloc[0],
        "data_pagamento": payment_date_str,
        "total_declarado": f"{total_declared:.2f}".replace('.', ','),
        "total_glosa": f"{total_glosa:.2f}".replace('.', ','),
        "total_pago": f"{total_paid:.2f}".replace('.', ',')
    }
    return statement_rows, summary

def generate_html(rows, summary, filename):
    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Demonstrativo {summary['remessa']}</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px}}
h1{{color:#2C3E50;text-align:center}}
.header{{background:#ecf0f1;padding:15px;border-radius:5px;margin-bottom:20px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background-color:#2980B9;color:white}}
tr:nth-child(even){{background-color:#f2f2f2}}
.val{{text-align:right}}
.glosa{{color:#c0392b;font-weight:bold}}
.pago{{color:#27ae60;font-weight:bold}}
</style>
</head>
<body>
<h1>KONOHA SAÚDE - DEMONSTRATIVO DE ANÁLISE DE CONTAS</h1>
<div class="header">
    <p><strong>Prestador:</strong> {summary['prestador']}</p>
    <p><strong>Remessa:</strong> {summary['remessa']}</p>
    <p><strong>Data Pagamento:</strong> {summary['data_pagamento']}</p>
</div>
<table>
    <thead>
        <tr>
            <th>Guia</th><th>Senha</th><th>Beneficiário</th><th>Data</th>
            <th>Código</th><th>Descrição</th>
            <th>Vlr. Decl.</th><th>Vlr. Glosa</th><th>Cód.</th><th>Vlr. Pago</th>
        </tr>
    </thead>
    <tbody>"""
    for r in rows:
        html += f"""
        <tr>
            <td>{r['guia']}</td><td>{r['senha']}</td><td>{r['beneficiario']} ({r['matricula']})</td><td>{r['data_atendimento']}</td>
            <td>{r['codigo']}</td><td>{r['descricao']}</td>
            <td class="val">{r['valor_declarado']}</td><td class="val glosa">{r['valor_glosa']}</td>
            <td style="text-align:center">{r['codigo_glosa']}</td><td class="val pago">{r['valor_pago']}</td>
        </tr>"""
    html += f"""
    </tbody>
</table>
<div style="margin-top:20px;text-align:right;font-size:16px">
    <p><strong>Total Declarado:</strong> R$ {summary['total_declarado']}</p>
    <p><strong>Total Glosa:</strong> R$ {summary['total_glosa']}</p>
    <p><strong>Total Pago:</strong> R$ {summary['total_pago']}</p>
</div>
</body></html>"""

    with open(filename, "w", encoding='utf-8') as f:
        f.write(html)

# --- Execução Principal ---
print("Gerando arquivos...")
df1 = generate_large_dataset(target_rows=300, start_date=datetime(2023, 11, 1))
df2 = generate_large_dataset(target_rows=300, start_date=datetime(2023, 12, 1))

rows1, sum1 = process_statement_data(df1)
rows2, sum2 = process_statement_data(df2)

df1.to_csv("faturamento_konoha_003.csv", index=False)
df2.to_csv("faturamento_konoha_004.csv", index=False)
generate_html(rows1, sum1, "demonstrativo_konoha_003.html")
generate_html(rows2, sum2, "demonstrativo_konoha_004.html")

print("Sucesso! Arquivos gerados:")
print("1. faturamento_konoha_003.csv")
print("2. faturamento_konoha_004.csv")
print("3. demonstrativo_konoha_003.html")
print("4. demonstrativo_konoha_004.html")
