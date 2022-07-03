# -*- coding:utf-8 -*-
import mymath


def rcMin(x, y):
    return x if x < y else y


def rcMax(x, y):
    return x if x > y else y


def rcVmin(mn, v):
    mn.x = rcMin(mn.x, v.x)
    mn.y = rcMin(mn.y, v.y)
    mn.z = rcMin(mn.z, v.z)


def rcVmax(mx, v):
    mx.x = rcMax(mx.x, v.x)
    mx.y = rcMax(mx.y, v.y)
    mx.z = rcMax(mx.z, v.z)


def rcClamp(v, min, max):
    if v < min:
        return min
    elif v > max:
        return max
    else:
        return v


def rcCalcGridSize(bmin, bmax, cs):
    w = int((bmax.x - bmin.x) / cs + 0.5)
    h = int((bmax.x - bmin.x) / cs + 0.5)
    return w, h


class RecastConfig(object):
    def __init__(self):
        # 体素化使用的格子大小
        self.width = 0
        self.height = 0
        
        self.tileSize = 0
        self.borderSize = 0

        self.cs = 0.2
        self.ch = 0.2
        
        self.bmin = mymath.Vector3(0, 0, 0)
        self.bmax = mymath.Vector3(0, 0, 0)

        self.walkableSlopeAngle = 15
        # agent height
        self.walkableHeight = 2
        # agent walk climb
        self.walkableClimb = 0.75
        # agent radius
        self.walkableRadius = 0.5

        self.maxEdgeLen = 0
        self.maxSimplificationError = 0

        self.minRegionArea = 0
        self.mergeRegionArea = 0

        self.maxVertsPerPoly = 6

        self.detailSampleDist = 0
        self.detailSampleMaxError = 0


class RecastSpan(object):
    def __init__(self):
        self.smin = 0
        self.smax = 0
        self.area = 0


class RecastSpanPool(object):
    def __init__(self):
        self.items = [] # rcSpan list
        self.next = -1


class RecastHeightField(object):
    def __init__(self): 
        self.width = 0	 # The width of the heightfield. (Along the x-axis in cell units.) int
        self.height = 0	 # The height of the heightfield. (Along the z-axis in cell units.) int
        self.bmin = mymath.Vector3(0, 0, 0)
        self.bmax = mymath.Vector3(0, 0, 0)
        self.cs = 0
        self.ch = 0					
        self.spans = []


def rcCreateHeightfield(hf, width, height, bmin, bmax, cs, ch):
    hf.width = width
    hf.height = height
    hf.bmin = bmin
    hf.bmax = bmax
    hf.cs = cs
    hf.ch = ch
    for i in range(hf.width):
        for j in range(height):
            hf.spans.append([])


RC_SPAN_HEIGHT_BITS = 13
# Defines the maximum value for rcSpan::smin and rcSpan::smax.
RC_SPAN_MAX_HEIGHT = (1 << RC_SPAN_HEIGHT_BITS) - 1 # 高度场的最大高度
# The number of spans allocated per span spool.
RC_SPANS_PER_POOL = 2048


if __name__ == "__main__":
    config = RecastConfig()
    print(config.bmin.x)
    a = []
    b = mymath.Vector3(1, 0, 0)
    a.append(b)
    a.insert(0, mymath.Vector3(1, 1, 1))
    a.remove(mymath.Vector3(1, 1, 1))
    for i in range(len(a)):
        print(a[i])