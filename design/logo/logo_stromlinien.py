# Logo/Icons aus dem Breva-Satellitenmittel (app/img/breva_mittel.png) + Uferlinie Natural Earth (ne_10m_lakes_europe.geojson, nicht im Repo).
# Variante: Stromlinien nördlich von Bellagio, Pfeilspitzen zufällig verteilt (seed=1, spacing=24).
import json, numpy as np, math
from PIL import Image
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, PathPatch
from scipy.ndimage import gaussian_filter, map_coordinates
G=json.load(open("ne_10m_lakes_europe.geojson"))
poly=[f for f in G["features"] if f["properties"].get("name")=="Lago di Como"][0]["geometry"]["coordinates"][0]
P=np.array(poly)
def chaikin(c,n=3):
    for _ in range(n):
        q=0.75*c[:-1]+0.25*c[1:]; r=0.25*c[:-1]+0.75*c[1:]
        c=np.empty((2*len(q),2)); c[0::2]=q; c[1::2]=r; c=np.vstack([c,c[:1]])
    return c
P=chaikin(np.vstack([P,P[:1]]),3)
k=math.cos(math.radians(46))
# Pixelraster in lon/lat
lo0,lo1,la0,la1=P[:,0].min()-0.01,P[:,0].max()+0.01,P[:,1].min()-0.01,P[:,1].max()+0.01
R=900; H=R; W=int(R*(lo1-lo0)*k/(la1-la0))
lon=np.linspace(lo0,lo1,W); lat=np.linspace(la1,la0,H)
LON,LAT=np.meshgrid(lon,lat)
m=Path(P).contains_points(np.c_[LON.ravel(),LAT.ravel()]).reshape(H,W)
# Satellitenwind (Breva-Mittel) auf das Raster
STOPS=[(0,(59,111,209)),(6,(47,163,224)),(10,(54,195,192)),(14,(242,211,59)),(18,(245,130,44)),(22,(224,54,42)),(28,(163,22,95))]
def color(kn):
    kn=np.clip(kn,0,28); out=np.zeros(kn.shape+(3,))
    for (a,ca),(b,cb) in zip(STOPS[:-1],STOPS[1:]):
        mm=(kn>=a)&(kn<=b); f=((kn-a)/(b-a))[mm][:,None]; out[mm]=np.array(ca)*(1-f)+np.array(cb)*f
    return out
