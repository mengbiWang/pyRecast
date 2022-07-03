# -*- coding:utf-8 -*-
import math
from vispy import scene, io
import numpy as np

from mymath import Vector3
import recast


def overlapBounds(amin, amax, bmin, bmax):
    overlap = True
    overlap = False if (amin.x > bmax.x or amax.x < bmin.x) else True
    overlap = False if (amin.y > bmax.y or amax.y < bmin.y) else True
    overlap = False if (amin.z > bmax.z or amax.z < bmin.z) else True
    return overlap


def addSpan(hf, x, z, smin, smax, area, flagMergeThr):
    idx = x + z * hf.width # 行存储
    spanList = hf.spans[idx] # list
    span = recast.RecastSpan()
    span.smin = smin
    span.smax = smax
    span.area = area
    spanSize = len(spanList)
    if spanSize == 0:
        # (x,z)位置处的第一个span
        spanList.append(span)
        return
    needRemoveSpans = []
    insertIndex = spanSize # 默然插在最后
    for i in range(spanSize):
        curSpan = spanList[i]
        if curSpan.smin > span.smax:
            # 找到了span的插入位置
            insertIndex = i
            break
        elif curSpan.smax < span.smin:
            continue
        else:
            # 两个span有重合的地方，对span进行merge操作，并标记curSpan需要删除
            needRemoveSpans.append(spanList[i])
            if curSpan.smin < span.smin:
                span.smin = curSpan.smin
            if curSpan.smax > span.smax:
                span.smax = curSpan.smax
            # 根据agent的可攀爬高度重设merge后span的area
            # 这里设不设置对最终烘焙结果影响不大
            if math.fabs(span.smax - curSpan.smax) <= flagMergeThr:
                # 如果curSpan.smax > span.smax，且 math.fabs(span.smax - curSpan.smax) > flagMergeThr， curSpan.area == 0 时，merge span的area会被span的area顶替
                # 可能会存在错误标记的问题
                span.area = recast.rcMax(span.area, curSpan.area)
    spanList.insert(insertIndex, span)
    for removeSpan in needRemoveSpans:
        spanList.remove(removeSpan)


def dividePoly(inputVerts, outputVerts1, outputVerts2, splitLine, splitAxis):
    '''
    二维平面的多边形分割：
    用直线splitLine将inputVerts表示的多边形分割为上下或者左右两个多边形，是上下还是左右分割取决于splitAxis，splitAxis代表分割轴，0表示splitLine垂直于x
    轴，2表示用splitLine垂直于z轴
    推及三维平面，splitLine就表示垂直于xz的平面，分割原理类似
    分割线下面或者左边的多边形的顶点会添加到outputVerts1，分割线上面或者右边的顶点会添加到outputVerts2
    '''
    d = []
    for vert in inputVerts:
        if splitAxis == 0:
            d.append(splitLine - vert.x)
        elif splitAxis == 2:
            d.append(splitLine - vert.z)

    inputVertsNum = len(inputVerts)
    for i in range(inputVertsNum):
        j = (i + 1) % inputVertsNum
        ina = (d[i] >= 0)
        inb = (d[j] >= 0)
        if ina != inb:
            # 顶点i和j在分割线的两侧,d[i],d[j]一正一负
            # 先处理i顶点
            if d[i] < 0:
                outputVerts2.append(inputVerts[i])
            elif d[i] > 0:
                outputVerts1.append(inputVerts[i])

            splitRation = d[j] / (d[j] - d[i])  # splitRation是一个正数
            splitPointX = inputVerts[j].x + (inputVerts[i].x - inputVerts[j].x) * splitRation
            splitPointY = inputVerts[j].y + (inputVerts[i].y - inputVerts[j].y) * splitRation
            splitPointZ = inputVerts[j].z + (inputVerts[i].z - inputVerts[j].z) * splitRation
            splitPoint = Vector3(splitPointX, splitPointY, splitPointZ)
            outputVerts1.append(splitPoint)
            outputVerts2.append(splitPoint)
        else:
            if d[i] < 0:
                outputVerts2.append(inputVerts[i])
            elif d[i] == 0:
                outputVerts1.append(inputVerts[i])
                outputVerts2.append(inputVerts[i])
            else:
                outputVerts1.append(inputVerts[i])


