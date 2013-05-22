#!/usr/bin/env python2
import random
import pygame
import time
import math
from pygame.locals import *
from pygame import mouse
from collections import defaultdict
from collections import deque
pygame.init()

LEFT=1
RIGHT=3

UP=0
DOWN=2

SCREENWIDTH=1024
SCREENHEIGHT=768

PI=3.14159

randrange=random.randrange
screen = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('CaveMaster')
key=pygame.key.get_pressed()

gameObjects=[]

random.seed()
def randcolor():
    return (randrange(256),randrange(256),randrange(256))

def unitify(x):
    if x>0: return 1
    elif x==0: return 0
    else: return -1

class Tile:
    color=(0,0,0)
    surf=pygame.Surface((10,10))
    passable=False
    def __init__(self):
        self.surf=pygame.Surface((10,10))
        self.setType("Wall")
    def randomize(self):
        self.color=randcolor()
        self.surf.fill(self.color)
    def setColor(self, color):
        self.color=color
        self.surf.fill(color)
    def setPassable(self, passable):
        self.passable=passable
    def setType(self, type):
        if type=="Ground":
            light=randrange(256)
            self.setColor((.3*light,.2*light,0*light))
            self.setPassable(True)
        elif type=="Wall":
            light=randrange(130,210)
            self.setColor((light,light,light))
            self.setPassable(False)
    def isWalkable(self):
        return self.passable
            
class KeyMove:
    offx=0
    offy=0
    def getOffset(self):
        return (self.offx, self.offy)
    def update(self):
        self.offx=0
        self.offy=0
        key=pygame.key.get_pressed()
        if key[K_UP]:self.offy-=1
        if key[K_DOWN]:self.offy+=1
        if key[K_LEFT]:self.offx-=1
        if key[K_RIGHT]:self.offx+=1
keymove=KeyMove()

class FollowMove:
    pos=(0,0)
    offx=0
    offy=0
    owner=0
    target=0
    def __init__(self, owner, target):
        self.target=target
        self.owner=owner
        self.pos=owner.getPos()
    def update(self):
        self.offx=self.offy=0
        self.pos=self.owner.getPos()
        targetpos=self.target.getPos()
        self.offx=targetpos[0]-self.pos[0]
        self.offy=targetpos[1]-self.pos[1]
        self.offx=unitify(self.offx)
        self.offy=unitify(self.offy)
    def getOffset(self):
        return (self.offx, self.offy)
    
class aNode:
    parent=None
    pos=(0,0)
    g=-1
    h=-1
    f=-1
    def __init__(self, pos, g, target):
        self.pos=pos
        self.g=g
        manx=abs(pos[0]-target[0])*11
        many=abs(pos[1]-target[1])*11
        self.h=manx+many
        self.f=self.g+self.h
    def getF(self):
        return g+h
        
        
#def heuristic(start, end): #manhattan style
#    return (abs(start[0]-end[0]), abs(start[1],end[1]))

def aStarPath(startpos, target):
    print("Finding path from ", startpos, "to ", target)
    if not world.isOpen(target):
        print("Unwalkable target")
        return []
    nodes={}
    start=aNode(startpos, 0, target)
    nodes[startpos]=start
    open=[startpos]
    closed=[]
    while open:
        current=nodes[open[0]]
        for i in open:
            if nodes[i].f<current.f:
                current=nodes[i]        #find lowest f cost
        open.remove(current.pos)
        #print "current node's position: ", current.pos
        
        if current.pos==target:
            print("Found target!")
            path=[]
            print("Retracing path")
            while current.pos!=startpos:
                #print "adding ", current.pos
                path.append(current.pos)
                current=current.parent
            print("Path found: ", path)
            for i in path:
                world.getTile(i).setColor((255,255,0))
            return path
            break
            
        world.getTile(current.pos).setColor((255,0,0))
        closed.append(current)
        
        
        x=current.pos[0]
        y=current.pos[1]
        neighbours=[]
        #check if adjecent tiles are walkable
        neighbours.append((x+1,y))
        neighbours.append((x-1,y))
        neighbours.append((x,y+1))
        neighbours.append((x,y-1))
        for n in neighbours:
            if world.isOpen(n)==False:
                #print "Ignoring: ", n, "(tile not open)"
                continue #tile not walkable or it is closed
            elif n in closed:
                #print "Ignoring: ", n, "(tile closed)"
                continue
            elif nodes.has_key(n):
                #node already seen
                nnode=nodes[n]
                if nnode.g>current.g+1:
                    nnode.g=current.g+1
                    nnode.parent=current
            else: #node is walkable and not on any list
                open.append(n) #add node to open list
                world.getTile(n).setColor((0,0,255))
                nodes[n]=aNode(n, current.g+10, target)
                nodes[n].parent=current    
    print("Unable to find path")
    return []

