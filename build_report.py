import json, os, secrets, shutil

ROOT  = r"C:/Users/msala/Data/app_store/data_analysis/MoMA+Art+Collection/artworks.Report/definition"
PAGES = os.path.join(ROOT, "pages")
SCHEMA_VIS  = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

PAGE1 = "c21b6f63e4282c3eabb0"   # Collection Overview (reuse)
PAGE2 = "4026ca00165d85b0ab8f"   # Artists (reuse)
PAGE3 = "bd643c87a2d111199f6f"   # Mediums & Acquisitions (reuse existing)

# ---- dark palette (softer slate, not near-black; white text for max contrast) ----
BG_PAGE = "#1E2536"   # page canvas
CARD    = "#2A3348"   # visual / card background
CARDHDR = "#333E56"   # table / column header background
BORDER  = "#3C4863"
TEXT    = "#FFFFFF"    # primary text -> pure white
MUTE    = "#C3CCDB"    # secondary text (axes, legend, kpi labels) -> bright, readable
GRID    = "#3A4257"
BLUE    = "#5BB0FF"
TEAL    = "#2DD4BF"
ORANGE  = "#FFAE5C"
PURPLE  = "#B892FF"
PLUM    = "#F87BC0"
GREEN   = "#5BE68A"
AMBER   = "#FCC94D"
CYAN    = "#4CC5FB"

def hexlit(v): return {"expr": {"Literal": {"Value": "'%s'" % v}}}
def lit(v):    return {"expr": {"Literal": {"Value": v}}}
def solid(c):  return {"solid": {"color": hexlit(c)}}

def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
def meas(entity, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}

def proj_col(entity, prop, active=None):
    p = {"field": col(entity, prop), "queryRef": "%s.%s" % (entity, prop), "nativeQueryRef": prop}
    if active is not None: p["active"] = active
    return p
def proj_meas(entity, prop):
    return {"field": meas(entity, prop), "queryRef": "%s.%s" % (entity, prop), "nativeQueryRef": prop}

def new_id(): return secrets.token_hex(10)