def rasterizeTri(v0, v1, v2, area, hf, bmin, bmax, cs, ics, ich, flagMergeThr):
    '''
    v0, v1, v2表示需要光栅化的三角形的三个顶点，area是三角形的area标记
    '''
    print(v0, v1, v2)
    w = hf.width
    h = hf.height
    tmin = Vector3(0, 0, 0)
    tmax = Vector3(0, 0, 0)
    by = bmax.y - bmin.y

    # 计算三角形的包围盒信息
    tmin.copy(v0)
    tmax.copy(v0)
    recast.rcVmin(tmin, v1)
    recast.rcVmin(tmin, v2)
    recast.rcVmax(tmax, v1)
    recast.rcVmax(tmax, v2)

    if not overlapBounds(tmin, tmax, bmin, bmax):
        return
    z0 = int((tmin.z - bmin.z) * ics)
    z1 = int((tmax.z - bmin.z) * ics)
    z0_ = recast.rcClamp(z0, 0, h - 1)
    z1_ = recast.rcClamp(z1, 0, h - 1)

    inputVerts = [v0, v1, v2]

    for z in range(z0_,  z1_ + 1):
        # Clip polygon to row. Store the remaining polygon as well
        cz = bmin.z + z * cs # split line
        outputVerts1 = []
        outputVerts2 = []
        dividePoly(inputVerts, outputVerts1, outputVerts2, cz + cs, 2)
        inputVerts = outputVerts2 # 更新inputVerts，下次循环接着对分割后的上部分或者右部分多边形进行分割
        if len(outputVerts1) < 3:
            continue
        # 对outputVerts1表示的多边形使用平行于z轴的分割线进行分割
        minX = outputVerts1[0].x
        maxX = outputVerts1[0].x
        for vert in outputVerts1:
            if minX > vert.x:
                minX = vert.x
            if maxX < vert.x:
                maxX = vert.x
        x0 = int((minX - bmin.x) * ics)
        x1 = int((maxX - bmin.x) * ics)
        x0 = recast.rcClamp(x0, 0, w - 1)
        x1 = recast.rcClamp(x1, 0, w - 1)
        for x in range(x0, x1 + 1):
            cx = bmin.x + x * cs # split line
            spanVerts = [] # 构成span的顶点
            needContinueSplitPolyVerts = [] #需要继续分割的多边形顶点
            dividePoly(outputVerts1, spanVerts, needContinueSplitPolyVerts, cx + cs, 0)
            outputVerts1 = needContinueSplitPolyVerts
            if len(spanVerts) < 3:
                continue
            # Calculate min and max of the span.
            smin = spanVerts[0].y
            smax = spanVerts[0].y
            for vert in spanVerts:
                if vert.y > smax:
                    smax = vert.y
                if vert.y < smin:
                    smin = vert.y
            smin = smin - bmin.y
            smax = smax - bmin.y
            # Skip the span if it is outside the heightfield bbox
            if smin < 0.0:
                continue
            if smax > by:
                continue

            ismin = recast.rcClamp(int(math.floor(smin * ich)), 0, recast.RC_SPAN_MAX_HEIGHT)
            ismax = recast.rcClamp(int(math.ceil(smax * ich)), ismin + 1, recast.RC_SPAN_MAX_HEIGHT)
            addSpan(hf, x, z, ismin, ismax, area, flagMergeThr)


def rcRasterizeTriangles(verts, tris, areas, solid, flagMergeThr):
    ics = 1.0 / solid.cs
    ich = 1.0 / solid.ch
    area = 1
    rasterizeTrianglesNum = 1
    idx = 0
    for tri in tris:
        idx = idx + 1
        if idx > rasterizeTrianglesNum:
            break
        vert0 = verts[tri[0]]
        vert1 = verts[tri[1]]
        vert2 = verts[tri[2]]
        v0 = Vector3(vert0[0], vert0[1], vert0[2])
        v1 = Vector3(vert1[0], vert1[1], vert1[2])
        v2 = Vector3(vert2[0], vert2[1], vert2[2])
        rasterizeTri(v0, v1, v2, area, solid, solid.bmin, solid.bmax, solid.cs, ics, ich, flagMergeThr)


def duAppendBox(view, minx, miny, minz, maxx, maxy, maxz):
    verts = np.array([(minx, miny, minz),
                        (maxx, miny, minz),
                        (maxx, miny, maxz),
                        (minx, miny, maxz),
                        (minx, maxy, minz),
                        (maxx, maxy, minz),
                        (maxx, maxy, maxz),
                        (minx, maxy, maxz)])
    inds = np.array([
        (7, 6, 5),
        (7, 5, 4),
        (0, 1, 2),
        (0, 2, 3),
        (1, 5, 6),
        (1, 6, 2),
        (3, 7, 4),
        (3, 4, 0),
        (2, 6, 7),
        (2, 7, 3),
        (0, 4, 5),
        (0, 5, 1)])
    mesh = scene.visuals.Mesh(vertices=verts, faces=inds, color=(0.5, 0.5, 1, 1), shading='smooth')
    view.add(mesh)


if __name__ == '__main__':
    canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor="white")
    view = canvas.central_widget.add_view()

    #verts, faces, normals, nothing = io.read_mesh("undulating.obj")
    verts = np.array([(1,0,0),(0,1,0),(0,0,1)])
    faces = np.array([(0,1,2)])
    mesh = scene.visuals.Mesh(vertices=verts, faces=faces, shading='smooth')
    xmin, xmax = mesh.bounds(0)
    ymin, ymax = mesh.bounds(1)
    zmin, zmax = mesh.bounds(2)
    bmin = Vector3(xmin, ymin, zmin)
    bmax = Vector3(xmax, ymax, zmax)
    config = recast.RecastConfig()
    config.cs = 0.1
    config.ch = 0.1
    config.width, config.height = recast.rcCalcGridSize(bmin, bmax, config.cs)
    config.bmin = bmin
    config.bmax = bmax
    heightField = recast.RecastHeightField()
    recast.rcCreateHeightfield(heightField, config.width, config.height, config.bmin, config.bmax, config.cs, config.ch)
    areas = []
    rcRasterizeTriangles(verts, faces, areas, heightField, config.walkableClimb)
    orig = bmin
    print(bmin)
    print(bmax)
    for y in range(config.height):
        for x in range(config.width):
            fx = orig.x + x * config.cs
            fz = orig.z + y * config.cs
            spanList = heightField.spans[x + y * config.width]
            for span in spanList:
                print(fx, orig.y + span.smin * config.ch, fz)
                print(fx + config.cs, orig.y + span.smax * config.ch, fz + config.cs)
                duAppendBox(view, fx, orig.y + span.smin * config.ch, fz, fx + config.cs, orig.y + span.smax * config.ch, fz + config.cs)
    #view.add(mesh)
    view.camera = scene.TurntableCamera()
    view.camera.depth_value = 10
    canvas.app.run()
