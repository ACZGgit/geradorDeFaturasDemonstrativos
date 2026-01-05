import pandas as pd
import numpy as np
import random
import yaml
from datetime import datetime, timedelta

# --- Configurações ---
random.seed(42)
np.random.seed(42)

provider_name = "HOSPITAL BOM ATENDIMENTO"
files_path    = "./files/"

glosa_chance  = 0.40
target_rows   = 500
num_remessas  = 1
start_date    = datetime(2023, 10, 1)


# Banco de dados de Itens (Código, Descrição, Faixa de Preço)
items_db = [
# GRUPO 1: CONSULTAS
    (10101012, "CONSULTA EM PRONTO SOCORRO", (80.0, 150.0)),
    (10101039, "CONSULTA EM CONSULTORIO (NO HORARIO NORMAL)", (100.0, 250.0)),

    # GRUPO 2: PROCEDIMENTOS CLÍNICOS E HOSPITALARES
    (20103478, "NEBULIZACAO (POR SESSAO)", (15.0, 30.0)),
    (20104040, "DIARIA DE UTI ADULTO (GERAL)", (800.0, 2500.0)),
    (20104199, "DIARIA DE QUARTO PRIVATIVO", (300.0, 600.0)),
    (20104148, "DIARIA DE ENFERMARIA", (150.0, 350.0)),
    (20103630, "CURATIVO DE EXTREMIDADES DE ORIGEM VASCULAR", (40.0, 90.0)),
    (20201046, "CARDIOVERSAO ELETRICA DE EMERGENCIA", (300.0, 500.0)),

    # GRUPO 3: PROCEDIMENTOS CIRÚRGICOS E INVASIVOS
    (30906060, "RESSONANCIA MAGNETICA DE CRANIO", (600.0, 1200.0)), # Tecnicamente Imagem, mas as vezes classificado aqui
    (31009050, "DRENAGEM DE ABSCESSO", (150.0, 400.0)),
    (30201012, "ELETROCARDIOGRAMA CONVENCIONAL", (40.0, 80.0)),

    # GRUPO 4: EXAMES DIAGNÓSTICOS E TERAPÊUTICOS
    # Laboratório
    (40304361, "HEMOGRAMA COMPLETO", (15.0, 35.0)),
    (40301011, "GLICOSE", (5.0, 15.0)),
    (40302020, "COLESTEROL TOTAL", (10.0, 25.0)),
    (40302012, "UREIA", (8.0, 20.0)),
    (40301062, "CREATININA", (8.0, 20.0)),
    (40306135, "TGP (ALANINA AMINOTRANSFERASE)", (10.0, 25.0)),
    (40306143, "TGO (ASPARTATO AMINOTRANSFERASE)", (10.0, 25.0)),
    (40316025, "TSH (HORMONIO TIREOESTIMULANTE)", (25.0, 50.0)),
    (40316050, "T4 LIVRE", (25.0, 50.0)),
    (40305023, "PROTEINA C REATIVA, QUALITATIVA", (15.0, 30.0)),
    (40302489, "TRIGLICERIDEOS", (12.0, 28.0)),
    (40311198, "URINA TIPO I", (10.0, 20.0)),
    (40304582, "TEMPO DE PROTROMBINA (TAP)", (12.0, 25.0)),

    # Imagem
    (40805011, "RX - TORAX PA E PERFIL", (50.0, 90.0)),
    (40804058, "RX - JOELHO", (50.0, 80.0)),
    (40804023, "RX - TORNOZELO", (50.0, 80.0)),
    (40901123, "ULTRASSONOGRAFIA ABDOME TOTAL", (120.0, 250.0)),
    (40901107, "ULTRASSONOGRAFIA OBSTETRICA", (100.0, 220.0)),
    (41001010, "TOMOGRAFIA COMPUTADORIZADA DE CRANIO", (300.0, 600.0)),
    (41001079, "TOMOGRAFIA COMPUTADORIZADA DE TORAX", (400.0, 800.0)),
    (41001125, "TOMOGRAFIA COMPUTADORIZADA DE ABDOME SUPERIOR", (450.0, 900.0)),
    (40201120, "ENDOSCOPIA DIGESTIVA ALTA", (350.0, 700.0)),

    # TAXAS E MATERIAIS (Simulação códigos TISS/SIMPRO)
    (60000001, "TAXA DE SALA DE OBSERVACAO", (50.0, 120.0)),
    (60000002, "TAXA DE MATERIAIS DESCARTAVEIS PEQUENO PORTE", (20.0, 60.0)),
    (70000010, "KIT DE ACESSO VENOSO", (25.0, 50.0)),
    (70000350, "SERINGA DESCARTAVEL 5ML C/ AGULHA", (2.0, 5.0)),
    (70000420, "LUVA CIRURGICA ESTERIL (PAR)", (3.0, 8.0)),
    (70000810, "CATETER INTRAVENOSO PERIFERICO", (15.0, 35.0)),

    # MEDICAMENTOS (Simulação códigos TISS/Brasíndice)
    (90000010, "DIPIRONA SODICA 1G/2ML INJ", (3.0, 12.0)),
    (90000020, "SORO FISIOLOGICO 0.9% 500ML SIST FECHADO", (8.0, 25.0)),
    (90000030, "CETOPROFENO 100MG IM", (10.0, 30.0)),
    (90010010, "AMOXICILINA 500MG (COMPRIMIDO)", (1.50, 4.00)),
    (90010050, "CEFTRIAXONA 1G INJ", (25.0, 60.0)),
    (90010120, "OMEPRAZOL 40MG PO LIOFILO INJ", (15.0, 40.0)),
    (90020055, "ONDANSETRONA 4MG INJ", (12.0, 35.0)),
    (90025010, "TRAMADOL 50MG INJ", (15.0, 45.0)),
    (90030015, "DIMENIDRINATO + PIRIDOXINA (DRAMIN B6) INJ", (5.0, 15.0))
]

