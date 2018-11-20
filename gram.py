# diagram creator

import math
import numpy as np

# native format is SVG + CSS
# use cairosvg to convert to PDF/PNG

# generators
def gen_css(sel, rules):
    css = f'{sel} {{\n'
    for k, v in rules.items():
        css += f'{k}: {v};'
    css += f'}}'
    return css

def gen_attr(attr):
    props = {k.replace('_', '-'): v for k, v in attr.items() if v is not None}
    return ' '.join([f'{k}="{v}"' for k, v in props.items()])

# data tools
def scale(data, zmin, zmax, dmin=None, dmax=None, pad=0.05):
    if dmin is None:
        dmin = min(data)
    if dmax is None:
        dmax = max(data)
    frac = [(d-dmin)/(dmax-dmin) for d in data]
    data1 = [zmin+(zmax-zmin)*(pad+(1-2*pad)*f) for f in frac]
    return data1

class Canvas:
    def __init__(self, root=None, box=(0, 0, 100, 80), **attr):
        self.box = box
        self.root = root
        self.attr = attr

    def set_root(self, root):
        self.root = root

    def render(self, fmt='svg'):
        core = self.root.render()
        attr0 = {
            'viewBox': ' '.join([f'{x}' for x in self.box])
        }
        attr1 = dict(attr0, **self.attr)
        props = gen_attr(attr1)
        svg = f'<svg {props}>\n{core}\n</svg>'
        if fmt == 'svg':
            return svg
        else:
            raise

    def save(self, filename, fmt='svg'):
        svg = self.render(fmt='svg')
        if fmt == 'svg':
            with open(filename, 'w+') as fout:
                fout.write(svg)
        else:
            raise

# element interface
class Element:
    # store core attributes and extra attributes
    def __init__(self, tag, klass=None, **attr):
        self.tag = tag
        self.attr = attr

        # hack because you can't use class as a keyword
        if klass is not None:
            self.attr['class'] = klass

    # return string wrapper and inner content given
    def render(self, inner=None):
        props = gen_attr(self.attr)
        if inner is None:
            return f'<{self.tag} {props} />'
        else:
            return f'<{self.tag} {props}>\n{inner}\n</{self.tag}>'

# parent/child interface
class Group(Element):
    def __init__(self, children={}, tag='g', **attr):
        super().__init__(tag, **attr)
        self.children = children

    def render(self):
        elems = self.children.values() if type(self.children) is dict else self.children
        inner = '\n'.join([e.render() for e in elems])
        return super().render(inner)

class Text(Element):
    def __init__(self, x, y, text, **attr):
        self.text = text
        attr1 = dict(x=x, y=y, **attr)
        super().__init__('text', **attr1)

    def render(self):
        return super().render(self.text)

class Line(Element):
    def __init__(self, x1, y1, x2, y2, **attr):
        attr1 = dict(x1=x1, y1=y1, x2=x2, y2=y2, **attr)
        super().__init__('line', **attr1)

class Path(Element):
    def __init__(self, points, **attr):
        x0, y0 = points[0]
        data = [f'M {x0},{y0}'] + [f'L {x},{y}' for x, y in points[1:]]
        path = ' '.join(data)
        attr1 = dict(d=path, fill='none', **attr)
        super().__init__('path', **attr1)

class Circle(Element):
    def __init__(self, cx, cy, r, **attr):
        attr1 = dict(cx=cx, cy=cy, r=r, **attr)
        super().__init__('circle', **attr1)

class Ellipse(Element):
    def __init__(self, cx, cy, rx, ry, **attr):
        attr1 = dict(cx=cx, cy=cy, rx=rx, ry=ry, **attr)
        super().__init__('ellipse', **attr1)

class Arrow(Group):
    def __init__(self, x1, y1, x2, y2, theta=45, length=1, **attr):
        # calculate arrow path
        rtheta = math.radians(theta)
        deg90 = math.radians(90)

        xdir = 1 if x2 > x1 else -1
        ydir = 1 if y2 > y1 else -1

        gammah = math.atan((y2-y1)/(x2-x1)) if x1 != x2 else -ydir*deg90 # angle of line
        gammal = deg90 - gammah # complement of angle

        etah = gammah - rtheta # residual angle high
        etal = gammal - rtheta # residual angle low

        dxh, dyh = length*math.cos(etah), length*math.sin(etah)
        dxl, dyl = length*math.sin(etal), length*math.cos(etal)

        pointh = (x2-xdir*dxh, y2-xdir*dyh)
        pointl = (x2-xdir*dxl, y2-xdir*dyl)

        # print(f'gammah = {math.degrees(gammah)}, gammal = {math.degrees(gammal)}')
        # print(f'etah = {math.degrees(etah)}, etal = {math.degrees(etal)}')
        # print(f'dxh = {dxh}, dyh = {dyh}')
        # print(f'dxl = {dxl}, dyl = {dyl}')

        # generate children
        children = {
            'line': Line(x1, y1, x2, y2),
            'head': Path([pointh, (x2, y2), pointl])
        }
        super().__init__(children, klass='arrow', **attr)

class Ticks(Group):
    def __init__(self, pos, dx, dy, **attr):
        children = [Line(x, y, x+dx, y+dy) for x, y in pos]
        attr1 = dict(shape_rendering='crispEdges', **attr)
        super().__init__(children=children, klass='ticks', **attr1)

class Axes(Path):
    def __init__(self, x, y, w, h, **attr):
        points = [(x, y-h), (x, y), (x+w, y)]
        attr1 = dict(shape_rendering='crispEdges', **attr)
        super().__init__(points, klass='axes', **attr1)

class Graph(Path):
    def __init__(self, xdata, ydata, x, y, w, h, xmin=None, xmax=None, ymin=None, ymax=None, pad=0.05, **attr):
        xdata1 = scale(xdata, x, x+w, dmin=xmin, dmax=xmax, pad=pad)
        ydata1 = scale(ydata, y, y-h, dmin=ymin, dmax=ymax, pad=pad)
        points = [d for d in zip(xdata1, ydata1)]
        attr1 = dict(shape_rendering='geometricPrecision', **attr)
        super().__init__(points, klass='graph', **attr1)
