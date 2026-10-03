import json, math, heapq
from shapely.geometry import shape, box, LineString, MultiLineString, Polygon, Point
from shapely.ops import unary_union, polygonize, linemerge

W, H = 1600, 900
LON0, LON1 = 19.912, 19.992
LAT0 = 50.0555
KX = math.cos(math.radians(LAT0)) * 111320
KY = 110540
SC = W / ((LON1 - LON0) * KX)            # px per metre
HM = H / SC                               # height in metres
LATC = 50.0555
LAT_TOP = LATC + (HM / 2) / KY
LAT_BOT = LATC - (HM / 2) / KY

def P(lon, lat):
    return ((lon - LON0) * KX * SC, (LAT_TOP - lat) * KY * SC)

BB = box(LON0 - 0.01, LAT_BOT - 0.008, LON1 + 0.01, LAT_TOP + 0.008)

def nm(f):
    v = f['properties']['full_name']
    return v['pl'] if isinstance(v, dict) else v

def path_d(coords):
    pts = [P(x, y) for x, y in coords]
    out, last = [], None
    for i, (x, y) in enumerate(pts):
        t = (round(x, 1), round(y, 1))
        if t == last:
            continue
        out.append(('M' if not out else 'L') + f"{t[0]:g} {t[1]:g}")
        last = t
    return ''.join(out) if len(out) > 1 else ''

def geom_d(g):
    if g.is_empty:
        return ''
    if g.geom_type == 'LineString':
        return path_d(g.coords)
    if g.geom_type in ('MultiLineString', 'GeometryCollection'):
        return ''.join(geom_d(x) for x in g.geoms)
    if g.geom_type == 'Polygon':
        return path_d(g.exterior.coords) + 'Z'
    if g.geom_type == 'MultiPolygon':
        return ''.join(geom_d(x) for x in g.geoms)
    return ''

streets = json.load(open('krakow_streets.geojson'))['features']
dz = json.load(open('dz.geojson'))['features']

MAJOR = ['Mickiewicza', 'Słowackiego', 'Krasińskiego', 'Dietla', 'Grzegórzecka', 'Kotlarska', 'aleja Pokoju',
         'Nowohucka', 'Mogilska', 'Lubicz', 'Westerplatte', 'Starowiślna', 'ulica Krakowska', 'Kalwaryjska', 'Wielicka',
         'Konopnickiej', 'Zwierzyniecka', 'Karmelicka', 'Basztowa', 'Powstania Warszawskiego', 'Kamieńskiego',
         'Limanowskiego', 'Klimeckiego', 'Daszyńskiego', 'Rondo', 'Kapelanka', 'Prądnicka', 'Pawia', 'Monte Cassino',
         'Grunwaldzka', 'Rakowicka', 'Kopernika', 'Królewska', 'Piastowska', 'Kościuszki', 'Podgórska', 'Wita Stwosza',
         'Most ', 'Na Zjeździe', 'Josepha Conrada', 'Sarego', 'Stradomska', 'Bulwarowa', 'Śliczna', 'Kordylewskiego']

minor_d, major_d = [], []
lines_all = []
for f in streets:
    g = shape(f['geometry'])
    if not g.intersects(BB):
        continue
    gi = g.intersection(BB)
    lines_all.append(g)
    n = nm(f)
    (major_d if any(k in n for k in MAJOR) else minor_d).append(geom_d(gi))

# river from district boundaries
NORTH = ['Zwierzyniec', 'Stare Miasto', 'Grzegórzki', 'Czyżyny', 'Nowa Huta', 'Bronowice', 'Krowodrza']
SOUTH = ['Dębniki', 'XIII Podgórze', 'Bieżanów', 'Swoszowice', 'Łagiewniki']
gN = unary_union([shape(f['geometry']).buffer(0) for f in dz if any(k in f['properties']['name'] for k in NORTH)])
gS = unary_union([shape(f['geometry']).buffer(0) for f in dz if any(k in f['properties']['name'] for k in SOUTH)])
river = gN.boundary.intersection(gS.buffer(0.0004)).intersection(box(19.85, 50.0, 20.10, 50.09))
river = linemerge(river) if river.geom_type != 'LineString' else river
river_d = geom_d(river)