# --- Dicionário de Glosas (Padrão TISS)
glosa_reasons = {
    "1001": "Número da carteira inválido",
    "1002": "A guia não pertence ao sistema",
    "1004": "Senha da guia inválida ou vencida",
    "1009": "Beneficiário com pagamento em aberto",
    "1013": "CNES do contratado inválido",
    "1203": "Acomodação não autorizada",
    "1204": "Acomodação não contratada",
    "1211": "Assinatura do médico ou prestador ausente",
    "1404": "Quantidade faturada acima da quantidade autorizada",
    "1409": "Quantidade solicitada acima da máxima permitida",
    "1419": "Procedimento não autorizado",
    "1426": "Procedimento/item não coberto pelo rol da ANS",
    "1612": "Serviço profissional hospitalar não compatível",
    "1707": "Paciente não identificado",
    "1802": "Procedimento incompatível com a idade",
    "1803": "Procedimento incompatível com o sexo",
    "2005": "Valor apresentado maior que o valor contratado",
    "2011": "Valor do item acima do acordado em pacote",
    "2204": "Material não autorizado",
    "2302": "Taxa ou aluguel não autorizado",
    "2505": "Medicamento não autorizado",
    "5001": "Beneficiário suspenso",
    "5006": "Beneficiário cancelado"
}

# Banco de dados de Beneficiários (Expandido)
beneficiaries_db = [
    # Bleach
    ("ICHIGO KUROSAKI", "SOUL001"), ("RUKIA KUCHIKI", "SOUL002"), ("ORIHIME INOUE", "SOUL003"), ("URYU ISHIDA", "SOUL004"),
    ("RENJI ABARAI", "SOUL005"), ("BYAKUYA KUCHIKI", "SOUL006"), ("KENPACHI ZARAKI", "SOUL007"), ("TOSHIRO HITSUGAYA", "SOUL008"),
    ("RANGIKU MATSUMOTO", "SOUL009"), ("SOSUKE AIZEN", "SOUL010"),

    # Boku no Hero Academia
    ("IZUKU MIDORIYA", "UA001"), ("KATSUKI BAKUGO", "UA002"), ("OCHACO URARAKA", "UA003"), ("SHOTO TODOROKI", "UA004"),
    ("TENYA IIDA", "UA005"), ("TSUYU ASUI", "UA006"), ("EIJIRO KIRISHIMA", "UA007"), ("ALL MIGHT", "UA008"),
    ("SHOTA AIZAWA", "UA009"), ("ENDEAVOR", "UA010"),

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
    ("REX SLOAN", "VILTRUM005"), ("DUPLI-KATE", "VILTRUM006"), ("WILLIAM CLOCKWELL", "VILTRUM007"),

    # Star Wars
    ("LUKE SKYWALKER", "JEDI001"), ("LEIA ORGANA", "JEDI002"), ("HAN SOLO", "JEDI003"), ("DARTH VADER", "SITH001"),
    ("YODA", "JEDI004"), ("OBI-WAN KENOBI", "JEDI005"), ("PADME AMIDALA", "REP001"), ("CHEWBACCA", "JEDI006"),

    # Harry Potter
    ("HARRY POTTER", "HOG001"), ("HERMIONE GRANGER", "HOG002"), ("RON WEASLEY", "HOG003"), ("ALBUS DUMBLEDORE", "HOG004"),
    ("SEVERUS SNAPE", "HOG005"), ("DRACO MALFOY", "SLY001"), ("RUBEUS HAGRID", "HOG006"), ("SIRIUS BLACK", "HOG007")
]

