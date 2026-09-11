"""
demo_custom_role.py
--------------------
Prova: un'entita' con un role che forge non conosce ("section"), accanto a
un vero contorno (role="outer"). Solo forge, niente unfold in mezzo.

Lancia: .venv/Scripts/python.exe demo_custom_role.py
"""
import forge

entities = [
    # quadrato 100x100 - il vero pezzo, role="outer"
    {"type": "line", "start": (0, 0),     "end": (100, 0),   "role": "outer"},
    {"type": "line", "start": (100, 0),   "end": (100, 100), "role": "outer"},
    {"type": "line", "start": (100, 100), "end": (0, 100),   "role": "outer"},
    {"type": "line", "start": (0, 100),   "end": (0, 0),     "role": "outer"},
    # linea a parte, role custom
    {"type": "line", "start": (150, 0), "end": (150, 100), "role": "section"},
]

doc = forge.load_geometry(entities)
result = forge.heal_and_detect(doc, label="demo")

print("clusters:", result.cluster_count)
print("trash_entities:", len(result.trash_entities))
for t in result.trash_entities:
    print("  role:", getattr(t, "role", None))

doc_out = forge.to_dxf(result)

# forge non ha una palette esterna configurabile: ogni role custom (qui
# "section") esce sempre grigio scuro (COLOR_CONSUMER, rules/palette.py).
# Ma to_dxf() restituisce il documento ezdxf vero e proprio, quindi il
# colore si puo' cambiare qui, dopo, prima di salvare - due righe, nessuna
# modifica a forge.
section_layer = doc_out.layers.get("section")
section_layer.rgb = (0, 100, 0)  # verde scuro (true color RGB)

doc_out.saveas("demo_custom_role.dxf")
print("layers:", [l.dxf.name for l in doc_out.layers])
print("colore layer 'section' (RGB):", section_layer.rgb)
