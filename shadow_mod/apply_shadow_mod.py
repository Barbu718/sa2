#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "shadow_mod" / "shadow_atlas.png"
OBJ_ROOT = ROOT / "graphics" / "sa2" / "obj_tiles" / "4bpp"
ANIM_C = ROOT / "src" / "data" / "sa2" / "animations" / "animations.c"
CHAR_SELECT_C = ROOT / "src" / "game" / "sa2" / "ui" / "character_select.c"
AMY_ANIM_BASE = 364
AMY_ANIM_COUNT = 91
ATLAS_CELL = 64
ATLAS_COLS = 10
ATLAS_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 19, 20, 21, 35, 36, 37, 38, 39, 40, 41, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 69, 70, 71, 72, 73, 74, 83, 84, 94, 95, 96, 97, 99, 101, 102, 103, 104, 105, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 138, 140, 144, 145, 147, 148, 154, 155, 183, 184, 187, 188, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218]
ATLAS_SLOT = {orig: n for n, orig in enumerate(ATLAS_IDS)}

ACTION_COMPONENTS = {
    0:[0,1,2,3,4,5,6],1:[15,16,17,18,19,20,21],2:[83,84],3:list(range(117,129)),
    4:[99,101,102,103,104,105],5:list(range(52,64)),6:list(range(52,64)),7:[69,70,71,72,73,74],
    8:[69,70,71,72,73,74],9:list(range(52,64)),10:[99,101,102,103,104,105],11:[101,102,103,104,105,99],
    12:[83,84,0],13:[94,95,96,97],14:[138,140,145],15:[145,147,148,155,183,184],16:[183,184,187,188],
    17:[147,148,155],18:[147,148,155],19:[94,95,96,97],20:[94,95,96,97],21:[94,95,96,97],22:[94,95,96,97],
    23:[94,95,96,97],24:[94,95,96,97],28:[145,154,155],29:[144,154],30:[0,1,2],31:[69,70,71,72,73,74],
    32:list(range(209,219)),33:[0,1],34:[0,1],35:[0,1],36:[15,16,17],37:[15,16,17],38:[15,16,17],39:[15,16,17],
    40:[0,1],41:[0,1],42:[0,1],43:[0,1],44:[0,1],45:[0,1],46:[0,1],47:[0,1],48:[94,95,96,97],
    49:[145,147,148,155,183,184,187,188],50:[94,95,96,97],51:[99,101,102,103,104,105],52:[145,147,148],
    53:[145,147,148],54:[145,147,148],55:[35,36,37,38,39,40,41],56:[94,95,96,97],57:[94,95,96,97],
    58:[99,101,102,103,104,105],59:[95,96,97],60:[95,96,97],61:[95,96,97],62:[99,101,102,103,104,105],
    63:[99,101,102,103,104,105],64:[99,101,102,103,104,105],65:[94,95,96,97],66:[94,95,96,97],
    67:[94,95,96,97],68:list(range(52,64)),69:[94,95,96,97],70:[94,95,96,97],71:[94,95,96,97],72:[94,95,96,97],
    73:[94,95,96,97],75:list(range(52,64)),80:[0,1],87:[0,1],
}

CENTER_ACTIONS={3,4,10,11,13,15,16,17,18,28,29,48,49,50,51,56,57,58,59,60,61,62,63,64,65,66,67,69,70,71,72,73}

