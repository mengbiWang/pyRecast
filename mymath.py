# -*- coding:utf-8 -*-
import cmath


class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "x = {}, y = {}, z = {}".format(self.x, self.y, self.z)

    def add(self, other):
        self.x = self.x + other.x
        self.y = self.y + other.y
        self.z = self.z + other.z
    
    def sub(self, other):
        self.x = self.x - other.x
        self.y = self.y - other.y
        self.z = self.z - other.z

    def dist(self, other):
        dx = self.x - other.x
        dy = self.x - other.y
        dz = self.x - other.z
        return cmath.sqrt(dx * dx + dy * dy + dz * dz)
    
    def distSqr(self, other):
        dx = self.x - other.x
        dy = self.x - other.y
        dz = self.x - other.z
        return dx * dx + dy * dy + dz * dz
    
    def length(self):
        return cmath.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        d = 1.0 / self.length()
        self.x *= d
        self.y *= d
        self.z *= d

    def copy(self, other):
        self.x = other.x
        self.y = other.y
        self.z = other.z