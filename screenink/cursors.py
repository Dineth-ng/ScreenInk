"""DPI-aware tool silhouettes; (8, 8) is always the drawing hotspot."""
from functools import lru_cache
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap
from .annotations import Tool


def drawing_cursor(tool, color, width, device_pixel_ratio=1.0, pen_style="Solid"):
    name = tool.value if isinstance(tool, Tool) else str(tool)
    return _cursor(name, QColor(color).rgba(), width, max(1., device_pixel_ratio), pen_style)


@lru_cache(maxsize=128)
def _cursor(name, rgba, width, ratio, style):
    image=QPixmap(round(48*ratio),round(48*ratio));image.fill(Qt.GlobalColor.transparent)
    p=QPainter(image);p.scale(ratio,ratio);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color=QColor.fromRgba(rgba)
    def path(points):
        shape=QPainterPath(QPointF(*points[0]))
        for point in points[1:]:shape.lineTo(*point)
        shape.closeSubpath()
        return shape
    def ink(shape, fill=None):
        p.setBrush(fill if fill is not None else Qt.BrushStyle.NoBrush)
        for shade,size in ((QColor('white'),3.5),(QColor('#17252d'),1.3)):
            p.setPen(QPen(shade,size,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin));p.drawPath(shape)
    def line(points):
        shape=QPainterPath(QPointF(*points[0]))
        for point in points[1:]:shape.lineTo(*point)
        ink(shape)
    if name=='Pen' and style=='Chalk':
        shape=path([(8,8),(12,20),(34,42),(43,35),(20,12)])
        ink(shape,color);line([(19,18),(36,35)])
    elif name=='Pen' and style=='Brush':
        handle=path([(18,22),(25,18),(43,37),(38,43)])
        ink(handle,QColor('#ba8756'))
        bristles=QPainterPath(QPointF(8,8));bristles.cubicTo(9,20,10,29,19,27);bristles.quadTo(30,24,22,16);bristles.quadTo(14,14,8,8)
        ink(bristles,color);line([(17,24),(23,19)])
    elif name=='Highlighter' or (name=='Pen' and style=='Marker'):
        ink(path([(8,8),(8,16),(14,22),(23,14),(16,8)]),color)
        ink(path([(14,22),(23,14),(43,34),(34,43)]),color)
        line([(19,25),(26,18)])
    elif name=='Pen':
        ink(path([(8,8),(12,23),(33,44),(44,33),(23,12)]),color)
        ink(path([(8,8),(12,23),(23,12)]),QColor('#f2dfb8'))
        line([(8,8),(12,12)])
        if style in ('Dashed','Dotted'):
            p.setPen(QPen(QColor('white'),2,Qt.PenStyle.DashLine if style=='Dashed' else Qt.PenStyle.DotLine,Qt.PenCapStyle.RoundCap))
            p.drawLine(23,24,36,37)
    elif name=='Eraser':
        ink(path([(8,8),(20,5),(41,26),(29,39),(8,18)]),QColor('#f3b0b8'))
        ink(path([(8,8),(20,5),(28,13),(16,25),(8,18)]),QColor('#eeeeee'))
    elif name=='Arrow':
        ink(path([(8,8),(27,12),(22,17),(40,35),(35,40),(17,22),(12,27)]),color)
    elif name=='Rectangle':
        shape=QPainterPath();shape.addRect(QRectF(8,8,29,23));ink(shape)
        p.setPen(QPen(color,2));p.drawRect(QRectF(9,9,27,21))
    elif name=='Text':
        line([(3,2),(13,2)]);line([(8,2),(8,26)]);line([(3,26),(13,26)])
    elif name=='Step':
        shape=QPainterPath();shape.addEllipse(QPointF(8,8),6,6);ink(shape,color)
        shape=QPainterPath();shape.addEllipse(QPointF(29,29),12,12);ink(shape,color)
        line([(26,24),(29,21),(29,36)]);line([(25,36),(33,36)])
    elif name in ('Laser','Spotlight','Magnifier'):
        shape=QPainterPath();shape.addEllipse(QPointF(8,8),6,6);ink(shape,color if name=='Laser' else None)
        if name=='Magnifier':line([(13,13),(31,31)])
        elif name=='Spotlight':
            shape=QPainterPath();shape.addEllipse(QPointF(8,8),2,2);ink(shape)
        else:
            ink(path([(21,18),(40,33),(34,41),(18,23)]),QColor('#344653'))
            line([(12,12),(17,17)])
    # A tiny contrasting tip locates the precise interaction point for all tools.
    p.setPen(QPen(QColor('#17252d'),3));p.drawPoint(QPointF(8,8))
    p.setPen(QPen(QColor('white'),1));p.drawPoint(QPointF(8,8))
    p.end();image.setDevicePixelRatio(ratio)
    return QCursor(image,8,8)
