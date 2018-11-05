# diagram creator

import math
import numpy as np

# native format is SVG + CSS
# use cairosvg to convert to PDF/PNG

def gen_css(sel, rules):
    css = f'{sel} {{\n'
    for k, v in rules.items():
        css += f'{k}: {v};'
    css += f'}}'
    return css

def gen_attr(attr):
    props = {k.replace('_', '-'): v for k, v in attr.items()}
    return ' '.join([f'{k}="{v}"' for k, v in props.items()])

class Canvas:
    def __init__(self, root=None, box=(0, 0, 100, 100), **attr):
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

# shell element class
class Element:
    # store core attributes and extra attributes
    def __init__(self, tag, **attr):
        self.tag = tag
        self.attr = attr

    # return dictionary of properties for the top level tag
    def props(self):
        return {}

    # return string wrapper and inner content given
    def render(self, inner=None):
        attr0 = self.props()
        attr1 = dict(attr0, **self.attr)
        props = gen_attr(attr1)
        if inner is None:
            return f'<{self.tag} {props} />'
        else:
            return f'<{self.tag} {props}>\n{inner}\n</{self.tag}>'

class Group(Element):
    def __init__(self, tag='g', children=[], **attr):
        super().__init__(tag, **attr)
        self.children = children

    def render(self):
        inner = '\n'.join([c.render() for c in self.children])
        return super().render(inner)

class Text(Element):
    def __init__(self, x, y, text, **attr):
        super().__init__('text', **attr)
        self.x = x
        self.y = y
        self.text = text

    def props(self):
        return {
            'x': self.x,
            'y': self.y
        }

    def render(self):
        return super().render(self.text)

class Line(Element):
    def __init__(self, x1, y1, x2, y2, **attr):
        super().__init__('line', **attr)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def props(self):
        return {
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2,
            'stroke': 'black',
            'stroke-width': 0.3
        }

class Path(Element):
    def __init__(self, points, **attr):
        super().__init__('path', **attr)
        self.points = points

    def props(self):
        x0, y0 = self.points[0]
        data = [f'M {x0},{y0}'] + [f'L {x},{y}' for x, y in self.points[1:]]
        return {
            'd': ' '.join(data),
            'stroke': 'black',
            'stroke-width': 0.3,
            'fill': 'none'
        }

class Arrow(Group):
    def __init__(self, x1, y1, x2, y2, theta=45, length=1, **attr):
        super().__init__(**attr)

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
        line = Line(x1, y1, x2, y2)
        arrow = Path([pointh, (x2, y2), pointl])

        self.children = [line, arrow]

class Axis(Group):
    def __init__(self, x, y, orient, length, ticks, labels=None, tick_size=1, **attr):
        super().__init__(**attr)

        if orient == 'h' or orient == 'horizontal':
            orient = 0
        elif orient == 'v' or orient == 'vertical':
            orient = 90
        orient = math.radians(orient)

        if type(ticks) is int:
            ticks = np.linspace(0, length, ticks)

        if labels is None:
            labels = np.arange(len(ticks))
        labels = [str(s) for s in labels]

        dx = length*math.cos(orient)
        dy = length*math.sin(orient)

        tx = tick_size*math.sin(orient)
        ty = tick_size*math.cos(orient)

        points = [(dx*t, dy*t) for t in ticks]

        arrow = Arrow(x, y, x+dx, y+dy)
        lines = [Line(zx-tx, zy-ty, zx+tx, zy+ty) for zx, zy in points]

        self.children = [arrow] + lines

class Plot(Group):
    pass