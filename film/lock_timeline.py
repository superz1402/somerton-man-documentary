#!/usr/bin/env python3
"""Lock the Somerton Man documentary timeline.
Reads lines.json + voices/dur.json + voices/words.json.
Writes: timeline.json, timeline.js (window.TL), cues.json (srt input), chips + wipes + hits.
Scene windows: t0 = cursor; lines placed at lead / gap offsets; t1 = max(last speech end + tail, t0+min).
"""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
lines = json.load(open('lines.json'))
dur  = json.load(open('voices/dur.json'))
by_id = {l['id']: l for l in lines}

# scene table: (id, sec, [line ids], lead, tail, min_dur, cut)  cut: 'wipe'|'hard'|'fade'
SCENES = [
 ('sc01a','S1',['L01'],9.5,0.4,12.0,'fade'),
 ('sc01b','S1',['L02'],1.0,0.4,7.0,'wipe'),
 ('sc01c','S1',['L03'],1.0,0.4,8.0,'hard'),
 ('sc01d','S1',['L04'],1.4,0.6,12.0,'wipe'),
 ('sc01e','S1',['L05'],1.0,1.4,12.0,'wipe'),
 ('sc02a','S2',['L06'],1.2,0.4,11.0,'wipe'),
 ('sc02b','S2',['L07'],1.0,0.4,12.0,'wipe'),
 ('sc02c','S2',['L08'],0.8,0.3,14.0,'hard'),
 ('sc02d','S2',['L09'],0.7,0.3,6.0,'hard'),
 ('sc02e','S2',['L10'],0.8,1.2,11.0,'wipe'),
 ('sc02f','S2',['L11'],0.7,0.3,10.0,'hard'),
 ('sc02g','S2',['L12'],0.8,0.3,16.0,'wipe'),
 ('sc02h','S2',['L13'],1.0,0.5,11.0,'wipe'),
 ('sc02i','S2',['L14'],0.8,0.4,10.0,'wipe'),
 ('sc02j','S2',['L15'],0.9,0.4,15.0,'hard'),
 ('sc02k','S2',['L16'],0.9,0.8,13.0,'wipe'),
 ('sc03a','S3',['L17'],1.2,0.4,8.0,'wipe'),
 ('sc03b','S3',['L18'],0.8,0.3,9.0,'hard'),
 ('sc03c','S3',['L19'],2.6,0.5,9.0,'hard'),   # silence before TAMÁM SHUD snap
 ('sc03d','S3',['L20'],0.8,0.3,9.0,'wipe'),
 ('sc03e','S3',['L21'],0.8,0.4,12.0,'wipe'),
 ('sc03f','S3',['L22'],0.8,0.4,12.0,'hard'),
 ('sc03g','S3',['L23'],0.7,0.4,8.0,'wipe'),
 ('sc03h','S3',['L24'],0.8,0.5,13.0,'wipe'),
 ('sc03i','S3',['L25'],0.8,0.8,7.0,'wipe'),
 ('sc04a','S4',['L26'],1.0,0.4,11.0,'wipe'),
 ('sc04b','S4',['L27'],0.8,0.4,11.0,'hard'),
 ('sc04c','S4',['L28'],0.7,0.3,9.0,'hard'),
 ('sc04d','S4',['L29'],0.8,0.5,15.0,'wipe'),
 ('sc04e','S4',['L30'],0.8,0.4,11.0,'wipe'),
 ('sc04f','S4',['L31'],0.7,0.3,11.0,'hard'),
 ('sc04g','S4',['L32'],0.8,0.4,13.0,'wipe'),
 ('sc04h','S4',['L33'],0.7,0.3,8.0,'hard'),
 ('sc04i','S4',['L34'],0.8,0.4,13.0,'wipe'),
 ('sc04j','S4',['L35'],0.7,0.4,15.0,'wipe'),
 ('sc04k','S4',['L36'],1.6,0.8,9.0,'wipe'),   # near-silence before UNBROKEN
 ('sc05a','S5',['L37'],1.2,0.4,12.0,'wipe'),
 ('sc05b','S5',['L38'],0.7,0.3,9.0,'hard'),
 ('sc05c','S5',['L39'],0.8,0.4,16.0,'wipe'),
 ('sc05d','S5',['L40'],0.7,0.3,10.0,'hard'),
 ('sc05e','S5',['L41'],0.8,0.3,11.0,'wipe'),
 ('sc05f','S5',['L42'],0.7,0.3,9.0,'hard'),
 ('sc05g','S5',['L43'],0.9,0.4,14.0,'wipe'),
 ('sc05h','S5',['L44'],0.7,0.4,8.0,'hard'),
 ('sc05i','S5',['L45'],0.9,0.4,9.0,'wipe'),
 ('sc05j','S5',['L46'],0.8,0.8,8.0,'wipe'),
 ('sc06a','S6',['L47'],1.2,0.4,9.0,'wipe'),
 ('sc06b','S6',['L48'],0.9,0.5,14.0,'hard'),
 ('sc06c','S6',['L49'],0.8,0.4,13.0,'wipe'),
 ('sc06d','S6',['L50'],0.8,0.5,18.0,'wipe'),
 ('sc06e','S6',['L51'],0.7,0.4,9.0,'hard'),
 ('sc06f','S6',['L52'],0.8,0.4,12.0,'wipe'),
 ('sc06g','S6',['L53'],0.9,1.0,10.0,'wipe'),
 ('sc07a','S7',['L54'],1.2,0.4,12.0,'wipe'),
 ('sc07b','S7',['L55'],0.8,0.3,11.0,'hard'),
 ('sc07c','S7',['L56'],0.8,0.4,12.0,'wipe'),
 ('sc07d','S7',['L57'],0.7,0.3,11.0,'hard'),
 ('sc07e','S7',['L58'],0.8,0.4,12.0,'wipe'),
 ('sc07f','S7',['L59'],2.4,0.5,13.0,'hard'),  # silence before the 2022 announcement
 ('sc07g','S7',['L60'],1.0,1.2,11.0,'hard'),  # NAME CARD
 ('sc07h','S7',['L61'],0.8,0.4,15.0,'wipe'),
 ('sc07i','S7',['L62'],0.7,0.4,10.0,'hard'),
 ('sc07j','S7',['L63'],0.8,1.0,13.0,'wipe'),
 ('sc08a','S8',['L64'],1.2,0.5,20.0,'wipe'),
 ('sc08b','S8',['L65'],0.8,0.4,12.0,'wipe'),
 ('sc08c','S8',['L66'],0.8,0.5,8.0,'hard'),
 ('sc08d','S8',['L67'],0.8,0.8,9.0,'wipe'),
 ('sc09a','S9',['L68'],1.2,0.5,10.0,'wipe'),
 ('sc09b','S9',['L69'],1.2,0.6,12.0,'wipe'),
 ('sc09c','S9',['L70'],1.0,6.0,12.0,'wipe'),
]
SECTION_TARGETS = {'S1':0.0,'S2':58.0,'S3':176.0,'S4':296.0,'S5':446.0,'S6':566.0,'S7':676.0,'S8':828.0,'S9':886.0}
SECTION_TITLES = {'S1':('PROLOGUE','SOMERTON BEACH'),'S2':('EXHIBIT 01','THE MAN WITHOUT AN IDENTITY'),
 'S3':('EXHIBIT 02','TAMÁM SHUD'),'S4':('EXHIBIT 03','THE BOOK AND THE CIPHER'),
 'S5':('EXHIBIT 04','THE SUITCASE'),'S6':('EXHIBIT 05','THE THEORIES'),
 'S7':('EXHIBIT 06','THE DNA INVESTIGATION'),'S8':('EXHIBIT 07','WHAT THE EVIDENCE PROVES'),
 'S9':('CLOSE','SOMERTON BEACH')}