def generate_large_dataset(num_remessas, start_date, target_rows):
    data = []
    rows_generated = 0
    remessa_id  = random.randint(10000, 99999)
    # Data Faturamento ~ 20 a 30 dias após start_date
    billing_date = start_date + timedelta(days=random.randint(20, 30))
    billing_date_str = billing_date.strftime("%Y-%m-%d 00:00:00.000000")

    while rows_generated < target_rows:
        name, matricula = random.choice(beneficiaries_db)
        guia_id = random.randint(1000000000, 9999999999)
        senha = random.randint(10000, 99999)
        # Data Atendimento ~ 0 a 15 dias após start_date (sempre antes do faturamento)
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

    protocol_id = random.randint(10000, 99999)

    statement_rows = []
    billing_date_str = df['data_faturamento'].iloc[0]
    billing_date = datetime.strptime(billing_date_str, "%Y-%m-%d 00:00:00.000000")

    # Pagamento 30 dias após faturamento (garante ser posterior ao atendimento)
    payment_date = billing_date + timedelta(days=30)
    payment_date_str = payment_date.strftime("%d/%m/%Y")

    total_declarado = 0.0
    total_pago = 0.0
    total_glosa = 0.0

    # Mapa para manter consistência: Guia Prestador -> Guia Operadora
    guide_map = {}

    for _, row in df.iterrows():
        val_str = row['valor_cobrado'].replace(',', '.')
        val_declared = float(val_str)

        is_glosa = random.random() < glosa_chance # glosa chance percentage
        val_glosa = 0.0
        cod_glosa = ""
        desc_glosa = ""

        if is_glosa:
            glosa_percent = random.uniform(0.1, 1.0)
            val_glosa = round(val_declared * glosa_percent, 2)
            cod_glosa = random.choice(list(glosa_reasons.keys()))
            desc_glosa = glosa_reasons[cod_glosa]
        else:
            cod_glosa = "-"
            desc_glosa = "-"

        val_paid = val_declared - val_glosa
        total_declarado += val_declared
        total_pago += val_paid
        total_glosa += val_glosa

        # Gerar/Recuperar Guia Operadora
        p_guide = row['numero_guia']
        if p_guide not in guide_map:
            guide_map[p_guide] = random.randint(5000000000, 9999999999)
        op_guide = guide_map[p_guide]

        statement_rows.append({
            "guia_prestador": row['numero_guia'],
            "guia_operadora": op_guide,
            "senha": row['senha'],
            "beneficiario": row['nome'],
            "matricula": row['matricula'],
            "data_atendimento": row['data_atendimento'],
            "codigo": row['codigo'],
            "descricao": row['descricao'],
            "valor_declarado": f"{val_declared:.2f}".replace('.', ','),
            "valor_glosa": f"{val_glosa:.2f}".replace('.', ',') if val_glosa > 0 else "0,00",
            "codigo_glosa": cod_glosa,
            "motivo_glosa": desc_glosa,
            "valor_pago": f"{val_paid:.2f}".replace('.', ',')
        })

    summary = {
        "prestador":       df['prestador'].iloc[0],
        "remessa":         df['numero_remessa'].iloc[0],
        "protocolo":       protocol_id,
        "data_pagamento":  payment_date_str,
        "total_declarado": f"{total_declarado:.2f}".replace('.', ','),
        "total_glosa":     f"{total_glosa:.2f}".replace('.', ','),
        "total_pago":      f"{total_pago:.2f}".replace('.', ',')
    }
    return statement_rows, summary

def generate_html(rows, summary, filename):
    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Demonstrativo {summary['remessa']}</title>