im=np.array(Image.open("/home/claude/wind-como/app/img/breva_mittel.png").convert("RGBA")).astype(float)
sm=im[...,3]>0; grid=np.linspace(0,28,561); cols=color(grid)
px=im[sm][:,:3]; kn=np.full(sm.shape,np.nan); kn[sm]=grid[((px[:,None]-cols[None])**2).sum(-1).argmin(1)]
B=[9.2,45.96,9.46,46.2]; h,w=kn.shape
filled=np.where(sm,kn,np.nan)
# Lücken füllen (Ufer) per gewichteter Glättung
v=np.nan_to_num(filled); wt=sm.astype(float)
filled=gaussian_filter(v,3)/np.maximum(gaussian_filter(wt,3),1e-6)
r=(B[3]-LAT)/(B[3]-B[1])*(h-1); c=(LON-B[0])/(B[2]-B[0])*(w-1)
inside=(r>=0)&(r<=h-1)&(c>=0)&(c<=w-1)
spd=np.where(inside, map_coordinates(filled,[r.clip(0,h-1),c.clip(0,w-1)],order=1), np.nan)
spd=gaussian_filter(np.nan_to_num(spd,nan=8),4)
# Richtung entlang der Seeachse, nach Norden
f=gaussian_filter(m.astype(float),10); gy,gx=np.gradient(f); s=26
Jxx=gaussian_filter(gx*gx,s); Jyy=gaussian_filter(gy*gy,s); Jxy=gaussian_filter(gx*gy,s)
th=0.5*np.arctan2(2*Jxy,Jxx-Jyy)+np.pi/2; u=np.cos(th); vv=np.sin(th); fl=vv>0; u[fl]*=-1; vv[fl]*=-1
# nur nördlich von Bellagio Linien, nach Süden ausblenden
N_ONLY = LAT>45.975
cm=LinearSegmentedColormap.from_list("b",["#0e5f7d","#1590a3","#2cc0b4","#9be3b0","#ffd25a","#ff9e40"])
NAVY="#07222e"; LAKE="#1f5f78"
def make(fn, density=2.2, lw_scale=3.2, bg=True, size=512, seed=1, spacing=26, frac=470/512, radius=112, arrows=True, lakeboost=1.0, ascale=1.35):
    fig=plt.figure(figsize=(5.12,5.12),dpi=size/5.12); ax=fig.add_axes([0,0,1,1]); ax.axis("off"); fig.patch.set_alpha(0)
    sc=frac*512/H; ox=(512-W*sc)/2; oy=(512-H*sc)/2
    if bg: ax.add_patch(FancyBboxPatch((0,0),512,512,boxstyle=f"round,pad=0,rounding_size={max(radius,0.01)}",fc=NAVY,ec="none",zorder=-5))
    xy=np.c_[ox+(P[:,0]-lo0)/(lo1-lo0)*W*sc, oy+(la1-P[:,1])/(la1-la0)*H*sc]
    lakepath=Path(xy)
    if lakeboost!=1.0:
        ax.add_patch(PathPatch(lakepath,fc=LAKE,ec=LAKE,lw=lakeboost,zorder=0))
    else:
        ax.add_patch(PathPatch(lakepath,fc=LAKE,ec="none",zorder=0))
    X=ox+np.arange(W)*sc; Y=oy+np.arange(H)*sc
    ok=m&N_ONLY
    U=np.where(ok,u,np.nan); V=np.where(ok,vv,np.nan); S=np.where(ok,spd,np.nan)
    sp=ax.streamplot(X,Y,U,V,color=S,cmap=cm,norm=plt.Normalize(6,17),density=density,
                  linewidth=np.nan_to_num(np.clip(S-4,1,14)/lw_scale,nan=0.6),arrowsize=0,
                  broken_streamlines=True,minlength=0.15,zorder=2)
    for p in list(ax.patches):
        if p.__class__.__name__=="FancyArrowPatch": p.remove()
    sp.lines.set_capstyle("round"); sp.lines.set_joinstyle("round")
    segs=sp.lines.get_segments(); vals=sp.lines.get_array(); lws=sp.lines.get_linewidths()
    rng=np.random.default_rng(seed); order=rng.permutation(len(segs)); acc=[]
    for i in order:
        sg=segs[i]; (x0,y0),(x1,y1)=sg[0],sg[-1]; d=math.hypot(x1-x0,y1-y0)
        if d<1e-3 or np.isnan(vals[i]): continue
        mx,my=(x0+x1)/2,(y0+y1)/2
        if any((mx-a)**2+(my-b)**2<spacing**2 for a,b in acc): continue
        if rng.random()>0.55 or not arrows: continue
        if not lakepath.contains_point((mx+9*math.cos(math.atan2(y1-y0,x1-x0)),my+9*math.sin(math.atan2(y1-y0,x1-x0)))): continue
        acc.append((mx,my)); a=math.atan2(y1-y0,x1-x0); lw=lws[i%len(lws)]; L=(8+lw*2.6)*ascale
        tip=(mx+L*0.6*math.cos(a),my+L*0.6*math.sin(a))
        b1=(mx-L*0.4*math.cos(a)+L*0.45*math.cos(a+math.pi/2),my-L*0.4*math.sin(a)+L*0.45*math.sin(a+math.pi/2))
        b2=(mx-L*0.4*math.cos(a)-L*0.45*math.cos(a+math.pi/2),my-L*0.4*math.sin(a)-L*0.45*math.sin(a+math.pi/2))
        ax.add_patch(plt.Polygon([tip,b1,b2],closed=True,fc=cm(plt.Normalize(6,17)(vals[i])),ec="none",zorder=3))
    ax.set_xlim(0,512); ax.set_ylim(512,0)
    fig.savefig(fn,transparent=True); plt.close(fig)

import os; os.makedirs("final",exist_ok=True)
from PIL import Image as I
make("final/big.png",3.2,4.2,seed=1,spacing=24,size=1024)
I.open("final/big.png").resize((512,512),I.LANCZOS).save("final/icon-512.png")
I.open("final/big.png").resize((192,192),I.LANCZOS).save("final/icon-192.png")
make("final/maskbig.png",3.2,4.2,seed=1,spacing=24,size=1024,frac=0.74,radius=0)
I.open("final/maskbig.png").resize((512,512),I.LANCZOS).save("final/icon-maskable-512.png")
make("final/smallbig.png",1.3,1.6,seed=1,spacing=80,size=512,frac=0.96,radius=90,lakeboost=10)
for n in (96,64,32): I.open("final/smallbig.png").resize((n,n),I.LANCZOS).save(f"final/icon-{n}.png")