GAP = 0.35          # default gap between consecutive lines
GAP_SILENCE = {'L19':2.6,'L59':2.4,'L36':1.6}   # extra pre-line gaps (music silences)

# place scenes and lines
cursor = 0.0
scenes_out = []
line_t = {}   # id -> [t0, t1] speech window
sec_bounds = {}
for (sid, sec, lids, lead, tail, mind, cut) in SCENES:
    if sec not in sec_bounds: sec_bounds[sec] = [cursor, cursor]
    t0 = cursor
    if sid == 'sc02a': t0 = max(t0, SECTION_TARGETS['S2'])   # section anchors
    elif sec in SECTION_TARGETS and sec_bounds[sec][0] == sec_bounds[sec][1]:
        pass
    t = t0 + lead
    starts = []
    for i, lid in enumerate(lids):
        gap = GAP_SILENCE.get(lid, 0) if i == 0 else GAP
        if i > 0: gap = GAP
        if i == 0 and lid in GAP_SILENCE: t += GAP_SILENCE[lid]
        st = t
        en = st + dur[lid]
        line_t[lid] = [st, en]
        t = en
        starts.append([lid, st, en])
    t1 = max(t + tail, t0 + mind)
    scenes_out.append({'id':sid,'sec':sec,'lines':starts,'t0':round(t0,3),'t1':round(t1,3),'cut':cut})
    sec_bounds[sec][1] = t1
    cursor = t1