# district boundaries (inside view)
VIEW = box(LON0, LAT_BOT, LON1, LAT_TOP)
dist_d = ''.join(geom_d(shape(f['geometry']).buffer(0).boundary.intersection(BB)) for f in dz)
labels = []
for f in dz:
    g = shape(f['geometry']).buffer(0)
    gi = g.intersection(VIEW.buffer(-0.004))
    if gi.area < 2e-6:
        continue
    pt = gi.representative_point()
    x, y = P(pt.x, pt.y)
    nmx = f['properties']['name'].split(' ', 2)[-1]
    labels.append({'name': nmx, 'x': round(x / W * 100, 2), 'y': round(y / H * 100, 2)})

# approximate parks (hand-traced from known landmarks)
def poly(latlon):
    return Polygon([(lo, la) for la, lo in latlon])
planty = poly([(50.0656, 19.9395), (50.0658, 19.9420), (50.0641, 19.9446), (50.0612, 19.9453), (50.0588, 19.9425),
               (50.0567, 19.9388), (50.0566, 19.9347), (50.0590, 19.9318), (50.0621, 19.9314), (50.0646, 19.9343)])
blonia = poly([(50.0629, 19.9100), (50.0632, 19.9208), (50.0592, 19.9240), (50.0566, 19.9152), (50.0590, 19.9093)])
wawel = poly([(50.0553, 19.9338), (50.0556, 19.9367), (50.0540, 19.9372), (50.0532, 19.9355), (50.0540, 19.9336)])
jordan = poly([(50.0637, 19.9139), (50.0647, 19.9178), (50.0628, 19.9196), (50.0619, 19.9160)])
parks_d = geom_d(blonia) + geom_d(wawel) + geom_d(jordan)
planty_d = geom_d(planty)

# Rynek plaza
rynek = [shape(f['geometry']) for f in streets if nm(f) == 'Rynek Główny']
rynek_d = ''
if rynek:
    polys = list(polygonize(unary_union(rynek)))
    if polys:
        rynek_d = geom_d(max(polys, key=lambda p: p.area))

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
       f'<rect width="{W}" height="{H}" fill="#F1EEE8"/>',
       f'<path d="{parks_d}" fill="#D3E5C6"/>',
       f'<path d="{planty_d}" fill="none" stroke="#C7DFB6" stroke-width="16" stroke-linejoin="round"/>',
       f'<path d="{river_d}" fill="none" stroke="#9CC9E2" stroke-width="{max(18, 125 * SC):.1f}" stroke-linecap="round" stroke-linejoin="round"/>',
       f'<path d="{dist_d}" fill="none" stroke="#B5ADA0" stroke-width="1.5" stroke-dasharray="6 5"/>',
       f'<path d="{"".join(minor_d)}" fill="none" stroke="#DDD7CC" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
       f'<path d="{"".join(major_d)}" fill="none" stroke="#CCC3B4" stroke-width="8.5" stroke-linecap="round" stroke-linejoin="round"/>',
       f'<path d="{"".join(minor_d)}" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
       f'<path d="{"".join(major_d)}" fill="none" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
       (f'<path d="{rynek_d}" fill="#FBF8F2" stroke="#CCC3B4" stroke-width="1.5"/>' if rynek_d else ''),
       '</svg>']
open('krakow-basemap.svg', 'w').write('\n'.join(svg))

# ---------- routing on the street graph ----------
adj = {}
def key(c):
    return (round(c[0], 6), round(c[1], 6))
def dist(a, b):
    return math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)
