"""Render original geometric interface icons. No downloaded icon font required."""
from pathlib import Path
import bootstrap
from PIL import Image, ImageDraw

DEST = Path(__file__).resolve().parent / 'assets' / 'ui'
DEST.mkdir(exist_ok=True)

def render(name, size, color):
    if name == 'nexus':
        # Keep the app, window and installer on the same editable brand artwork.
        with Image.open(DEST / 'nexus-master.png') as source:
            image = source.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
        image.save(DEST / f'{name}-{size}.png')
        return image
    scale = 4
    image = Image.new('RGBA', (size*scale, size*scale))
    draw = ImageDraw.Draw(image)
    k = size*scale/24
    def line(points, fill=color, width=1.7):
        draw.line([(round(x*k), round(y*k)) for x,y in points], fill=fill, width=max(1,round(width*k)), joint='curve')
    def box(coords, fill=None, radius=2):
        draw.rounded_rectangle(tuple(round(v*k) for v in coords),radius=round(radius*k),fill=fill,outline=color,width=round(1.6*k))
    def circle(coords):
        draw.ellipse(tuple(round(v*k) for v in coords),outline=color,width=round(1.7*k))
    if name in ('draft','shield'):
        line([(12,3),(20,6),(19,14),(16,18),(12,21),(8,18),(5,14),(4,6),(12,3)])
        line([(8,12),(11,15),(16,9)])
    elif name == 'heroes':
        circle((8,3,16,11));line([(5,21),(5,18),(8,14),(16,14),(19,18),(19,21)])
        line([(3,8),(2,11),(4,14)]);line([(21,8),(22,11),(20,14)])
    elif name == 'build':
        line([(12,6),(7,4),(3,4),(3,19),(7,19),(12,21),(17,19),(21,19),(21,4),(17,4),(12,6),(12,21)])
        line([(6,8),(9,9)]);line([(15,9),(18,8)])
    elif name == 'collection':
        box((4,3,20,21));line([(8,8),(16,8)]);line([(8,12),(16,12)]);line([(8,16),(13,16)])
    elif name == 'history':
        line([(3,3),(3,21),(22,21)]);box((6,12,9,18),radius=0);box((12,8,15,18),radius=0);box((18,3,21,18),radius=0)
    elif name == 'star':
        points=[(12,3),(15,9),(21,10),(17,15),(18,21),(12,18),(6,21),(7,15),(3,10),(9,9),(12,3)]
        line(points)
    elif name == 'ban':
        circle((3,3,21,21));line([(6,6),(18,18)])
    elif name == 'check':
        line([(4,12),(9,17),(20,6)])
    elif name == 'play':
        line([(7,4),(20,12),(7,20),(7,4)])
    elif name == 'pause':
        line([(8,4),(8,20)],width=3);line([(16,4),(16,20)],width=3)
    elif name == 'refresh':
        draw.arc((3*k,3*k,21*k,21*k),30,300,fill=color,width=round(1.7*k));line([(21,3),(21,9),(15,9)])
    elif name == 'photo':
        box((3,6,21,21));line([(8,6),(9,3),(15,3),(16,6)]);circle((8,10,16,18))
    elif name == 'search':
        circle((3,3,16,16));line([(15,15),(21,21)])
    elif name == 'external':
        line([(14,3),(21,3),(21,10)]);line([(21,3),(11,13)]);line([(10,5),(4,5),(4,20),(19,20),(19,14)])
    elif name == 'plus':
        line([(12,4),(12,20)]);line([(4,12),(20,12)])
    elif name == 'download':
        line([(12,3),(12,16),(7,11)]);line([(12,16),(17,11)]);line([(4,17),(4,21),(20,21),(20,17)])
    elif name == 'trophy':
        line([(7,3),(17,3),(17,11),(15,15),(9,15),(7,11),(7,3)])
        line([(7,5),(3,5),(3,10),(7,11)]);line([(17,5),(21,5),(21,10),(17,11)])
        line([(12,15),(12,21),(7,21),(17,21)])
    elif name == 'loss':
        circle((3,3,21,21));line([(8,8),(16,16)]);line([(16,8),(8,16)])
    elif name == 'target':
        circle((3,3,21,21));circle((7,7,17,17));circle((11,11,13,13))
    image = image.resize((size,size),Image.Resampling.LANCZOS)
    image.save(DEST / f'{name}-{size}.png')
    return image

if __name__ == '__main__':
    for name in ('draft','heroes','build','collection','history','star','ban','check','play','pause','refresh','photo','search','external','plus','download','trophy','loss','target'):
        color = '#76dded' if name not in ('loss','trophy','star') else {'loss':'#f49ca7','trophy':'#69d9a6','star':'#edc674'}[name]
        for size in (18,24):render(name,size,color)
    for size in (24,48,64):render('nexus',size,'#76dded')
    with Image.open(DEST/'nexus-master.png') as source:
        source.save(DEST/'nexus.ico',sizes=[(s,s) for s in (16,20,24,32,40,48,64,128,256)])
    print('Original UI icons rendered.')