def vco(title):
    # dark card chrome applied per-visual (belt-and-suspenders over the theme)
    return {
        "title": [{"properties": {
            "show": lit("true"), "text": hexlit(title), "fontSize": lit("15D"),
            "bold": lit("true"), "fontColor": solid(TEXT), "alignment": lit("'left'"),
            "background": solid(CARD)
        }}],
        "background": [{"properties": {"show": lit("true"), "color": solid(CARD), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": solid(BORDER), "radius": lit("10D")}}],
        "padding": [{"properties": {"top": lit("8D"), "bottom": lit("8D"), "left": lit("12D"), "right": lit("12D")}}],
        "dropShadow": [{"properties": {
            "show": lit("true"), "color": solid("#0B0F17"), "position": lit("'Outer'"),
            "preset": lit("'Custom'"), "shadowSpread": lit("4D"), "shadowBlur": lit("14D"),
            "transparency": lit("55D"), "angle": lit("90D"), "shadowDistance": lit("3D")
        }}]
    }

def write_visual(page, name, obj):
    d = os.path.join(PAGES, page, "visuals", name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "visual.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def container(x, y, w, h, z, visual):
    return {"$schema": SCHEMA_VIS, "name": new_id(),
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
            "visual": visual}

# ---------- textbox (title + subtitle) ----------
def textbox(x, y, w, h, runs):
    text_runs = []
    for (txt, size, color, bold) in runs:
        tr = {"value": txt, "textStyle": {"fontSize": "%dpt" % size, "color": color}}
        if bold: tr["textStyle"]["fontWeight"] = "bold"
        text_runs.append(tr)
    visual = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": text_runs}]}}]},
        "visualContainerObjects": {"background": [{"properties": {"show": lit("false")}}]}
    }
    return container(x, y, w, h, 1000, visual)

# ---------- multi-value KPI card ----------
def kpi_card(x, y, w, h, measures, accent):
    proj = [proj_meas(e, p) for (e, p) in measures]
    visual = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": proj}}},
        "objects": {
            "value": [{"properties": {"fontSize": lit("34D"), "fontColor": solid(accent), "bold": lit("true")}}],
            "label": [{"properties": {"show": lit("true"), "fontSize": lit("14D"), "fontColor": solid(MUTE)}}]
        },
        "visualContainerObjects": {
            "background": [{"properties": {"show": lit("true"), "color": solid(CARD)}}],
            "border": [{"properties": {"show": lit("true"), "color": solid(BORDER), "radius": lit("10D")}}],
            "padding": [{"properties": {"top": lit("10D"), "bottom": lit("10D"), "left": lit("16D"), "right": lit("16D")}}],
            "dropShadow": [{"properties": {"show": lit("true"), "color": solid("#0B0F17"), "position": lit("'Outer'"),
                "preset": lit("'Custom'"), "shadowSpread": lit("4D"), "shadowBlur": lit("14D"),
                "transparency": lit("55D"), "angle": lit("90D"), "shadowDistance": lit("3D")}}]
        }
    }
    return container(x, y, w, h, 1001, visual)

# ---------- slicer (dropdown, dark) ----------
def slicer(x, y, w, h, entity, prop, title, sync=None):
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj_col(entity, prop)]}}},
        "objects": {
            "data": [{"properties": {"mode": lit("'Dropdown'")}}],
            "header": [{"properties": {"show": lit("true"), "text": hexlit(title),
                        "fontColor": solid(TEXT), "background": solid(CARD), "textSize": lit("13D")}}],
            "items": [{"properties": {"fontColor": solid(TEXT), "background": solid(CARD), "textSize": lit("12D")}}]
        },
        "visualContainerObjects": {
            "background": [{"properties": {"show": lit("true"), "color": solid(CARD)}}],
            "border": [{"properties": {"show": lit("true"), "color": solid(BORDER), "radius": lit("10D")}}],
            "padding": [{"properties": {"top": lit("8D"), "bottom": lit("8D"), "left": lit("8D"), "right": lit("8D")}}]
        }
    }
    if sync:
        visual["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
    return container(x, y, w, h, 1002, visual)

# ---------- TopN visual-level filter (subquery form) ----------
def topn_filter(entity, cat_prop, key_prop, top):
    fid = "Filter" + secrets.token_hex(12)
    return {
        "name": fid, "field": col(entity, cat_prop), "type": "TopN",
        "filter": {"Version": 2,
            "From": [
                {"Name": "subquery", "Type": 2, "Expression": {"Subquery": {"Query": {
                    "Version": 2,
                    "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": cat_prop}, "Name": "field"}],
                    "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {
                        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": key_prop}}, "Function": 5}}}],
                    "Top": top}}}},
                {"Name": "e", "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "e"}}, "Property": cat_prop}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
        "howCreated": "User"}

# ---------- cartesian (bar / column / line) ----------
def cartesian(x, y, w, h, vtype, cat_entity, cat_prop, m_entity, m_prop,
              title, color, sort_dir=None, sort_by="measure", topn=None, topn_key=None,
              labels=False):
    cat_proj = proj_col(cat_entity, cat_prop, active=True)
    m_proj = proj_meas(m_entity, m_prop)
    query = {"queryState": {"Category": {"projections": [cat_proj]}, "Y": {"projections": [m_proj]}}}
    if sort_dir:
        sort_field = (meas(m_entity, m_prop) if sort_by == "measure" else col(cat_entity, cat_prop))
        query["sortDefinition"] = {"sort": [{"field": sort_field, "direction": sort_dir}], "isDefaultSort": True}
    obj = {
        "dataPoint": [{"properties": {"fill": solid(color)}}],
        "categoryAxis": [{"properties": {"show": lit("true"), "fontSize": lit("13D"),
                          "labelColor": solid(MUTE), "gridlineShow": lit("false")}}],
        "valueAxis": [{"properties": {"show": lit("true"), "fontSize": lit("13D"),
                       "labelColor": solid(MUTE), "gridlineColor": solid(GRID)}}],
        "labels": [{"properties": {"show": lit("true" if labels else "false"), "color": solid(TEXT), "fontSize": lit("12D")}}]
    }
    if vtype == "lineChart":
        obj["lineStyles"] = [{"properties": {"strokeWidth": lit("3D"), "showMarker": lit("true")}}]
    visual = {"visualType": vtype, "query": query, "objects": obj, "visualContainerObjects": vco(title)}
    c = container(x, y, w, h, 1003, visual)
    if topn:
        c["filterConfig"] = {"filters": [topn_filter(cat_entity, cat_prop, topn_key, topn)]}
    return c

# ---------- donut ----------
def donut(x, y, w, h, cat_entity, cat_prop, m_entity, m_prop, title):
    cat_proj = proj_col(cat_entity, cat_prop, active=True)
    m_proj = proj_meas(m_entity, m_prop)
    visual = {
        "visualType": "donutChart",
        "query": {"queryState": {"Category": {"projections": [cat_proj]}, "Y": {"projections": [m_proj]}}},
        "objects": {
            "legend": [{"properties": {"show": lit("true"), "position": lit("'Right'"),
                        "labelColor": solid("#DBE1EC"), "fontSize": lit("12D")}}],
            "labels": [{"properties": {"show": lit("true"), "color": solid(TEXT), "fontSize": lit("11D"),
                        "labelStyle": lit("'Category, percent of total'")}}]
        },
        "visualContainerObjects": vco(title)
    }
    return container(x, y, w, h, 1003, visual)

# ---------- table (tableEx) ----------
def table(x, y, w, h, cols, title, sort_field=None, sort_dir="Descending"):
    # cols: list of ("col"|"meas", entity, prop)
    proj = []
    for (kind, e, p) in cols:
        proj.append(proj_col(e, p, active=True) if kind == "col" else proj_meas(e, p))
    query = {"queryState": {"Values": {"projections": proj}}}
    if sort_field:
        query["sortDefinition"] = {"sort": [{"field": sort_field, "direction": sort_dir}], "isDefaultSort": True}
    visual = {"visualType": "tableEx", "query": query,
              "objects": {
                  "columnHeaders": [{"properties": {"fontSize": lit("14D"), "fontColor": solid(TEXT), "backColor": solid(CARDHDR)}}],
                  "values": [{"properties": {"fontSize": lit("13D"), "fontColorPrimary": solid(TEXT), "backColorPrimary": solid(CARD)}}]
              },
              "visualContainerObjects": vco(title)}
    return container(x, y, w, h, 1003, visual)

# ============================ LAYOUT ============================
# 2 x 2 grid of large charts -> fewer, bigger, more readable visuals.
CX = [40, 972]          # 2-column x positions
CW = 908                # column width
R1, R2 = 344, 708       # chart row y
CH = 356                # chart height
SL_Y, SL_H = 250, 78
SLX5 = [40, 412, 784, 1156, 1528]; SL_W5 = 340   # 5-slicer row
SLX4 = [40, 490, 940, 1390];       SL_W4 = 410   # 4-slicer row

def page_json_obj(page_id, display_name):
    return {
        "$schema": SCHEMA_PAGE, "name": page_id, "displayName": display_name,
        "displayOption": "FitToPage", "height": 1080, "width": 1920,
        "objects": {
            "background": [{"properties": {"color": solid(BG_PAGE), "transparency": lit("0D")}}],
            "outspace": [{"properties": {"color": solid(BG_PAGE), "transparency": lit("0D")}}]
        }
    }

def write_page_json(page_id, display_name):
    d = os.path.join(PAGES, page_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "page.json"), "w", encoding="utf-8") as f:
        json.dump(page_json_obj(page_id, display_name), f, indent=2)

