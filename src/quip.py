"""Gate-level netlists of Quip benchmark circuits (Altera and OpenCores designs in ispras/hdl-benchmarks), synthesised
with Yosys (yowasp-yosys, default `synth -flatten -top TOP`, no options tuned) and read from Yosys JSON.

Graph: one node per cell (gate or flip-flop) and per primary input; one edge per driven cell input (driver -> sink),
labelled (driver type, sink type) like the ISCAS netlists in netlist.py. Constant drivers are left out.
To rebuild the JSON files: see scripts/synth_quip.sh."""
import json, os, collections
import paths

QUIP = os.path.join(paths.DATA, 'quip_synth')
CIRCUITS = ['barrel16', 'barrel32', 'barrel64', 'mux8_64bit', 'mux8_128bit', 'mux32_16bit', 'mux64_16bit', 'oc_aes_core', 'oc_des_area_opt', 'oc_des_perf_opt']

def load_quip(name):
    d = json.load(open(os.path.join(QUIP, name + '.json'))); mods = d['modules']
    top = [m for m, v in mods.items() if v.get('attributes', {}).get('top')]
    mod = mods[top[0] if top else list(mods)[0]]
    driver = {}; typ = {}
    for pn, p in mod['ports'].items():
        if p['direction'] == 'input':
            for k, bit in enumerate(p['bits']):
                if isinstance(bit, int): driver[bit] = f'in:{pn}[{k}]'; typ[f'in:{pn}[{k}]'] = 'IN'
    cells = sorted(mod['cells'])
    for cn in cells:
        c = mod['cells'][cn]; t = c['type'].strip('$_').rstrip('_')
        typ[cn] = t
        for pn, dirn in c['port_directions'].items():
            if dirn == 'output':
                for bit in c['connections'][pn]:
                    if isinstance(bit, int): driver[bit] = cn
    E = []
    for cn in cells:
        c = mod['cells'][cn]
        for pn in sorted(c['port_directions']):
            if c['port_directions'][pn] != 'input': continue
            for bit in c['connections'][pn]:
                if isinstance(bit, int) and bit in driver: E.append((driver[bit], cn, (typ[driver[bit]], typ[cn])))
    return E

if __name__ == '__main__':
    for n in CIRCUITS:
        E = load_quip(n); nodes = {x for u, v, _ in E for x in (u, v)}
        print(n, 'edges', len(E), 'nodes', len(nodes), 'labels', len({l for *_, l in E}), collections.Counter(l for *_, l in E).most_common(4))