DUR = round(cursor + 0.001, 3)

# cues for srt + captions: chunked to ≤9 words, timed by word timestamps (display digits, spoken words for timing)
words = json.load(open('voices/words.json'))
cues = []
for l in lines:
    lid = l['id']; st, en = line_t[lid]
    disp = l['display']
    # split display into word tokens keeping «» highlight flags
    toks, kw = [], False
    for part in disp.split(' '):
        if part.startswith('«'): kw = True
        clean = part.replace('«','').replace('»','')
        toks.append({'w': clean, 'kw': kw})
        if part.endswith('»'): kw = False
    # spoken words for timing
    sw = words.get(lid) or [[l['text'].split()[i], 0, 0] for i in range(len(l['text'].split()))]
    nsp = len(sw)
    ndisp = len(toks)
    # chunk display tokens: sentence-based; merge short sentences; split very long ones
    # build sentence groups first
    sents, cur = [], []
    for tk in toks:
        cur.append(tk)
        if tk['w'].endswith(('.', '!', '?')):
            sents.append(cur); cur = []
    if cur:
        if sents: sents[-1].extend(cur)
        else: sents.append(cur)
    # split sentences longer than 170 chars at nearest clause break
    def split_sent(s):
        text_len = sum(len(t['w']) + 1 for t in s)
        if text_len <= 100: return [s]
        best, bi = None, None
        for i, t in enumerate(s):
            if i == 0 or i == len(s) - 1: continue
            if t['w'].endswith(('—', ',')):
                l = sum(len(x['w']) + 1 for x in s[:i + 1])
                d = abs(l - text_len / 2)
                if best is None or d < best: best, bi = d, i
        if bi is None: bi = len(s) // 2
        return [s[:bi]] + split_sent(s[bi:])
    sents2 = []
    for s in sents: sents2.extend(split_sent(s))
    # merge until chunk has >= 45 chars (except the very last leftover joins previous)
    chunks, curc, curlen = [], [], 0
    for s in sents2:
        curc.append(s); curlen += sum(len(t['w']) + 1 for t in s)
        if curlen >= 45:
            chunks.append([t for sen in curc for t in sen]); curc, curlen = [], 0
    if curc:
        leftover = [t for sen in curc for t in sen]
        ll = sum(len(t['w']) + 1 for t in leftover)
        if chunks and sum(len(t['w']) + 1 for t in chunks[-1]) + ll <= 100:
            chunks[-1].extend(leftover)
        else: chunks.append(leftover)
    # map chunk boundaries to spoken times by character-ratio (digits/abbrev-safe)
    m = len(chunks)
    dchars = [len(t['w']) + 1 for tk in chunks for t in tk]
    tot_d = sum(dchars)
    scum, acc = [], 0
    for wd in sw:
        acc += len(wd[0]) + 1
        scum.append(acc / max(1, len(' '.join(w[0] for w in sw)) + m))
    def ratio_to_time(r):
        for idx, cr in enumerate(scum):
            if cr >= r: return st + sw[idx][1]
        return st + sw[-1][2]
    for k, ch in enumerate(chunks):
        r0 = sum(dchars[:sum(len(c) for c in chunks[:k])]) / tot_d if k else 0.0
        k_end = sum(len(c) for c in chunks[:k + 1])
        r1 = sum(dchars[:k_end]) / tot_d
        t0 = ratio_to_time(r0)
        t1 = ratio_to_time(r1)
        text = ' '.join(t['w'] for t in ch)
        parts = [[t['w'] + (' ' if j < len(ch) - 1 else ''), bool(t['kw'])] for j, t in enumerate(ch)]
        cues.append({'id': f'{lid}c{k}','line': lid,'sec': l['sec'],'t0': round(t0 - 0.05,3),'t1': round(t1 + 0.8,3),
                     'text': text, 'parts': parts})