class PathMove:
    pos=(0,0)
    offx=0
    offy=0
    owner=0
    path=[]
    nextpoint=(0,0)
    def __init__(self, owner, path):
        self.owner=owner
        self.setPath(path)
    def setPath(self, path):
        self.path=path
        if path:
            self.nextpoint=self.path.pop()
        #print self.path
    def update(self):
        if not self.path:
            self.offx=self.offy=0
            return
        self.pos=self.owner.getPos()
        if self.nextpoint==self.pos:
            #print "Checkpoint: ", self.nextpoint
            self.nextpoint=self.path.pop()
        self.offx=unitify(self.nextpoint[0]-self.pos[0])
        self.offy=unitify(self.nextpoint[1]-self.pos[1])
    def getOffset(self):
        return (self.offx, self.offy)
            
        

class Player:
    x=0
    y=0
    steptime=.06 #s between steps
    laststep=0 #last step timestamp
    movement=keymove
    def __init__(self):
        self.movement=keymove
        self.laststep=time.time()
        self.x=0 
        self.y=0
        self.tile=Tile()
        self.tile.setColor((255,255,255))
        addGameObject(self)
    def update(self):
        self.movement.update()
        offset=self.movement.getOffset()
#        if world.getTile(newpos).isWalkable():
#            self.setPos(newpos)
        if abs(offset[0])+abs(offset[1])==2: #diagonal move was initiated move one way first
            #try horizontally first
            newpos=(self.x+offset[0], self.y)
            if world.getTile(newpos).isWalkable():
                self.x=newpos[0]
                newpos=(newpos[0], newpos[1]+offset[1])
                if world.getTile(newpos).isWalkable():
                    self.y=newpos[1]
            #same, but try vertically first
            else:
                newpos=(self.x, self.y+offset[1])
                if world.getTile(newpos).isWalkable():
                    self.y=newpos[1]
                    newpos=(newpos[0]+offset[1], newpos[1])
                    if world.getTile(newpos).isWalkable():
                        self.y=newpos[1]
        else:
            newpos=(self.x+offset[0], self.y+offset[1])
            if world.getTile(newpos).isWalkable():
                self.setPos(newpos)
    def setPos(self, pos):
        x = pos[0]
        y = pos[1]
        self.x=x
        self.y=y
    def getPos(self):
        return (self.x, self.y)
    def setColor(self, color):
        self.tile.setColor(color)
    def move(self, dir):
        if(self.laststep+self.steptime>time.time()):
            return
        self.laststep=time.time()
        destx=self.x-(dir==LEFT)+(dir==RIGHT)
        desty=self.y-(dir==UP)+(dir==DOWN)
        if world.getTile((destx
                          ,desty)).isWalkable():
            self.x=destx
            self.y=desty
    def render(self):
        screen.blit(self.tile.surf, camera.getScreen(self.x, self.y))

def update(gameobject):
    gameobject.update()
def render(gameobject):
    gameobject.render()
def addGameObject(object):
    gameObjects.append(object)
def updateGameObjects():
    map(update, gameObjects)
def renderGameObjects():
    map(render, gameObjects)

def spawnEnemy():
    enemy=Player()
    enemy.movement=FollowMove(enemy,player)
    enemy.setPos((randrange(100)-50+player.x, randrange(100)-50+player.y))
    enemy.setColor((255,0,0))
    
player=Player()
    