def get_component(atlas:Image.Image, original_id:int)->Image.Image:
    n=ATLAS_SLOT[original_id]
    x=(n%ATLAS_COLS)*ATLAS_CELL; y=(n//ATLAS_COLS)*ATLAS_CELL
    cell=atlas.crop((x,y,x+ATLAS_CELL,y+ATLAS_CELL)).convert("RGBA")
    box=cell.getbbox()
    return cell.crop(box) if box else cell

def fit_sprite(src:Image.Image,size:tuple[int,int],anchor:str="bottom")->Image.Image:
    tw,th=size; src=src.convert("RGBA")
    scale=min(1.0,(tw-2)/max(1,src.width),(th-2)/max(1,src.height))
    if scale<1:
        src=src.resize((max(1,int(src.width*scale)),max(1,int(src.height*scale))),Image.Resampling.NEAREST)
    out=Image.new("RGBA",size,(0,0,0,0)); x=(tw-src.width)//2
    y=(th-src.height)//2 if anchor=="center" else th-src.height
    out.alpha_composite(src,(x,y)); return out

def save_using_original_palette(path:Path,rgba:Image.Image)->None:
    original=Image.open(path)
    if original.mode!="P" or original.getpalette() is None:
        rgba.save(path); return
    pal=original.getpalette(); trans=original.info.get("transparency",0)
    if not isinstance(trans,int): trans=0
    colors=[tuple(pal[i*3:i*3+3]) for i in range(256)]; candidates=[i for i in range(16) if i!=trans]
    out=Image.new("P",original.size); out.putpalette(pal); cache={}; dst=[]
    for r,g,b,a in rgba.convert("RGBA").getdata():
        if a<128: dst.append(trans); continue
        key=(r,g,b)
        if key not in cache:
            cache[key]=min(candidates,key=lambda i:(colors[i][0]-r)**2+(colors[i][1]-g)**2+(colors[i][2]-b)**2)
        dst.append(cache[key])
    out.putdata(dst); out.save(path,transparency=trans)

def source_sequence_for(offset:int)->list[int]:
    if offset in ACTION_COMPONENTS: return ACTION_COMPONENTS[offset]
    if 5<=offset<=9: return list(range(52,64))
    if 10<=offset<=18: return [99,101,102,103,104,105]
    return [0,1,2]

def replace_amy_gameplay(atlas:Image.Image)->None:
    replaced=0
    for offset in range(AMY_ANIM_COUNT):
        if offset==74: continue
        d=OBJ_ROOT/f"anim_{AMY_ANIM_BASE+offset:04d}"
        if not d.is_dir(): continue
        frames=sorted(d.glob("f*.png"))
        if not frames: continue
        srcs=[get_component(atlas,i) for i in source_sequence_for(offset)]
        anchor="center" if offset in CENTER_ACTIONS else "bottom"
        for n,path in enumerate(frames):
            save_using_original_palette(path,fit_sprite(srcs[n%len(srcs)],Image.open(path).size,anchor)); replaced+=1
    print(f"replaced {replaced} Amy gameplay frame PNGs")

def variant_frame_ids(anim_id:int,variant:int)->list[int]:
    text=ANIM_C.read_text()
    pat=re.compile(rf"const s32 anim_{anim_id:04d}__v{variant}(?:_l\d+)?\[\]\s*=\s*\{{(.*?)\n\}};",re.S)
    ids=[]
    for body in pat.findall(text):
        for m in re.finditer(r"SHOW_FRAME\([^,]+,\s*(\d+)\)",body):
            v=int(m.group(1))
            if v not in ids: ids.append(v)
    return ids

def draw_text(size:tuple[int,int],text:str,red=False)->Image.Image:
    font=ImageFont.load_default(); scratch=Image.new("RGBA",(512,80),(0,0,0,0)); d=ImageDraw.Draw(scratch)
    d.text((4,4),text,font=font,fill=(235,40,55,255) if red else (255,255,255,255),stroke_width=1,stroke_fill=(15,15,20,255))
    box=scratch.getbbox()
    if not box: return Image.new("RGBA",size,(0,0,0,0))
    glyph=scratch.crop(box); tw,th=size; scale=1
    while glyph.width*(scale+1)<=tw-2 and glyph.height*(scale+1)<=th-2: scale+=1
    glyph=glyph.resize((glyph.width*scale,glyph.height*scale),Image.Resampling.NEAREST)
    out=Image.new("RGBA",size,(0,0,0,0)); out.alpha_composite(glyph,((tw-glyph.width)//2,(th-glyph.height)//2)); return out

def replace_variant_with_art(anim_id:int,variants:Iterable[int],ids:list[int],atlas:Image.Image)->None:
    d=OBJ_ROOT/f"anim_{anim_id:04d}"
    if not d.is_dir(): return
    srcs=[get_component(atlas,i) for i in ids]
    for variant in variants:
        for n,fid in enumerate(variant_frame_ids(anim_id,variant)):
            p=d/f"f{fid:03d}.png"
            if p.exists(): save_using_original_palette(p,fit_sprite(srcs[n%len(srcs)],Image.open(p).size,"bottom"))

def replace_variant_with_text(anim_id:int,variants:Iterable[int],text:str,red=False)->None:
    d=OBJ_ROOT/f"anim_{anim_id:04d}"
    if not d.is_dir(): return
    for variant in variants:
        for fid in variant_frame_ids(anim_id,variant):
            p=d/f"f{fid:03d}.png"
            if p.exists(): save_using_original_palette(p,draw_text(Image.open(p).size,text,red))

def patch_character_select_source()->None:
    text=CHAR_SELECT_C.read_text(); marker="    lang = LOADED_SAVE->language - 1;"
    if "SHADOW MOD: always expose fifth slot" not in text:
        text=text.replace(marker,"    // SHADOW MOD: always expose fifth slot (repurposed Amy slot).\n    allUnlocked = TRUE;\n"+marker,1)
    text=text.replace("    characterScreen->availableCharacters = LOADED_SAVE->unlockedCharacters;","    characterScreen->availableCharacters = LOADED_SAVE->unlockedCharacters | CHARACTER_BIT(CHARACTER_AMY);",1)
    text=text.replace("        m4aSongNumStart(gCharacterAnnouncements[characterScreen->selectedCharacter]);","        // SHADOW MOD: no stock Shadow announcer sample.\n        if (characterScreen->selectedCharacter != CHARACTER_AMY) {\n            m4aSongNumStart(gCharacterAnnouncements[characterScreen->selectedCharacter]);\n        }",1)
    CHAR_SELECT_C.write_text(text)

def patch_character_select_graphics(atlas:Image.Image)->None:
    replace_variant_with_art(736,[8,9],[7,8],atlas)
    replace_variant_with_text(739,[6,7],"SHADOW",True)
    replace_variant_with_text(741,[4],"SHADOW",False)
    replace_variant_with_text(747,[4],"SHADOW THE HEDGEHOG",False)

def main()->None:
    atlas=Image.open(ATLAS).convert("RGBA")
    patch_character_select_source(); replace_amy_gameplay(atlas); patch_character_select_graphics(atlas)
    print("Shadow native GBA patch applied; Amy slot is now Shadow.")

if __name__=="__main__": main()