# enforce reading-time: t1 = max(speech_end+0.8, t0 + chars/15 + 1.5); resolve overlaps by
# pushing later cues up to 0.45s each (caption may lag speech slightly)
for c in cues:
    need = len(c['text']) / 15.0 + 1.5
    c['t1'] = max(c['t1'], c['t0'] + need, c['t0'] + 1.8)
for _ in range(4):
    for i in range(len(cues) - 1):
        c, nx = cues[i], cues[i + 1]
        want = c['t0'] + max(len(c['text']) / 15.0 + 1.5, 1.8)
        cap = nx['t0'] - 0.02
        if cap >= want:
            c['t1'] = cap
        else:
            deficit = want - cap
            room = max(0.0, 0.8 - nx.get('_lag', 0))
            shift = min(deficit, room)
            if shift > 0:
                nx['t0'] += shift; nx['t1'] += shift; nx['_lag'] = nx.get('_lag', 0) + shift
            c['t1'] = nx['t0'] - 0.02

chips = []
for sec,(exh,title) in SECTION_TITLES.items():
    t0,t1 = sec_bounds[sec]
    chips.append([round(t0,2), round(t1,2), exh, title])
# silence windows (music empties): pre-cue gaps for the big reveals + near-silence before UNBROKEN
SILENCE_LINES = ['L19','L59','L36','L60']
silences = []
for lid in SILENCE_LINES:
    st = line_t[lid][0]
    silences.append([round(st - 2.4, 2), round(st - 0.15, 2)])
wipes = [{'t':round(s['t0'],3),'cut':s['cut']} for s in scenes_out if s['cut'] in ('wipe','fade')]

tl = {'DUR':DUR,'fps':24,'W':1920,'H':1080,
      'sections':{s:[round(v[0],2),round(v[1],2)] for s,v in sec_bounds.items()},
      'scenes':scenes_out,'lines':{k:round(v[0],3) for k,v in line_t.items()},
      'chips':chips,'wipes':wipes,'cues':cues,'silences':silences}
json.dump(tl, open('timeline.json','w'), ensure_ascii=False, indent=1)
# timeline.js for the page
tljs = {k:tl[k] for k in ('DUR','fps','W','H','sections','scenes','lines','chips','wipes','cues','silences')}
open('timeline.js','w').write('window.TL = ' + json.dumps(tljs, ensure_ascii=False, separators=(',',':')) + ';\n')
# cues.json for srt.py
json.dump([{'t0':c['t0'],'t1':c['t1'],'text':c['text']} for c in cues], open('cues.json','w'), ensure_ascii=False, indent=0)

print(f'DUR {DUR:.2f}s = {int(DUR//60)}:{DUR%60:04.1f}')
for sec,(t0,t1) in sec_bounds.items():
    print(f'  {sec} {int(t0//60)}:{t0%60:04.1f} → {int(t1//60)}:{t1%60:04.1f}  (target {SECTION_TITLES[sec][0]})')