class Camera:
    camx, camy = 0, 0
    def getScreen(self, x, y): #returns world coordinates in screen coordinates
        x=(x-self.camx)*10+SCREENWIDTH/2
        y=(y-self.camy)*10+SCREENHEIGHT/2
        return (x,y)
    def getWorld(self, screenpos):
        x=(screenpos[0]-SCREENWIDTH/2)/10+self.camx
        y=(screenpos[1]-SCREENHEIGHT/2)/10+self.camy
        return (x,y)
    def set(self, pos):
        self.camx=pos[0]
        self.camy=pos[1]
    def minx(self):
        return self.camx-SCREENWIDTH/20-1
    def miny(self):
        return self.camy-SCREENHEIGHT/20-1
    def maxx(self):
        return self.camx+SCREENWIDTH/20+1
    def maxy(self):
        return self.camy+SCREENHEIGHT/20+1
camera=Camera()
          
class World:
    grid=defaultdict(Tile)
    def __init__(self):
        print("Initializing world")
#        for i in range(80):
#            for j in range(80):
#                self.grid[(i, j)]=Tile() #obsolete, defaultdict creates tiles on the fly
    def getTile(self, pos):
        return self.grid[pos]
    def setTile(self,x,y,type):
        self.getTile(x,y).setType(type)
    def digFour(self, x, y):
        self.getTile((x, y)).setType("Ground")
        self.getTile((x+1, y)).setType("Ground")
        self.getTile((x+1, y+1)).setType("Ground")
        self.getTile((x, y+1)).setType("Ground")
    def createRoom(self):
        for i in range(100):
            for j in range(100):
                self.getTile((i,j)).setType("Ground")
    def randomize(self):
        print("Randomizing world")
    def render(self):
        for i in range(camera.minx(), camera.maxx()):
            for j in range(camera.miny(), camera.maxy()):
                screen.blit(self.getTile((i,j)).surf, camera.getScreen(i,j))
    def reset(self):
        for i in self.grid:
            self.grid[i].setType("Wall")
        makeCave()
    def isOpen(self, pos):
        return self.getTile(pos).isWalkable()

world=World()


def doCave(x=40,y=40, ttl=400):
    world.digFour(x,y)
    if ttl==0:
        return
    if(randrange(100)<1):
        doCave(x+randrange(3)-1, y+randrange(3)-1, ttl/2)
    doCave(x+randrange(3)-1, y+randrange(3)-1, ttl-1)



def makeCave():
    print("Digging cave")
    #doCave()
    dirCave()
    #world.createRoom()
    print("Cave dug")
    
def dirCave(x=.0, y=.0, dir=0.0, ttl=400):
    if ttl==0: return
    world.digFour(int(x), int(y))
    x+=math.cos(dir)
    y+=math.sin(dir)
    dir+=random.random()-.5
    if random.random()<.01:
        dirCave(x,y, dir+PI/2, ttl-1)
    if random.random()<.005:
        #print "diggin undercave"
        doCave(int(x),int(y), 400)
    dirCave(x, y, dir, ttl-1)

clock = pygame.time.Clock()
def main():
    makeCave()
    
    map(spawnEnemy(), range(5))
    
    player.setPos((5,5))
    player.movement=PathMove(player, [])
    player.setColor((0,255,0))
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
                elif event.key == K_SPACE:
                    world.randomize()
                elif event.key == K_RETURN:
                    world.reset()
#                elif event.key == K_LEFT:
#                    player.move(LEFT)
#                elif event.key == K_RIGHT:
#                    player.move(RIGHT)
#                elif event.key == K_UP:
#                    player.move(UP)
#                elif event.key == K_DOWN:
#                    player.move(DOWN)
                    
            elif event.type == MOUSEBUTTONDOWN:
                if event.button==LEFT:
                    1
                elif event.button==RIGHT:
                    target=camera.getWorld(pygame.mouse.get_pos())
                    path=aStarPath(player.getPos(), target)
                    player.movement.setPath(path)
#            elif event.type == MOUSEBUTTONUP:
        
        #screen.blit(background, (0, 0))
        
        if mouse.get_pressed()[2]:
            world.getTile(camera.getWorld(pygame.mouse.get_pos())).setType("Ground")
        if mouse.get_pressed()[0]:
            mousepos=camera.getWorld(pygame.mouse.get_pos())
            world.digFour(mousepos[0], mousepos[1])
        
        key=pygame.key.get_pressed()
        
        
        updateGameObjects()
        camera.set(player.getPos())
        
        #drawing here
        world.render()
        renderGameObjects()  
        
        
        pygame.display.flip()
        clock.tick(60)
    pygame.display.quit()
    pygame.quit()
main()
