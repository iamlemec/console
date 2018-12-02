# high-level, pandas-native plotting

import numpy as np
import pandas as pd
import gram

def merge_dicts(dins):
    dout = {}
    for d in dins:
        for x in d:
            dout[x] = d[x]
    return dout

def graph_series(x, y, w, h, s, **kwargs):
    if s.name is not None:
        kwargs['id'] = s.name
    return gram.Graph(s.index.values, s.values, x, y, w, h, **kwargs)

def apply_margin(box, margin):
    x0, y0, w0, h0 = box
    x = x0 + margin*w0
    y = y0 + margin*h0
    w = (1-2*margin)*w0
    h = (1-2*margin)*h0
    return x, y, w, h

def plot(data, margin=0.1, padding=0.05, ticks=False, canvas=True, render=True, box=(0, 0, 100, 80), id=None):
    # ensure a dataframe
    data = pd.DataFrame(data)

    # determine display bounds
    x0, y0, w0, h0 = apply_margin(box, margin)
    x, y, w, h = x0, y0+h0, w0, h0 # reorient y-axis

    # determine data bounds
    dxmin = data.index.min()
    dxmax = data.index.max()
    dymin = data.min().min()
    dymax = data.max().max()
    dbounds = {'xmin': dxmin, 'xmax': dxmax, 'ymin': dymin, 'ymax': dymax, 'pad': padding}

    # construct objects
    children = {c: graph_series(x, y, w, h, data[c], **dbounds) for c in data}
    children['axes'] = gram.Axes(x, y, w, h)
    if ticks is not None:
        tick_size = 0.005*(w+h)
        xticks = np.linspace(x, x+w, ticks+2)[1:-1]
        yticks = np.linspace(y, y-h, ticks+2)[1:-1]
        children['xticks'] = gram.Ticks([(tx, y) for tx in xticks], 0, -tick_size)
        children['yticks'] = gram.Ticks([(x, ty) for ty in yticks], tick_size, 0)
    
    # construct doc
    doc = gram.Group(children, klass='plot', id=id)
    doc.attr['stroke'] = 'black'
    doc.attr['stroke-width'] = 0.2

    # wrap if needed
    if canvas:
        doc = gram.Canvas(doc, box=box)

    # return render
    if render:
        return doc.render()
    else:
        return doc

class Sign(gram.Group):
    def __init__(self, x, y, rx, ry, text, margin=0.2, base=0.35, shape=gram.Ellipse, **attr):
        x0 = x - (1-margin)*rx
        y0 = y + base*ry
        w0 = 2*(1-margin)*rx
        children = {
            'box': shape(x, y, rx, ry),
            'text': gram.Text(x0, y0, text)
        }
        super().__init__(children=children, klass='sign', **attr)

def network(labels, positions=None, labeler=Sign):
    pass