def clean_visuals(page_id):
    vdir = os.path.join(PAGES, page_id, "visuals")
    if os.path.isdir(vdir):
        shutil.rmtree(vdir)
    os.makedirs(vdir, exist_ok=True)

def title_block(subtitle):
    return textbox(40, 20, 1200, 60, [
        ("MoMA Collection  ", 26, TEXT, True),
        (subtitle, 26, BLUE, True),
    ])

def make_page1():
    clean_visuals(PAGE1)
    write_page_json(PAGE1, "Collection Overview")
    ids = []
    def add(o): write_visual(PAGE1, o["name"], o); ids.append(o["name"])
    add(title_block("Overview"))
    add(kpi_card(40, 96, 1840, 140, [
        ("Artworks", "# Artworks"), ("Artworks", "# On View"),
        ("Artworks", "% On View"), ("Artists", "# Artists")], BLUE))
    add(slicer(SLX5[0], SL_Y, SL_W5, SL_H, "Artworks", "Department", "Department", sync="ArtworkFilters"))
    add(slicer(SLX5[1], SL_Y, SL_W5, SL_H, "Artworks", "Classification", "Classification"))
    add(slicer(SLX5[2], SL_Y, SL_W5, SL_H, "Artworks", "Decade Created", "Decade Created"))
    add(slicer(SLX5[3], SL_Y, SL_W5, SL_H, "Artworks", "On View", "On View"))
    add(slicer(SLX5[4], SL_Y, SL_W5, SL_H, "Artworks", "Cataloged Status", "Cataloged Status"))
    add(cartesian(CX[0], R1, CW, CH, "barChart", "Artworks", "Classification", "Artworks", "# Artworks",
        "Top Classifications", BLUE, sort_dir="Descending", sort_by="measure", topn=12, topn_key="ObjectID", labels=True))
    add(cartesian(CX[1], R1, CW, CH, "columnChart", "Artworks", "Decade Created", "Artworks", "# Artworks",
        "Artworks by Decade Created", ORANGE, sort_dir="Ascending", sort_by="category"))
    add(cartesian(CX[0], R2, CW, CH, "lineChart", "Artworks", "Year Acquired", "Artworks", "# Artworks",
        "Acquisitions by Year", TEAL, sort_dir="Ascending", sort_by="category"))
    add(cartesian(CX[1], R2, CW, CH, "barChart", "Artworks", "Department", "Artworks", "# Artworks",
        "Artworks by Department", PURPLE, sort_dir="Descending", sort_by="measure", labels=True))
    return ids

