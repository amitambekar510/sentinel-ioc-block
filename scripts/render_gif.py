from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
out=Path("assets/ioc-workflow.gif")
out.parent.mkdir(exist_ok=True)
stages=["SOURCE REVIEW","VALIDATION","BUSINESS EXCLUSIONS","HUMAN APPROVAL","AUDIT EVIDENCE"]
frames=[]
for i,stage in enumerate(stages):
 im=Image.new("RGB",(1000,340),"#0b2032")
 d=ImageDraw.Draw(im)
 d.rounded_rectangle((20,20,980,320),radius=20,fill="#17384a",outline="#4fd9bc",width=3)
 d.text((55,58),"SENTINEL IOC BLOCK 2.0",fill="#6ae8d0",stroke_width=0)
 d.text((55,110),f"STEP {i+1}: {stage}",fill="white",stroke_width=0)
 for j,name in enumerate(stages):
  x=55+j*184
  d.rounded_rectangle((x,180,x+166,234),radius=10,fill="#40cbb0" if j<=i else "#35566a")
  d.text((x+12,199),name[:18],fill="#0b2032" if j<=i else "white")
 d.text((55,273),"ILLUSTRATIVE WORKFLOW • OBSERVE FIRST • NO LIVE FIREWALL CHANGES",fill="#b7d1de")
 frames.append(im)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=1100,loop=0,optimize=True)
assert Image.open(out).n_frames==5