for g in lines_all:
    parts = g.geoms if g.geom_type == 'MultiLineString' else [g]
    for ln in parts:
        cs = list(ln.coords)
        for a, b in zip(cs, cs[1:]):
            ka, kb = key(a), key(b)
            d = dist(ka, kb)
            adj.setdefault(ka, []).append((kb, d))
            adj.setdefault(kb, []).append((ka, d))
nodes = list(adj.keys())
# keep largest connected component
comp, seen = {}, set()
best = None
for n0 in nodes:
    if n0 in seen:
        continue
    st, cc = [n0], []
    seen.add(n0)
    while st:
        u = st.pop(); cc.append(u)
        for v, _ in adj[u]:
            if v not in seen:
                seen.add(v); st.append(v)
    if best is None or len(cc) > len(best):
        best = cc
MAIN = set(best)

def snap(lon, lat):
    return min(MAIN, key=lambda n: dist(n, (lon, lat)))

def route(a, b):
    pq, dd, prev = [(0, a)], {a: 0}, {}
    while pq:
        d, u = heapq.heappop(pq)
        if u == b:
            break
        if d > dd[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dd.get(v, 1e18):
                dd[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
    path, u = [b], b
    while u != a:
        u = prev[u]; path.append(u)
    return path[::-1], dd[b]

PTS = {
    'base': (19.97517, 50.04558),
    'c1': (19.9373, 50.0617), 'c2': (19.9322, 50.0603), 'c3': (19.9445, 50.0515), 'c4': (19.9585, 50.0600),
    'c5': (19.9405, 50.0556),
    'k10': (19.9482, 50.0497), 'k21': (19.9408, 50.0508), 'sm07': (19.9398, 50.0648), 'r03': (19.9392, 50.0628),
    'a01': (19.9622, 50.0630), 'a02': (19.9607, 50.0573),
}
pos = {k: {'x': round(P(*v)[0] / W * 100, 2), 'y': round(P(*v)[1] / H * 100, 2)} for k, v in PTS.items()}

def seq_path(seq, ret=True):
    pts, total = [], 0
    for a, b in zip(seq, seq[1:]):
        p, d = route(snap(*PTS[a]), snap(*PTS[b]))
        total += d
        pts += p if not pts else p[1:]
    ret_pts = []
    if ret:
        p, d = route(snap(*PTS[seq[-1]]), snap(*PTS[seq[0]]))
        ret_pts = p
        total += d
    ls = LineString([P(*c) for c in pts]).simplify(0.8)
    rs = LineString([P(*c) for c in ret_pts]).simplify(0.8) if ret_pts else None
    f = lambda l: ' '.join(f"{x:.1f},{y:.1f}" for x, y in l.coords)
    return f(ls), (f(rs) if rs else ''), total, ls.length

street = seq_path(['base', 'c4', 'c1', 'c2', 'c5', 'k21', 'c3', 'k10'])
alt = seq_path(['base', 'a02', 'a01'])
zones = []
for (lon, lat, r) in [(19.9373, 50.0617, 330), (19.9450, 50.0515, 230)]:
    x, y = P(lon, lat)
    zones.append({'x': round(x / W * 100, 2), 'y': round(y / H * 100, 2), 'w': round(2 * r * SC / W * 100, 2), 'h': round(2 * r * SC / H * 100, 2)})
river_mid = None
out = {'pos': pos, 'street': street[0], 'streetRet': street[1], 'streetKm': round(street[2] / 1000, 1),
       'alt': alt[0], 'altRet': alt[1], 'altKm': round(alt[2] / 1000, 1), 'zones': zones, 'labels': labels,
       'scale_m_per_px': round(1 / SC, 2), 'lat': [LAT_BOT, LAT_TOP]}
json.dump(out, open('mapdata.json', 'w'), ensure_ascii=False, indent=1)
print('km', out['streetKm'], out['altKm'], 'labels', [l['name'] for l in labels], 'm/px', out['scale_m_per_px'])
print('river', river.geom_type, round(river.length, 4))
import os; print('svg KB', os.path.getsize('krakow-basemap.svg') // 1024, 'rynek', bool(rynek_d))