def make_page2():
    clean_visuals(PAGE2)
    write_page_json(PAGE2, "Artists")
    ids = []
    def add(o): write_visual(PAGE2, o["name"], o); ids.append(o["name"])
    add(title_block("Artists"))
    add(kpi_card(40, 96, 1840, 140, [
        ("Artists", "# Artists"), ("Artists", "# Living Artists")], PURPLE))
    add(slicer(SLX4[0], SL_Y, SL_W4, SL_H, "Artists", "Nationality", "Nationality"))
    add(slicer(SLX4[1], SL_Y, SL_W4, SL_H, "Artists", "Gender", "Gender"))
    add(slicer(SLX4[2], SL_Y, SL_W4, SL_H, "Artists", "Living Status", "Living Status"))
    add(slicer(SLX4[3], SL_Y, SL_W4, SL_H, "Artists", "Birth Decade", "Birth Decade"))
    add(cartesian(CX[0], R1, CW, CH, "barChart", "Artists", "Nationality", "Artists", "# Artists",
        "Top Nationalities", TEAL, sort_dir="Descending", sort_by="measure", topn=12, topn_key="ConstituentID", labels=True))
    add(donut(CX[1], R1, CW, CH, "Artists", "Gender", "Artists", "# Artists", "Artists by Gender"))
    add(cartesian(CX[0], R2, CW, CH, "columnChart", "Artists", "Birth Decade", "Artists", "# Artists",
        "Artists by Birth Decade", BLUE, sort_dir="Ascending", sort_by="category"))
    add(table(CX[1], R2, CW, CH, [
        ("col", "Artists", "Nationality"), ("meas", "Artists", "# Artists"), ("meas", "Artists", "# Living Artists")],
        "Artists by Nationality", sort_field=meas("Artists", "# Artists")))
    return ids

def make_page3():
    clean_visuals(PAGE3)
    write_page_json(PAGE3, "Mediums & Acquisitions")
    ids = []
    def add(o): write_visual(PAGE3, o["name"], o); ids.append(o["name"])
    add(title_block("Mediums & Acquisitions"))
    add(kpi_card(40, 96, 1840, 140, [
        ("Artworks", "# Artworks"), ("Artworks", "# On View"),
        ("Artworks", "% On View"), ("Artworks", "% Cataloged")], ORANGE))
    add(slicer(SLX5[0], SL_Y, SL_W5, SL_H, "Artworks", "Department", "Department", sync="ArtworkFilters"))
    add(slicer(SLX5[1], SL_Y, SL_W5, SL_H, "Artworks", "Classification", "Classification"))
    add(slicer(SLX5[2], SL_Y, SL_W5, SL_H, "Artworks", "Decade Created", "Decade Created"))
    add(slicer(SLX5[3], SL_Y, SL_W5, SL_H, "Artworks", "Artist Gender", "Artist Gender"))
    add(slicer(SLX5[4], SL_Y, SL_W5, SL_H, "Artworks", "Primary Nationality", "Primary Nationality"))
    add(cartesian(CX[0], R1, CW, CH, "barChart", "Artworks", "Medium", "Artworks", "# Artworks",
        "Top Mediums", CYAN, sort_dir="Descending", sort_by="measure", topn=12, topn_key="ObjectID", labels=True))
    add(cartesian(CX[1], R1, CW, CH, "barChart", "Artworks", "Artist", "Artworks", "# Artworks",
        "Top Artists by Works", PLUM, sort_dir="Descending", sort_by="measure", topn=12, topn_key="ObjectID", labels=True))
    add(cartesian(CX[0], R2, CW, CH, "lineChart", "Artworks", "Year Acquired", "Artworks", "# Artworks",
        "Acquisitions by Year", TEAL, sort_dir="Ascending", sort_by="category"))
    add(donut(CX[1], R2, CW, CH, "Artworks", "Artist Gender", "Artworks", "# Artworks", "Works by Artist Gender"))
    return ids

def write_pages_json():
    obj = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
           "pageOrder": [PAGE1, PAGE2, PAGE3], "activePageName": PAGE1}
    with open(os.path.join(PAGES, "pages.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

if __name__ == "__main__":
    v1 = make_page1()
    v2 = make_page2()
    v3 = make_page3()
    write_pages_json()
    print("PAGE3 id:", PAGE3)
    print("Page1 visuals:", len(v1))
    print("Page2 visuals:", len(v2))
    print("Page3 visuals:", len(v3))