<style>
body{{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;margin:20px;background-color:#f4f4f4}}
.container{{background-color:white;padding:20px;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,0.1)}}
h1{{color:#2C3E50;text-align:center;border-bottom:2px solid #E67E22;padding-bottom:10px}}
.header{{background:#ecf0f1;padding:15px;border-radius:5px;margin-bottom:20px;display:flex;justify-content:space-between;flex-wrap:wrap}}
.header p{{margin:5px 20px 5px 0}}
table{{width:100%;border-collapse:collapse;font-size:11px;margin-top:20px}}
th,td{{border:1px solid #ddd;padding:6px;text-align:left}}
th{{background-color:#E67E22;color:white;position:sticky;top:0}}
tr:nth-child(even){{background-color:#f9f9f9}}
tr:hover{{background-color:#f1f1f1}}
.val{{text-align:right}}
.glosa-row td{{color:#c0392b}}
.glosa-val{{color:#c0392b;font-weight:bold}}
.pago-val{{color:#27ae60;font-weight:bold}}
.footer{{margin-top:20px;text-align:right;font-size:14px;border-top:2px solid #ddd;padding-top:10px}}
</style>
</head>
<body>
<div class="container">
    <h1>KONOHA SAÚDE - DEMONSTRATIVO DE CONTAS MÉDICAS</h1>

    <div class="header">
        <div>
            <p><strong>Prestador:</strong> {summary['prestador']}</p>
            <p><strong>Remessa (Lote):</strong> {summary['remessa']}</p>
            <p><strong>Protocolo:</strong> {summary['protocolo']}</p>
        </div>
        <div>
            <p><strong>Data Pagamento:</strong> {summary['data_pagamento']}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Guia Prest.</th>
                <th>Guia Oper.</th>
                <th>Senha</th>
                <th>Beneficiário</th>
                <th>Data Atend.</th>
                <th>Cód. Serv.</th>
                <th>Descrição</th>
                <th>Vlr. Decl.</th>
                <th>Vlr. Glosa</th>
                <th>Cód. Glosa</th>
                <th>Motivo Glosa</th>
                <th>Vlr. Pago</th>
            </tr>
        </thead>
        <tbody>"""

    for r in rows:
        # Se houver glosa, destacamos visualmente a célula do valor glosado
        is_glosa_row = r['codigo_glosa'] != "-"
        glosa_style = 'color:red' if is_glosa_row else ''

        html += f"""
            <tr>
                <td>{r['guia_prestador']}</td>
                <td>{r['guia_operadora']}</td>
                <td>{r['senha']}</td>
                <td>{r['beneficiario']}<br><small>({r['matricula']})</small></td>
                <td>{r['data_atendimento']}</td>
                <td>{r['codigo']}</td>
                <td>{r['descricao']}</td>
                <td class="val">{r['valor_declarado']}</td>
                <td class="val glosa-val">{r['valor_glosa']}</td>
                <td style="text-align:center; {glosa_style}">{r['codigo_glosa']}</td>
                <td style="font-size:10px; {glosa_style}">{r['motivo_glosa']}</td>
                <td class="val pago-val">{r['valor_pago']}</td>
            </tr>"""

    html += f"""
        </tbody>
</table>

    <div class="footer">
        <p><strong>Total Declarado:</strong> R$ {summary['total_declarado']}</p>
        <p style="color:#c0392b"><strong>Total Glosado:</strong> R$ {summary['total_glosa']}</p>
        <p style="color:#27ae60;font-size:18px"><strong>Total Líquido Pago:</strong> R$ {summary['total_pago']}</p>
    </div>
</div>
</body>
</html>"""

    with open(filename, "w", encoding='utf-8') as f:
        f.write(html)


def generate_yml(rows, summary, filename):
    """Gera o arquivo YAML estruturado para o demonstrativo."""

    # Estrutura os dados de forma mais hierárquica para o YAML
    data_structure = {
        "cabecalho_demonstrativo": {
            "prestador": summary['prestador'],
            "numero_remessa_lote": int(summary['remessa']),
            "protocolo": summary['protocolo'],
            "data_pagamento": summary['data_pagamento'],
            "resumo_financeiro": {
                "total_declarado": summary['total_declarado'],
                "total_glosado": summary['total_glosa'],
                "total_liquido_pago": summary['total_pago']
            }
        },
        "detalhes_itens": rows
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(
                data_structure,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
    except Exception as e:
        print(f"❌ Erro ao gerar YAML: {e}")





# --- Execução Principal ---
if __name__ == "__main__":
    print("Iniciando geração de arquivos...")

    # Gera datasets
    df1 = generate_large_dataset(num_remessas, start_date, target_rows, )
    df2 = generate_large_dataset(num_remessas, start_date, target_rows)

    # Processa para demonstrativo
    rows1, sum1 = process_statement_data(df1)
    rows2, sum2 = process_statement_data(df2)

    # Nomes dos arquivos
    csv_name1            = "faturamento_konoha_003.csv"
    csv_name2            = "faturamento_konoha_004.csv"
    demonstrativo_html_1 = "demonstrativo_konoha_003.html"
    demonstrativo_yml_1  = "demonstrativo_konoha_004.yml"

    #Gerando arquivos de faturamento
    df1.to_csv(files_path + csv_name1, index=False)
    df2.to_csv(files_path + csv_name2, index=False)

    #Gerando arquivos de demonstrativo
    generate_html(rows1, sum1,  files_path + demonstrativo_html_1)
    generate_yml(rows2, sum2,   files_path + demonstrativo_yml_1)

    print("Concluído com sucesso!")
    print("Arquivos gerados na pasta" + files_path + ":")
    print("- faturamento_konoha_003.csv")
    print("- faturamento_konoha_004.csv")
    print("- demonstrativo_konoha_003.html")
    print("- demonstrativo_konoha_004.html")