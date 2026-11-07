import sys, skia, numpy as np
sys.path.insert(0, 'src')
from core import *
from character import Character
S = '/tmp/claude-0/-home-user-cartoons/e3564bd2-6e7b-5487-9175-5649ed9eb08c/scratchpad/'
tests = [('toly', ('cross', 'cross'), dict()), ('toly', ('rest', 'mic'), dict(mouth=0.8, yaw=0.25)),
         ('eminem', ('point_self', 'rest'), dict(mouth=0.5, yaw=-0.25, brow=1)), ('eminem', ('rest', 'beckon'), dict(blink=1, mouth=1)),
         ('eminem', ('point_up', 'open'), dict(mouth=0.3)), ('eminem', ('fist_up', 'chest'), dict(yaw=0.3))]
surf = skia.Surface(1620, 1920)
c = surf.getCanvas(); c.clear(C('#3a0a12'))
for i, (n, poses, kw) in enumerate(tests):
    ch = Character(n)
    x = 270 + (i % 3) * 540; y = 520 + (i // 3) * 960
    c.save(); c.clipRect(skia.Rect(x - 270, y - 520, x + 270, y + 440))
    ch.draw(c, x, y, 0.5, 0.0, poses=poses, **kw)
    c.restore()
surf.makeImageSnapshot().save(S + 'poses.png')
